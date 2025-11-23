"""Example: Policy-based model allowlisting"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.policy_checker import ModelPolicyChecker, check_model_before_loading


def main():
    """Example of policy checking"""
    policy_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'config', 
        'model_policy.yaml'
    )
    
    print("Loading policy...")
    checker = ModelPolicyChecker(policy_path)
    
    # Test cases
    test_cases = [
        {
            'model_id': 'object_detector_v2',
            'model_version': '2.1.1',
            'device_group': 'fleet-a',
            'issuer': 'your-ca',
            'expected': True
        },
        {
            'model_id': 'object_detector_v2',
            'model_version': '2.0.0',  # Vulnerable version
            'device_group': 'fleet-a',
            'issuer': 'your-ca',
            'expected': False
        },
        {
            'model_id': 'object_detector_v2',
            'model_version': '2.1.1',
            'device_group': 'fleet-c',  # Not allowed group
            'issuer': 'your-ca',
            'expected': False
        },
        {
            'model_id': 'object_detector_v2',
            'model_version': '2.1.1',
            'device_group': 'fleet-a',
            'issuer': 'untrusted-ca',  # Untrusted issuer
            'expected': False
        },
    ]
    
    print("\nRunning policy checks...\n")
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}:")
        print(f"  Model: {test['model_id']} v{test['model_version']}")
        print(f"  Device Group: {test['device_group']}")
        print(f"  Issuer: {test['issuer']}")
        
        # Check issuer
        if not checker.is_issuer_trusted(test['issuer']):
            result = False
            reason = "Issuer not trusted"
        else:
            # Check model
            result, reason = checker.is_model_allowed(
                test['model_id'],
                test['model_version'],
                test['device_group']
            )
        
        if result == test['expected']:
            print(f"  ✓ Result: {reason} (expected)")
        else:
            print(f"  ✗ Result: {reason} (unexpected)")
        
        print()
    
    # Example: Check before loading
    print("Example: Check before loading model...")
    try:
        check_model_before_loading(
            model_id='object_detector_v2',
            model_version='2.1.1',
            device_group='fleet-a',
            issuer='your-ca',
            policy_path=policy_path
        )
        print("✓ Model is allowed, proceeding with load")
    except ValueError as e:
        print(f"✗ Model not allowed: {e}")


if __name__ == '__main__':
    main()

