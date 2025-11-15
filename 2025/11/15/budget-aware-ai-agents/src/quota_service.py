"""Quota service for multi-tenant budget management."""

from typing import Dict, Optional
from datetime import datetime, timedelta


class QuotaService:
    """Manages quotas for multiple tenants/users."""
    
    def __init__(self, default_daily_quota: int = 100000):
        """
        Initialize quota service.
        
        Args:
            default_daily_quota: Default daily token quota per tenant
        """
        self.default_daily_quota = default_daily_quota
        self.quotas: Dict[str, Dict] = {}  # tenant_id -> {remaining, reset_time}
    
    def _get_or_create_quota(self, tenant_id: str) -> Dict:
        """Get or create quota entry for tenant."""
        if tenant_id not in self.quotas:
            self.quotas[tenant_id] = {
                "remaining": self.default_daily_quota,
                "reset_time": datetime.now() + timedelta(days=1)
            }
        
        # Reset quota if reset time has passed
        quota = self.quotas[tenant_id]
        if datetime.now() >= quota["reset_time"]:
            quota["remaining"] = self.default_daily_quota
            quota["reset_time"] = datetime.now() + timedelta(days=1)
        
        return quota
    
    def check_quota(self, tenant_id: str, tokens_needed: int, priority: str = "normal") -> bool:
        """
        Check if tenant has enough quota.
        
        Args:
            tenant_id: Tenant identifier
            tokens_needed: Tokens needed for the operation
            priority: Priority level ("critical", "high", "normal", "low")
        
        Returns:
            True if quota is available, False otherwise
        """
        if priority == "critical":
            # Always allow critical workloads
            return True
        
        quota = self._get_or_create_quota(tenant_id)
        return quota["remaining"] >= tokens_needed
    
    def consume_quota(self, tenant_id: str, tokens_used: int):
        """Consume quota for a tenant."""
        quota = self._get_or_create_quota(tenant_id)
        quota["remaining"] -= tokens_used
    
    def get_remaining_quota(self, tenant_id: str) -> int:
        """Get remaining quota for a tenant."""
        quota = self._get_or_create_quota(tenant_id)
        return quota["remaining"]
    
    def reset_quota(self, tenant_id: str):
        """Manually reset quota for a tenant."""
        if tenant_id in self.quotas:
            self.quotas[tenant_id] = {
                "remaining": self.default_daily_quota,
                "reset_time": datetime.now() + timedelta(days=1)
            }

