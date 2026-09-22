#!/usr/bin/env bash
# gcp-setup.sh — One-time GCP project bootstrap for EchoTrack Cloud Run.
#
# Usage:
#   GCP_PROJECT_ID=my-project-123 ./scripts/gcp-setup.sh
#
# What this script does:
#   1. Enables required GCP APIs
#   2. Creates an Artifact Registry repository
#   3. Creates GCP Secret Manager secrets (values must be set separately)
#   4. Creates a Cloud Run service account with minimum required permissions
#   5. Configures Workload Identity Federation for GitHub Actions (keyless CI)
#
# Prerequisites: gcloud CLI installed and authenticated as a project owner.

set -euo pipefail

GCP_PROJECT_ID="${GCP_PROJECT_ID:?GCP_PROJECT_ID is required}"
GCP_REGION="${GCP_REGION:-us-central1}"
AR_REPOSITORY="${AR_REPOSITORY:-echotrack}"
SERVICE_ACCOUNT_NAME="echotrack-cloudrun"
GITHUB_REPO="${GITHUB_REPO:-XiaosongWen/EchoTrack}"  # owner/repo

SA_EMAIL="${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
WIF_POOL="echotrack-github-pool"
WIF_PROVIDER="echotrack-github-provider"

echo "=========================================="
echo "  EchoTrack GCP Bootstrap"
echo "  Project: ${GCP_PROJECT_ID}"
echo "  Region : ${GCP_REGION}"
echo "=========================================="

# ── 1. Enable APIs ────────────────────────────────────────────────────────────
echo "[1/5] Enabling GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  --project="${GCP_PROJECT_ID}"

# ── 2. Create Artifact Registry repository ────────────────────────────────────
echo "[2/5] Creating Artifact Registry repository..."
gcloud artifacts repositories create "${AR_REPOSITORY}" \
  --repository-format=docker \
  --location="${GCP_REGION}" \
  --description="EchoTrack container images" \
  --project="${GCP_PROJECT_ID}" \
  2>/dev/null || echo "  Repository already exists, skipping."

# ── 3. Create Secret Manager secrets (empty — values set separately) ──────────
echo "[3/5] Creating Secret Manager secrets..."
for SECRET_NAME in \
  echotrack-database-url \
  echotrack-supabase-url \
  echotrack-supabase-publishable-key \
  echotrack-supabase-secret-key \
  echotrack-supabase-jwt-secret; do
  gcloud secrets create "${SECRET_NAME}" \
    --replication-policy="automatic" \
    --project="${GCP_PROJECT_ID}" \
    2>/dev/null || echo "  Secret ${SECRET_NAME} already exists, skipping."
done

echo ""
echo "  *** ACTION REQUIRED: populate each secret with its value: ***"
echo "  echo -n 'postgresql+asyncpg://...' | gcloud secrets versions add echotrack-database-url --data-file=- --project=${GCP_PROJECT_ID}"
echo "  (repeat for all secrets above)"
echo ""

# ── 4. Create Cloud Run service account ───────────────────────────────────────
echo "[4/5] Creating Cloud Run service account..."
gcloud iam service-accounts create "${SERVICE_ACCOUNT_NAME}" \
  --display-name="EchoTrack Cloud Run SA" \
  --project="${GCP_PROJECT_ID}" \
  2>/dev/null || echo "  Service account already exists, skipping."

# Grant the SA permission to access secrets
gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor" \
  --condition=None

# Grant Artifact Registry reader (to pull its own image at startup)
gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/artifactregistry.reader" \
  --condition=None

# ── 5. Workload Identity Federation for keyless GitHub Actions ────────────────
echo "[5/5] Configuring Workload Identity Federation for GitHub Actions..."

# Create WIF pool
gcloud iam workload-identity-pools create "${WIF_POOL}" \
  --location="global" \
  --display-name="EchoTrack GitHub pool" \
  --project="${GCP_PROJECT_ID}" \
  2>/dev/null || echo "  WIF pool already exists, skipping."

# Create OIDC provider
gcloud iam workload-identity-pools providers create-oidc "${WIF_PROVIDER}" \
  --workload-identity-pool="${WIF_POOL}" \
  --location="global" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="attribute.repository=='${GITHUB_REPO}'" \
  --project="${GCP_PROJECT_ID}" \
  2>/dev/null || echo "  WIF provider already exists, skipping."

WIF_POOL_RESOURCE=$(gcloud iam workload-identity-pools describe "${WIF_POOL}" \
  --location="global" \
  --project="${GCP_PROJECT_ID}" \
  --format="value(name)")

# Allow the GitHub repo to impersonate the service account
gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${WIF_POOL_RESOURCE}/attribute.repository/${GITHUB_REPO}" \
  --project="${GCP_PROJECT_ID}"

# Grant the SA permissions to deploy to Cloud Run
gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.admin" \
  --condition=None

gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/iam.serviceAccountUser" \
  --condition=None

gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/artifactregistry.writer" \
  --condition=None

PROVIDER_RESOURCE=$(gcloud iam workload-identity-pools providers describe "${WIF_PROVIDER}" \
  --workload-identity-pool="${WIF_POOL}" \
  --location="global" \
  --project="${GCP_PROJECT_ID}" \
  --format="value(name)")

echo ""
echo "=========================================="
echo "  Bootstrap complete!"
echo ""
echo "  Add these secrets to your GitHub repo"
echo "  (Settings → Secrets → Actions):"
echo ""
echo "  GCP_PROJECT_ID               = ${GCP_PROJECT_ID}"
echo "  GCP_WORKLOAD_IDENTITY_PROVIDER = ${PROVIDER_RESOURCE}"
echo "  GCP_SERVICE_ACCOUNT          = ${SA_EMAIL}"
echo "  CORS_ORIGINS                 = https://<your-cloudflare-pages-url>"
echo "=========================================="
