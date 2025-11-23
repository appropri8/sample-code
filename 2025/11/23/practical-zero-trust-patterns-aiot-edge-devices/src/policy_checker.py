"""Policy-based model allowlisting for edge devices"""

import yaml
from typing import Optional, Tuple


class ModelPolicyChecker:
    """Check if models are allowed based on policy"""
    
    def __init__(self, policy_path: str):
        """Initialize policy checker with policy file"""
        with open(policy_path, 'r') as f:
            self.policy = yaml.safe_load(f)
    
    def is_model_allowed(
        self, 
        model_id: str, 
        model_version: str, 
        device_group: str
    ) -> Tuple[bool, str]:
        """Check if model is allowed for this device"""
        # Find model in policy
        model_config = None
        for model in self.policy.get('allowed_models', []):
            if model['model_id'] == model_id:
                model_config = model
                break
        
        if not model_config:
            return False, "Model not in policy"
        
        # Check version is allowed
        if model_version not in model_config.get('allowed_versions', []):
            return False, f"Version {model_version} not in allowed list"
        
        # Check device group is allowed
        if device_group not in model_config.get('allowed_device_groups', []):
            return False, f"Device group {device_group} not allowed for this model"
        
        # Check version is not vulnerable
        vulnerable_key = f"{model_id}:{model_version}"
        if vulnerable_key in self.policy.get('vulnerable_versions', []):
            return False, f"Version {model_version} is marked as vulnerable"
        
        # Check version meets minimum safe version
        min_safe = model_config.get('min_safe_version')
        if min_safe and self._version_compare(model_version, min_safe) < 0:
            return False, f"Version {model_version} is below minimum safe version {min_safe}"
        
        return True, "Model allowed"
    
    def is_issuer_trusted(self, issuer: str) -> bool:
        """Check if issuer is trusted"""
        return issuer in self.policy.get('trusted_issuers', [])
    
    def _version_compare(self, v1: str, v2: str) -> int:
        """Compare version strings (simplified, assumes semantic versioning)"""
        v1_parts = [int(x) for x in v1.split('.')]
        v2_parts = [int(x) for x in v2.split('.')]
        
        for i in range(max(len(v1_parts), len(v2_parts))):
            v1_val = v1_parts[i] if i < len(v1_parts) else 0
            v2_val = v2_parts[i] if i < len(v2_parts) else 0
            
            if v1_val < v2_val:
                return -1
            elif v1_val > v2_val:
                return 1
        
        return 0


def check_model_before_loading(
    model_id: str,
    model_version: str,
    device_group: str,
    issuer: str,
    policy_path: str
) -> bool:
    """Check model against policy before loading (convenience function)"""
    checker = ModelPolicyChecker(policy_path)
    
    # Check issuer is trusted
    if not checker.is_issuer_trusted(issuer):
        raise ValueError(f"Issuer {issuer} is not trusted")
    
    # Check model is allowed
    allowed, reason = checker.is_model_allowed(model_id, model_version, device_group)
    if not allowed:
        raise ValueError(f"Model not allowed: {reason}")
    
    print(f"Model {model_id} v{model_version} is allowed for device group {device_group}")
    return True

