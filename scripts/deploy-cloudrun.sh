#!/usr/bin/env bash
# deploy-cloudrun.sh — Build the backend image, push to Docker Hub,
# and deploy to Google Cloud Run.
#
# Usage:
#   ./scripts/deploy-cloudrun.sh [IMAGE_TAG]
#
# Required env vars (or set them in your shell before running):
#   DOCKERHUB_USERNAME — Docker Hub username (default: tomaswen)
#   GCP_PROJECT_ID     — GCP project id (e.g. my-project-123)
#   GCP_REGION         — Cloud Run region (default: us-central1)
#   CORS_ORIGINS       — Comma-separated allowed frontend URLs
#                        (e.g. https://echotrack.pages.dev)
#
# The script uses Application Default Credentials (ADC) for GCP.
# Run `gcloud auth application-default login` once to set up ADC locally.
# Docker Hub login uses your local `docker login` session.

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
DOCKERHUB_USERNAME="${DOCKERHUB_USERNAME:-tomaswen}"
GCP_PROJECT_ID="${GCP_PROJECT_ID:?GCP_PROJECT_ID is required}"
GCP_REGION="${GCP_REGION:-us-central1}"
IMAGE_TAG="${1:-$(git rev-parse --short HEAD)}"
SERVICE_NAME="echotrack-backend"
SERVICE_YAML="$(dirname "$0")/../infra/cloudrun/service.yaml"

FULL_IMAGE="${DOCKERHUB_USERNAME}/${SERVICE_NAME}:${IMAGE_TAG}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}/.."

echo "=========================================="
echo "  EchoTrack Cloud Run Deployment"
echo "  Image : ${FULL_IMAGE}"
echo "  Region: ${GCP_REGION}"
echo "=========================================="

# ── Build the backend image ───────────────────────────────────────────────────
echo "[1/3] Building backend Docker image..."
docker build \
  -t "${FULL_IMAGE}" \
  -f "${REPO_ROOT}/backend/Dockerfile" \
  "${REPO_ROOT}/backend"

# ── Push to Docker Hub ────────────────────────────────────────────────────────
echo "[2/3] Pushing image to Docker Hub..."
docker push "${FULL_IMAGE}"

# ── Deploy to Cloud Run ───────────────────────────────────────────────────────
echo "[3/3] Deploying to Cloud Run..."
sed "s|IMAGE_PLACEHOLDER|${FULL_IMAGE}|g" "${SERVICE_YAML}" \
  | gcloud run services replace - \
      --region="${GCP_REGION}" \
      --project="${GCP_PROJECT_ID}"

# Set CORS_ORIGINS env var if provided
if [ -n "${CORS_ORIGINS:-}" ]; then
  echo "Updating CORS_ORIGINS on Cloud Run service..."
  gcloud run services update "${SERVICE_NAME}" \
    --region="${GCP_REGION}" \
    --project="${GCP_PROJECT_ID}" \
    --update-env-vars "CORS_ORIGINS=${CORS_ORIGINS}"
fi

# Make the service publicly accessible
gcloud run services add-iam-policy-binding "${SERVICE_NAME}" \
  --region="${GCP_REGION}" \
  --project="${GCP_PROJECT_ID}" \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --quiet || true  # idempotent

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
