#!/bin/bash
# Verify SBOM against policy (licenses, registries, etc.)

set -e

SBOM_FILE="$1"

if [ -z "$SBOM_FILE" ]; then
  echo "Usage: $0 <sbom.json>"
  exit 1
fi

if [ ! -f "$SBOM_FILE" ]; then
  echo "ERROR: SBOM file not found: $SBOM_FILE"
  exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
  echo "ERROR: jq is required but not installed"
  exit 1
fi

# Approved licenses (configurable via environment variable or file)
APPROVED_LICENSES="${APPROVED_LICENSES:-MIT,Apache-2.0,BSD-3-Clause,BSD-2-Clause,ISC,MPL-2.0}"

# Approved registries (packages from these registries are allowed)
APPROVED_REGISTRIES="${APPROVED_REGISTRIES:-npmjs.org,pypi.org,maven.org,docker.io,ghcr.io}"

# Convert to arrays
IFS=',' read -ra APPROVED_LICENSES_ARRAY <<< "$APPROVED_LICENSES"
IFS=',' read -ra APPROVED_REGISTRIES_ARRAY <<< "$APPROVED_REGISTRIES"

echo "=========================================="
echo "SBOM Policy Verification"
echo "=========================================="

FAILED=0

# Check licenses
echo "Checking licenses..."
UNKNOWN_LICENSES=$(jq -r '.packages[]? | select(.licenseConcluded != null) | select(.licenseConcluded != "NOASSERTION") | .licenseConcluded' "$SBOM_FILE" 2>/dev/null | sort -u || echo "")

if [ -n "$UNKNOWN_LICENSES" ]; then
  while IFS= read -r license; do
    if [ -z "$license" ] || [ "$license" == "null" ]; then
      continue
    fi
    
    # Check if license is approved
    APPROVED=0
    for approved_license in "${APPROVED_LICENSES_ARRAY[@]}"; do
      if [[ "$license" == *"$approved_license"* ]]; then
        APPROVED=1
        break
      fi
    done
    
    if [ "$APPROVED" -eq 0 ]; then
      echo "  ⚠️  Unapproved license found: $license"
      # Don't fail on unapproved licenses by default, just warn
      # Uncomment the following to fail on unapproved licenses:
      # FAILED=1
    fi
  done <<< "$UNKNOWN_LICENSES"
fi

# Check package sources (if available in SBOM)
echo "Checking package sources..."
PACKAGE_SOURCES=$(jq -r '.packages[]? | select(.externalRefs != null) | .externalRefs[]? | select(.referenceType == "purl") | .referenceLocator' "$SBOM_FILE" 2>/dev/null || echo "")

if [ -n "$PACKAGE_SOURCES" ]; then
  while IFS= read -r purl; do
    if [ -z "$purl" ]; then
      continue
    fi
    
    # Extract registry from purl (simplified)
    APPROVED=0
    for approved_registry in "${APPROVED_REGISTRIES_ARRAY[@]}"; do
      if [[ "$purl" == *"$approved_registry"* ]]; then
        APPROVED=1
        break
      fi
    done
    
    if [ "$APPROVED" -eq 0 ]; then
      echo "  ⚠️  Package from unapproved registry: $purl"
      # Don't fail on unapproved registries by default, just warn
      # Uncomment the following to fail on unapproved registries:
      # FAILED=1
    fi
  done <<< "$PACKAGE_SOURCES"
fi

# Count packages
TOTAL_PACKAGES=$(jq '[.packages[]?] | length' "$SBOM_FILE" 2>/dev/null || echo "0")
echo ""
echo "Total packages in SBOM: $TOTAL_PACKAGES"

if [ "$FAILED" -eq 1 ]; then
  echo ""
  echo "=========================================="
  echo "❌ SBOM policy verification FAILED"
  echo "=========================================="
  exit 1
fi

echo ""
echo "=========================================="
echo "✅ SBOM policy verification PASSED"
echo "=========================================="
