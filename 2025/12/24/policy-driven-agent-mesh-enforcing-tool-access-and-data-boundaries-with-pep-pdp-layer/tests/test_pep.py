"""Tests for PEP middleware."""
import pytest
from src.pep.middleware import PEPMiddleware
from src.pep.pdp_client import PDPClient
from src.pep.audit_logger import AuditLogger
from src.storage.memory_log_store import MemoryLogStore


def test_pep_allows_valid_request():
    """Test PEP allows valid request."""
    log_store = MemoryLogStore()
    audit_logger = AuditLogger(log_store)
    pdp_client = PDPClient()
    pep = PEPMiddleware(pdp_client, audit_logger)
    
    request = {
        "identity": {
            "user_id": "alice@company.com",
            "tenant_id": "acme-corp",
            "roles": ["support_role"],
            "risk_tier": "low"
        },
        "tool_call": {
            "tool_name": "ReadOrders",
            "action": "read",
            "params": {
                "tenant_id": "acme-corp",
                "limit": 100
            }
        }
    }
    
    constrained = pep.enforce(request, trace_id="trace-1")
    assert constrained is not None
    assert constrained["tool_call"]["params"]["tenant_id"] == "acme-corp"


def test_pep_denies_invalid_request():
    """Test PEP denies invalid request."""
    log_store = MemoryLogStore()
    audit_logger = AuditLogger(log_store)
    pdp_client = PDPClient()
    pep = PEPMiddleware(pdp_client, audit_logger)
    
    request = {
        "identity": {
            "user_id": "alice@company.com",
            "tenant_id": "acme-corp",
            "roles": ["support_role"],
            "risk_tier": "low"
        },
        "tool_call": {
            "tool_name": "IssueRefund",
            "action": "write",
            "params": {
                "order_id": "order-123",
                "amount": 100.00
            }
        }
    }
    
    with pytest.raises(PermissionError):
        pep.enforce(request, trace_id="trace-2")


def test_pep_applies_constraints():
    """Test PEP applies constraints."""
    log_store = MemoryLogStore()
    audit_logger = AuditLogger(log_store)
    pdp_client = PDPClient()
    pep = PEPMiddleware(pdp_client, audit_logger)
    
    request = {
        "identity": {
            "user_id": "admin@company.com",
            "tenant_id": "acme-corp",
            "roles": ["admin_role"],
            "risk_tier": "low"
        },
        "tool_call": {
            "tool_name": "ExportCSV",
            "action": "read",
            "params": {
                "dataset": "orders",
                "limit": 5000
            }
        }
    }
    
    constrained = pep.enforce(request, trace_id="trace-3")
    # Row limit should be applied (1000 from policy)
    assert constrained["tool_call"]["params"]["limit"] == 1000

