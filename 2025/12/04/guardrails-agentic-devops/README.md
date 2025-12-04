# Guardrails for Agentic DevOps: Designing Safe, Observable AI Ops Agents

Complete executable code samples demonstrating how to let AI agents touch real infrastructure without turning your cluster into a sandbox accident.

## Overview

This repository contains implementations of guardrail patterns for agentic DevOps systems:

- **Capability Boundaries**: RBAC, scopes, and sandboxes for least-privilege access
- **Policy Engine**: Open Policy Agent (OPA) integration for action authorization
- **Human-in-the-Loop**: Slack and ITSM approval workflows
- **Observability**: OpenTelemetry tracing for audit trails
- **Cost Limits**: Budget and rate limiting to prevent cost explosions

## Structure

```
.
├── k8s/
│   └── ops-agent-role.yaml          # Kubernetes RBAC example
├── config/
│   ├── tool-permissions.yaml       # Tool permission configuration
│   └── cost-limits.yaml            # Cost and rate limit configuration
├── policies/
│   └── deployment-scaling.rego      # OPA policy for deployment scaling
├── python/
│   ├── src/
│   │   ├── policy/
│   │   │   └── client.py            # Policy client for OPA
│   │   ├── approval/
│   │   │   ├── slack.py             # Slack approval integration
│   │   │   └── itsm.py              # ITSM approval integration
│   │   ├── observability/
│   │   │   └── tracing.py           # OpenTelemetry tracing
│   │   └── guardrails/
│   │       └── cost_limits.py       # Cost and rate limiting
│   ├── examples/
│   │   ├── policy_example.py        # Policy engine usage
│   │   ├── approval_example.py      # Approval workflows
│   │   ├── observability_example.py # Tracing examples
│   │   └── cost_limits_example.py   # Cost limits examples
│   └── requirements.txt
└── README.md
```

## Installation

### Prerequisites

- Python 3.11+
- Kubernetes cluster (for RBAC examples)
- Open Policy Agent (OPA) server (for policy examples)
- Optional: Slack webhook URL or ITSM API credentials (for approval examples)

### Python Setup

```bash
cd python
pip install -r requirements.txt
```

## Quick Start

### 1. Kubernetes RBAC

Apply the RBAC configuration to create a service account with least-privilege permissions:

```bash
kubectl apply -f k8s/ops-agent-role.yaml
```

This creates:
- Service account `ops-agent` in `production` namespace
- Role with read-only access to pods and deployments
- Limited write access (can scale, restart pods, but cannot delete)

### 2. Policy Engine

Start OPA server:

```bash
# Using Docker
docker run -d -p 8181:8181 openpolicyagent/opa run --server

# Load policy
curl -X PUT http://localhost:8181/v1/policies/deployment-scaling \
  --data-binary @policies/deployment-scaling.rego
```

Test policy:

```bash
cd python
python examples/policy_example.py
```

### 3. Cost Limits

Configure cost limits in `config/cost-limits.yaml`, then test:

```bash
cd python
python examples/cost_limits_example.py
```

### 4. Observability

Test tracing (uses console exporter by default):

```bash
cd python
python examples/observability_example.py
```

In production, configure OTLP endpoint:

```python
from src.observability import setup_tracer

setup_tracer(
    service_name="ops-agent",
    service_version="1.0.0",
    otlp_endpoint="http://jaeger:4317"  # Your observability backend
)
```

### 5. Approval Workflows

#### Slack Approval

1. Create a Slack webhook URL
2. Update `python/examples/approval_example.py` with your webhook URL
3. Run:

```bash
cd python
python examples/approval_example.py
```

#### ITSM Approval

1. Configure ITSM API credentials
2. Update `python/examples/approval_example.py` with your API URL and key
3. Run:

```bash
cd python
python examples/approval_example.py
```

## Key Patterns

### 1. Capability Boundaries (RBAC)

Define roles with least-privilege access:

```yaml
# k8s/ops-agent-role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
rules:
  - apiGroups: ["apps"]
    resources: ["deployments/scale"]
    verbs: ["update", "patch"]  # Can scale, but not delete
```

### 2. Policy Engine

Check actions before execution:

