# CI/CD for Agentic AI: How to Ship Tool-Using Agents Without Breaking Production

Complete executable code samples demonstrating how to design CI/CD pipelines that treat agentic AI (multi-step, tool-using agents) as first-class deployable units.

## Overview

This repository contains implementations of CI/CD patterns for agentic AI systems:

- **Versioning**: Separate versioning for models, agents, and workflows
- **Testing**: Behavioral tests, eval suites, and static validation
- **Deployment**: Shadow, canary, and full rollout strategies
- **Observability**: Structured logging and metrics collection
- **Governance**: Safety toggles, tool permissions, and approval workflows

Both Python and TypeScript implementations are provided.

## Installation

### Python

```bash
cd python
pip install -r requirements.txt
```

### TypeScript

```bash
cd typescript
npm install
npm run build
```

## Prerequisites

- Python 3.11+ (for Python examples)
- Node.js 18+ (for TypeScript examples)
- Optional: OpenAI API key for eval suite tests

## Quick Start

### Python Example

```bash
cd python
python examples/shadow_deployment_example.py
```

### TypeScript Example

```bash
cd typescript
npm run dev -- examples/canary-example.ts
```

## Structure

```
.
├── python/
│   ├── src/
│   │   ├── agent.py              # Agent with versioning
│   │   ├── workflow.py           # Workflow with state management
│   │   ├── deployment/
│   │   │   ├── shadow.py         # Shadow deployment
│   │   │   ├── canary.py         # Canary deployment
│   │   │   └── full_rollout.py   # Full rollout with SLOs
│   │   ├── observability/
│   │   │   ├── logging.py         # Structured logging
│   │   │   └── metrics.py         # Metrics collection
│   │   └── governance/
│   │       ├── safety.py          # Safety toggles
│   │       └── approval.py        # Approval workflows
│   ├── examples/
│   │   ├── shadow_deployment_example.py
│   │   ├── canary_deployment_example.py
│   │   ├── observability_example.py
│   │   └── governance_example.py
│   ├── tests/
│   │   ├── test_agent_behavior.py
│   │   ├── test_eval_suite.py
│   │   └── test_observability.py
│   └── requirements.txt
│
├── typescript/
│   ├── src/
│   │   ├── agent.ts
│   │   ├── workflow.ts
│   │   └── deployment/
│   │       └── canary.ts
│   ├── examples/
│   │   └── canary-example.ts
│   ├── package.json
│   └── tsconfig.json
│
├── config/
│   └── tool_permissions.yaml      # Tool permissions config
│
├── .github/
│   └── workflows/
│       ├── ci.yml                 # CI pipeline
│       └── cd.yml                 # CD pipeline
│
└── README.md
```

## Key Patterns

### 1. Versioning Layers Separately

Version models, agents, and workflows independently:

**Python:**
```python
from src.agent import Agent, AgentRole

agent = Agent(
    role=AgentRole.PLANNER,
    model_config={"model": "gpt-4", "version": "2024-11-20"},
    tools=["search_kb", "create_ticket"],
    version="1.2.0"  # Agent version
)
```

**TypeScript:**
```typescript
import { Agent, AgentRole } from "./src/agent";

const agent = new Agent(
  AgentRole.PLANNER,
  { model: "gpt-4", temperature: 0.7 },
  ["search_kb", "create_ticket"],
  "1.2.0"  // Agent version
);
```

### 2. Behavioral Testing

Test agent behavior, not just code:

```python
def test_planner_selects_correct_tools():
    agent = Agent(...)
    result = agent.run({"input": "User wants to reset password"})
    
    assert "search_kb" in result["tools_called"]
    assert "create_ticket" in result["tools_called"]
```

### 3. Shadow Deployment

Mirror traffic to compare baseline and candidate:

```python
from src.deployment.shadow import ShadowDeployment

shadow = ShadowDeployment(
    baseline_workflow=baseline,
    candidate_workflow=candidate
)

result = shadow.run_shadow(input_data)
```

### 4. Canary Deployment

Route percentage of traffic to new version:

```python
from src.deployment.canary import CanaryDeployment

canary = CanaryDeployment(
    baseline_workflow=baseline,
    candidate_workflow=candidate,
    canary_percentage=0.01  # 1%
)

result = canary.route(input_data)
```

### 5. Observability

Structured logging and metrics:

```python
from src.observability.logging import AgentLogger
from src.observability.metrics import track_agent_execution

logger = AgentLogger()
logger.log_tool_call(
    trace_id=trace_id,
    agent_version="1.2.0",
    tool_name="search_kb",
    input={"query": "test"},
    output={"results": []},
    latency_ms=100,
    success=True
)

track_agent_execution(
    agent_version="1.2.0",
    success=True,
    latency_ms=150,
    tokens_used=1000,
    cost=0.01
)
```

### 6. Governance

Safety toggles and approval workflows:

```python
from src.governance.safety import SafetyToggles
from src.governance.approval import ApprovalWorkflow

safety = SafetyToggles()
can_write = safety.can_write("support_agent")
can_call = safety.can_call_tool("support_agent", "search_kb")

approval = ApprovalWorkflow()
if approval.requires_approval("update_billing"):
    approval_id = approval.request_approval(...)
```

## Examples

### Shadow Deployment

Compare baseline and candidate workflows:

```bash
cd python
python examples/shadow_deployment_example.py
```

### Canary Deployment

Gradual rollout with automatic rollback:

```bash
cd python
python examples/canary_deployment_example.py
```

### Observability

Structured logging and metrics:

```bash
cd python
python examples/observability_example.py
```

### Governance

Safety toggles and approvals:

```bash
cd python
python examples/governance_example.py
```

## Testing

### Python

```bash
cd python
pytest tests/ -v
```

### TypeScript

```bash
cd typescript
npm test
```

## CI/CD Pipelines

The repository includes GitHub Actions workflows:

- **CI Pipeline** (`.github/workflows/ci.yml`): Runs static checks, unit tests, eval suite, and observability tests
- **CD Pipeline** (`.github/workflows/cd.yml`): Deploys through shadow, canary, and full rollout stages

## Best Practices

1. **Version each layer separately** - Models, agents, and workflows
2. **Test behavior, not just code** - Use eval suites with gold test cases
3. **Deploy in stages** - Shadow → Canary → Full rollout
4. **Observe everything** - Log all tool calls, track metrics, emit traces
5. **Enforce governance** - Tool permissions, safety toggles, approvals
6. **Fail fast** - Rollback on error rate, latency, or cost spikes
7. **Monitor SLOs** - Track error rates, latency, availability

## Production Checklist

- [ ] All agents and workflows are versioned
- [ ] Tests cover planner + tool selection
- [ ] Eval suite exists and is part of CI
- [ ] Shadow + canary deployment paths in CD
- [ ] Observability + governance hooked in
- [ ] Tool permissions defined and enforced
- [ ] Approval workflows for destructive actions
- [ ] Cost and latency budgets set
- [ ] Rollback procedures documented
- [ ] Monitoring and alerting configured

## License

MIT

