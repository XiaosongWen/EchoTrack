#!/usr/bin/env bash
# deploy-cloudrun.sh — Build the backend image, push to Artifact Registry,
# and deploy to Google Cloud Run.
#
# Usage:
#   ./scripts/deploy-cloudrun.sh [IMAGE_TAG]
#
# Required env vars (or set them in your shell before running):
#   GCP_PROJECT_ID     — GCP project id (e.g. my-project-123)
#   GCP_REGION         — Cloud Run region (default: us-central1)
#   AR_REPOSITORY      — Artifact Registry repo name (default: echotrack)
#   CORS_ORIGINS       — Comma-separated allowed frontend URLs
#                        (e.g. https://echotrack.pages.dev)
#
# The script uses Application Default Credentials (ADC).
# Run `gcloud auth application-default login` once to set up ADC locally.
# In CI, use Workload Identity Federation or a service account key.

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
GCP_PROJECT_ID="${GCP_PROJECT_ID:?GCP_PROJECT_ID is required}"
GCP_REGION="${GCP_REGION:-us-central1}"
AR_REPOSITORY="${AR_REPOSITORY:-echotrack}"
IMAGE_TAG="${1:-$(git rev-parse --short HEAD)}"
SERVICE_NAME="echotrack-backend"
SERVICE_YAML="$(dirname "$0")/../infra/cloudrun/service.yaml"

AR_HOST="${GCP_REGION}-docker.pkg.dev"
FULL_IMAGE="${AR_HOST}/${GCP_PROJECT_ID}/${AR_REPOSITORY}/${SERVICE_NAME}:${IMAGE_TAG}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}/.."

echo "=========================================="
echo "  EchoTrack Cloud Run Deployment"
echo "  Image : ${FULL_IMAGE}"
echo "  Region: ${GCP_REGION}"
echo "=========================================="

# ── Authenticate Docker with Artifact Registry ────────────────────────────────
echo "[1/4] Configuring Docker for Artifact Registry..."
gcloud auth configure-docker "${AR_HOST}" --quiet

# ── Build the backend image ───────────────────────────────────────────────────
echo "[2/4] Building backend Docker image..."
docker build \
  -t "${FULL_IMAGE}" \
  -f "${REPO_ROOT}/backend/Dockerfile" \
  "${REPO_ROOT}/backend"

# ── Push to Artifact Registry ─────────────────────────────────────────────────
echo "[3/4] Pushing image to Artifact Registry..."
docker push "${FULL_IMAGE}"

# ── Deploy to Cloud Run ───────────────────────────────────────────────────────
echo "[4/4] Deploying to Cloud Run..."
# Substitute the IMAGE_PLACEHOLDER in service.yaml with the real image reference,
# then pipe to `gcloud run services replace` for a declarative deployment.
sed "s|IMAGE_PLACEHOLDER|${FULL_IMAGE}|g" "${SERVICE_YAML}" \
  | gcloud run services replace - \
      --region="${GCP_REGION}" \
      --project="${GCP_PROJECT_ID}"

# Set CORS_ORIGINS env var if provided (safe to run even if empty)
if [ -n "${CORS_ORIGINS:-}" ]; then
  echo "Updating CORS_ORIGINS on Cloud Run service..."
  gcloud run services update "${SERVICE_NAME}" \
    --region="${GCP_REGION}" \
    --project="${GCP_PROJECT_ID}" \
    --update-env-vars "CORS_ORIGINS=${CORS_ORIGINS}"
fi

# Make the service publicly accessible (unauthenticated at network level;
# app-level auth is enforced via Supabase JWT).
gcloud run services add-iam-policy-binding "${SERVICE_NAME}" \
  --region="${GCP_REGION}" \
  --project="${GCP_PROJECT_ID}" \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --quiet || true  # idempotent — ignore if binding already exists

SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region="${GCP_REGION}" \
  --project="${GCP_PROJECT_ID}" \
  --format="value(status.url)")

echo ""
echo "=========================================="
echo "  Deployment complete!"
echo "  Service URL: ${SERVICE_URL}"
echo "  Health check: ${SERVICE_URL}/api/v1/health"
echo "=========================================="
