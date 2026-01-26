#!/bin/bash
# Create a waiver request for a CVE or policy violation

set -e

CVE_ID="$1"
REASON="$2"
EXPIRY_DAYS="${3:-30}"

if [ -z "$CVE_ID" ] || [ -z "$REASON" ]; then
  echo "Usage: $0 <CVE_ID> <reason> [expiry_days]"
  echo ""
  echo "Example:"
  echo "  $0 CVE-2024-1234 'False positive, not exploitable in our context' 30"
  exit 1
fi

# Create waivers directory if it doesn't exist
mkdir -p waivers

# Generate waiver request
WAIVER_FILE="waivers/${CVE_ID}.json"

# Get current user (from environment or git config)
REQUESTED_BY="${USER:-$(git config user.name || echo 'unknown')}"
REQUESTED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EXPIRES_AT=$(date -u -d "+${EXPIRY_DAYS} days" +%Y-%m-%dT%H:%M:%SZ)

cat > "$WAIVER_FILE" <<EOF
{
  "cve_id": "$CVE_ID",
  "reason": "$REASON",
  "requested_by": "$REQUESTED_BY",
  "requested_at": "$REQUESTED_AT",
  "expires_at": "$EXPIRES_AT",
  "approved": false,
  "approved_by": null,
  "approved_at": null
}
EOF

echo "Waiver request created: $WAIVER_FILE"
echo ""
echo "Next steps:"
echo "  1. Submit for approval via your ticketing system"
echo "  2. Security team will review and approve/reject"
echo "  3. Once approved, update 'approved' field to true"
echo ""
echo "Waiver will expire on: $EXPIRES_AT"
