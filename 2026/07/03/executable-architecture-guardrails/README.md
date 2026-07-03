# Executable Architecture Guardrails

Complete executable code samples for turning architecture principles into automated guardrails.

## Structure

```
.
├── service.yaml                    # Service metadata template
├── slo.yaml                        # Service-level objectives
├── openapi.yaml                    # API contract with security
├── policies/
│   ├── terraform/
│   │   ├── require_tags.rego       # Tag and backup policy
│   │   └── require_tags_test.rego  # Policy tests
│   └── kubernetes/
│       ├── api_auth.rego           # Public API auth requirement
│       └── resource_limits.yaml    # Kyverno resource limits
├── .github/
│   └── workflows/
│       └── architecture-guardrails.yml # CI pipeline gates
├── scripts/
│   ├── check-owner.sh              # Ownership fitness function
│   ├── check_openapi_security.py   # OpenAPI security validation
│   └── setup_telemetry.py          # OpenTelemetry instrumentation
├── examples/
│   ├── terraform/
│   │   └── good-database.tf        # Compliant database config
│   └── kubernetes/
│       └── good-service.yaml       # Compliant service manifest
└── requirements.txt                # Python dependencies
```

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/appropri8/sample-code.git
cd sample-code/2026/07/03/executable-architecture-guardrails
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
brew install conftest  # macOS
```

### 3. Run fitness functions locally

```bash
bash scripts/check-owner.sh payment-api
python scripts/check_openapi_security.py openapi.yaml
```

### 4. Test policies locally

```bash
conftest test examples/terraform/good-database.tf -p policies/terraform/
conftest test policies/kubernetes/*.yaml
```

### 5. Deploy CI pipeline

Copy `.github/workflows/architecture-guardrails.yml` into your repository. The pipeline runs automatically on every PR.

## Key Samples

### Service Metadata

`service.yaml` defines ownership, tier, data classification, and SLOs. This single file feeds CI checks, admission policies, scorecards, and cost dashboards.

### Policy-as-Code

- `policies/terraform/require_tags.rego`: Enforces owner, environment, and backup tags on all Terraform resources.
- `policies/kubernetes/api_auth.rego`: Blocks public LoadBalancer services without authentication policies.

### CI Pipeline

`.github/workflows/architecture-guardrails.yml` runs four checks on every PR:
1. Validates `service.yaml` exists.
2. Runs Rego policies against Terraform and Kubernetes manifests.
3. Validates OpenAPI security schemes.
4. Checks for SLO definition.

### Runtime Telemetry

`scripts/setup_telemetry.py` is a golden-path instrumentation snippet for Python services. It configures OTLP traces and metrics with minimal boilerplate.

### Fitness Functions

`scripts/check-owner.sh` enforces ownership at CI time. `scripts/check_openapi_security.py` enforces API security contracts.

## License

MIT
