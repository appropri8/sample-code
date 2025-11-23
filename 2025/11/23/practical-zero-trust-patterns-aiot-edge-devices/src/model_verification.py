"""Model signature verification for edge devices"""

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
import json
import hashlib
import os


class ModelVerifier:
    """Verify model signatures and checksums before loading"""
    
    def __init__(self, public_key_path):
        """Initialize verifier with public key"""
        with open(public_key_path, 'rb') as f:
            self.public_key = serialization.load_pem_public_key(
                f.read(), backend=default_backend()
            )
    
    def verify_signature(self, model_data, signature):
        """Verify model signature"""
        try:
            self.public_key.verify(
                signature,
                model_data,
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except Exception as e:
            print(f"Signature verification failed: {e}")
            return False
    
    def verify_checksum(self, model_data, expected_hash):
        """Verify model checksum"""
        computed_hash = hashlib.sha256(model_data).hexdigest()
        return computed_hash == expected_hash
    
    def load_metadata(self, metadata_path):
        """Load model metadata"""
        with open(metadata_path, 'r') as f:
            return json.load(f)
    
    def verify_model(self, model_path, signature_path, metadata_path):
        """Verify model signature and checksum"""
        # Load model data
        with open(model_path, 'rb') as f:
            model_data = f.read()
        
        # Load signature
        with open(signature_path, 'rb') as f:
            signature = f.read()
        
        # Load metadata
        metadata = self.load_metadata(metadata_path)
        
        # Verify signature
        if not self.verify_signature(model_data, signature):
            return False, "Signature verification failed"
        
        # Verify checksum
        if not self.verify_checksum(model_data, metadata['sha256']):
            return False, "Checksum mismatch"
        
        # Check version is allowed
        allowed_versions = metadata.get('allowed_versions', [])
        if metadata['version'] not in allowed_versions:
            return False, f"Version {metadata['version']} not in allowed list"
        
        return True, metadata


def verify_model_signature(model_path, signature_path, metadata_path, public_key_path=None):
    """Verify model signature before loading (convenience function)"""
    if public_key_path is None:
        public_key_path = os.getenv('MODEL_SIGNING_PUBLIC_KEY', '/etc/device/trusted_keys/model_signing_key.pem')
    
    verifier = ModelVerifier(public_key_path)
    success, result = verifier.verify_model(model_path, signature_path, metadata_path)
    
    if not success:
        raise ValueError(f"Model verification failed: {result}")
    
    return result


def load_model_safely(model_path, signature_path, metadata_path, public_key_path=None):
    """Load model only if signature and checksum verify"""
    # Verify first
    metadata = verify_model_signature(model_path, signature_path, metadata_path, public_key_path)
    
    print(f"Model verified: {metadata['model_id']} v{metadata['version']}")
    
    # Load model (example for TensorFlow Lite)
    try:
        import tflite_runtime.interpreter as tflite
        interpreter = tflite.Interpreter(model_path=model_path)
        interpreter.allocate_tensors()
        return interpreter
    except ImportError:
        # Fallback: just return model path if tflite not available
        print("TensorFlow Lite not available, returning model path")
        return model_path

