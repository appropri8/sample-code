import json
from pathlib import Path

from .gateway import AgentGateway


def main():
    root = Path(__file__).resolve().parents[1]
    gateway = AgentGateway.from_config(root)

    read_request = {
        "traceId": "tr_demo_read",
        "agentId": "support-agent-v3",
        "toolName": "read_order_history",
        "arguments": {"customerId": "cus_42"},
        "context": {
            "userId": "usr_9",
            "tenantId": "tenant_a",
            "roles": ["support_agent"],
            "scopes": ["orders:read"],
        },
    }

    refund_request = {
        "traceId": "tr_demo_refund",
        "agentId": "support-agent-v3",
        "toolName": "refund_customer",
        "arguments": {
            "customerId": "cus_42",
            "orderId": "ord_7781",
            "amount": 250.0,
            "reason": "Duplicate charge confirmed by support case.",
        },
        "context": {
            "userId": "usr_9",
            "tenantId": "tenant_a",
            "roles": ["support_agent"],
            "scopes": ["payments:refund"],
        },
    }

    print("read order history")
    print(json.dumps(gateway.invoke(read_request), indent=2))

    print("\nrefund request")
    pending = gateway.invoke(refund_request)
    print(json.dumps(pending, indent=2))

    print("\napprove refund")
    gateway.approve(
        pending["approvalId"],
        approver="maya.finance@example.com",
        reason="Duplicate charge validated in support case.",
    )
    approved_request = {**refund_request, "approvalId": pending["approvalId"]}
    print(json.dumps(gateway.invoke(approved_request), indent=2))

    print("\naudit records")
    print(json.dumps(gateway.audit.records, indent=2))


if __name__ == "__main__":
    main()

