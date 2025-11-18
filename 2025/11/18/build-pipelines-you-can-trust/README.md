# Build Pipelines You Can Trust: SBOMs, Signing, and Policy as Code

Complete working example for adding SBOM generation, image signing, and policy enforcement to your CI/CD pipeline.

## Overview

This repository demonstrates how to:

- Generate Software Bill of Materials (SBOM) for container images
- Sign container images using Cosign (keyless signing)
- Enforce security policies using Kyverno in Kubernetes
- Integrate all steps into a GitHub Actions workflow

## Architecture

```
Source Code → Build Image → Generate SBOM → Sign Image → Push to Registry
                                                              ↓
                                                         Policy Check
                                                              ↓
                                                      Kubernetes Cluster
```

## Prerequisites

- GitHub repository with Actions enabled
- Kubernetes cluster (for policy enforcement)
- kubectl configured (for deployment)
- Container registry access (GitHub Container Registry, Docker Hub, etc.)

## Quick Start

### 1. Set Up GitHub Actions

The workflow is already configured in `.github/workflows/build-and-deploy.yml`. It will:

1. Build and push Docker image
2. Generate SBOM using Syft
3. Attach SBOM as OCI artifact
4. Sign image with Cosign (keyless)
5. Verify signature
6. Check SBOM for critical CVEs
7. Deploy to Kubernetes (on main branch)

### 2. Install Kyverno

Install Kyverno in your Kubernetes cluster:

```bash
kubectl apply -f https://github.com/kyverno/kyverno/releases/latest/download/install.yaml
```

Wait for Kyverno to be ready:

```bash
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=kyverno -n kyverno --timeout=300s
```

### 3. Apply Policies

Apply the security policies:

```bash
# Start with audit mode (logging only)
kubectl apply -f kyverno/require-signed-images.yaml

# Check policy status
kubectl get clusterpolicies
```

### 4. Test the Pipeline

Push code to trigger the workflow:

```bash
git add .
git commit -m "Add SBOM and signing"
git push origin main
```

Watch the workflow in GitHub Actions. It will:

- Build the image
- Generate SBOM
- Sign the image
- Verify signature
- Check for CVEs

## Manual Usage

### Generate SBOM

```bash
# Build image first
docker build -t myapp:latest .

# Generate SBOM
./scripts/generate-sbom.sh myapp:latest spdx-json sbom.spdx.json

# View SBOM
cat sbom.spdx.json | jq '.packages[0:10]'
```

### Sign Image

```bash
# Sign with keyless (OIDC)
export COSIGN_EXPERIMENTAL=1
./scripts/sign-image.sh ghcr.io/yourorg/yourrepo:v1.0.0

# Or sign with a key
export COSIGN_KEY_PATH=/path/to/key.pem
export COSIGN_PASSWORD=your-password
./scripts/sign-image.sh ghcr.io/yourorg/yourrepo:v1.0.0 false
```

### Verify Signature

```bash
# Verify signature
./scripts/verify-signature.sh ghcr.io/yourorg/yourrepo:v1.0.0
```

### Check SBOM for CVEs

```bash
# Check for high/critical CVEs
./scripts/check-sbom-cves.sh sbom.spdx.json HIGH,CRITICAL

# Or just warn (don't fail)
./scripts/check-sbom-cves.sh sbom.spdx.json HIGH,CRITICAL 0
```

## Policy Configuration

### Require Signed Images

The `require-signed-images` policy ensures all images are signed:

```yaml
# kyverno/require-signed-images.yaml
spec:
  validationFailureAction: enforce
  rules:
  - name: check-image-signature
    match:
      resources:
        kinds:
        - Pod
        namespaces:
        - production
```

**Start in audit mode:**

```yaml
validationFailureAction: audit  # Log violations, don't block
```

**Then enforce:**

```yaml
validationFailureAction: enforce  # Block violations
```

### Customize Policies

Edit the policy files in `kyverno/`:

- `require-signed-images.yaml` - Enforce signed images
- `require-sbom.yaml` - Require SBOM (audit mode)
- `deny-critical-cves.yaml` - Block critical CVEs

## Local Development

### Build and Run

```bash
# Build image
docker build -t myapp:local .

# Run container
docker run -p 8080:8080 -e VERSION=local myapp:local

# Test
curl http://localhost:8080/health
curl http://localhost:8080/ready
```

