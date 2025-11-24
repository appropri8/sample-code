"""Example: Device-side OTA update flow"""

import os
import tempfile
from src.device_ota_client import DeviceOTAClient, Partition, UpdateState
from src.firmware_manifest import FirmwareManifest, create_manifest


def example_complete_update_flow():
    """Complete OTA update flow example"""
    print("Device OTA Update Flow Example")
    print("=" * 50)
    
    # Create temporary directories for partitions
    with tempfile.TemporaryDirectory() as temp_dir:
        partition_a = os.path.join(temp_dir, "partition_a.bin")
        partition_b = os.path.join(temp_dir, "partition_b.bin")
        
        # Create dummy partition files
        with open(partition_a, 'wb') as f:
            f.write(b'A' * 1024)  # 1 KB dummy firmware
        
        # Initialize device client
        client = DeviceOTAClient(
            device_id="device-12345",
            current_version="1.2.2",
            partition_a_path=partition_a,
            partition_b_path=partition_b,
            active_partition=Partition.A
        )
        
        print(f"Device ID: {client.device_id}")
        print(f"Current version: {client.current_version}")
        print(f"Active partition: {client.active_partition.value}")
        print(f"Inactive partition: {client.get_inactive_partition().value}")
        
        # Set progress callback
        def progress_callback(progress: float):
            print(f"Download progress: {progress:.1f}%")
        
        client.set_progress_callback(progress_callback)
        
        # Step 1: Check for updates
        print("\n1. Checking for updates...")
        # In real implementation, this would fetch from server
        # For demo, create a manifest directly
        manifest = create_manifest(
            version="1.2.3",
            build_id="20251124-143022",
            target_hardware=["esp32-v2"],
            image_url="https://ota.example.com/firmware/1.2.3/esp32-v2.bin",
            image_size=2048,
            image_hash="sha256:abc123def456...",
            signature="base64:xyz789..."
        )
        client.manifest = manifest
        
        update_available = manifest.version != client.current_version
        print(f"Update available: {update_available}")
        print(f"New version: {manifest.version}")
        
        if not update_available:
            print("No update needed")
            return
        
        # Step 2: Download firmware
        print("\n2. Downloading firmware...")
        # In real implementation, this would download from URL
        # For demo, create a dummy firmware file
        with open(partition_b, 'wb') as f:
            f.write(b'B' * 2048)  # 2 KB dummy firmware
        
        # Simulate download
        print("Downloading...")
        print("Download progress: 100.0%")
        client.downloaded_firmware_path = partition_b
        print("✓ Download completed")
        
        # Step 3: Verify firmware
        print("\n3. Verifying firmware...")
        # In real implementation, compute hash and verify signature
        # For demo, just check file exists
        if os.path.exists(partition_b):
            print("✓ Firmware file exists")
            # Simulate hash verification
            print("✓ Hash verified")
            print("✓ Signature verified")
        else:
            print("✗ Firmware file not found")
            return
        
        # Step 4: Install firmware
        print("\n4. Installing firmware...")
        # In real implementation, this would write to flash and update boot flags
        ready_flag = f"{partition_b}.ready"
        with open(ready_flag, 'w') as f:
            f.write('{"version": "1.2.3", "installed_at": "2025-11-24T14:30:22"}')
        print("✓ Firmware installed to partition B")
        print("✓ Partition B marked as ready")
        
        # Step 5: Reboot (simulated)
        print("\n5. Rebooting device...")
        print("Device will boot from partition B")
        print("(In real implementation, device would reboot here)")
        
        print("\n✓ Update flow completed successfully")
        print("Device should now be running version 1.2.3")


def example_update_with_verification_failure():
    """Example of update flow with verification failure"""
    print("\n\nUpdate Flow with Verification Failure")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        partition_a = os.path.join(temp_dir, "partition_a.bin")
        partition_b = os.path.join(temp_dir, "partition_b.bin")
        
        with open(partition_a, 'wb') as f:
            f.write(b'A' * 1024)
        
        client = DeviceOTAClient(
            device_id="device-67890",
            current_version="1.2.2",
            partition_a_path=partition_a,
            partition_b_path=partition_b,
            active_partition=Partition.A
        )
        
        # Create manifest
        manifest = create_manifest(
            version="1.2.3",
            build_id="20251124-143022",
            target_hardware=["esp32-v2"],
            image_url="https://ota.example.com/firmware/1.2.3/esp32-v2.bin",
            image_size=2048,
            image_hash="sha256:correct_hash",
            signature="base64:correct_signature"
        )
        client.manifest = manifest
        
        # Download firmware
        print("1. Downloading firmware...")
        with open(partition_b, 'wb') as f:
            f.write(b'B' * 2048)
        client.downloaded_firmware_path = partition_b
        print("✓ Download completed")
        
        # Verification fails (corrupted download)
        print("\n2. Verifying firmware...")
        print("✗ Hash verification failed (corrupted download)")
        print("✗ Update aborted")
        print("Device remains on partition A (version 1.2.2)")
        
        # Clean up corrupted download
        if os.path.exists(partition_b):
            os.remove(partition_b)
        print("✓ Corrupted firmware removed")


if __name__ == "__main__":
    example_complete_update_flow()
    example_update_with_verification_failure()
    
    print("\n✓ All examples completed")

