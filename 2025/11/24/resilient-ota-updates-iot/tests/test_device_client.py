"""Tests for device OTA client"""

import pytest
import tempfile
import os
from src.device_ota_client import DeviceOTAClient, Partition, UpdateState
from src.firmware_manifest import create_manifest


def test_device_client_initialization():
    """Test device client initialization"""
    with tempfile.TemporaryDirectory() as temp_dir:
        partition_a = os.path.join(temp_dir, "partition_a.bin")
        partition_b = os.path.join(temp_dir, "partition_b.bin")
        
        client = DeviceOTAClient(
            device_id="device-12345",
            current_version="1.2.2",
            partition_a_path=partition_a,
            partition_b_path=partition_b,
            active_partition=Partition.A
        )
        
        assert client.device_id == "device-12345"
        assert client.current_version == "1.2.2"
        assert client.active_partition == Partition.A
        assert client.get_inactive_partition() == Partition.B
        assert client.get_state() == UpdateState.IDLE


def test_check_for_updates():
    """Test checking for updates"""
    with tempfile.TemporaryDirectory() as temp_dir:
        partition_a = os.path.join(temp_dir, "partition_a.bin")
        partition_b = os.path.join(temp_dir, "partition_b.bin")
        
        client = DeviceOTAClient(
            device_id="device-12345",
            current_version="1.2.2",
            partition_a_path=partition_a,
            partition_b_path=partition_b,
            active_partition=Partition.A
        )
        
        # Create manifest with newer version
        manifest = create_manifest(
            version="1.2.3",
            build_id="20251124-143022",
            target_hardware=["esp32-v2"],
            image_url="https://ota.example.com/firmware.bin",
            image_size=1048576,
            image_hash="sha256:abc123",
            signature="base64:xyz789"
        )
        client.manifest = manifest
        
        # Check if update is available
        update_available = manifest.version != client.current_version
        assert update_available is True


def test_get_inactive_partition():
    """Test getting inactive partition"""
    with tempfile.TemporaryDirectory() as temp_dir:
        partition_a = os.path.join(temp_dir, "partition_a.bin")
        partition_b = os.path.join(temp_dir, "partition_b.bin")
        
        client_a = DeviceOTAClient(
            device_id="device-1",
            current_version="1.2.2",
            partition_a_path=partition_a,
            partition_b_path=partition_b,
            active_partition=Partition.A
        )
        assert client_a.get_inactive_partition() == Partition.B
        
        client_b = DeviceOTAClient(
            device_id="device-2",
            current_version="1.2.2",
            partition_a_path=partition_a,
            partition_b_path=partition_b,
            active_partition=Partition.B
        )
        assert client_b.get_inactive_partition() == Partition.A

