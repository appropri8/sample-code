#!/bin/bash
# Script to test Gateway API routing
# Usage: ./test-routing.sh <gateway-namespace> <gateway-name>

set -e

GATEWAY_NS=${1:-platform}
GATEWAY_NAME=${2:-production-gateway}

echo "Testing Gateway API setup..."
echo "Gateway: $GATEWAY_NAME in namespace $GATEWAY_NS"
echo ""

# Check Gateway status
echo "1. Checking Gateway status..."
kubectl get gateway $GATEWAY_NAME -n $GATEWAY_NS
echo ""

# Get Gateway details
echo "2. Gateway details:"
kubectl describe gateway $GATEWAY_NAME -n $GATEWAY_NS
echo ""

# List all HTTPRoutes
echo "3. Listing HTTPRoutes:"
kubectl get httproute --all-namespaces
echo ""

# Check HTTPRoute statuses
echo "4. HTTPRoute statuses:"
for route in $(kubectl get httproute --all-namespaces -o jsonpath='{.items[*].metadata.name}'); do
  ns=$(kubectl get httproute $route --all-namespaces -o jsonpath='{.metadata.namespace}')
  echo "  HTTPRoute: $route in namespace $ns"
  kubectl describe httproute $route -n $ns | grep -A 10 "Status:"
  echo ""
done

# Get Gateway IP/address
echo "5. Gateway address:"
GATEWAY_IP=$(kubectl get gateway $GATEWAY_NAME -n $GATEWAY_NS -o jsonpath='{.status.addresses[0].value}' 2>/dev/null || echo "Not assigned yet")
if [ -z "$GATEWAY_IP" ] || [ "$GATEWAY_IP" = "Not assigned yet" ]; then
  echo "  Gateway address not yet assigned. Check controller logs."
  echo "  kubectl logs -n <controller-namespace> -l app.kubernetes.io/name=traefik"
else
  echo "  Gateway IP: $GATEWAY_IP"
fi
echo ""

# Test connectivity (if IP is available)
if [ ! -z "$GATEWAY_IP" ] && [ "$GATEWAY_IP" != "Not assigned yet" ]; then
  echo "6. Testing connectivity..."
  echo "  curl -H 'Host: <your-hostname>' http://$GATEWAY_IP/"
  echo "  Replace <your-hostname> with a hostname from your HTTPRoute"
fi

echo ""
echo "Done!"
