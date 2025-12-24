"""Demo script showing PEP/PDP pattern in action."""
from src.pep.middleware import PEPMiddleware
from src.pep.pdp_client import PDPClient
from src.pep.audit_logger import AuditLogger
from src.pep.cache import DecisionCache
from src.tools.read_orders_tool import ReadOrdersTool
from src.tools.issue_refund_tool import IssueRefundTool
from src.tools.export_csv_tool import ExportCSVTool
from src.tools.tenant_guard import TenantGuard
from src.storage.memory_log_store import MemoryLogStore


def main():
    """Run PEP/PDP demo."""
    print("Setting up PEP/PDP system...")
    
    # Setup
    log_store = MemoryLogStore()
    audit_logger = AuditLogger(log_store)
    pdp_client = PDPClient()
    cache = DecisionCache(ttl_seconds=60)
    pep = PEPMiddleware(pdp_client, audit_logger, cache=cache)
    
    tenant_guard = TenantGuard()
    
    # Create tools
    read_orders = ReadOrdersTool(database=None, tenant_guard=tenant_guard)
    issue_refund = IssueRefundTool()
    export_csv = ExportCSVTool()
    
    print("\n" + "="*60)
    print("Example 1: Support agent reads orders (allowed)")
    print("="*60)
    
    # Example 1: Support agent reads orders (allowed)
    request1 = {
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
        },
        "policy_context": {
            "request_id": "req-1",
            "trace_id": "trace-1"
        }
    }
    
    try:
        constrained_request = pep.enforce(request1, trace_id="trace-1")
        print("✓ Request 1 allowed: Support agent can read orders")
        print(f"  Constraints applied: {constrained_request['tool_call']['params'].get('_mask_fields', [])}")
        
        # Execute tool
        result = read_orders.call(
            constrained_request["tool_call"]["params"],
            request1["identity"]["tenant_id"]
        )
        print(f"  Result: {result['count']} orders returned")
    except PermissionError as e:
        print(f"✗ Request 1 denied: {e}")
    
    print("\n" + "="*60)
    print("Example 2: Support agent tries to issue refund (denied)")
    print("="*60)
    
    # Example 2: Support agent tries to issue refund (denied)
    request2 = {
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
        },
        "policy_context": {
            "request_id": "req-2",
            "trace_id": "trace-2"
        }
    }
    
    try:
        constrained_request = pep.enforce(request2, trace_id="trace-2")
        print("✓ Request 2 allowed")
        result = issue_refund.call(constrained_request["tool_call"]["params"])
        print(f"  Result: {result}")
    except PermissionError as e:
        print(f"✗ Request 2 denied: {e}")
    
    print("\n" + "="*60)
    print("Example 3: Cross-tenant access attempt (denied)")
    print("="*60)
    
    # Example 3: Cross-tenant access attempt (denied)
    request3 = {
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
                "tenant_id": "competitor-corp",  # Different tenant!
                "limit": 100
            }
        },
        "policy_context": {
            "request_id": "req-3",
            "trace_id": "trace-3"
        }
    }
    
    try:
        constrained_request = pep.enforce(request3, trace_id="trace-3")
        print("✓ Request 3 allowed")
        result = read_orders.call(
            constrained_request["tool_call"]["params"],
            request3["identity"]["tenant_id"]
        )
        print(f"  Result: {result['count']} orders returned")
    except PermissionError as e:
        print(f"✗ Request 3 denied: {e}")
    
    print("\n" + "="*60)
    print("Example 4: Finance agent issues refund (allowed)")
    print("="*60)
    
    # Example 4: Finance agent issues refund (allowed)
    request4 = {
        "identity": {
            "user_id": "bob@company.com",
            "tenant_id": "acme-corp",
            "roles": ["finance_role"],
            "risk_tier": "low"
        },
        "tool_call": {
            "tool_name": "IssueRefund",
            "action": "write",
            "params": {
                "order_id": "order-456",
                "amount": 200.00
            }
        },
        "policy_context": {
            "request_id": "req-4",
            "trace_id": "trace-4"
        }
    }
    
    try:
        constrained_request = pep.enforce(request4, trace_id="trace-4")
        print("✓ Request 4 allowed: Finance agent can issue refunds")
        result = issue_refund.call(constrained_request["tool_call"]["params"])
        print(f"  Result: {result}")
    except PermissionError as e:
        print(f"✗ Request 4 denied: {e}")
    
    print("\n" + "="*60)
    print("Example 5: Admin exports CSV with row limit")
    print("="*60)
    
    # Example 5: Admin exports CSV with row limit
    request5 = {
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
                "limit": 5000  # Requesting more than policy allows
            }
        },
        "policy_context": {
            "request_id": "req-5",
            "trace_id": "trace-5"
        }
    }
    
    try:
        constrained_request = pep.enforce(request5, trace_id="trace-5")
        print("✓ Request 5 allowed: Admin can export CSV")
        print(f"  Requested limit: 5000")
        print(f"  Applied limit: {constrained_request['tool_call']['params']['limit']}")
        result = export_csv.call(constrained_request["tool_call"]["params"])
        print(f"  Result: {result['row_count']} rows exported (limit: {result['limit_applied']})")
    except PermissionError as e:
        print(f"✗ Request 5 denied: {e}")
    
    print("\n" + "="*60)
    print("Audit Log")
    print("="*60)
    for entry in log_store.get_all():
        print(f"  [{entry['timestamp']}] {entry['decision'].upper():6} - "
              f"{entry['action']['tool_name']:15} - "
              f"trace_id: {entry['trace_id']} - "
              f"reason: {entry['reason']}")


if __name__ == "__main__":
    main()

