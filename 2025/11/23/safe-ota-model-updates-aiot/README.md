# Safe OTA Model Updates for AIoT

A collection of code samples demonstrating safe over-the-air (OTA) model update patterns for AIoT edge devices. This repository includes implementations for A/B slot management, canary rollouts, health monitoring, and gradual deployment strategies.

## Features

- **A/B Slot Management**: Safe model activation with rollback support
- **OTA Agent**: Device-side update agent with signature verification
- **Health Monitoring**: Real-time health checks and automatic rollback
- **Metrics Emission**: Device metrics collection and reporting
- **Deployment Manifests**: Cloud-side rollout configuration
- **Canary Rollouts**: Gradual deployment with cohort management

## Installation

### Python

```bash
pip install -r requirements.txt
```

## Quick Start

### OTA Agent

**Python:**

```python
from src.ota_agent import OTAAgent
import os

# Create OTA agent
agent = OTAAgent(
    device_id=os.environ.get("DEVICE_ID", "device-001"),
    ota_service_url=os.environ.get("OTA_SERVICE_URL", "https://ota.example.com")
)

# Poll for updates and apply
manifest = agent.poll_for_updates()
if manifest:
    success = agent.apply_update(manifest)
    if success:
        print(f"Update applied: {manifest['version']}")
```

### Health Monitor

```python
from src.health_monitor import HealthMonitor

monitor = HealthMonitor()
metrics = monitor.get_current_metrics()

# Check if metrics are within thresholds
if monitor.check_health(metrics, thresholds):
    print("Device is healthy")
else:
    print("Device health check failed")
```

### Metrics Emitter

```python
from src.metrics_emitter import MetricsEmitter
import paho.mqtt.client as mqtt

# Create MQTT client
mqtt_client = mqtt.Client()
mqtt_client.connect("iot.example.com", 8883)

# Create metrics emitter
emitter = MetricsEmitter("device-001", mqtt_client)

# Record inference and emit metrics
emitter.record_inference(latency_ms=45.2, success=True)
emitter.emit_metrics()
```

## Examples

See the `examples/` directory for complete examples:

- `ota_agent_example.py`: Basic OTA agent usage
- `health_monitor_example.py`: Health monitoring and rollback
- `metrics_emitter_example.py`: Metrics collection and reporting
- `canary_rollout_example.py`: Canary rollout simulation

## Architecture

### Components

1. **OTA Agent** (`src/ota_agent.py`): Device-side update agent that polls for updates, downloads models, verifies signatures, and applies updates to A/B slots
2. **Health Monitor** (`src/health_monitor.py`): Monitors device health metrics (CPU, RAM, latency, errors) and triggers rollback if thresholds are exceeded
3. **Metrics Emitter** (`src/metrics_emitter.py`): Collects and emits device metrics to the cloud via MQTT or HTTP
4. **Deployment Manifest** (`config/deployment-manifest.yaml`): Cloud-side configuration for model rollouts

## Design Principles

1. **Safe Activation**: Always verify before applying, always have rollback path
2. **Gradual Rollouts**: Start small, expand gradually, monitor closely
3. **Health Monitoring**: Continuous health checks with automatic rollback
4. **Atomic Switches**: Model slot switching is atomic, no partial state
5. **Resumable Downloads**: Handle network interruptions gracefully

## Usage Patterns

### A/B Slot Pattern

```python
# Download to slot B
agent.download_to_slot_b(manifest)

# Verify signature
if agent.verify_signature(manifest):
    # Switch to slot B
    agent.switch_to_slot_b()
    
    # Run health checks
    if agent.run_health_checks(manifest):
        # Mark slot B as stable
        agent.mark_slot_stable("B")
    else:
        # Roll back to slot A
        agent.rollback_to_slot_a()
```

### Canary Rollout

```python
# Deploy to canary group (1% of devices)
manifest = {
    "target_cohort": "region:us-east AND hw:rev2",
    "rollout_percentage": 1
}

# Monitor health
if health_metrics_ok:
    # Expand to 5%
    manifest["rollout_percentage"] = 5
```

## Testing

Run the test suite:

```bash
pytest
```

## Limitations

- OTA agent uses simple polling (use push notifications in production)
- Health checks use basic thresholds (tune per model and device)
- Metrics emission is simplified (add batching and compression in production)
- Signature verification uses basic schemes (use hardware security modules in production)

## Contributing

When adding features:

1. Add tests for new functionality
2. Update documentation
3. Consider edge cases (network failures, device reboots, etc.)
4. Test with various device configurations

## License

This code is provided as example code for educational purposes. Adapt it to your specific requirements and use cases.

