#!/bin/bash
# Script to help migrate from Ingress to Gateway API
# This script inventories existing Ingress resources and helps map them to HTTPRoutes

set -e

OUTPUT_DIR="./migration-output"
mkdir -p $OUTPUT_DIR

echo "Ingress to Gateway API Migration Helper"
echo "======================================="
echo ""

# Inventory all Ingress resources
echo "1. Inventorying Ingress resources..."
kubectl get ingress --all-namespaces -o wide > $OUTPUT_DIR/ingress-inventory.txt
echo "  Saved to: $OUTPUT_DIR/ingress-inventory.txt"
echo ""

# Get detailed YAML for each Ingress
echo "2. Exporting Ingress manifests..."
for ns in $(kubectl get ingress --all-namespaces -o jsonpath='{.items[*].metadata.namespace}' | tr ' ' '\n' | sort -u); do
  for ingress in $(kubectl get ingress -n $ns -o jsonpath='{.items[*].metadata.name}'); do
    echo "  Exporting: $ns/$ingress"
    kubectl get ingress $ingress -n $ns -o yaml > $OUTPUT_DIR/ingress-$ns-$ingress.yaml
  done
done
echo ""

# Check IngressClasses
echo "3. Checking IngressClasses..."
kubectl get ingressclass -o wide > $OUTPUT_DIR/ingressclasses.txt
echo "  Saved to: $OUTPUT_DIR/ingressclasses.txt"
echo ""

# Check Gateway API resources (if any exist)
echo "4. Checking existing Gateway API resources..."
if kubectl get gatewayclass &>/dev/null; then
  kubectl get gatewayclass -o wide > $OUTPUT_DIR/gatewayclasses.txt
  echo "  Saved to: $OUTPUT_DIR/gatewayclasses.txt"
fi

if kubectl get gateway --all-namespaces &>/dev/null; then
  kubectl get gateway --all-namespaces -o wide > $OUTPUT_DIR/gateways.txt
  echo "  Saved to: $OUTPUT_DIR/gateways.txt"
fi

if kubectl get httproute --all-namespaces &>/dev/null; then
  kubectl get httproute --all-namespaces -o wide > $OUTPUT_DIR/httproutes.txt
  echo "  Saved to: $OUTPUT_DIR/httproutes.txt"
fi
echo ""

# Generate migration checklist
echo "5. Generating migration checklist..."
cat > $OUTPUT_DIR/migration-checklist.md <<EOF
# Migration Checklist

## Pre-Migration
- [ ] Review all Ingress resources in: ingress-inventory.txt
- [ ] Identify which IngressClass each Ingress uses
- [ ] Document all annotations used
- [ ] Identify cross-namespace patterns
- [ ] Choose Gateway API controller

## Migration Steps
- [ ] Install Gateway API controller
- [ ] Verify GatewayClass is created
- [ ] Create Gateway(s) for each environment
- [ ] Create HTTPRoute for first test service
- [ ] Test routing with separate hostname
- [ ] Gradually migrate services
- [ ] Update DNS records
- [ ] Monitor metrics and logs
- [ ] Remove old Ingress resources

## Post-Migration
- [ ] Remove Ingress controller (if not needed)
- [ ] Update documentation
- [ ] Train team on Gateway API
- [ ] Update runbooks

EOF
echo "  Saved to: $OUTPUT_DIR/migration-checklist.md"
echo ""

echo "Migration inventory complete!"
echo "Review files in: $OUTPUT_DIR/"
echo ""
echo "Next steps:"
echo "1. Review the inventory files"
echo "2. Map Ingress patterns to HTTPRoute patterns"
echo "3. Start with a low-risk service"
echo "4. Follow the migration checklist"
