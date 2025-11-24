# Zero-Touch Secure Provisioning for IoT Fleets

A complete reference implementation for zero-touch device provisioning in IoT fleets. This repository demonstrates how to securely onboard thousands of devices without manual configuration, using PKI-based authentication and automated credential management.

## Features

- **Device-Side Provisioning**: Automated bootstrap flow with CSR generation and factory key signing
- **Bootstrap Service**: Server-side service that verifies device identity and issues temporary credentials
- **Platform Registration**: Device registration with IoT platform and long-lived credential rotation
- **Multi-Tenant Policies**: Topic-based isolation and authorization for multi-tenant deployments
- **Security Best Practices**: PKI, mTLS, short-lived credentials, and key rotation

## Architecture

The provisioning flow consists of four main phases:

1. **Manufacturing**: Device gets unique ID and key pair, stored in secure registry
2. **Bootstrap**: Device proves identity and receives temporary credentials
3. **Registration**: Device registers with IoT platform and gets long-lived credentials
4. **Activation**: Device is bound to tenant and policies are applied

## Installation

### Python

```bash
pip install -r requirements.txt
```

## Quick Start

### Device Bootstrap

```python
from src.device_provisioner import DeviceProvisioner

# Initialize provisioner
provisioner = DeviceProvisioner(
    device_id="DEV-12345",
    factory_private_key_path="factory_key.pem",
    factory_cert_path="factory_cert.pem",
    bootstrap_url="https://bootstrap.yourapp.com"
)

# Bootstrap device
result = provisioner.bootstrap()
if result:
    # Store temporary certificate
    with open('temp_cert.pem', 'w') as f:
        f.write(result['certificate'])
    print("Bootstrap successful")
```

### Bootstrap Service

```python
from src.bootstrap_service import app

# Run bootstrap service
if __name__ == '__main__':
    app.run(ssl_context='adhoc', host='0.0.0.0', port=443)
```

### Platform Registration

```python
from src.platform_client import IoTPlatformClient

# Initialize platform client
client = IoTPlatformClient(
    device_id="DEV-12345",
    temp_cert_path="temp_cert.pem",
    temp_key_path="temp_key.pem",
    platform_url="https://iot.yourapp.com"
)

# Register device
registration_result = client.register(
    device_type="sensor-v2",
    firmware_version="1.2.3",
    capabilities=["temperature", "humidity"]
)

# Get long-lived credentials
credentials = client.get_long_lived_credentials()
```

## Examples

See the `examples/` directory for complete examples:

- `device_bootstrap_example.py`: Device-side bootstrap flow
- `platform_registration_example.py`: Platform registration and credential rotation
- `policy_example.py`: Multi-tenant policy and authorization
- `complete_flow_example.py`: End-to-end provisioning flow

## Components

### Device Provisioner (`src/device_provisioner.py`)

Handles device-side provisioning:
- Generates Certificate Signing Requests (CSR)
- Signs challenges with factory private key
- Connects to bootstrap service with mTLS
- Implements exponential backoff for retries

### Bootstrap Service (`src/bootstrap_service.py`)

Server-side bootstrap endpoint:
- Verifies device identity using factory certificates
- Validates CSR signatures
- Issues short-lived certificates (24 hours)
- Logs provisioning events

### Platform Client (`src/platform_client.py`)

IoT platform integration:
- Registers devices using temporary credentials
- Requests long-lived credentials
- Handles certificate rotation

### Policy (`src/policy.py`)

Multi-tenant authorization:
- Topic namespace generation (per-tenant isolation)
- Certificate-based authorization checks
- MQTT topic access control
- Example IAM policy documents

## Security Considerations

### Production Deployment

This is a reference implementation. For production use:

1. **Secure Key Storage**: Use hardware security modules (HSM) or secure elements for key storage
2. **Certificate Authority**: Set up proper CA hierarchy (root CA, intermediate CA, device CA)
3. **Database**: Use secure database for device registry (encrypted at rest, access controlled)
4. **Rate Limiting**: Implement rate limiting and DDoS protection on bootstrap endpoint
5. **Monitoring**: Add comprehensive logging and alerting for provisioning events
6. **Revocation**: Implement certificate revocation lists (CRL) or OCSP
7. **Key Rotation**: Implement automated key rotation for long-lived credentials

### Device Constraints

This implementation assumes:
- Device has sufficient resources for TLS and cryptography operations
- Device can store certificates securely (encrypted flash or secure element)
- Device has network connectivity for bootstrap

For resource-constrained devices (MCUs), consider:
- Lightweight TLS implementations (mbedTLS, WolfSSL)
- Certificate pinning instead of full CA chain validation
- Simplified bootstrap flow with fewer round trips

## Testing

Run tests with pytest:

```bash
pytest
```

With coverage:

```bash
pytest --cov=src --cov-report=html
```

## Design Principles

1. **Zero-Touch**: Devices provision automatically without human intervention
2. **Security First**: PKI-based authentication, mTLS, short-lived credentials
3. **Scalable**: Designed for thousands of devices
4. **Observable**: Comprehensive logging and metrics
5. **Resilient**: Retry logic, backoff, and error handling

## Adapting for Your Stack

This code is language-agnostic in concepts but Python in implementation. To adapt:

1. **Device Side**: Port to C/C++ for embedded devices, or use MicroPython
2. **Bootstrap Service**: Port to Node.js, Go, or your preferred backend language
3. **Platform**: Integrate with AWS IoT Core, Azure IoT Hub, or your custom platform
4. **Protocols**: Adapt for CoAP, MQTT, or HTTP-based provisioning

## Common Patterns

### Manufacturing Integration

- Generate device IDs and key pairs during manufacturing
- Store public keys in secure database
- Embed factory certificates in firmware
- Track manufacturing metadata (date, batch, model)

### Activation Flow

- Customer receives device with claim code or QR code
- Customer enters code in web portal or mobile app
- System binds device ID to customer account (tenant)
- Device receives tenant-specific policies

### Reprovisioning

- Device reset clears tenant assignment
- Device goes through bootstrap again
- New owner activates device
- Device gets new tenant assignment

## Limitations

This is example code for educational purposes:

- Simplified certificate issuance (use proper CA in production)
- In-memory device registry (use database in production)
- Basic error handling (add comprehensive error handling)
- No revocation implementation (add CRL/OCSP)
- No key rotation automation (implement scheduled rotation)

## Contributing

When adapting this code:

1. Add proper error handling and logging
2. Implement secure key storage
3. Add comprehensive tests
4. Follow security best practices
5. Document your changes

## License

This code is provided as example code for educational purposes. Adapt it to your specific requirements and use cases.

## Related Resources

- [Article: Zero-Touch Secure Provisioning for Large IoT Fleets](/blog/2025/11/24/zero-touch-secure-provisioning-iot-fleets)
- PKI Best Practices for IoT
- mTLS Configuration Guides
- Certificate Lifecycle Management

