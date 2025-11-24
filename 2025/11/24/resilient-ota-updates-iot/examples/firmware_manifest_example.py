"""Example: Creating and validating firmware manifests"""

from src.firmware_manifest import (
    FirmwareManifest,
    FirmwareImage,
    FirmwareMetadata,
    create_manifest,
    UpdateType
)


def example_basic_manifest():
    """Create a basic firmware manifest"""
    print("Creating basic firmware manifest...")
    
    manifest = create_manifest(
        version="1.2.3",
        build_id="20251124-143022",
        target_hardware=["esp32-v2", "esp32-v3"],
        image_url="https://ota.example.com/firmware/1.2.3/esp32-v2.bin",
        image_size=1048576,  # 1 MB
        image_hash="sha256:abc123def4567890123456789012345678901234567890123456789012345678",
        signature="base64:xyz789...",
        release_notes="Security patch for CVE-2025-1234",
        rollout_percentage=0,
        required=False
    )
    
    print(f"Manifest created: {manifest.version}")
    print(f"Target hardware: {manifest.target_hardware}")
    print(f"Image size: {manifest.image.size} bytes")
    print(f"Image hash: {manifest.image.hash}")
    
    # Validate manifest
    if manifest.validate():
        print("✓ Manifest is valid")
    else:
        print("✗ Manifest is invalid")
    
    # Save to file
    manifest.save("manifests/firmware_manifest_v1.2.3.json")
    print("✓ Manifest saved to file")
    
    return manifest


def example_manifest_with_min_bootloader():
    """Create a manifest with minimum bootloader version requirement"""
    print("\nCreating manifest with bootloader requirement...")
    
    manifest = create_manifest(
        version="2.0.0",
        build_id="20251124-150000",
        target_hardware=["esp32-v3"],
        image_url="https://ota.example.com/firmware/2.0.0/esp32-v3.bin",
        image_size=2097152,  # 2 MB
        image_hash="sha256:def456abc7890123456789012345678901234567890123456789012345678901",
        signature="base64:abc123...",
        min_bootloader_version="2.1.0",
        release_notes="Major update with new features",
        rollout_percentage=0,
        required=False
    )
    
    print(f"Manifest version: {manifest.version}")
    print(f"Min bootloader version: {manifest.min_bootloader_version}")
    
    # Check compatibility
    print(f"Compatible with bootloader 2.0.0: {manifest.is_compatible_with_bootloader('2.0.0')}")
    print(f"Compatible with bootloader 2.1.0: {manifest.is_compatible_with_bootloader('2.1.0')}")
    print(f"Compatible with bootloader 2.2.0: {manifest.is_compatible_with_bootloader('2.2.0')}")
    
    # Save to file
    manifest.save("manifests/firmware_manifest_v2.0.0_min_bootloader.json")
    print("✓ Manifest saved to file")
    
    return manifest


def example_load_manifest():
    """Load and validate a manifest from file"""
    print("\nLoading manifest from file...")
    
    try:
        manifest = FirmwareManifest.from_file("manifests/firmware_manifest_v1.2.3.json")
        print(f"Loaded manifest: {manifest.version}")
        print(f"Build ID: {manifest.build_id}")
        print(f"Target hardware: {manifest.target_hardware}")
        
        # Check hardware compatibility
        print(f"Compatible with esp32-v2: {manifest.is_compatible_with_hardware('esp32-v2')}")
        print(f"Compatible with esp32-v1: {manifest.is_compatible_with_hardware('esp32-v1')}")
        
    except FileNotFoundError:
        print("Manifest file not found. Run example_basic_manifest() first.")


if __name__ == "__main__":
    import os
    
    # Create manifests directory
    os.makedirs("manifests", exist_ok=True)
    
    # Run examples
    example_basic_manifest()
    example_manifest_with_min_bootloader()
    example_load_manifest()
    
    print("\n✓ All examples completed")

