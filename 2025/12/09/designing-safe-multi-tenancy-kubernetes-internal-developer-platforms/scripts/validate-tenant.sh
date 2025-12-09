#!/bin/bash

# Script to validate a tenant namespace setup
# Usage: ./validate-tenant.sh <tenant-name>

set -e

TENANT_NAME="${1}"

if [ -z "$TENANT_NAME" ]; then
  echo "Usage: $0 <tenant-name>"
  echo "Example: $0 team-a"
  exit 1
fi

echo "Validating tenant: $TENANT_NAME"
echo ""

# Check namespace exists
if ! kubectl get namespace "$TENANT_NAME" &>/dev/null; then
  echo "❌ Namespace $TENANT_NAME does not exist"
  exit 1
fi

echo "✅ Namespace exists"

# Check labels
TENANT_LABEL=$(kubectl get namespace "$TENANT_NAME" -o jsonpath='{.metadata.labels.tenant}')
if [ "$TENANT_LABEL" != "$TENANT_NAME" ]; then
  echo "❌ Namespace missing or incorrect 'tenant' label"
  exit 1
fi
echo "✅ Namespace has correct 'tenant' label"

# Check ResourceQuota
if ! kubectl get resourcequota -n "$TENANT_NAME" &>/dev/null; then
  echo "❌ No ResourceQuota found in namespace"
  exit 1
fi
echo "✅ ResourceQuota exists"

# Check LimitRange
if ! kubectl get limitrange -n "$TENANT_NAME" &>/dev/null; then
  echo "❌ No LimitRange found in namespace"
  exit 1
fi
echo "✅ LimitRange exists"

# Check NetworkPolicy
NP_COUNT=$(kubectl get networkpolicy -n "$TENANT_NAME" --no-headers 2>/dev/null | wc -l | tr -d ' ')
if [ "$NP_COUNT" -eq "0" ]; then
  echo "❌ No NetworkPolicy found in namespace"
  exit 1
fi
echo "✅ NetworkPolicy exists ($NP_COUNT policies)"

# Check RBAC
ROLE_COUNT=$(kubectl get role -n "$TENANT_NAME" --no-headers 2>/dev/null | wc -l | tr -d ' ')
if [ "$ROLE_COUNT" -eq "0" ]; then
  echo "⚠️  No Roles found in namespace (this is optional)"
else
  echo "✅ RBAC configured ($ROLE_COUNT roles)"
fi

# Check ServiceAccount
SA_COUNT=$(kubectl get serviceaccount -n "$TENANT_NAME" --no-headers 2>/dev/null | wc -l | tr -d ' ')
if [ "$SA_COUNT" -eq "0" ]; then
  echo "⚠️  No ServiceAccounts found (using default)"
else
  echo "✅ ServiceAccounts exist ($SA_COUNT service accounts)"
fi

echo ""
echo "✅ Tenant validation complete!"
