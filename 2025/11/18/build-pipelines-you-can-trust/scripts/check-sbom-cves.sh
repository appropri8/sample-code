#!/bin/bash
set -e

SBOM_FILE="${1:-sbom.spdx.json}"
SEVERITY="${2:-HIGH,CRITICAL}"
EXIT_CODE="${3:-0}"

if [ ! -f "$SBOM_FILE" ]; then
  echo "Error: SBOM file not found: $SBOM_FILE"
  exit 1
fi

echo "Checking SBOM for CVEs: $SBOM_FILE"
echo "Severity levels: $SEVERITY"

# Check if Trivy is installed
if ! command -v trivy &> /dev/null; then
  echo "Installing Trivy..."
  # This is a simplified install - adjust for your platform
  echo "Please install Trivy from: https://github.com/aquasecurity/trivy"
  exit 1
fi

# Scan SBOM for vulnerabilities
if trivy sbom "$SBOM_FILE" --severity "$SEVERITY" --exit-code "$EXIT_CODE"; then
  echo "✓ No critical vulnerabilities found"
  exit 0
else
  echo "✗ Critical vulnerabilities found"
  exit 1
fi

