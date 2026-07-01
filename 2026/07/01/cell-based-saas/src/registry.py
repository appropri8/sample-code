"""
Tenant registry schema and operations.

This module defines the data model for tenant-to-cell mapping
with optimistic concurrency for safe migrations.
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass, field
import time


class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    MIGRATING = "migrating"


class MigrationState(str, Enum):
    NONE = "none"
    DRAINING = "draining"
    SHADOWING = "shadowing"
    CUT_OVER = "cutover"
    ROLLED_BACK = "rolled_back"


@dataclass
class TenantRegistryRecord:
    """
    Schema for tenant registry table.
    
    In PostgreSQL, this maps to:
    
    CREATE TABLE tenant_registry (
        tenant_id VARCHAR(64) PRIMARY KEY,
        cell_id VARCHAR(64) NOT NULL,
        region VARCHAR(32) NOT NULL,
        status VARCHAR(16) NOT NULL DEFAULT 'active',
        migration_state VARCHAR(32) NOT NULL DEFAULT 'none',
        version INTEGER NOT NULL DEFAULT 1,
        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """
    tenant_id: str
    cell_id: str
    region: str
    status: TenantStatus = TenantStatus.ACTIVE
    migration_state: MigrationState = MigrationState.NONE
    version: int = 1
    updated_at: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)


class TenantRegistry:
    """
    Simulated tenant registry with optimistic concurrency.
    
    In production, use a real PostgreSQL or DynamoDB client.
    """
    
    def __init__(self):
        self._store: dict[str, TenantRegistryRecord] = {}
    
    def get_tenant(self, tenant_id: str) -> Optional[TenantRegistryRecord]:
        """Get tenant record by ID."""
        return self._store.get(tenant_id)
    
    def update_tenant(
        self,
        tenant_id: str,
        *,
        cell_id: Optional[str] = None,
        status: Optional[TenantStatus] = None,
        migration_state: Optional[MigrationState] = None,
        version: Optional[int] = None,
    ) -> bool:
        """
        Update tenant with optimistic concurrency.
        
        Returns True if update succeeded, False if version conflict.
        """
        record = self._store.get(tenant_id)
        if not record:
            return False
        
        if version is not None and record.version != version:
            return False
        
        if cell_id is not None:
            record.cell_id = cell_id
        if status is not None:
            record.status = status
        if migration_state is not None:
            record.migration_state = migration_state
        
        record.version += 1
        record.updated_at = time.time()
        return True
    
    def create_tenant(
        self,
        tenant_id: str,
        cell_id: str,
        region: str,
    ) -> TenantRegistryRecord:
        """Create a new tenant record."""
        record = TenantRegistryRecord(
            tenant_id=tenant_id,
            cell_id=cell_id,
            region=region,
        )
        self._store[tenant_id] = record
        return record


# Example registry instance
_registry = TenantRegistry()


def get_registry_client() -> TenantRegistry:
    """Get the global registry client."""
    return _registry