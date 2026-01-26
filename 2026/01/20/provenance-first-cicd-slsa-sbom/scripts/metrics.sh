#!/bin/bash
# Collect metrics about provenance and policy gates

set -e

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
  echo "WARNING: GitHub CLI (gh) not installed. Some metrics will be unavailable."
  GH_AVAILABLE=0
else
  GH_AVAILABLE=1
fi

echo "=========================================="
echo "Provenance-First CI/CD Metrics"
echo "=========================================="
echo ""

# Count releases with provenance (if gh is available)
if [ "$GH_AVAILABLE" -eq 1 ]; then
  echo "Releases with Provenance:"
  TOTAL_RELEASES=$(gh release list --limit 100 2>/dev/null | wc -l || echo "0")
  if [ "$TOTAL_RELEASES" -gt 0 ]; then
    # This is a simplified check - in production, you'd verify attestations
    RELEASES_WITH_PROVENANCE=$(gh release list --limit 100 2>/dev/null | grep -c "provenance" || echo "0")
    if [ "$TOTAL_RELEASES" -gt 0 ]; then
      PROVENANCE_RATE=$(echo "scale=2; $RELEASES_WITH_PROVENANCE * 100 / $TOTAL_RELEASES" | bc 2>/dev/null || echo "0")
      echo "  Total releases: $TOTAL_RELEASES"
      echo "  With provenance: $RELEASES_WITH_PROVENANCE"
      echo "  Rate: ${PROVENANCE_RATE}%"
    fi
  else
    echo "  No releases found"
  fi
  echo ""
fi

# Count policy gate failures
if [ -f "policy-decisions.log" ]; then
  echo "Policy Gate Statistics:"
  TOTAL=$(wc -l < policy-decisions.log 2>/dev/null || echo "0")
  FAILURES=$(grep -c "DENY" policy-decisions.log 2>/dev/null || echo "0")
  ALLOWS=$(grep -c "ALLOW" policy-decisions.log 2>/dev/null || echo "0")
  
  if [ "$TOTAL" -gt 0 ]; then
    FAILURE_RATE=$(echo "scale=2; $FAILURES * 100 / $TOTAL" | bc 2>/dev/null || echo "0")
    echo "  Total decisions: $TOTAL"
    echo "  Allowed: $ALLOWS"
    echo "  Denied: $FAILURES"
    echo "  Failure rate: ${FAILURE_RATE}%"
  else
    echo "  No policy decisions logged yet"
  fi
  echo ""
fi

# Count waivers
if [ -d "waivers" ]; then
  echo "Active Waivers:"
  TOTAL_WAIVERS=$(find waivers -name "*.json" 2>/dev/null | wc -l || echo "0")
  ACTIVE_WAIVERS=0
  EXPIRED_WAIVERS=0
  
  if [ "$TOTAL_WAIVERS" -gt 0 ]; then
    CURRENT_DATE=$(date -u +%s)
    
    for waiver_file in waivers/*.json; do
      if [ -f "$waiver_file" ]; then
        EXPIRES_AT=$(jq -r '.expires_at' "$waiver_file" 2>/dev/null || echo "")
        if [ -n "$EXPIRES_AT" ] && [ "$EXPIRES_AT" != "null" ]; then
          EXPIRES_TIMESTAMP=$(date -u -d "$EXPIRES_AT" +%s 2>/dev/null || echo "0")
          if [ "$EXPIRES_TIMESTAMP" -gt "$CURRENT_DATE" ]; then
            ACTIVE_WAIVERS=$((ACTIVE_WAIVERS + 1))
          else
            EXPIRED_WAIVERS=$((EXPIRED_WAIVERS + 1))
          fi
        fi
      fi
    done
    
    echo "  Total waivers: $TOTAL_WAIVERS"
    echo "  Active: $ACTIVE_WAIVERS"
    echo "  Expired: $EXPIRED_WAIVERS"
  else
    echo "  No waivers found"
  fi
  echo ""
fi

# Mean time to patch (simplified - would need vulnerability tracking)
echo "Mean Time to Patch:"
echo "  (Requires vulnerability tracking system)"
echo "  Target: < 7 days"
echo ""

echo "=========================================="
