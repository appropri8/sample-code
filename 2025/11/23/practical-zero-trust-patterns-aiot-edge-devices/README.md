# Practical Zero-Trust Patterns for AIoT Edge Devices

A collection of code samples demonstrating zero-trust security patterns for AIoT edge devices. This repository includes implementations for model signature verification, mutual TLS connections, and policy-based model allowlisting.

## Features

- **Model Signature Verification**: Verify model integrity before loading (C++ and Python)
- **Mutual TLS MQTT**: Secure MQTT connections with client certificates (Python and Node.js)
- **Policy-Based Allowlisting**: Device-side policy checking for model versions and device groups
- **Privacy Filters**: Basic PII redaction and data minimization patterns

## Installation

### Python

```bash
pip install -r requirements.txt
```

### Node.js

```bash
npm install
```

### C++ (for MCU)

Requires mbedTLS library. See `cpp/README.md` for build instructions.

## Quick Start

### Model Signature Verification

**Python:**

```python
from src.model_verification import verify_model_signature, load_model_safely

# Verify and load model
try:
    interpreter = load_model_safely(
        model_path='models/object_detector.tflite',
        signature_path='models/object_detector.sig',
        metadata_path='models/object_detector.json'
    )
    print("Model loaded successfully")
except ValueError as e:
    print(f"Model verification failed: {e}")
```

**C++:**

See `cpp/model_verification.cpp` for MCU implementation.

### Mutual TLS MQTT Connection

**Python:**

```python
from src.mqtt_client import create_mqtt_client, connect_with_retry
import os

device_id = os.environ.get('DEVICE_ID', 'device-001')
client = create_mqtt_client(device_id)

if connect_with_retry(client):
    client.publish(f"devices/{device_id}/telemetry", '{"temp": 25.5}')
```

**Node.js:**

```javascript
const { createMQTTClient } = require('./src/mqtt_client');

const client = createMQTTClient('device-001');
client.on('connect', () => {
  client.publish('devices/device-001/telemetry', JSON.stringify({ temp: 25.5 }));
});
```

### Policy-Based Allowlisting

```python
from src.policy_checker import ModelPolicyChecker

checker = ModelPolicyChecker('config/model_policy.yaml')

allowed, reason = checker.is_model_allowed(
    model_id='object_detector_v2',
    model_version='2.1.1',
    device_group='fleet-a'
)

if allowed:
    print(f"Model allowed: {reason}")
else:
    print(f"Model not allowed: {reason}")
```

## Examples

See the `examples/` directory for complete examples:

- `model_verification_example.py`: Model signature verification
- `mqtt_example.py`: mTLS MQTT connection
- `policy_check_example.py`: Policy-based allowlisting
- `privacy_filter_example.py`: PII redaction and data minimization

## Architecture

### Components

1. **Model Verification** (`src/model_verification.py`, `cpp/model_verification.cpp`): Verify model signatures and checksums before loading
2. **MQTT Client** (`src/mqtt_client.py`, `src/mqtt_client.js`): Secure MQTT connections with client certificates
3. **Policy Checker** (`src/policy_checker.py`): Device-side policy checking for models and updates
4. **Privacy Filters** (`src/privacy_filters.py`): Basic PII redaction and data minimization

## Design Principles

1. **Zero-Trust**: Verify everything, trust nothing
2. **Defense in Depth**: Multiple layers of security
3. **Fail Secure**: Refuse to operate if verification fails
4. **Least Privilege**: Minimal permissions for each component
5. **Privacy by Design**: Minimize and redact data at the edge

## Security Considerations

- **Key Management**: Store keys in secure elements or TPMs when possible
- **Certificate Rotation**: Implement certificate rotation mechanisms
- **Policy Updates**: Update policies securely via signed channels
- **Audit Logging**: Log all security events (verification failures, policy violations)

## Testing

Run the test suite:

```bash
# Python
pytest

# Node.js
npm test
```

## Limitations

- Model verification uses simple signature schemes (use hardware security modules in production)
- Privacy filters use basic regex patterns (use proper tools in production)
- Policy checker is simplified (add more sophisticated policy engines for production)

## Contributing

When adding features:

1. Add tests for new functionality
2. Update documentation
3. Consider security implications
4. Test with various edge cases

## License

This code is provided as example code for educational purposes. Adapt it to your specific requirements and use cases.

