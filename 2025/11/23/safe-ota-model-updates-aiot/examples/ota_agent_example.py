"""Example: Basic OTA agent usage."""

import os
import time
from src.ota_agent import OTAAgent

def main():
    """Run OTA agent example."""
    # Create OTA agent
    agent = OTAAgent(
        device_id=os.getenv("DEVICE_ID", "device-001"),
        ota_service_url=os.getenv("OTA_SERVICE_URL", "https://ota.example.com")
    )
    
    print(f"OTA Agent started for device: {agent.device_id}")
    print(f"Current model version: {agent.get_current_version() or 'none'}")
    
    # Poll for updates
    print("\nPolling for updates...")
    manifest = agent.poll_for_updates()
    
    if manifest:
        print(f"\nUpdate available:")
        print(f"  Model: {manifest.get('model_id')}")
        print(f"  Version: {manifest.get('version')}")
        print(f"  Target cohort: {manifest.get('target_cohort')}")
        
        # Apply update
        print("\nApplying update...")
        success = agent.apply_update(manifest)
        
        if success:
            print(f"\n✓ Update applied successfully: {manifest.get('version')}")
            print(f"  Current model version: {agent.get_current_version()}")
        else:
            print(f"\n✗ Update failed, rolled back to previous version")
    else:
        print("No updates available")

if __name__ == "__main__":
    main()

