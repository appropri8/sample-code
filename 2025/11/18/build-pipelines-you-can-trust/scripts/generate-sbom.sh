#!/bin/bash
set -e

IMAGE_NAME="${1:-myapp:latest}"
OUTPUT_FORMAT="${2:-spdx-json}"
OUTPUT_FILE="${3:-sbom.spdx.json}"

echo "Generating SBOM for image: $IMAGE_NAME"
echo "Output format: $OUTPUT_FORMAT"
echo "Output file: $OUTPUT_FILE"

# Check if Syft is installed
if ! command -v syft &> /dev/null; then
  echo "Installing Syft..."
  curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
fi

# Generate SBOM
syft "$IMAGE_NAME" -o "$OUTPUT_FORMAT" > "$OUTPUT_FILE"

echo "SBOM generated successfully: $OUTPUT_FILE"
echo "File size: $(du -h "$OUTPUT_FILE" | cut -f1)"

# Show first few packages
if command -v jq &> /dev/null; then
  echo ""
  echo "Sample packages from SBOM:"
  jq -r '.packages[0:5] | .[] | "\(.name) \(.versionInfo // "unknown")"' "$OUTPUT_FILE" || true
fi

