#!/bin/bash
# Setup script for Gateway API multi-team routing
# Run this as the platform team to set up the shared gateway infrastructure

set -e

echo "Setting up Gateway API infrastructure..."

# Create gateway-system namespace
kubectl create namespace gateway-system --dry-run=client -o yaml | kubectl apply -f -

# Label gateway-system namespace
kubectl label namespace gateway-system gateway-access=enabled --overwrite

# Apply GatewayClass
echo "Creating GatewayClass..."
kubectl apply -f gateways/gatewayclass-traefik.yaml

# Apply Gateway
echo "Creating Gateway..."
kubectl apply -f gateways/production-gateway.yaml

# Wait for Gateway to be ready
echo "Waiting for Gateway to be ready..."
kubectl wait --for=condition=Ready gateway/production-gateway -n gateway-system --timeout=300s

# Show Gateway status
echo "Gateway status:"
kubectl get gateway production-gateway -n gateway-system

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Label app team namespaces with 'gateway-access: enabled'"
echo "2. Teams can now create HTTPRoutes that reference production-gateway"

