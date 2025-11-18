# Ephemeral Environments on Kubernetes

Complete working example for creating ephemeral PR environments on Kubernetes using GitHub Actions.

## Overview

This repository demonstrates how to:
- Automatically create isolated Kubernetes namespaces for each PR
- Deploy applications with unique URLs (pr-{number}.myapp.dev)
- Clean up environments when PRs are closed
- Use both kubectl manifests and Helm charts

## Architecture

```
GitHub PR → GitHub Actions → Build Image → Deploy to K8s → Preview URL
```

When a PR opens:
1. GitHub Actions builds a Docker image tagged with PR number
2. Creates a Kubernetes namespace (pr-{number})
3. Deploys the application
4. Creates an Ingress with unique hostname
5. Posts preview URL as PR comment

When a PR closes:
1. Deletes the namespace and all resources
2. Posts cleanup confirmation

## Prerequisites

- Kubernetes cluster (minikube, kind, or cloud cluster)
- kubectl configured
- GitHub repository with Actions enabled
- Container registry (GitHub Container Registry, Docker Hub, etc.)
- Ingress controller (nginx-ingress recommended)
- cert-manager (optional, for TLS)

## Setup

### 1. Configure Kubernetes Access

Encode your kubeconfig as base64 and add it as a GitHub secret:

```bash
cat ~/.kube/config | base64 -w 0
```

Add as secret `KUBECONFIG` in GitHub repository settings.

### 2. Configure DNS

Set up wildcard DNS to point to your ingress controller:

```
*.myapp.dev → <ingress-controller-ip>
```

Or use a service like nip.io for testing:
```
pr-1234.myapp.192.168.1.100.nip.io
```

### 3. Install Ingress Controller

```bash
# Using nginx-ingress
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
```

### 4. Install cert-manager (Optional)

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

## Usage

### Using kubectl Manifests

The workflow uses `envsubst` to replace variables in manifests:

```yaml
# In workflow
envsubst < k8s/deployment.yaml | kubectl apply -f -
```

Manifests use environment variables:
- `${NAMESPACE}` - Namespace name (pr-{number})
- `${PR_NUMBER}` - PR number
- `${IMAGE_TAG}` - Image tag
- `${REGISTRY}` - Container registry
- `${IMAGE_NAME}` - Image name

### Using Helm

Deploy with Helm instead:

```yaml
- name: Deploy with Helm
  run: |
    helm upgrade --install pr-${{ github.event.pull_request.number }} ./helm \
      --namespace pr-${{ github.event.pull_request.number }} \
      --create-namespace \
      --set image.tag=pr-${{ github.event.pull_request.number }} \
      --set ingress.host=pr-${{ github.event.pull_request.number }}.myapp.dev \
      --set namespace=pr-${{ github.event.pull_request.number }}
```

## Local Testing

### Build and Run Locally

```bash
# Build image
docker build -t myapp:test .

# Run container
docker run -p 8080:8080 -e ENV=local -e PR_NUMBER=test myapp:test

# Test
curl http://localhost:8080/
curl http://localhost:8080/health
curl http://localhost:8080/ready
```

### Deploy to Local Cluster

```bash
# Set variables
export PR_NUMBER=1234
export NAMESPACE=pr-1234
export IMAGE_TAG=pr-1234
export REGISTRY=ghcr.io/org/myapp
export IMAGE_NAME=myapp
export GITHUB_REF_NAME=feature/test

# Create namespace
kubectl create namespace $NAMESPACE

# Deploy
envsubst < k8s/deployment.yaml | kubectl apply -f -
envsubst < k8s/service.yaml | kubectl apply -f -
envsubst < k8s/ingress.yaml | kubectl apply -f -

# Check status
kubectl get all -n $NAMESPACE
```

### Cleanup

```bash
# Using script
./scripts/cleanup-pr.sh 1234

# Or manually
kubectl delete namespace pr-1234
```

## Resource Quotas

Set resource quotas to prevent resource exhaustion:

```bash
envsubst < k8s/resource-quota.yaml | kubectl apply -f -
```

This limits each PR environment to:
- 2 CPU requests, 4 CPU limits
- 4Gi memory requests, 8Gi limits
- 1 PVC
- No load balancers or node ports

## Customization

### Change Hostname Pattern

Edit `k8s/ingress.yaml`:

```yaml
host: pr-${PR_NUMBER}.myapp.dev
```

Change to:

```yaml
host: ${PR_NUMBER}-preview.myapp.dev
```

### Add Database per PR

Create a database in the namespace:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: ${NAMESPACE}
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: ${NAMESPACE}
spec:
  # ... postgres deployment
```

### Add Resource Limits

Edit `k8s/deployment.yaml`:

```yaml
resources:
  requests:
    cpu: 200m
    memory: 256Mi
  limits:
    cpu: 1000m
    memory: 1Gi
```

## Monitoring

### Check PR Environments

```bash
# List all PR namespaces
kubectl get namespaces -l managed-by=pr-env

# Get resources for a PR
kubectl get all -n pr-1234

# Check logs
kubectl logs -n pr-1234 deployment/myapp
```

### Cleanup Old Environments

```bash
# List namespaces older than 7 days
kubectl get namespaces -o json | jq -r '.items[] | select(.metadata.name | startswith("pr-")) | select((.metadata.creationTimestamp | fromdateiso8601) < (now - 604800)) | .metadata.name'

# Delete old namespaces
kubectl get namespaces -o json | jq -r '.items[] | select(.metadata.name | startswith("pr-")) | select((.metadata.creationTimestamp | fromdateiso8601) < (now - 604800)) | .metadata.name' | xargs -I {} kubectl delete namespace {}
```

## Troubleshooting

### Image Pull Errors

Check:
- Image exists in registry
- Registry credentials are correct
- Image pull secrets are set

```bash
kubectl describe pod -n pr-1234
```

### Ingress Not Working

Check:
- Ingress controller is running
- DNS points to ingress controller
- Ingress resource is created

```bash
kubectl get ingress -n pr-1234
kubectl describe ingress -n pr-1234
```

### Namespace Stuck Deleting

Sometimes namespaces get stuck. Force delete:

```bash
kubectl get namespace pr-1234 -o json | jq '.spec.finalizers = []' | kubectl replace --raw /api/v1/namespaces/pr-1234/finalize -f -
```

## Best Practices

1. **Set Resource Quotas** - Prevent one PR from consuming all resources
2. **Use TTL** - Automatically clean up old environments
3. **Monitor Costs** - Track resource usage per PR
4. **Limit Active PRs** - Queue new PRs if limit is reached
5. **Use Idempotent Deploys** - Safe to run multiple times
6. **Tag Everything** - Labels and annotations for tracking
7. **Secure Access** - Network policies, RBAC, no prod data

## Extending

### Add Database Seeding

```yaml
- name: Seed database
  run: |
    kubectl run seed-job -n pr-${{ github.event.pull_request.number }} \
      --image=postgres:15 \
      --restart=Never \
      --command -- psql -h postgres -U user -d myapp -f /seed.sql
```

### Add Integration Tests

```yaml
- name: Run integration tests
  run: |
    PREVIEW_URL="https://pr-${{ github.event.pull_request.number }}.myapp.dev"
    npm run test:integration -- --url=$PREVIEW_URL
```

### Add Cost Tracking

```yaml
- name: Track costs
  run: |
    # Calculate resource costs
    # Send to monitoring system
```

## License

MIT

