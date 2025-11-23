"""Tests for policy checker"""

import pytest
import os
import tempfile
import yaml
from src.policy_checker import ModelPolicyChecker


@pytest.fixture
def sample_policy():
    """Create a sample policy file"""
    policy = {
        'allowed_models': [
            {
                'model_id': 'test_model',
                'allowed_versions': ['1.0.0', '1.0.1'],
                'allowed_device_groups': ['fleet-a'],
                'issuer': 'test-ca',
                'min_safe_version': '1.0.0'
            }
        ],
        'vulnerable_versions': ['test_model:0.9.0'],
        'trusted_issuers': ['test-ca']
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(policy, f)
        temp_path = f.name
    
    yield temp_path
    
    os.unlink(temp_path)


def test_model_allowed(sample_policy):
    """Test that allowed model passes"""
    checker = ModelPolicyChecker(sample_policy)
    allowed, reason = checker.is_model_allowed('test_model', '1.0.0', 'fleet-a')
    assert allowed is True
    assert 'allowed' in reason.lower()


def test_model_version_not_allowed(sample_policy):
    """Test that disallowed version fails"""
    checker = ModelPolicyChecker(sample_policy)
    allowed, reason = checker.is_model_allowed('test_model', '2.0.0', 'fleet-a')
    assert allowed is False
    assert 'version' in reason.lower() or 'not' in reason.lower()


def test_device_group_not_allowed(sample_policy):
    """Test that disallowed device group fails"""
    checker = ModelPolicyChecker(sample_policy)
    allowed, reason = checker.is_model_allowed('test_model', '1.0.0', 'fleet-b')
    assert allowed is False
    assert 'group' in reason.lower() or 'not' in reason.lower()


def test_vulnerable_version_rejected(sample_policy):
    """Test that vulnerable version is rejected"""
    checker = ModelPolicyChecker(sample_policy)
    allowed, reason = checker.is_model_allowed('test_model', '0.9.0', 'fleet-a')
    assert allowed is False
    assert 'vulnerable' in reason.lower()


def test_issuer_trusted(sample_policy):
    """Test trusted issuer check"""
    checker = ModelPolicyChecker(sample_policy)
    assert checker.is_issuer_trusted('test-ca') is True
    assert checker.is_issuer_trusted('untrusted-ca') is False


def test_model_not_in_policy(sample_policy):
    """Test that model not in policy fails"""
    checker = ModelPolicyChecker(sample_policy)
    allowed, reason = checker.is_model_allowed('unknown_model', '1.0.0', 'fleet-a')
    assert allowed is False
    assert 'not in policy' in reason.lower() or 'not found' in reason.lower()

