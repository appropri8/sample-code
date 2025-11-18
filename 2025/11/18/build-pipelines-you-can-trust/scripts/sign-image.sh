#!/bin/bash
set -e

IMAGE_NAME="${1}"
KEYLESS="${2:-true}"

if [ -z "$IMAGE_NAME" ]; then
  echo "Usage: $0 <image-name> [keyless=true]"
  echo "Example: $0 ghcr.io/user/app:v1.0.0"
  exit 1
fi

echo "Signing image: $IMAGE_NAME"

# Check if Cosign is installed
if ! command -v cosign &> /dev/null; then
  echo "Error: Cosign is not installed"
  echo "Install from: https://github.com/sigstore/cosign"
  exit 1
fi

if [ "$KEYLESS" = "true" ]; then
  echo "Using keyless signing (OIDC)..."
  export COSIGN_EXPERIMENTAL=1
  cosign sign "$IMAGE_NAME"
else
  echo "Using key-based signing..."
  if [ -z "$COSIGN_KEY_PATH" ] || [ -z "$COSIGN_PASSWORD" ]; then
    echo "Error: COSIGN_KEY_PATH and COSIGN_PASSWORD must be set for key-based signing"
    exit 1
  fi
  cosign sign --key "$COSIGN_KEY_PATH" "$IMAGE_NAME"
fi

echo "Image signed successfully: $IMAGE_NAME"

