# Designing Safe Multi-Tenancy in Kubernetes for Internal Developer Platforms

Complete executable Kubernetes manifests demonstrating multi-tenant cluster design patterns.

## Overview

This repository contains production-ready Kubernetes configurations for implementing safe multi-tenancy:

- **Namespace-based tenant isolation** with RBAC, NetworkPolicy, and ResourceQuota
- **Admission policies** using Kyverno for enforcing tenant labels and security
- **GitOps structure** for managing multiple tenants
- **Reference implementations** for common multi-tenancy patterns

## Prerequisites

- Kubernetes cluster (1.26+)
- kubectl configured to access your cluster
- Kyverno installed (for admission policies) - see [Installation](#installation)
- Basic understanding of Kubernetes RBAC, NetworkPolicy, and ResourceQuota

## Installation

### Install Kyverno

Kyverno is used for admission policies. Install it first:

```bash
# Install Kyverno
kubectl create namespace kyverno
helm repo add kyverno https://kyverno.github.io/kyverno/
helm repo update
helm install kyverno kyverno/kyverno -n kyverno

# Wait for Kyverno to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=kyverno -n kyverno --timeout=90s
```

### Apply Cluster Policies

Apply the cluster-wide admission policies:

```bash
kubectl apply -f policies/
```

These policies enforce:
- All workloads must have a `tenant` label
- All containers must have CPU and memory limits
- Block privileged containers
- Block hostNetwork usage

## Quick Start

### 1. Create a Tenant Namespace

Create a complete tenant setup for Team A:

```bash
kubectl apply -f tenants/team-a/
```

This creates:
- Namespace with proper labels
- ResourceQuota (10 CPU, 20Gi memory)
- LimitRange (defaults and constraints)
- NetworkPolicy (default deny + allow same namespace)
- RBAC (Role + RoleBinding)
- Service accounts

### 2. Verify Tenant Isolation

Check that the namespace was created with quotas:

```bash
kubectl describe namespace team-a
```

You should see:
- ResourceQuota with CPU/memory limits
- LimitRange with container defaults
- Labels: `tenant=team-a`, `owner=team-a@company.com`

### 3. Test Admission Policies

Try creating a pod without a tenant label (should be rejected):

```bash
kubectl run test-pod --image=nginx -n team-a
```

The pod should be rejected with a message about missing `tenant` label.

Create a pod with proper labels:

```bash
kubectl run test-pod --image=nginx -n team-a \
  --labels="tenant=team-a,app=test" \
  --requests="cpu=100m,memory=128Mi" \
  --limits="cpu=500m,memory=512Mi"
```

This should succeed.

### 4. Test Network Isolation

Verify NetworkPolicy is working:

```bash
# Create a test pod in team-a
kubectl run test-pod-a --image=nginx -n team-a \
  --labels="tenant=team-a,app=test" \
  --requests="cpu=100m,memory=128Mi" \
  --limits="cpu=500m,memory=512Mi"

# Try to create a pod in team-b
kubectl run test-pod-b --image=nginx -n team-b \
  --labels="tenant=team-b,app=test" \
  --requests="cpu=100m,memory=128Mi" \
  --limits="cpu=500m,memory=512Mi"

# Try to reach team-b from team-a (should fail)
kubectl exec -n team-a test-pod-a -- curl http://test-pod-b.team-b.svc.cluster.local
```

The curl should fail because NetworkPolicy blocks cross-namespace traffic.

## Repository Structure

```
.
├── README.md
├── tenants/
│   ├── team-a/              # Complete tenant setup for Team A
│   │   ├── namespace.yaml
│   │   ├── resource-quota.yaml
│   │   ├── limit-range.yaml
│   │   ├── network-policy.yaml
│   │   ├── rbac.yaml
│   │   └── service-accounts.yaml
│   └── team-b/              # Complete tenant setup for Team B
│       ├── namespace.yaml
│       ├── resource-quota.yaml
│       ├── limit-range.yaml
│       ├── network-policy.yaml
│       ├── rbac.yaml
│       └── service-accounts.yaml
├── policies/                 # Cluster-wide admission policies (Kyverno)
│   ├── require-tenant-label.yaml
│   ├── require-resource-limits.yaml
│   ├── block-privileged.yaml
│   └── block-host-network.yaml
├── shared-services/          # Shared services namespace
│   ├── namespace.yaml
│   ├── postgres-service.yaml
│   └── network-policy.yaml
├── examples/                 # Example workloads
│   ├── deployment-example.yaml
│   ├── statefulset-example.yaml
│   └── job-example.yaml
└── scripts/                  # Utility scripts
    ├── create-tenant.sh
    ├── validate-tenant.sh
    └── cleanup-tenant.sh
```

## Tenant Configuration

### Namespace

Each tenant gets a namespace with:
- Labels: `tenant`, `owner`, `environment`
- Pod Security Standards: Restricted mode
- Annotations: description, cost-center

### ResourceQuota

Limits per namespace:
- CPU requests: 10 cores
- Memory requests: 20Gi
- CPU limits: 20 cores
- Memory limits: 40Gi
- PersistentVolumeClaims: 10
- LoadBalancers: 2
- Deployments: 10
- StatefulSets: 5

Adjust these based on your cluster size and tenant needs.

### LimitRange

Container defaults and constraints:
- Default CPU limit: 500m
- Default memory limit: 512Mi
- Default CPU request: 100m
- Default memory request: 128Mi
- Max CPU: 2 cores
- Max memory: 2Gi
- Min CPU: 50m
- Min memory: 64Mi

### NetworkPolicy

Three policies per namespace:
1. **default-deny-all**: Denies all ingress and egress
2. **allow-same-namespace**: Allows pods in same namespace to communicate
3. **allow-shared-services**: Allows egress to shared-services namespace

### RBAC

Two roles per tenant:
- **tenant-admin**: Full access within namespace
- **tenant-developer**: Read-only access

Bind users or groups to these roles as needed.

## Admission Policies

### Require Tenant Label

All workloads (Pods, Deployments, StatefulSets, etc.) must have a `tenant` label matching the namespace name.

### Require Resource Limits

All containers must have CPU and memory limits and requests specified.

### Block Privileged

Blocks pods with `securityContext.privileged: true`.

### Block Host Network

Blocks pods with `hostNetwork: true`.

## Shared Services

Some services are shared across tenants (databases, message queues, etc.). These go in the `shared-services` namespace.

Tenants can access shared services via NetworkPolicy rules. See `shared-services/network-policy.yaml` for an example.

## Creating a New Tenant

### Manual Method

1. Copy `tenants/team-a/` to `tenants/your-team/`
2. Replace `team-a` with `your-team` in all files
3. Update labels, owner email, quotas as needed
4. Apply: `kubectl apply -f tenants/your-team/`

### Automated Method

Use the provided script:

```bash
./scripts/create-tenant.sh your-team your-team@company.com production
```

This creates all necessary resources automatically.

## Validation

Validate a tenant setup:

```bash
./scripts/validate-tenant.sh team-a
```

This checks:
- Namespace exists with correct labels
- ResourceQuota is set
- LimitRange is set
- NetworkPolicy is configured
- RBAC is configured
- Service accounts exist

## Cleanup

Remove a tenant (use with caution):

```bash
./scripts/cleanup-tenant.sh team-a
```

This deletes the namespace and all resources in it.

## Testing Multi-Tenancy

### Test Resource Isolation

1. Create a deployment in team-a that requests all available CPU
2. Verify team-b can still deploy (ResourceQuota prevents team-a from consuming everything)

### Test Network Isolation

1. Create pods in team-a and team-b
2. Verify they cannot communicate (NetworkPolicy blocks it)
3. Verify both can reach shared-services

### Test Security Policies

1. Try to create a privileged pod (should be blocked)
2. Try to create a pod without resource limits (should be blocked)
3. Try to create a pod without tenant label (should be blocked)

## Monitoring and Observability

### Labels for Prometheus

All resources should have these labels for monitoring:
- `tenant`: Team name
- `app`: Application name
- `component`: Component name (api, worker, etc.)
- `environment`: Environment (dev, staging, prod)

### Prometheus Queries

```promql
# CPU usage per tenant
sum(rate(container_cpu_usage_seconds_total{namespace=~"team-.*"}[5m])) by (tenant)

# Memory usage per tenant
sum(container_memory_working_set_bytes{namespace=~"team-.*"}) by (tenant)

# Error rate per tenant
sum(rate(http_requests_total{status=~"5..", namespace=~"team-.*"}[5m])) by (tenant)
```

## Cost Tracking

Use tools like Kubecost to track costs per tenant. Ensure all resources have proper labels (`tenant`, `app`, `environment`).

## Best Practices

1. **Always use labels**: Every resource should have `tenant`, `app`, `environment` labels
2. **Set resource limits**: Use LimitRange defaults, but always specify limits in production
3. **Default deny network**: Start with deny-all, then allow only what's needed
4. **Enforce policies**: Use admission controllers to enforce rules, don't rely on documentation
5. **Monitor quotas**: Alert when tenants approach their quotas
6. **Regular audits**: Review tenant configurations regularly
7. **Document exceptions**: If a tenant needs special permissions, document why

## Common Issues

### Pod Rejected: Missing Tenant Label

**Error**: `All workloads must have a 'tenant' label`

**Fix**: Add `tenant` label to your pod/deployment:

```yaml
metadata:
  labels:
    tenant: team-a
```

### Pod Rejected: Missing Resource Limits

**Error**: `All containers must have CPU and memory limits`

**Fix**: Add resource limits to your container:

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"
```

### Cannot Deploy: ResourceQuota Exceeded

**Error**: `exceeded quota: team-a-quota`

**Fix**: Either reduce resource requests or request a quota increase from platform team.

### Network Policy Blocking Traffic

**Issue**: Pods can't communicate

**Fix**: Check NetworkPolicy rules. Ensure pods have proper labels and NetworkPolicy allows the traffic.

## Advanced: Virtual Clusters

For teams that need stronger isolation (CRD conflicts, different K8s versions), consider virtual clusters. See `examples/vcluster/` for vcluster configuration examples.

## Next Steps

- Add monitoring dashboards per tenant
- Set up cost tracking (Kubecost)
- Implement automated tenant provisioning (GitOps)
- Add security scanning per tenant
- Set up backup/disaster recovery per tenant

## Resources

- [Kubernetes Multi-Tenancy Documentation](https://kubernetes.io/docs/concepts/security/multi-tenancy/)
- [Kyverno Documentation](https://kyverno.io/docs/)
- [NetworkPolicy Guide](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [ResourceQuota Guide](https://kubernetes.io/docs/concepts/policy/resource-quotas/)

## License

MIT

## Author

Yusuf Elborey
