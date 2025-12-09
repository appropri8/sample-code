#!/bin/bash

# Script to create a new tenant namespace with all required resources
# Usage: ./create-tenant.sh <tenant-name> <owner-email> <environment>

set -e

TENANT_NAME="${1}"
OWNER_EMAIL="${2}"
ENVIRONMENT="${3:-production}"

if [ -z "$TENANT_NAME" ] || [ -z "$OWNER_EMAIL" ]; then
  echo "Usage: $0 <tenant-name> <owner-email> [environment]"
  echo "Example: $0 team-c team-c@company.com production"
  exit 1
fi

echo "Creating tenant: $TENANT_NAME"
echo "Owner: $OWNER_EMAIL"
echo "Environment: $ENVIRONMENT"

# Create namespace
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: ${TENANT_NAME}
  labels:
    tenant: ${TENANT_NAME}
    owner: ${OWNER_EMAIL}
    environment: ${ENVIRONMENT}
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
  annotations:
    description: "Namespace for ${TENANT_NAME} ${ENVIRONMENT} workloads"
    cost-center: "engineering"
EOF

# Create ResourceQuota and LimitRange
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: ${TENANT_NAME}-quota
  namespace: ${TENANT_NAME}
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    persistentvolumeclaims: "10"
    services.loadbalancers: "2"
    count/deployments.apps: "10"
    count/statefulsets.apps: "5"
    count/jobs.batch: "20"
---
apiVersion: v1
kind: LimitRange
metadata:
  name: ${TENANT_NAME}-limits
  namespace: ${TENANT_NAME}
spec:
  limits:
  - default:
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    max:
      cpu: "2"
      memory: "2Gi"
    min:
      cpu: "50m"
      memory: "64Mi"
    type: Container
EOF

# Create NetworkPolicies
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: ${TENANT_NAME}
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-same-namespace
  namespace: ${TENANT_NAME}
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector: {}
  egress:
  - to:
    - podSelector: {}
  - to: []
    ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 80
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-shared-services
  namespace: ${TENANT_NAME}
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: shared-services
    ports:
    - protocol: TCP
      port: 5432
    - protocol: TCP
      port: 6379
EOF

# Create ServiceAccount
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ${TENANT_NAME}-default
  namespace: ${TENANT_NAME}
  labels:
    tenant: ${TENANT_NAME}
EOF

echo "Tenant ${TENANT_NAME} created successfully!"
echo ""
echo "Next steps:"
echo "1. Create RBAC bindings for team members"
echo "2. Verify namespace: kubectl describe namespace ${TENANT_NAME}"
echo "3. Test deployment: kubectl run test-pod --image=nginx -n ${TENANT_NAME} --labels=\"tenant=${TENANT_NAME},app=test\" --requests=\"cpu=100m,memory=128Mi\" --limits=\"cpu=500m,memory=512Mi\""
