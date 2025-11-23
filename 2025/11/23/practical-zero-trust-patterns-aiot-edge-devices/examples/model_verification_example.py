"""Example: Model signature verification"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.model_verification import verify_model_signature, load_model_safely


def main():
    """Example of model verification"""
    # Paths (adjust to your setup)
    model_path = 'models/object_detector.tflite'
    signature_path = 'models/object_detector.sig'
    metadata_path = 'models/object_detector.json'
    public_key_path = '/etc/device/trusted_keys/model_signing_key.pem'
    
    print("Verifying model signature...")
    
    try:
        # Verify model
        metadata = verify_model_signature(
            model_path, 
            signature_path, 
            metadata_path,
            public_key_path
        )
        print(f"✓ Model verified: {metadata['model_id']} v{metadata['version']}")
        
        # Load model safely
        interpreter = load_model_safely(
            model_path,
            signature_path,
            metadata_path,
            public_key_path
        )
        print("✓ Model loaded successfully")
        
    except FileNotFoundError as e:
        print(f"✗ File not found: {e}")
        print("Note: This is a demo. Create test files to run.")
    except ValueError as e:
        print(f"✗ Verification failed: {e}")


if __name__ == '__main__':
    main()

