# Safe Rollouts for AI Agents

Complete executable code samples demonstrating safe rollout patterns for AI agents: shadow mode, progressive delivery, quality gates, and kill switches.

## Overview

This repository contains a complete implementation of safe rollout patterns for AI agents:

- **Agent Versioning**: Version agents as first-class artifacts (prompt + tools + config + model)
- **Shadow Mode**: Run candidate agents on real traffic without affecting users
- **Progressive Delivery**: Gradual rollout from 1% to 100% with automatic rollback
- **Quality Gates**: Automated checks that block bad versions
- **Kill Switches**: Instant rollback without code deployment

## Architecture

```
User Request
    ↓
Router (Traffic Split)
    ├──→ Current Agent (v1.3.2) - 95% traffic
    ├──→ Candidate Agent (v1.3.3) - 5% traffic
    └──→ Shadow Agent (v1.3.4) - 0% (learning)
         ↓
    Metrics & Monitoring
         ↓
    Quality Gates → Kill Switch
```

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run Examples

```bash
# Shadow mode example
python scripts/example_shadow_mode.py

# Progressive rollout example
python scripts/example_rollout.py

# Quality gates example
python scripts/example_quality_gates.py

# Kill switch example
python scripts/example_kill_switch.py
```

### Run Tests

```bash
pytest tests/ -v
```

## Project Structure

```
.
├── src/
│   ├── agent_config.py          # Agent configuration with versioning
│   ├── agent.py                 # Agent implementation
│   ├── agent_factory.py         # Factory for creating agents
│   ├── shadow_mode.py           # Shadow mode router
│   ├── rollout_controller.py    # Progressive rollout controller
│   ├── quality_gates.py         # Quality gate checker
│   └── kill_switch.py           # Kill switch implementation
├── agents/
│   └── support-agent/
│       ├── v1.3.2.yaml          # Current version
│       ├── v1.3.3.yaml          # Candidate version
│       └── v1.3.4.yaml          # Shadow version
├── scripts/
│   ├── example_shadow_mode.py   # Shadow mode example
│   ├── example_rollout.py       # Progressive rollout example
│   ├── example_quality_gates.py # Quality gates example
│   └── example_kill_switch.py    # Kill switch example
├── tests/
│   ├── test_agent_config.py     # Config tests
│   ├── test_kill_switch.py     # Kill switch tests
│   └── test_quality_gates.py    # Quality gates tests
├── quality_gates.yaml           # Quality gate definitions
└── README.md
```

## Key Concepts

### 1. Agent Versioning

Agents are versioned as complete artifacts:

```python
from src.agent_config import AgentConfig

config = AgentConfig.load("support-agent", "v1.3.2")
```

Each version includes:
- Model configuration
- Prompt (system + instructions)
- Available tools
- Policies (max steps, cost limits, etc.)

### 2. Shadow Mode

Run candidate agents on real traffic without affecting users:

```python
from src.shadow_mode import ShadowModeRouter

router = ShadowModeRouter(
    agent_name="support-agent",
    current_version="v1.3.2",
    candidate_version="v1.3.3"
)

# User gets response from v1.3.2
# v1.3.3 runs in background and logs comparison
response = router.process("Search for user")
```

### 3. Progressive Rollout

Gradually increase traffic to new version:

```python
from src.rollout_controller import RolloutController, RolloutThresholds

controller = RolloutController(
    agent_name="support-agent",
    current_version="v1.3.2",
    candidate_version="v1.3.3",
    thresholds=RolloutThresholds()
)

# Check if user should get candidate version
if controller.should_use_candidate(user_id):
    version = "v1.3.3"
else:
    version = "v1.3.2"

# Record metrics
controller.record_metrics(version, error, latency_ms, cost, violations)

# Evaluate and advance
controller.evaluate_and_advance()
```

### 4. Quality Gates

Automated checks that block bad versions:

```python
from src.quality_gates import QualityGateChecker

checker = QualityGateChecker("quality_gates.yaml")

metrics = {
    "offline_quality_score": 0.87,
    "safety_checker_score": 0.96,
    "critical_scenarios": [...],
    "p95_latency_ms": 1500,
    "avg_cost_per_request": 0.45
}

all_passed, messages = checker.check_all(metrics)
```

### 5. Kill Switches

Instant rollback without code deployment:

```python
from src.kill_switch import KillSwitch

kill_switch = KillSwitch()

# Check if version is killed
if kill_switch.is_killed("support-agent", "v1.3.3"):
    version = "v1.3.2"  # Roll back
else:
    version = "v1.3.3"

# Kill a version (instant rollback)
kill_switch.kill_version(
    agent_name="support-agent",
    version="v1.3.3",
    reason="High error rate"
)
```

## Rollout Stages

1. **Shadow Mode**: Candidate runs on real traffic, responses not shown to users
2. **Canary 1%**: 1% of traffic goes to candidate
3. **Canary 5%**: 5% of traffic goes to candidate
4. **Canary 25%**: 25% of traffic goes to candidate
5. **Canary 50%**: 50% of traffic goes to candidate
6. **Full Rollout**: 100% of traffic goes to candidate

Each stage monitors metrics and automatically rolls back if thresholds are exceeded.

## Quality Gates

Quality gates are defined in `quality_gates.yaml`:

```yaml
gates:
  - name: "quality_score"
    type: "threshold"
    metric: "offline_quality_score"
    threshold: 0.85
    operator: ">="
  
  - name: "safety_score"
    type: "threshold"
    metric: "safety_checker_score"
    threshold: 0.95
    operator: ">="
```

Gates can be:
- **Threshold gates**: Check if a metric meets a threshold
- **Test suite gates**: Check if test suites pass

## Kill Switches

Kill switches can be:
- **Global**: Kill a version for all traffic
- **Feature-specific**: Kill a version for a specific feature
- **Tenant-specific**: Kill a version for a specific tenant

Kill switches are stored in JSON and can be updated without code deployment.

## Best Practices

1. **Always run shadow mode first**: Learn from real traffic without risk
2. **Start with small percentages**: 1% → 5% → 25% → 50% → 100%
3. **Monitor metrics at each stage**: Error rate, latency, cost, policy violations
4. **Set clear thresholds**: Automatic rollback if thresholds exceeded
5. **Have kill switches ready**: Instant rollback when things go wrong
6. **Version everything**: Prompt, tools, config, model all together
7. **Run quality gates**: Block bad versions before they reach production

## Extending

### Adding a New Agent Version

1. Create config file in `agents/{agent_name}/vX.Y.Z.yaml`
2. Update version number
3. Test in shadow mode
4. Run quality gates
5. Start progressive rollout

### Adding a New Quality Gate

1. Add gate definition to `quality_gates.yaml`
2. Ensure metrics are collected
3. Gate will be checked automatically

### Customizing Rollout Stages

Modify `RolloutStage` enum in `rollout_controller.py` to add or remove stages.

## Troubleshooting

### Shadow Mode Not Logging

- Check that candidate_version is set
- Verify logging is configured
- Check file permissions

### Rollout Not Advancing

- Check if metrics are being recorded
- Verify thresholds are not too strict
- Check minimum stage duration

### Kill Switch Not Working

- Verify kill_switches.json exists
- Check file permissions
- Ensure kill switch is checked in request handler

## Resources

- [Article: Safe Rollouts for AI Agents](https://appropri8.com/blog/2025/12/08/safe-rollouts-ai-agents-shadow-mode-progressive-delivery-kill-switches)
- [Feature Flags Best Practices](https://featureflags.io/best-practices)
- [Progressive Delivery Patterns](https://progressive-delivery.io/)

## License

MIT
