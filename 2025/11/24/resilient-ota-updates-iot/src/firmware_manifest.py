"""Firmware manifest handling for OTA updates"""

import json
import hashlib
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum


class UpdateType(str, Enum):
    """Type of update"""
    FIRMWARE = "firmware"
    CONFIG = "config"
    FEATURE_FLAG = "feature_flag"
    SECURITY_PATCH = "security_patch"


@dataclass
class FirmwareImage:
    """Firmware image metadata"""
    url: str
    size: int
    hash: str  # SHA-256 hash
    signature: str  # Base64-encoded signature
    compression: Optional[str] = None  # e.g., "gzip"


@dataclass
class FirmwareMetadata:
    """Additional firmware metadata"""
    release_notes: str
    rollout_percentage: int = 0  # 0-100
    required: bool = False
    min_ram_kb: Optional[int] = None
    min_flash_kb: Optional[int] = None


@dataclass
class FirmwareManifest:
    """Firmware manifest for OTA updates"""
    version: str  # Semantic version: major.minor.patch
    build_id: str  # Unique build identifier
    target_hardware: List[str]  # Supported hardware revisions
    min_bootloader_version: Optional[str] = None
    image: Optional[FirmwareImage] = None
    metadata: Optional[FirmwareMetadata] = None
    update_type: UpdateType = UpdateType.FIRMWARE
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary"""
        result = asdict(self)
        if self.image:
            result["image"] = asdict(self.image)
        if self.metadata:
            result["metadata"] = asdict(self.metadata)
        result["update_type"] = self.update_type.value
        return result
    
    def to_json(self, indent: int = 2) -> str:
        """Convert manifest to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)
    
    def save(self, filepath: str) -> None:
        """Save manifest to file"""
        with open(filepath, 'w') as f:
            f.write(self.to_json())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FirmwareManifest':
        """Create manifest from dictionary"""
        image_data = data.get("image")
        image = FirmwareImage(**image_data) if image_data else None
        
        metadata_data = data.get("metadata")
        metadata = FirmwareMetadata(**metadata_data) if metadata_data else None
        
        return cls(
            version=data["version"],
            build_id=data["build_id"],
            target_hardware=data["target_hardware"],
            min_bootloader_version=data.get("min_bootloader_version"),
            image=image,
            metadata=metadata,
            update_type=UpdateType(data.get("update_type", "firmware"))
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'FirmwareManifest':
        """Create manifest from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def from_file(cls, filepath: str) -> 'FirmwareManifest':
        """Load manifest from file"""
        with open(filepath, 'r') as f:
            return cls.from_json(f.read())
    
    def validate(self) -> bool:
        """Validate manifest structure"""
        if not self.version:
            return False
        if not self.build_id:
            return False
        if not self.target_hardware:
            return False
        if self.image:
            if not self.image.url or not self.image.hash or not self.image.signature:
                return False
        return True
    
    def is_compatible_with_hardware(self, hardware_revision: str) -> bool:
        """Check if manifest is compatible with hardware revision"""
        return hardware_revision in self.target_hardware
    
    def is_compatible_with_bootloader(self, bootloader_version: str) -> bool:
        """Check if manifest is compatible with bootloader version"""
        if not self.min_bootloader_version:
            return True
        
        # Simple version comparison (assumes semantic versioning)
        def version_tuple(v: str) -> tuple:
            parts = v.split('.')
            return tuple(int(p) for p in parts)
        
        return version_tuple(bootloader_version) >= version_tuple(self.min_bootloader_version)


def create_manifest(
    version: str,
    build_id: str,
    target_hardware: List[str],
    image_url: str,
    image_size: int,
    image_hash: str,
    signature: str,
    min_bootloader_version: Optional[str] = None,
    release_notes: str = "",
    rollout_percentage: int = 0,
    required: bool = False
) -> FirmwareManifest:
    """Create a firmware manifest"""
    image = FirmwareImage(
        url=image_url,
        size=image_size,
        hash=image_hash,
        signature=signature
    )
    
    metadata = FirmwareMetadata(
        release_notes=release_notes,
        rollout_percentage=rollout_percentage,
        required=required
    )
    
    return FirmwareManifest(
        version=version,
        build_id=build_id,
        target_hardware=target_hardware,
        min_bootloader_version=min_bootloader_version,
        image=image,
        metadata=metadata
    )

