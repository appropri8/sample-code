"""Example: Device-side bootstrap flow"""

from src.device_provisioner import DeviceProvisioner

# Initialize provisioner
provisioner = DeviceProvisioner(
    device_id="DEV-12345",
    factory_private_key_path="factory_key.pem",
    factory_cert_path="factory_cert.pem",
    bootstrap_url="https://bootstrap.yourapp.com"
)

# Attempt bootstrap
print("Starting bootstrap...")
result = provisioner.bootstrap()

if result:
    # Store temporary certificate
    with open('temp_cert.pem', 'w') as f:
        f.write(result['certificate'])
    
    print(f"Bootstrap successful!")
    print(f"Certificate expires in: {result['expires_in']} seconds")
    print(f"Platform URL: {result['platform_url']}")
else:
    print("Bootstrap failed, will retry with backoff")

