#!/bin/bash
set -e

IMAGE_NAME="${1}"
OIDC_ISSUER="${2:-https://token.actions.githubusercontent.com}"

if [ -z "$IMAGE_NAME" ]; then
  echo "Usage: $0 <image-name> [oidc-issuer]"
  echo "Example: $0 ghcr.io/user/app:v1.0.0"
  exit 1
fi

echo "Verifying signature for image: $IMAGE_NAME"
echo "OIDC Issuer: $OIDC_ISSUER"

# Check if Cosign is installed
if ! command -v cosign &> /dev/null; then
  echo "Error: Cosign is not installed"
  echo "Install from: https://github.com/sigstore/cosign"
  exit 1
fi

# Verify signature
if cosign verify "$IMAGE_NAME" \
  --certificate-identity-regexp ".*" \
  --certificate-oidc-issuer "$OIDC_ISSUER"; then
  echo "✓ Signature verified successfully"
  exit 0
else
  echo "✗ Signature verification failed"
  exit 1
fi

