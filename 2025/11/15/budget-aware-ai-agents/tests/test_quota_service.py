"""Tests for quota service."""

import pytest
from src.quota_service import QuotaService


class TestQuotaService:
    """Tests for QuotaService."""
    
    def test_create_service(self):
        service = QuotaService(default_daily_quota=10000)
        assert service.default_daily_quota == 10000
    
    def test_check_quota_new_tenant(self):
        service = QuotaService(default_daily_quota=10000)
        
        assert service.check_quota("tenant1", 1000) is True
    
    def test_check_quota_insufficient(self):
        service = QuotaService(default_daily_quota=10000)
        
        service.consume_quota("tenant1", 9500)
        
        assert service.check_quota("tenant1", 1000) is False
        assert service.check_quota("tenant1", 500) is True
    
    def test_check_quota_critical_priority(self):
        service = QuotaService(default_daily_quota=10000)
        
        # Exhaust quota
        service.consume_quota("tenant1", 10000)
        
        # Critical priority should still work
        assert service.check_quota("tenant1", 1000, priority="critical") is True
    
    def test_consume_quota(self):
        service = QuotaService(default_daily_quota=10000)
        
        service.consume_quota("tenant1", 2000)
        
        assert service.get_remaining_quota("tenant1") == 8000
    
    def test_get_remaining_quota(self):
        service = QuotaService(default_daily_quota=10000)
        
        assert service.get_remaining_quota("tenant1") == 10000
        
        service.consume_quota("tenant1", 3000)
        
        assert service.get_remaining_quota("tenant1") == 7000
    
    def test_reset_quota(self):
        service = QuotaService(default_daily_quota=10000)
        
        service.consume_quota("tenant1", 5000)
        service.reset_quota("tenant1")
        
        assert service.get_remaining_quota("tenant1") == 10000

