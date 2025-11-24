"""Tests for firmware manifest"""

import pytest
import tempfile
import os
from src.firmware_manifest import (
    FirmwareManifest,
    FirmwareImage,
    FirmwareMetadata,
    create_manifest,
    UpdateType
)


def test_create_manifest():
    """Test creating a firmware manifest"""
    manifest = create_manifest(
        version="1.2.3",
        build_id="20251124-143022",
        target_hardware=["esp32-v2"],
        image_url="https://ota.example.com/firmware.bin",
        image_size=1048576,
        image_hash="sha256:abc123",
        signature="base64:xyz789"
    )
    
    assert manifest.version == "1.2.3"
    assert manifest.build_id == "20251124-143022"
    assert manifest.target_hardware == ["esp32-v2"]
    assert manifest.image is not None
    assert manifest.image.url == "https://ota.example.com/firmware.bin"
    assert manifest.image.size == 1048576


def test_manifest_validation():
    """Test manifest validation"""
    manifest = create_manifest(
        version="1.2.3",
        build_id="20251124-143022",
        target_hardware=["esp32-v2"],
        image_url="https://ota.example.com/firmware.bin",
        image_size=1048576,
        image_hash="sha256:abc123",
        signature="base64:xyz789"
    )
    
    assert manifest.validate() is True


def test_manifest_invalid():
    """Test invalid manifest"""
    manifest = FirmwareManifest(
        version="",
        build_id="",
        target_hardware=[],
        image=None
    )
    
    assert manifest.validate() is False


def test_manifest_save_and_load():
    """Test saving and loading manifest"""
    manifest = create_manifest(
        version="1.2.3",
        build_id="20251124-143022",
        target_hardware=["esp32-v2"],
        image_url="https://ota.example.com/firmware.bin",
        image_size=1048576,
        image_hash="sha256:abc123",
        signature="base64:xyz789"
    )
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = f.name
    
    try:
        manifest.save(temp_path)
        loaded = FirmwareManifest.from_file(temp_path)
        
        assert loaded.version == manifest.version
        assert loaded.build_id == manifest.build_id
        assert loaded.target_hardware == manifest.target_hardware
    finally:
        os.unlink(temp_path)


def test_hardware_compatibility():
    """Test hardware compatibility check"""
    manifest = create_manifest(
        version="1.2.3",
        build_id="20251124-143022",
        target_hardware=["esp32-v2", "esp32-v3"],
        image_url="https://ota.example.com/firmware.bin",
        image_size=1048576,
        image_hash="sha256:abc123",
        signature="base64:xyz789"
    )
    
    assert manifest.is_compatible_with_hardware("esp32-v2") is True
    assert manifest.is_compatible_with_hardware("esp32-v3") is True
    assert manifest.is_compatible_with_hardware("esp32-v1") is False


def test_bootloader_compatibility():
    """Test bootloader compatibility check"""
    manifest = create_manifest(
        version="1.2.3",
        build_id="20251124-143022",
        target_hardware=["esp32-v2"],
        image_url="https://ota.example.com/firmware.bin",
        image_size=1048576,
        image_hash="sha256:abc123",
        signature="base64:xyz789",
        min_bootloader_version="2.1.0"
    )
    
    assert manifest.is_compatible_with_bootloader("2.0.0") is False
    assert manifest.is_compatible_with_bootloader("2.1.0") is True
    assert manifest.is_compatible_with_bootloader("2.2.0") is True
    assert manifest.is_compatible_with_bootloader("3.0.0") is True


def test_manifest_without_bootloader_requirement():
    """Test manifest without bootloader requirement"""
    manifest = create_manifest(
        version="1.2.3",
        build_id="20251124-143022",
        target_hardware=["esp32-v2"],
        image_url="https://ota.example.com/firmware.bin",
        image_size=1048576,
        image_hash="sha256:abc123",
        signature="base64:xyz789"
    )
    
    assert manifest.is_compatible_with_bootloader("1.0.0") is True
    assert manifest.is_compatible_with_bootloader("2.0.0") is True

