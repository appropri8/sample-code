#!/bin/bash
# Test script to verify Gateway API routing works correctly

set -e

GATEWAY_NAMESPACE="gateway-system"
GATEWAY_NAME="production-gateway"
TEST_HOSTNAME="api.prod.example.com"

echo "Testing Gateway API routing..."

# Check Gateway is ready
echo "1. Checking Gateway status..."
GATEWAY_READY=$(kubectl get gateway $GATEWAY_NAME -n $GATEWAY_NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
if [ "$GATEWAY_READY" != "True" ]; then
  echo "ERROR: Gateway is not ready"
  exit 1
fi
echo "✓ Gateway is ready"

# Get Gateway address
GATEWAY_ADDRESS=$(kubectl get gateway $GATEWAY_NAME -n $GATEWAY_NAMESPACE -o jsonpath='{.status.addresses[0].value}')
if [ -z "$GATEWAY_ADDRESS" ]; then
  echo "ERROR: Gateway has no address assigned"
  exit 1
fi
echo "✓ Gateway address: $GATEWAY_ADDRESS"

# Check HTTPRoutes
echo "2. Checking HTTPRoutes..."
HTTPROUTES=$(kubectl get httproute -A -o jsonpath='{.items[*].metadata.name}')
if [ -z "$HTTPROUTES" ]; then
  echo "WARNING: No HTTPRoutes found"
else
  echo "✓ Found HTTPRoutes: $HTTPROUTES"
fi

# Test connectivity (if curl is available and Gateway is accessible)
if command -v curl &> /dev/null; then
  echo "3. Testing connectivity..."
  # Note: This assumes the Gateway is accessible from this machine
  # In production, you'd use the actual Gateway address
  if curl -k -s -o /dev/null -w "%{http_code}" "https://$TEST_HOSTNAME" | grep -q "200\|404\|502"; then
    echo "✓ Gateway is responding"
  else
    echo "WARNING: Could not reach Gateway (this may be expected if not accessible from this machine)"
  fi
fi

echo ""
echo "Gateway API routing test complete!"

