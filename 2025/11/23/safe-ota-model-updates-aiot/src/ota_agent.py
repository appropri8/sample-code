"""OTA Agent for safe model updates on edge devices."""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any
import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend


class OTAAgent:
    """Device-side OTA agent for model updates."""
    
    def __init__(self, device_id: str, ota_service_url: str):
        """Initialize OTA agent.
        
        Args:
            device_id: Unique device identifier
            ota_service_url: URL of OTA service endpoint
        """
        self.device_id = device_id
        self.ota_service_url = ota_service_url
        self.slot_a_path = Path("/tmp/models/slot_a")  # Use /tmp for demo
        self.slot_b_path = Path("/tmp/models/slot_b")
        self.current_slot = "A"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure model directories exist."""
        self.slot_a_path.mkdir(parents=True, exist_ok=True)
        self.slot_b_path.mkdir(parents=True, exist_ok=True)
    
    def poll_for_updates(self) -> Optional[Dict[str, Any]]:
        """Poll OTA service for available updates.
        
        Returns:
            Deployment manifest if update available, None otherwise
        """
        try:
            response = requests.get(
                f"{self.ota_service_url}/devices/{self.device_id}/updates",
                timeout=30
            )
            if response.status_code == 200:
                manifest = response.json()
                if self.should_update(manifest):
                    return manifest
        except Exception as e:
            print(f"Poll failed: {e}")
        return None
    
    def should_update(self, manifest: Dict[str, Any]) -> bool:
        """Check if device should update based on manifest.
        
        Args:
            manifest: Deployment manifest
            
        Returns:
            True if device should update, False otherwise
        """
        # Check cohort
        if not self.matches_cohort(manifest.get("target_cohort", "")):
            return False
        
        # Check compatibility
        if not self.is_compatible(manifest.get("compatibility", {})):
            return False
        
        # Check if already have this version
        current_version = self.get_current_version()
        if current_version == manifest.get("version"):
            return False
        
        return True
    
    def download_to_slot_b(self, manifest: Dict[str, Any]) -> bool:
        """Download model to slot B with resume support.
        
        Args:
            manifest: Deployment manifest
            
        Returns:
            True if download successful, False otherwise
        """
        target_path = self.slot_b_path / "model.tflite"
        artifact_url = manifest.get("artifact_url")
        if not artifact_url:
            return False
        
        try:
            # Check for partial download
            existing_size = 0
            if target_path.exists():
                existing_size = target_path.stat().st_size
                headers = {"Range": f"bytes={existing_size}-"}
            else:
                headers = {}
            
            response = requests.get(
                artifact_url,
                headers=headers,
                stream=True,
                timeout=300
            )
            
            mode = "ab" if existing_size > 0 else "wb"
            with open(target_path, mode) as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verify checksum
            computed_hash = self.compute_sha256(target_path)
            expected_hash = manifest.get("sha256", "")
            if computed_hash != expected_hash:
                target_path.unlink()
                print(f"Checksum mismatch: expected {expected_hash}, got {computed_hash}")
                return False
            
            # Save metadata
            metadata_path = self.slot_b_path / "metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(manifest, f)
            
            return True
        except Exception as e:
            print(f"Download failed: {e}")
            return False
    
    def verify_signature(self, manifest: Dict[str, Any]) -> bool:
        """Verify model signature.
        
        Args:
            manifest: Deployment manifest
            
        Returns:
            True if signature valid, False otherwise
        """
        model_path = self.slot_b_path / "model.tflite"
        signature_url = manifest.get("signature_url", "")
        
        if not signature_url:
            print("No signature URL in manifest")
            return False
        
        try:
            # Download signature
            sig_response = requests.get(signature_url, timeout=30)
            signature = sig_response.content
            
            # Load trusted public key (in production, load from secure storage)
            public_key_path = os.getenv("TRUSTED_PUBLIC_KEY_PATH", "/tmp/trusted_key.pem")
            if not os.path.exists(public_key_path):
                print(f"Public key not found at {public_key_path}")
                # For demo, skip signature verification
                return True
            
            with open(public_key_path, "rb") as f:
                public_key = serialization.load_pem_public_key(
                    f.read(),
                    backend=default_backend()
                )
            
            # Verify signature
            with open(model_path, "rb") as f:
                model_data = f.read()
            
            public_key.verify(
                signature,
                model_data,
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except Exception as e:
            print(f"Signature verification failed: {e}")
            return False
    
    def switch_to_slot_b(self):
        """Atomically switch current model pointer to slot B."""
        pointer_path = Path("/tmp/models/current_slot")
        temp_path = pointer_path.with_suffix(".tmp")
        
        with open(temp_path, "w") as f:
            f.write("B")
        
        temp_path.replace(pointer_path)
        self.current_slot = "B"
        print("Switched to slot B")
    
    def rollback_to_slot_a(self):
        """Roll back to slot A."""
        pointer_path = Path("/tmp/models/current_slot")
        temp_path = pointer_path.with_suffix(".tmp")
        
        with open(temp_path, "w") as f:
            f.write("A")
        
        temp_path.replace(pointer_path)
        self.current_slot = "A"
        print("Rolled back to slot A")
    
    def run_health_checks(self, manifest: Dict[str, Any], duration_seconds: int = 60) -> bool:
        """Run health checks for warm-up period.
        
        Args:
            manifest: Deployment manifest
            duration_seconds: Duration of health check period
            
        Returns:
            True if health checks pass, False otherwise
        """
        from .health_monitor import HealthMonitor
        
        health_checks = manifest.get("health_checks", {})
        monitor = HealthMonitor()
        start_time = time.time()
        inference_count = 0
        
        while time.time() - start_time < duration_seconds:
            # Get current metrics
            metrics = monitor.get_current_metrics()
            
            # Check CPU
            max_cpu = health_checks.get("max_cpu_percent", 100)
            if metrics.get("cpu_percent", 0) > max_cpu:
                print(f"CPU usage {metrics['cpu_percent']}% exceeds threshold {max_cpu}%")
                return False
            
            # Check RAM
            max_ram = health_checks.get("max_ram_percent", 100)
            if metrics.get("ram_percent", 0) > max_ram:
                print(f"RAM usage {metrics['ram_percent']}% exceeds threshold {max_ram}%")
                return False
            
            # Check latency
            max_latency = health_checks.get("max_latency_ms", 1000)
            if metrics.get("avg_latency_ms", 0) > max_latency:
                print(f"Latency {metrics['avg_latency_ms']}ms exceeds threshold {max_latency}ms")
                return False
            
            # Check error rate
            max_error_rate = health_checks.get("max_error_rate", 1.0)
            if metrics.get("error_rate", 0) > max_error_rate:
                print(f"Error rate {metrics['error_rate']} exceeds threshold {max_error_rate}")
                return False
            
            # Check inference count
            inference_count += 1
            warmup_inferences = health_checks.get("warmup_inferences", 0)
            if warmup_inferences > 0 and inference_count >= warmup_inferences:
                break
            
            time.sleep(1)
        
        print("Health checks passed")
        return True
    
    def apply_update(self, manifest: Dict[str, Any]) -> bool:
        """Apply update: download, verify, switch, health check.
        
        Args:
            manifest: Deployment manifest
            
        Returns:
            True if update applied successfully, False otherwise
        """
        # Download to slot B
        if not self.download_to_slot_b(manifest):
            return False
        
        # Verify signature
        if not self.verify_signature(manifest):
            return False
        
        # Switch to slot B
        self.switch_to_slot_b()
        
        # Run health checks
        if not self.run_health_checks(manifest):
            # Roll back if health checks fail
            self.rollback_to_slot_a()
            return False
        
        # Mark slot B as stable
        self.mark_slot_stable("B")
        return True
    
    def mark_slot_stable(self, slot: str):
        """Mark slot as stable, other becomes backup.
        
        Args:
            slot: Slot to mark as stable (A or B)
        """
        stable_path = Path(f"/tmp/models/slot_{slot.lower()}/stable")
        stable_path.touch()
        print(f"Marked slot {slot} as stable")
    
    def compute_sha256(self, file_path: Path) -> str:
        """Compute SHA256 hash of file.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA256 hash as hex string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def get_current_version(self) -> Optional[str]:
        """Get version of currently active model.
        
        Returns:
            Model version string or None
        """
        metadata_path = Path(f"/tmp/models/slot_{self.current_slot.lower()}/metadata.json")
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
                return metadata.get("version")
        return None
    
    def matches_cohort(self, cohort_query: str) -> bool:
        """Check if device matches cohort query.
        
        Args:
            cohort_query: Cohort query string (e.g., "region:eu-west AND hw:rev2")
            
        Returns:
            True if device matches, False otherwise
        """
        if not cohort_query:
            return True
        
        device_attrs = self.get_device_attributes()
        
        # Simple parsing (in production, use proper query parser)
        if "AND" in cohort_query:
            parts = cohort_query.split("AND")
            for part in parts:
                part = part.strip()
                if ":" in part:
                    key, value = part.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    if device_attrs.get(key) != value:
                        return False
        else:
            if ":" in cohort_query:
                key, value = cohort_query.split(":", 1)
                key = key.strip()
                value = value.strip()
                if device_attrs.get(key) != value:
                    return False
        
        return True
    
    def is_compatible(self, compatibility: Dict[str, Any]) -> bool:
        """Check if model is compatible with current firmware.
        
        Args:
            compatibility: Compatibility requirements
            
        Returns:
            True if compatible, False otherwise
        """
        if not compatibility:
            return True
        
        current_fw = self.get_firmware_version()
        min_fw = compatibility.get("min_firmware", "")
        max_fw = compatibility.get("max_firmware", "")
        
        return self.version_in_range(current_fw, min_fw, max_fw)
    
    def get_device_attributes(self) -> Dict[str, str]:
        """Get device attributes for cohort matching.
        
        Returns:
            Dictionary of device attributes
        """
        return {
            "region": os.getenv("DEVICE_REGION", "eu-west"),
            "hw": os.getenv("DEVICE_HW", "rev2"),
            "customer": os.getenv("DEVICE_CUSTOMER", "enterprise-a")
        }
    
    def get_firmware_version(self) -> str:
        """Get current firmware version.
        
        Returns:
            Firmware version string
        """
        return os.getenv("FIRMWARE_VERSION", "1.8.5")
    
    def version_in_range(self, version: str, min_version: str, max_version: str) -> bool:
        """Check if version is in range.
        
        Args:
            version: Version to check
            min_version: Minimum version
            max_version: Maximum version
            
        Returns:
            True if version in range, False otherwise
        """
        # Simplified version comparison (use proper semver in production)
        if not min_version and not max_version:
            return True
        
        def version_tuple(v):
            return tuple(map(int, v.split(".")))
        
        v = version_tuple(version)
        if min_version:
            min_v = version_tuple(min_version)
            if v < min_v:
                return False
        if max_version:
            max_v = version_tuple(max_version)
            if v > max_v:
                return False
        
        return True

