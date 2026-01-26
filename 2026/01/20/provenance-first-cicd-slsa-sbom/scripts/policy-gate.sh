#!/bin/bash
# Policy gate script that fails builds on CVE thresholds

set -e

VULN_FILE="$1"

if [ -z "$VULN_FILE" ]; then
  echo "Usage: $0 <vulnerabilities.json>"
  exit 1
fi

if [ ! -f "$VULN_FILE" ]; then
  echo "ERROR: Vulnerability file not found: $VULN_FILE"
  exit 1
fi

# Thresholds (configurable via environment variables)
MAX_CRITICAL="${MAX_CRITICAL:-0}"
MAX_HIGH="${MAX_HIGH:-5}"
MAX_MEDIUM="${MAX_MEDIUM:-20}"

# Check if jq is installed
if ! command -v jq &> /dev/null; then
  echo "ERROR: jq is required but not installed"
  exit 1
fi

# Count vulnerabilities by severity
CRITICAL=$(jq '[.matches[]? | select(.vulnerability.severity == "Critical")] | length' "$VULN_FILE" || echo "0")
HIGH=$(jq '[.matches[]? | select(.vulnerability.severity == "High")] | length' "$VULN_FILE" || echo "0")
MEDIUM=$(jq '[.matches[]? | select(.vulnerability.severity == "Medium")] | length' "$VULN_FILE" || echo "0")
LOW=$(jq '[.matches[]? | select(.vulnerability.severity == "Low")] | length' "$VULN_FILE" || echo "0")

echo "=========================================="
echo "Vulnerability Summary"
echo "=========================================="
echo "  Critical: $CRITICAL (max: $MAX_CRITICAL)"
echo "  High:     $HIGH (max: $MAX_HIGH)"
echo "  Medium:   $MEDIUM (max: $MAX_MEDIUM)"
echo "  Low:      $LOW (no limit)"
echo ""

# Check thresholds
FAILED=0

if [ "$CRITICAL" -gt "$MAX_CRITICAL" ]; then
  echo "❌ ERROR: Critical vulnerabilities exceed threshold ($CRITICAL > $MAX_CRITICAL)"
  FAILED=1
fi

if [ "$HIGH" -gt "$MAX_HIGH" ]; then
  echo "❌ ERROR: High vulnerabilities exceed threshold ($HIGH > $MAX_HIGH)"
  FAILED=1
fi

if [ "$MEDIUM" -gt "$MAX_MEDIUM" ]; then
  echo "❌ ERROR: Medium vulnerabilities exceed threshold ($MEDIUM > $MAX_MEDIUM)"
  FAILED=1
fi

# Show critical vulnerabilities if any
if [ "$CRITICAL" -gt 0 ]; then
  echo ""
  echo "Critical Vulnerabilities:"
  jq -r '.matches[]? | select(.vulnerability.severity == "Critical") | "  - \(.vulnerability.id): \(.artifact.name)@\(.artifact.version)"' "$VULN_FILE" || true
fi

# Show high vulnerabilities if threshold exceeded
if [ "$HIGH" -gt "$MAX_HIGH" ]; then
  echo ""
  echo "High Vulnerabilities (showing first 10):"
  jq -r '.matches[]? | select(.vulnerability.severity == "High") | "  - \(.vulnerability.id): \(.artifact.name)@\(.artifact.version)"' "$VULN_FILE" | head -10 || true
fi

if [ "$FAILED" -eq 1 ]; then
  echo ""
  echo "=========================================="
  echo "Policy gate FAILED. Blocking release."
  echo "=========================================="
  echo "Review vulnerabilities: $VULN_FILE"
  echo ""
  echo "To override (requires approval):"
  echo "  ./scripts/waiver-request.sh <CVE_ID> <reason> <days>"
  exit 1
fi

echo "=========================================="
echo "✅ Policy gate PASSED"
echo "=========================================="
