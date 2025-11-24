"""Device-side provisioning client"""

import ssl
import json
import urllib.request
import urllib.error
import time
from typing import Optional, Dict
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography import x509
from cryptography.hazmat.backends import default_backend


class DeviceProvisioner:
    """Handles device-side provisioning flow"""
    
    def __init__(self, device_id: str, factory_private_key_path: str, factory_cert_path: str, bootstrap_url: str):
        """
        Initialize device provisioner
        
        Args:
            device_id: Unique device identifier
            factory_private_key_path: Path to factory private key
            factory_cert_path: Path to factory certificate
            bootstrap_url: URL of bootstrap service
        """
        self.device_id = device_id
        self.bootstrap_url = bootstrap_url
        self.factory_private_key = self._load_private_key(factory_private_key_path)
        self.factory_cert = self._load_certificate(factory_cert_path)
        self.max_retries = 5
        self.base_backoff = 1  # seconds
    
    def _load_private_key(self, path: str):
        """Load private key from file"""
        with open(path, 'rb') as f:
            return serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )
    
    def _load_certificate(self, path: str):
        """Load certificate from file"""
        with open(path, 'rb') as f:
            return x509.load_pem_x509_certificate(f.read(), default_backend())
    
    def generate_csr(self) -> Dict:
        """
        Generate a Certificate Signing Request for operational credentials
        
        Returns:
            Dictionary containing CSR, signature, and device info
        """
        # Generate new key pair for operations
        operational_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Create CSR
        csr = x509.CertificateSigningRequestBuilder().subject_name(
            x509.Name([
                x509.NameAttribute(x509.NameOID.COMMON_NAME, self.device_id),
            ])
        ).sign(operational_key, hashes.SHA256(), default_backend())
        
        # Sign CSR with factory key
        csr_bytes = csr.public_bytes(serialization.Encoding.PEM)
        signature = self.factory_private_key.sign(
            csr_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return {
            'device_id': self.device_id,
            'csr': csr_bytes.decode('utf-8'),
            'signature': signature.hex(),
            'factory_cert': self.factory_cert.public_bytes(
                serialization.Encoding.PEM
            ).decode('utf-8')
        }
    
    def sign_challenge(self, challenge: str) -> Dict:
        """
        Sign a challenge from the server using factory private key
        
        Args:
            challenge: Challenge string from server
            
        Returns:
            Dictionary containing challenge, signature, and device info
        """
        challenge_bytes = challenge.encode('utf-8')
        signature = self.factory_private_key.sign(
            challenge_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return {
            'device_id': self.device_id,
            'challenge': challenge,
            'signature': signature.hex(),
            'factory_cert': self.factory_cert.public_bytes(
                serialization.Encoding.PEM
            ).decode('utf-8')
        }
    
    def bootstrap(self, retry: bool = True) -> Optional[Dict]:
        """
        Connect to bootstrap endpoint and get temporary credentials
        
        Args:
            retry: Whether to retry on failure with exponential backoff
            
        Returns:
            Dictionary with certificate and platform URL, or None on failure
        """
        csr_data = self.generate_csr()
        request_data = json.dumps(csr_data).encode('utf-8')
        
        for attempt in range(self.max_retries if retry else 1):
            try:
                req = urllib.request.Request(
                    f"{self.bootstrap_url}/bootstrap",
                    data=request_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                # Use factory certificate for mTLS
                context = ssl.create_default_context()
                context.load_cert_chain(
                    certfile=self.factory_cert.public_bytes(serialization.Encoding.PEM).decode('utf-8'),
                    keyfile=None  # In real implementation, load from file
                )
                
                with urllib.request.urlopen(req, context=context, timeout=30) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    return result
                    
            except urllib.error.HTTPError as e:
                print(f"Bootstrap failed: {e.code} {e.reason}")
                if not retry or attempt == self.max_retries - 1:
                    return None
                    
            except Exception as e:
                print(f"Bootstrap error: {e}")
                if not retry or attempt == self.max_retries - 1:
                    return None
            
            # Exponential backoff
            if retry and attempt < self.max_retries - 1:
                wait_time = self.base_backoff * (2 ** attempt)
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        return None