```python
from src.policy import PolicyClient, PolicyDecision

policy_client = PolicyClient("http://localhost:8181")

decision, reason = policy_client.authorize(
    tool="scale_deployment",
    parameters={"namespace": "production", "deployment": "api", "replicas": 10},
    context={
        "environment": "production",
        "time": "2025-12-04T14:23:00Z",
        "current_replicas": 5
    }
)

if decision == PolicyDecision.ALLOW:
    # Execute action
    pass
elif decision == PolicyDecision.ESCALATE:
    # Request human approval
    pass
```

### 3. Human Approval

Request approval via Slack:

```python
from src.approval import SlackApproval

slack_approval = SlackApproval(
    webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    channel="#ops-alerts"
)

approval_id = slack_approval.request_approval(
    trace_id="abc123",
    agent_name="ops-agent-v3",
    action={"tool": "scale_deployment", ...},
    plan_summary="Scale deployment from 5 to 10 replicas",
    diff="- replicas: 5\n+ replicas: 10"
)
```

### 4. Observability

Trace all agent actions:

```python
from src.observability import trace_tool_call

result = trace_tool_call(
    tool_name="scale_deployment",
    parameters={"namespace": "production", "deployment": "api", "replicas": 10},
    context={
        "agent_name": "ops-agent-v3",
        "agent_role": "operator",
        "environment": "production",
        "trace_id": "abc123"
    },
    execute_func=lambda: scale_deployment("production", "api", 10)
)
```

### 5. Cost Limits

Enforce budgets and rate limits:

```python
from src.guardrails import CostLimiter

cost_limiter = CostLimiter(config)

allowed, reason = cost_limiter.check_budget(
    agent_name="ops-agent",
    tool_name="scale_deployment",
    estimated_cost=0.01
)

if allowed:
    # Execute action
    cost_limiter.record_cost("ops-agent", "scale_deployment", 0.01)
```

## Configuration

### Tool Permissions

Define tool permissions and agent roles in `config/tool-permissions.yaml`:

```yaml
tools:
  - name: scale_deployment
    permission: write
    requires_approval: false

agent_roles:
  operator:
    allowed_permissions: ["read", "write"]
    max_scale_factor: 2.0
```

### Cost Limits

Configure budgets in `config/cost-limits.yaml`:

```yaml
agents:
  ops-agent:
    daily_budget_usd: 100.0
    per_request_max_usd: 1.0
    per_tool_limits:
      scale_deployment:
        max_calls_per_hour: 10
```

### OPA Policies

Write policies in Rego (see `policies/deployment-scaling.rego`):

```rego
package deployment.scaling

allow if {
    input.tool == "scale_deployment"
    input.context.environment != "production"
}

escalate if {
    input.tool == "scale_deployment"
    input.context.environment == "production"
    not is_business_hours(input.context.time)
}
```

## Best Practices

1. **Start with least privilege** - Give agents only the permissions they need
2. **Policy before execution** - Check policy before every tool call
3. **Human approval for risky actions** - Escalate destructive or high-risk actions
4. **Trace everything** - Use OpenTelemetry to track all agent actions
5. **Set cost limits** - Prevent budget overruns with hard limits
6. **Test in non-production** - Validate guardrails in staging first
7. **Monitor and alert** - Set up alerts for policy violations and cost thresholds

## Production Checklist

- [ ] RBAC roles defined and applied
- [ ] Policy engine configured and tested
- [ ] Approval workflows integrated (Slack/ITSM)
- [ ] Observability backend configured (Jaeger/Tempo)
- [ ] Cost limits configured and enforced
- [ ] Runbooks documented for agent-caused changes
- [ ] Alerts configured for policy violations
- [ ] Tested in staging environment

## Troubleshooting

### Policy Engine Not Responding

- Check OPA server is running: `curl http://localhost:8181/health`
- Verify policy is loaded: `curl http://localhost:8181/v1/policies`
- Check policy syntax: `opa test policies/`

### Approval Not Working

- Verify webhook URL is correct (Slack)
- Check API credentials (ITSM)
- Ensure channel exists and bot has permissions (Slack)

### Traces Not Appearing

- Check OTLP endpoint is reachable
- Verify tracer is initialized with correct endpoint
- Check observability backend is receiving data

## License

MIT

## Related Articles

- [Guardrails for Agentic DevOps: Designing Safe, Observable AI Ops Agents](https://appropri8.io/blog/2025/12/04/guardrails-agentic-devops)