### Test SBOM Generation

```bash
# Build image
docker build -t myapp:test .

# Generate SBOM
syft myapp:test -o spdx-json > sbom.spdx.json

# View packages
cat sbom.spdx.json | jq '.packages | length'
```

### Test Signing (Local Registry)

```bash
# Start local registry
docker run -d -p 5000:5000 --name registry registry:2

# Tag and push
docker tag myapp:test localhost:5000/myapp:test
docker push localhost:5000/myapp:test

# Sign (requires Cosign setup)
export COSIGN_EXPERIMENTAL=1
cosign sign localhost:5000/myapp:test

# Verify
cosign verify localhost:5000/myapp:test
```

## Kubernetes Deployment

### Deploy Application

```bash
# Create namespace
kubectl create namespace production

# Deploy
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Check status
kubectl get pods -n production
kubectl get svc -n production
```

### Test Policy Enforcement

Try to deploy an unsigned image:

```bash
# This should be blocked by Kyverno
kubectl run test --image=myregistry.io/myapp:unsigned -n production

# Check policy violations
kubectl get policyreports -n production
```

## CI/CD Integration

### GitHub Actions

The workflow in `.github/workflows/build-and-deploy.yml` includes all steps:

1. **Build** - Docker build and push
2. **SBOM** - Generate and attach SBOM
3. **Sign** - Sign image with Cosign
4. **Verify** - Verify signature
5. **Scan** - Check SBOM for CVEs
6. **Deploy** - Deploy to Kubernetes

### GitLab CI

Example `.gitlab-ci.yml`:

```yaml
build:
  stage: build
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - syft $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA -o spdx-json > sbom.spdx.json
    - cosign sign $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

### Jenkins

Example Jenkinsfile:

```groovy
pipeline {
  agent any
  stages {
    stage('Build') {
      steps {
        sh 'docker build -t myapp:${BUILD_NUMBER} .'
      }
    }
    stage('SBOM') {
      steps {
        sh 'syft myapp:${BUILD_NUMBER} -o spdx-json > sbom.spdx.json'
      }
    }
    stage('Sign') {
      steps {
        sh 'cosign sign myapp:${BUILD_NUMBER}'
      }
    }
  }
}
```

## Troubleshooting

### SBOM Generation Fails

**Issue:** Image not found locally

**Fix:** Pull image first or use remote scanning:

```bash
syft registry:ghcr.io/user/app:v1.0.0 -o spdx-json > sbom.spdx.json
```

### Signing Fails with OIDC Error

**Issue:** Missing permissions in GitHub Actions

**Fix:** Add permissions to workflow:

```yaml
permissions:
  id-token: write  # Required for keyless signing
```

### Policy Blocks All Images

**Issue:** Policy regex too strict

**Fix:** Check image pattern matches your registry:

```yaml
image: "ghcr.io/*"  # Make sure this matches your images
```

### Verification Fails in Cluster

**Issue:** OIDC issuer mismatch

**Fix:** Verify issuer matches your CI provider:

```yaml
issuer: "https://token.actions.githubusercontent.com"  # For GitHub Actions
```

## Best Practices

1. **Start in Audit Mode** - Log violations before enforcing
2. **Limit Scope** - Start with production namespace only
3. **Monitor Metrics** - Track % of signed images, policy violations
4. **Document Policies** - Make it clear what's blocked and why
5. **Test Locally** - Verify SBOM and signing work before CI
6. **Version SBOMs** - Store SBOMs with image digests
7. **Automate Everything** - Don't rely on manual steps

## Extending

### Add More Policies

Create new Kyverno policies:

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: your-policy
spec:
  rules:
  - name: your-rule
    # ... policy rules
```

### Integrate with Other Tools

- **Trivy** - CVE scanning
- **Grype** - Vulnerability scanning
- **OPA Gatekeeper** - Alternative to Kyverno
- **Falco** - Runtime security

### Store SBOMs in Dedicated System

Instead of attaching to images, store in:

- S3/GCS buckets
- Dedicated SBOM registry
- Security scanning platform

## Resources

- [Syft Documentation](https://github.com/anchore/syft)
- [Cosign Documentation](https://github.com/sigstore/cosign)
- [Kyverno Documentation](https://kyverno.io/)
- [SPDX Specification](https://spdx.dev/)
- [SLSA Framework](https://slsa.dev/)

## License

MIT

