"""Policy and authorization for multi-tenant IoT devices"""

from typing import Optional
from cryptography import x509
from cryptography.hazmat.backends import default_backend


def extract_tenant_id_from_cert(cert_pem: str) -> Optional[str]:
    """
    Extract tenant ID from certificate
    
    Args:
        cert_pem: Certificate as PEM string
        
    Returns:
        Tenant ID if found, None otherwise
    """
    try:
        cert = x509.load_pem_x509_certificate(cert_pem.encode('utf-8'), default_backend())
        # Look for tenant ID in subject alternative name or custom extension
        # This is a simplified example - adapt to your certificate structure
        for ext in cert.extensions:
            if isinstance(ext.value, x509.SubjectAlternativeName):
                for name in ext.value:
                    if isinstance(name, x509.DNSName):
                        # Assuming format: tenant_id.device_id
                        parts = name.value.split('.')
                        if len(parts) >= 2:
                            return parts[0]
        return None
    except Exception:
        return None


def extract_device_id_from_cert(cert_pem: str) -> Optional[str]:
    """
    Extract device ID from certificate
    
    Args:
        cert_pem: Certificate as PEM string
        
    Returns:
        Device ID if found, None otherwise
    """
    try:
        cert = x509.load_pem_x509_certificate(cert_pem.encode('utf-8'), default_backend())
        # Get CN from subject
        for attr in cert.subject:
            if attr.oid == x509.NameOID.COMMON_NAME:
                return attr.value
        return None
    except Exception:
        return None


def get_telemetry_topic(tenant_id: str, device_id: str) -> str:
    """
    Get MQTT topic for device telemetry
    
    Args:
        tenant_id: Tenant identifier
        device_id: Device identifier
        
    Returns:
        Topic string
    """
    return f"devices/{tenant_id}/{device_id}/telemetry"


def get_command_topic(tenant_id: str, device_id: str) -> str:
    """
    Get MQTT topic for device commands
    
    Args:
        tenant_id: Tenant identifier
        device_id: Device identifier
        
    Returns:
        Topic string
    """
    return f"devices/{tenant_id}/{device_id}/commands"


def get_status_topic(tenant_id: str, device_id: str) -> str:
    """
    Get MQTT topic for device status
    
    Args:
        tenant_id: Tenant identifier
        device_id: Device identifier
        
    Returns:
        Topic string
    """
    return f"devices/{tenant_id}/{device_id}/status"


def can_publish(device_cert_pem: str, topic: str) -> bool:
    """
    Check if device can publish to topic based on certificate
    
    Args:
        device_cert_pem: Device certificate as PEM string
        topic: MQTT topic to check
        
    Returns:
        True if device can publish, False otherwise
    """
    tenant_id = extract_tenant_id_from_cert(device_cert_pem)
    device_id = extract_device_id_from_cert(device_cert_pem)
    
    if not tenant_id or not device_id:
        return False
    
    # Parse topic
    parts = topic.split('/')
    if len(parts) != 4 or parts[0] != 'devices':
        return False
    
    topic_tenant_id = parts[1]
    topic_device_id = parts[2]
    
    # Device can only publish to its own topics
    return tenant_id == topic_tenant_id and device_id == topic_device_id


def can_subscribe(device_cert_pem: str, topic: str) -> bool:
    """
    Check if device can subscribe to topic based on certificate
    
    Args:
        device_cert_pem: Device certificate as PEM string
        topic: MQTT topic to check
        
    Returns:
        True if device can subscribe, False otherwise
    """
    # Similar to can_publish, but may have different rules
    return can_publish(device_cert_pem, topic)


# Example IAM policy document (JSON format)
EXAMPLE_IAM_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["iot:Connect"],
            "Resource": "arn:aws:iot:region:account:client/${iot:Connection.Thing.ThingName}"
        },
        {
            "Effect": "Allow",
            "Action": ["iot:Publish"],
            "Resource": "arn:aws:iot:region:account:topic/devices/${iot:Connection.Thing.Attributes[tenant_id]}/${iot:Connection.Thing.ThingName}/*"
        },
        {
            "Effect": "Allow",
            "Action": ["iot:Subscribe"],
            "Resource": "arn:aws:iot:region:account:topicfilter/devices/${iot:Connection.Thing.Attributes[tenant_id]}/${iot:Connection.Thing.ThingName}/*"
        }
    ]
}

