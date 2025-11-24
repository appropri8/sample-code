# Resilient OTA Updates for IoT - Code Examples

A complete implementation of OTA (Over-The-Air) update system for IoT devices with rollout, rollback, and safety checks.

## Features

- **Firmware Manifest**: Version, target hardware, hash, signature, and metadata
- **Device OTA Client**: Download, verify, install firmware with A/B partitions
- **Rollout Orchestrator**: Staged rollouts with device groups, rate limiting, and health monitoring
- **Health Checks**: Device health reporting with automatic rollback triggers
- **Safety Features**: A/B partitions, firmware signing, staged rollouts, observability

## Installation

### Python

```bash
pip install -r requirements.txt
```

## Quick Start

### Firmware Manifest

```python
from src.firmware_manifest import FirmwareManifest, create_manifest

# Create a firmware manifest
manifest = create_manifest(
    version="1.2.3",
    build_id="20251124-143022",
    target_hardware=["esp32-v2", "esp32-v3"],
    image_url="https://ota.example.com/firmware/1.2.3/esp32-v2.bin",
    image_size=1048576,
    image_hash="sha256:abc123def456...",
    signature="base64:xyz789...",
    min_bootloader_version="2.1.0"
)

# Save to file
manifest.save("manifests/firmware_manifest_v1.2.3.json")
```

### Device OTA Client

```python
from src.device_ota_client import DeviceOTAClient

# Initialize device client
client = DeviceOTAClient(
    device_id="device-12345",
    current_version="1.2.2",
    partition_a_path="/flash/partition_a.bin",
    partition_b_path="/flash/partition_b.bin",
    active_partition="A"
)

# Check for updates
update_available = client.check_for_updates("https://ota.example.com/manifests/latest.json")

if update_available:
    # Download firmware
    client.download_firmware()
    
    # Verify signature and hash
    if client.verify_firmware():
        # Install to inactive partition
        client.install_firmware()
        
        # Reboot device
        client.reboot()
    else:
        print("Firmware verification failed")
```

### Rollout Orchestrator

```python
from src.rollout_orchestrator import RolloutOrchestrator, DeviceGroup

# Initialize orchestrator
orchestrator = RolloutOrchestrator()

# Define rollout plan
plan = orchestrator.create_rollout_plan(
    firmware_version="1.2.3",
    target_groups=[
        DeviceGroup.CANARY,
        DeviceGroup.INTERNAL,
        DeviceGroup.PILOT,
        DeviceGroup.GENERAL
    ],
    batch_size_percentage=5,  # 5% per batch
    pause_conditions={
        "failure_rate_threshold": 0.01,  # 1% failure rate
        "rollback_rate_threshold": 0.01,  # 1% rollback rate
        "health_check_failure_rate": 0.10  # 10% health check failures
    }
)

# Execute rollout
orchestrator.execute_rollout(plan)
```

### Health Check Reporting

```python
from src.health_check import HealthReporter, HealthStatus

# Initialize health reporter
reporter = HealthReporter(
    device_id="device-12345",
    firmware_version="1.2.3",
    server_url="https://ota.example.com/api/health"
)

# Report health status
reporter.report_health(
    status=HealthStatus.OK,
    boot_count=1,
    watchdog_resets=0,
    can_connect_to_broker=True,
    can_send_heartbeat=True
)

# Check if rollback is needed
if reporter.should_rollback():
    reporter.trigger_rollback()
```

## Examples

See the `examples/` directory for complete examples:

- `firmware_manifest_example.py`: Creating and validating firmware manifests
- `device_client_example.py`: Complete device-side OTA update flow
- `rollout_example.py`: Staged rollout orchestration
- `health_check_example.py`: Health check reporting and rollback triggers

## Architecture

### Components

1. **Firmware Manifest** (`src/firmware_manifest.py`): Defines firmware metadata, version, target hardware, and signatures
2. **Device OTA Client** (`src/device_ota_client.py`): Handles device-side update operations (download, verify, install)
3. **Rollout Orchestrator** (`src/rollout_orchestrator.py`): Manages staged rollouts with device groups and rate limiting
4. **Health Check** (`src/health_check.py`): Reports device health and triggers rollbacks

### Design Principles

1. **Safety First**: A/B partitions, firmware signing, health checks, automatic rollback
2. **Staged Rollouts**: Canary → Internal → Pilot → General availability
3. **Observability**: Track all update events, failures, and rollbacks
4. **Resilience**: Handle network failures, corrupted downloads, and device failures gracefully

## Usage

### Running Examples

```bash
# Firmware manifest
python examples/firmware_manifest_example.py

# Device client
python examples/device_client_example.py

# Rollout orchestration
python examples/rollout_example.py

# Health check
python examples/health_check_example.py
```

### Running Tests

```bash
pytest
```

## Firmware Manifest Format

The firmware manifest is a JSON file that describes the update:

```json
{
  "version": "1.2.3",
  "build_id": "20251124-143022",
  "target_hardware": ["esp32-v2", "esp32-v3"],
  "min_bootloader_version": "2.1.0",
  "image": {
    "url": "https://ota.example.com/firmware/1.2.3/esp32-v2.bin",
    "size": 1048576,
    "hash": "sha256:abc123def456...",
    "signature": "base64:xyz789..."
  },
  "metadata": {
    "release_notes": "Security patch for CVE-2025-1234",
    "rollout_percentage": 0,
    "required": false
  }
}
```

## Device Update Flow

1. **Check for Updates**: Device queries OTA service for available updates
2. **Download Firmware**: Device downloads firmware to inactive partition (B)
3. **Verify Signature**: Device verifies firmware signature and hash
4. **Install**: Device marks partition B as ready for boot
5. **Reboot**: Device reboots and boots from partition B
6. **Health Check**: Device performs health checks after boot
7. **Rollback**: If health checks fail, device automatically boots from partition A

## Rollout Strategy

Rollouts proceed in stages:

1. **Canary** (1%): Internal test devices
2. **Internal** (5%): Team devices
3. **Pilot** (10%): Opt-in customers
4. **General** (100%): All devices

Each stage waits for health metrics before proceeding. If failure rate exceeds threshold, rollout pauses.

## Safety Features

- **A/B Partitions**: Always keep previous firmware available
- **Firmware Signing**: All firmware must be signed and verified
- **Staged Rollouts**: Update devices gradually, not all at once
- **Health Checks**: Verify device health after updates
- **Automatic Rollback**: Roll back on health check failures
- **Observability**: Track all update events and failures
- **Rate Limiting**: Don't update all devices at once
- **Scheduling**: Respect maintenance windows

## Limitations

- Simulated device operations (adapt for real hardware)
- Simplified network handling (add retry logic for production)
- Basic health checks (extend for your use case)

## Contributing

When adding features:

1. Add tests for new functionality
2. Update documentation
3. Follow the existing code structure
4. Add examples for new features

## License

This code is provided as example code for educational purposes. Adapt it to your specific requirements and use cases.

