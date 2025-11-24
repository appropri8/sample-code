"""Example: Device registration with IoT platform"""

from src.platform_client import IoTPlatformClient

# Initialize platform client
client = IoTPlatformClient(
    device_id="DEV-12345",
    temp_cert_path="temp_cert.pem",
    temp_key_path="temp_key.pem",
    platform_url="https://iot.yourapp.com"
)

# Register device
print("Registering device with platform...")
registration_result = client.register(
    device_type="sensor-v2",
    firmware_version="1.2.3",
    capabilities=["temperature", "humidity", "motion"]
)

if registration_result:
    print(f"Device registered: {registration_result.get('device_record_id')}")
    
    # Get long-lived credentials
    print("Requesting long-lived credentials...")
    credentials = client.get_long_lived_credentials()
    
    if credentials:
        # Store long-lived certificate
        with open('device_cert.pem', 'w') as f:
            f.write(credentials['certificate'])
        print("Long-lived credentials received and stored")
    else:
        print("Failed to get long-lived credentials")
else:
    print("Registration failed")

