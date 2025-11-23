"""Tests for OTA agent."""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from src.ota_agent import OTAAgent


class TestOTAAgent:
    """Test OTA agent functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def agent(self, temp_dir):
        """Create OTA agent for testing."""
        # Override paths to use temp directory
        agent = OTAAgent("test-device", "https://ota.example.com")
        agent.slot_a_path = Path(temp_dir) / "slot_a"
        agent.slot_b_path = Path(temp_dir) / "slot_b"
        agent._ensure_directories()
        return agent
    
    def test_compute_sha256(self, agent):
        """Test SHA256 computation."""
        # Create test file
        test_file = agent.slot_a_path / "test.txt"
        test_file.write_text("test content")
        
        # Compute hash
        hash_value = agent.compute_sha256(test_file)
        
        # Should be valid hex string
        assert len(hash_value) == 64
        assert all(c in '0123456789abcdef' for c in hash_value)
    
    def test_matches_cohort(self, agent):
        """Test cohort matching."""
        # Set device attributes
        os.environ["DEVICE_REGION"] = "eu-west"
        os.environ["DEVICE_HW"] = "rev2"
        
        # Should match
        assert agent.matches_cohort("region:eu-west AND hw:rev2")
        assert agent.matches_cohort("region:eu-west")
        
        # Should not match
        assert not agent.matches_cohort("region:us-east")
        assert not agent.matches_cohort("region:eu-west AND hw:rev1")
    
    def test_version_in_range(self, agent):
        """Test version range checking."""
        # Version in range
        assert agent.version_in_range("1.8.5", "1.8.0", "2.0.0")
        assert agent.version_in_range("1.8.0", "1.8.0", "2.0.0")
        assert agent.version_in_range("2.0.0", "1.8.0", "2.0.0")
        
        # Version out of range
        assert not agent.version_in_range("1.7.9", "1.8.0", "2.0.0")
        assert not agent.version_in_range("2.0.1", "1.8.0", "2.0.0")
        
        # No min/max
        assert agent.version_in_range("1.8.5", "", "")
    
    def test_is_compatible(self, agent):
        """Test compatibility checking."""
        # Compatible
        os.environ["FIRMWARE_VERSION"] = "1.8.5"
        compatibility = {"min_firmware": "1.8.0", "max_firmware": "2.0.0"}
        assert agent.is_compatible(compatibility)
        
        # Not compatible (too old)
        os.environ["FIRMWARE_VERSION"] = "1.7.9"
        assert not agent.is_compatible(compatibility)
        
        # Not compatible (too new)
        os.environ["FIRMWARE_VERSION"] = "2.0.1"
        assert not agent.is_compatible(compatibility)
        
        # No compatibility requirements
        assert agent.is_compatible({})

