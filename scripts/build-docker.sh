#!/usr/bin/env bash
set -e

# Default Docker Hub username / repository namespace (override via DOCKERHUB_USERNAME env var)
DEFAULT_DOCKERHUB_USERNAME="${DOCKERHUB_USERNAME:-tomaswen}"

INPUT_NAME=${1:-"echotrack"}
IMAGE_TAG=${2:-"latest"}
PUSH_FLAG=${3:-"--no-push"}

# Prepend Docker Hub username if not already included in INPUT_NAME
if [[ "${INPUT_NAME}" != *"/"* ]]; then
    FULL_IMAGE="${DEFAULT_DOCKERHUB_USERNAME}/${INPUT_NAME}:${IMAGE_TAG}"
else
    FULL_IMAGE="${INPUT_NAME}:${IMAGE_TAG}"
fi

echo "=========================================="
echo "Building Unified Docker Image: ${FULL_IMAGE}"
echo "=========================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="${SCRIPT_DIR}/.."

docker build -t "${FULL_IMAGE}" -f "${REPO_ROOT}/Dockerfile" "${REPO_ROOT}"

echo "=========================================="
echo "Successfully built ${FULL_IMAGE}"
echo "=========================================="

if [ "${PUSH_FLAG}" = "--push" ] || [ "${PUSH_FLAG}" = "-p" ]; then
    echo "=========================================="
    echo "Pushing Docker Image: ${FULL_IMAGE}"
    echo "=========================================="
    docker push "${FULL_IMAGE}"
    echo "=========================================="
    echo "Successfully pushed ${FULL_IMAGE}"
    echo "=========================================="
fi
