"""Example: Complete provisioning flow from bootstrap to activation"""

from src.device_provisioner import DeviceProvisioner
from src.platform_client import IoTPlatformClient
import os

# Step 1: Bootstrap
print("=== Step 1: Bootstrap ===")
provisioner = DeviceProvisioner(
    device_id="DEV-12345",
    factory_private_key_path="factory_key.pem",
    factory_cert_path="factory_cert.pem",
    bootstrap_url="https://bootstrap.yourapp.com"
)

bootstrap_result = provisioner.bootstrap()
if not bootstrap_result:
    print("Bootstrap failed, exiting")
    exit(1)

# Save temporary certificate
with open('temp_cert.pem', 'w') as f:
    f.write(bootstrap_result['certificate'])

print(f"✓ Bootstrap successful")
print(f"  Certificate expires in: {bootstrap_result['expires_in']} seconds")
print(f"  Platform URL: {bootstrap_result['platform_url']}")

# Step 2: Register with platform
print("\n=== Step 2: Platform Registration ===")
platform_client = IoTPlatformClient(
    device_id="DEV-12345",
    temp_cert_path="temp_cert.pem",
    temp_key_path="temp_key.pem",  # In real implementation, extract from CSR
    platform_url=bootstrap_result['platform_url']
)

registration_result = platform_client.register(
    device_type="sensor-v2",
    firmware_version="1.2.3",
    capabilities=["temperature", "humidity"]
)

if not registration_result:
    print("Registration failed, exiting")
    exit(1)

print(f"✓ Device registered")
print(f"  Device record ID: {registration_result.get('device_record_id')}")

# Step 3: Get long-lived credentials
print("\n=== Step 3: Long-Lived Credentials ===")
credentials = platform_client.get_long_lived_credentials()
if not credentials:
    print("Failed to get long-lived credentials")
    exit(1)

# Save long-lived certificate
with open('device_cert.pem', 'w') as f:
    f.write(credentials['certificate'])

print(f"✓ Long-lived credentials received")
print(f"  Certificate valid until: {credentials.get('expires_at')}")

# Step 4: Cleanup temporary files
print("\n=== Step 4: Cleanup ===")
if os.path.exists('temp_cert.pem'):
    os.remove('temp_cert.pem')
    print("✓ Temporary certificate removed")

print("\n=== Provisioning Complete ===")
print("Device is now fully provisioned and ready for activation")

