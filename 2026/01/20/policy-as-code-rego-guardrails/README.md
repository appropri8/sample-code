# Policy-as-Code: Rego Guardrails for Terraform + Kubernetes

Complete executable code samples for enforcing policies in CI and at admission time using Rego/OPA.

## Structure

```
.
├── policies/
│   ├── terraform/
│   │   ├── iam.rego              # IAM least privilege policy
│   │   └── iam_test.rego         # Tests for IAM policy
│   └── kubernetes/
│       ├── podsecurity.rego      # Pod security baseline
│       ├── images.rego           # Approved registries + signatures
│       └── podsecurity_test.rego # Tests for pod security
├── gatekeeper/
│   ├── constrainttemplate.yaml   # Gatekeeper ConstraintTemplate
│   └── constraint.yaml           # Gatekeeper Constraint
├── examples/
│   ├── terraform/
│   │   ├── good-iam.tf           # Compliant IAM policy
│   │   └── bad-iam.tf            # Non-compliant IAM policy
│   └── kubernetes/
│       ├── good-pod.yaml         # Compliant pod
│       └── bad-pod.yaml          # Non-compliant pod
├── .github/
│   └── workflows/
│       └── policy-check.yml      # CI workflow
├── exceptions.yaml                # Allow-list for exceptions
└── requirements.txt               # Python dependencies (if needed)

```

## Quick Start

### 1. Test Policies Locally

```bash
# Install conftest
brew install conftest  # macOS
# or
wget https://github.com/open-policy-agent/conftest/releases/download/v0.45.0/conftest_0.45.0_Linux_x86_64.tar.gz
tar xzf conftest_0.45.0_Linux_x86_64.tar.gz
sudo mv conftest /usr/local/bin

# Test Terraform policies
cd examples/terraform
terraform init
terraform plan -out=tfplan.binary
terraform show -json tfplan.binary > tfplan.json
conftest test tfplan.json -p ../../policies/terraform/

# Test Kubernetes policies
conftest test ../kubernetes/*.yaml -p ../../policies/kubernetes/
```

### 2. Deploy Gatekeeper

```bash
# Install Gatekeeper
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/release-3.14/deploy/gatekeeper.yaml

# Wait for readiness
kubectl wait --for=condition=Ready pod -l control-plane=controller-manager -n gatekeeper-system --timeout=90s

# Deploy policies
kubectl apply -f gatekeeper/constrainttemplate.yaml
kubectl apply -f gatekeeper/constraint.yaml
```

### 3. Test Enforcement

```bash
# Try to create a non-compliant pod (should be blocked)
kubectl apply -f examples/kubernetes/bad-pod.yaml

# Create a compliant pod (should succeed)
kubectl apply -f examples/kubernetes/good-pod.yaml
```

## Policies

### Terraform IAM Policy

Enforces least privilege by blocking:
- Wildcard actions (`*`)
- Wildcard resources (`*`)
- Overly broad service permissions (e.g., `s3:*`)

### Kubernetes Pod Security Policy

Enforces:
- Containers must run as non-root
- Read-only root filesystem
- No privileged mode
- Privilege escalation disabled

### Kubernetes Image Policy

Enforces:
- Only approved registries
- Image digests instead of tags

## CI Integration

The GitHub Actions workflow (`.github/workflows/policy-check.yml`) automatically runs policy checks on PRs.

## Exceptions

Document exceptions in `exceptions.yaml`. All exceptions require:
- Documentation of why it's needed
- Review and approval
- Migration plan (if temporary)

## Testing

Run policy tests:

```bash
conftest test --policy policies/ policies/**/*_test.rego
```

## License

MIT
