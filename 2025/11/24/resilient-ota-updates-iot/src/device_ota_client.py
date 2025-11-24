"""Device-side OTA client for downloading and installing firmware updates"""

import os
import hashlib
import json
import time
import requests
from typing import Optional, Callable
from enum import Enum
from pathlib import Path

from .firmware_manifest import FirmwareManifest


class Partition(str, Enum):
    """Device partition identifiers"""
    A = "A"
    B = "B"


class UpdateState(str, Enum):
    """OTA update state"""
    IDLE = "idle"
    CHECKING = "checking"
    DOWNLOADING = "downloading"
    VERIFYING = "verifying"
    INSTALLING = "installing"
    REBOOTING = "rebooting"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class DeviceOTAClient:
    """Device-side OTA update client"""
    
    def __init__(
        self,
        device_id: str,
        current_version: str,
        partition_a_path: str,
        partition_b_path: str,
        active_partition: Partition = Partition.A,
        manifest_url: Optional[str] = None,
        download_chunk_size: int = 8192,
        max_retries: int = 3,
        retry_backoff: float = 1.0
    ):
        """
        Initialize device OTA client
        
        Args:
            device_id: Unique device identifier
            current_version: Current firmware version
            partition_a_path: Path to partition A firmware
            partition_b_path: Path to partition B firmware
            active_partition: Currently active partition (A or B)
            manifest_url: URL to fetch firmware manifest
            download_chunk_size: Chunk size for downloads
            max_retries: Maximum retry attempts
            retry_backoff: Backoff multiplier for retries
        """
        self.device_id = device_id
        self.current_version = current_version
        self.partition_a_path = partition_a_path
        self.partition_b_path = partition_b_path
        self.active_partition = active_partition
        self.manifest_url = manifest_url
        self.download_chunk_size = download_chunk_size
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        
        self.state = UpdateState.IDLE
        self.manifest: Optional[FirmwareManifest] = None
        self.downloaded_firmware_path: Optional[str] = None
        self.progress_callback: Optional[Callable[[float], None]] = None
    
    def set_progress_callback(self, callback: Callable[[float], None]) -> None:
        """Set callback for download progress updates"""
        self.progress_callback = callback
    
    def check_for_updates(self, manifest_url: Optional[str] = None) -> bool:
        """
        Check for available firmware updates
        
        Args:
            manifest_url: URL to fetch manifest (overrides instance manifest_url)
            
        Returns:
            True if update is available, False otherwise
        """
        self.state = UpdateState.CHECKING
        url = manifest_url or self.manifest_url
        
        if not url:
            raise ValueError("Manifest URL not provided")
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            self.manifest = FirmwareManifest.from_json(response.text)
            
            if not self.manifest.validate():
                return False
            
            # Check if update is needed
            if self.manifest.version == self.current_version:
                return False
            
            # Check if update is compatible
            # In real implementation, check hardware revision and bootloader version
            return True
            
        except Exception as e:
            print(f"Error checking for updates: {e}")
            return False
        finally:
            self.state = UpdateState.IDLE
    
    def download_firmware(self, resume: bool = True) -> bool:
        """
        Download firmware image
        
        Args:
            resume: Whether to resume interrupted downloads
            
        Returns:
            True if download successful, False otherwise
        """
        if not self.manifest or not self.manifest.image:
            raise ValueError("No manifest or image available")
        
        self.state = UpdateState.DOWNLOADING
        
        # Determine inactive partition
        inactive_partition = Partition.B if self.active_partition == Partition.A else Partition.A
        inactive_path = self.partition_b_path if inactive_partition == Partition.B else self.partition_a_path
        
        self.downloaded_firmware_path = inactive_path
        
        url = self.manifest.image.url
        total_size = self.manifest.image.size
        
        # Check if file exists and can be resumed
        downloaded_size = 0
        if resume and os.path.exists(inactive_path):
            downloaded_size = os.path.getsize(inactive_path)
            if downloaded_size >= total_size:
                # Already downloaded
                return True
        
        try:
            headers = {}
            if resume and downloaded_size > 0:
                headers["Range"] = f"bytes={downloaded_size}-"
            
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # Open file for writing (append if resuming)
            mode = "ab" if resume and downloaded_size > 0 else "wb"
            with open(inactive_path, mode) as f:
                for chunk in response.iter_content(chunk_size=self.download_chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Report progress
                        if self.progress_callback and total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            self.progress_callback(progress)
            
            # Verify downloaded size
            if os.path.getsize(inactive_path) != total_size:
                raise ValueError(f"Download size mismatch: expected {total_size}, got {os.path.getsize(inactive_path)}")
            
            return True
            
        except Exception as e:
            print(f"Error downloading firmware: {e}")
            # Clean up partial download
            if os.path.exists(inactive_path):
                os.remove(inactive_path)
            return False
        finally:
            self.state = UpdateState.IDLE
    
    def verify_firmware(self) -> bool:
        """
        Verify firmware signature and hash
        
        Returns:
            True if verification successful, False otherwise
        """
        if not self.manifest or not self.manifest.image:
            raise ValueError("No manifest or image available")
        
        if not self.downloaded_firmware_path or not os.path.exists(self.downloaded_firmware_path):
            raise ValueError("Firmware file not found")
        
        self.state = UpdateState.VERIFYING
        
        try:
            # Compute hash of downloaded file
            sha256 = hashlib.sha256()
            with open(self.downloaded_firmware_path, 'rb') as f:
                while True:
                    chunk = f.read(self.download_chunk_size)
                    if not chunk:
                        break
                    sha256.update(chunk)
            
            computed_hash = f"sha256:{sha256.hexdigest()}"
            expected_hash = self.manifest.image.hash
            
            # Verify hash
            if computed_hash != expected_hash:
                print(f"Hash mismatch: expected {expected_hash}, got {computed_hash}")
                return False
            
            # In real implementation, verify signature using public key
            # For now, just check that signature exists
            if not self.manifest.image.signature:
                print("No signature in manifest")
                return False
            
            # Signature verification would happen here
            # verify_signature(self.downloaded_firmware_path, self.manifest.image.signature)
            
            return True
            
        except Exception as e:
            print(f"Error verifying firmware: {e}")
            return False
        finally:
            self.state = UpdateState.IDLE
    
    def install_firmware(self) -> bool:
        """
        Install firmware to inactive partition and mark it as ready
        
        Returns:
            True if installation successful, False otherwise
        """
        if not self.manifest:
            raise ValueError("No manifest available")
        
        if not self.downloaded_firmware_path or not os.path.exists(self.downloaded_firmware_path):
            raise ValueError("Firmware file not found")
        
        self.state = UpdateState.INSTALLING
        
        try:
            # In real implementation, this would:
            # 1. Write firmware to inactive partition
            # 2. Update partition table
            # 3. Mark inactive partition as ready for boot
            # 4. Set boot flag to inactive partition
            
            # For simulation, just verify the file exists and is correct size
            if os.path.getsize(self.downloaded_firmware_path) != self.manifest.image.size:
                return False
            
            # Mark partition as ready (in real implementation, update boot flags)
            ready_flag_path = f"{self.downloaded_firmware_path}.ready"
            with open(ready_flag_path, 'w') as f:
                json.dump({
                    "version": self.manifest.version,
                    "build_id": self.manifest.build_id,
                    "installed_at": time.time()
                }, f)
            
            return True
            
        except Exception as e:
            print(f"Error installing firmware: {e}")
            return False
        finally:
            self.state = UpdateState.IDLE
    
    def reboot(self) -> None:
        """Reboot device to activate new firmware"""
        self.state = UpdateState.REBOOTING
        
        # In real implementation, this would:
        # 1. Set boot flag to inactive partition
        # 2. Trigger device reboot
        # 3. Device boots from inactive partition
        
        print(f"Rebooting device to activate firmware {self.manifest.version if self.manifest else 'unknown'}")
        # os.system("reboot")  # Uncomment for real device
    
    def get_inactive_partition(self) -> Partition:
        """Get the inactive partition"""
        return Partition.B if self.active_partition == Partition.A else Partition.A
    
    def get_state(self) -> UpdateState:
        """Get current update state"""
        return self.state

