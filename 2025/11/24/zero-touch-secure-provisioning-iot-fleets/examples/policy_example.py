"""Example: Policy and authorization checks"""

from src.policy import (
    get_telemetry_topic,
    get_command_topic,
    can_publish,
    can_subscribe,
    EXAMPLE_IAM_POLICY
)

# Example: Get topic namespaces
tenant_id = "tenant-abc"
device_id = "DEV-12345"

telemetry_topic = get_telemetry_topic(tenant_id, device_id)
command_topic = get_command_topic(tenant_id, device_id)

print(f"Telemetry topic: {telemetry_topic}")
print(f"Command topic: {command_topic}")

# Example: Check authorization
device_cert = """
-----BEGIN CERTIFICATE-----
...certificate content...
-----END CERTIFICATE-----
"""

# Check if device can publish to its own telemetry topic
if can_publish(device_cert, telemetry_topic):
    print("Device can publish to telemetry topic")
else:
    print("Device cannot publish to telemetry topic")

# Check if device can subscribe to commands
if can_subscribe(device_cert, command_topic):
    print("Device can subscribe to command topic")
else:
    print("Device cannot subscribe to command topic")

# Show example IAM policy
print("\nExample IAM Policy:")
print(EXAMPLE_IAM_POLICY)

