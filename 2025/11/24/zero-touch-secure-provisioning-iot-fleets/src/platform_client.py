"""IoT platform client for device registration"""

import ssl
import json
import urllib.request
import urllib.error
from typing import Optional, Dict


class IoTPlatformClient:
    """Client for registering devices with IoT platform"""
    
    def __init__(self, device_id: str, temp_cert_path: str, temp_key_path: str, platform_url: str):
        """
        Initialize platform client
        
        Args:
            device_id: Device identifier
            temp_cert_path: Path to temporary certificate
            temp_key_path: Path to temporary private key
            platform_url: URL of IoT platform
        """
        self.device_id = device_id
        self.temp_cert_path = temp_cert_path
        self.temp_key_path = temp_key_path
        self.platform_url = platform_url
    
    def register(self, device_type: str = 'sensor-v2', firmware_version: str = '1.0.0', capabilities: list = None) -> Optional[Dict]:
        """
        Register device with IoT platform using temporary credentials
        
        Args:
            device_type: Type/model of device
            firmware_version: Firmware version string
            capabilities: List of device capabilities
            
        Returns:
            Registration result dictionary, or None on failure
        """
        if capabilities is None:
            capabilities = ['temperature', 'humidity']
        
        # Create registration request
        registration_data = {
            'device_id': self.device_id,
            'device_type': device_type,
            'firmware_version': firmware_version,
            'capabilities': capabilities
        }
        
        # Use temporary certificate for mTLS
        context = ssl.create_default_context()
        context.load_cert_chain(
            certfile=self.temp_cert_path,
            keyfile=self.temp_key_path
        )
        
        request_data = json.dumps(registration_data).encode('utf-8')
        req = urllib.request.Request(
            f"{self.platform_url}/devices/register",
            data=request_data,
            headers={'Content-Type': 'application/json'}
        )
        
        try:
            with urllib.request.urlopen(req, context=context, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result
        except urllib.error.HTTPError as e:
            print(f"Registration failed: {e.code} {e.reason}")
            return None
        except Exception as e:
            print(f"Registration error: {e}")
            return None
    
    def get_long_lived_credentials(self) -> Optional[Dict]:
        """
        Request long-lived credentials from platform
        
        Returns:
            Dictionary with long-lived certificate, or None on failure
        """
        context = ssl.create_default_context()
        context.load_cert_chain(
            certfile=self.temp_cert_path,
            keyfile=self.temp_key_path
        )
        
        req = urllib.request.Request(
            f"{self.platform_url}/devices/{self.device_id}/credentials",
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req, context=context, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result
        except urllib.error.HTTPError as e:
            print(f"Failed to get credentials: {e.code} {e.reason}")
            return None
        except Exception as e:
            print(f"Error getting credentials: {e}")
            return None

