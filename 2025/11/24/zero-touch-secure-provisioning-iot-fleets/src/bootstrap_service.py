"""Bootstrap service for device provisioning"""

from flask import Flask, request, jsonify
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# In production, load from secure database
DEVICE_REGISTRY: Dict[str, Dict] = {
    'DEV-12345': {
        'public_key': None,  # Load from database
        'manufacturing_date': '2025-11-01',
        'model': 'Sensor-V2'
    }
}

# CA for signing operational certificates (in production, load from secure storage)
OPERATIONAL_CA_KEY = None  # Load from secure storage
OPERATIONAL_CA_CERT = None  # Load from secure storage


def verify_factory_signature(device_id: str, csr_bytes: str, signature_hex: str, factory_cert_pem: str) -> bool:
    """
    Verify that CSR is signed by device's factory key
    
    Args:
        device_id: Device identifier
        csr_bytes: Certificate signing request as PEM string
        signature_hex: Hex-encoded signature
        factory_cert_pem: Factory certificate as PEM string
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Load factory certificate
        factory_cert = x509.load_pem_x509_certificate(
            factory_cert_pem.encode('utf-8'),
            default_backend()
        )
        
        # Get public key from certificate
        factory_public_key = factory_cert.public_key()
        
        # Verify signature
        factory_public_key.verify(
            bytes.fromhex(signature_hex),
            csr_bytes.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        logging.error(f"Signature verification failed: {e}")
        return False


def verify_device_in_registry(device_id: str) -> bool:
    """
    Check if device ID exists in registry
    
    Args:
        device_id: Device identifier
        
    Returns:
        True if device exists, False otherwise
    """
    return device_id in DEVICE_REGISTRY


def issue_short_lived_certificate(csr_pem: str, device_id: str) -> Optional[str]:
    """
    Issue a short-lived certificate (24 hours) for the device
    
    Args:
        csr_pem: Certificate signing request as PEM string
        device_id: Device identifier
        
    Returns:
        Certificate as PEM string, or None on error
    """
    try:
        # Load CSR
        csr = x509.load_pem_x509_csr(csr_pem.encode('utf-8'), default_backend())
        
        # In production, use proper CA signing
        # This is a simplified example
        if OPERATIONAL_CA_KEY is None or OPERATIONAL_CA_CERT is None:
            logging.error("CA key or certificate not loaded")
            return None
        
        # Create certificate (simplified - in production use proper CA)
        builder = x509.CertificateBuilder()
        builder = builder.subject_name(csr.subject)
        builder = builder.issuer_name(OPERATIONAL_CA_CERT.subject)
        builder = builder.public_key(csr.public_key())
        builder = builder.serial_number(x509.random_serial_number())
        builder = builder.not_valid_before(datetime.utcnow())
        builder = builder.not_valid_after(datetime.utcnow() + timedelta(hours=24))
        
        # Add device ID as extension
        builder = builder.add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(device_id)
            ]),
            critical=False
        )
        
        certificate = builder.sign(
            OPERATIONAL_CA_KEY,
            hashes.SHA256(),
            default_backend()
        )
        
        return certificate.public_bytes(serialization.Encoding.PEM).decode('utf-8')
    except Exception as e:
        logging.error(f"Failed to issue certificate: {e}")
        return None


@app.route('/bootstrap', methods=['POST'])
def bootstrap():
    """
    Bootstrap endpoint: verify device identity and issue temporary credentials
    """
    try:
        data = request.json
        device_id = data.get('device_id')
        csr = data.get('csr')
        signature = data.get('signature')
        factory_cert = data.get('factory_cert')
        
        if not device_id or not csr or not signature or not factory_cert:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Verify device exists in registry
        if not verify_device_in_registry(device_id):
            logging.warning(f"Unknown device ID: {device_id}")
            return jsonify({'error': 'Unknown device'}), 403
        
        # Verify factory signature
        if not verify_factory_signature(device_id, csr, signature, factory_cert):
            logging.warning(f"Invalid signature for device: {device_id}")
            return jsonify({'error': 'Invalid signature'}), 403
        
        # Issue short-lived certificate
        temp_cert = issue_short_lived_certificate(csr, device_id)
        if not temp_cert:
            return jsonify({'error': 'Failed to issue certificate'}), 500
        
        # Log provisioning event
        logging.info(f"Device provisioned: {device_id}")
        
        return jsonify({
            'certificate': temp_cert,
            'expires_in': 86400,  # 24 hours in seconds
            'platform_url': 'https://iot.yourapp.com'
        })
    
    except Exception as e:
        logging.error(f"Bootstrap error: {e}")
        return jsonify({'error': 'Internal error'}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    app.run(ssl_context='adhoc', host='0.0.0.0', port=443)

