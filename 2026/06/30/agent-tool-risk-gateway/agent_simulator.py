#!/usr/bin/env python3
"""
Agent Simulator: Demonstrates the complete Tool-Risk Gateway flow.

This script simulates an AI agent making tool calls through the gateway,
showing different policy outcomes: auto-approve, pending approval, and denial.

Usage:
    # Terminal 1: Start the gateway
    uvicorn gateway:app --reload --port 8000

    # Terminal 2: Run this simulator
    python agent_simulator.py
"""

import httpx
import json
import time

GATEWAY_URL = "http://localhost:8000"


def print_separator(title: str):
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_response(label: str, data: dict):
    print(f"  {label}: {json.dumps(data, indent=4)}")
    print()


def run_demo():
    with httpx.Client(base_url=GATEWAY_URL, timeout=30) as client:

        # Demo 1: Health Check
        print_separator("Demo 1: Health Check")
        resp = client.get("/health")
        print_response("Gateway health", resp.json())

        # Demo 2: List Tools
        print_separator("Demo 2: List Registered Tools")
        resp = client.get("/tools")
        tools = resp.json()
        for name, info in tools.items():
            print(f"  {name}")
            print(f"    Risk: {info['risk_class']} | "
                  f"Approval: {info['requires_approval']} | "
                  f"Roles: {info['allowed_roles']}")
        print()

        # Demo 3: Auto-Approve (Knowledge Base Search)
        print_separator("Demo 3: Auto-Approve (Knowledge Base Search)")
        proposal = {
            "agent_id": "assistant_v1",
            "agent_role": "read_only",
            "tool_name": "knowledge_base.search",
            "arguments": {"query": "How do I reset my password?", "max_results": 5},
            "request_id": "demo_001",
        }
        resp = client.post("/agent/propose-tool-call", json=proposal)
        print_response("Result (should be auto-executed)", resp.json())

        # Demo 4: Pending Approval (CRM update) + Approve
        print_separator("Demo 4: Pending Approval (CRM Update)")
        proposal = {
            "agent_id": "sales_agent_v2",
            "agent_role": "account_manager",
            "tool_name": "crm.update_customer_status",
            "arguments": {"customer_id": "acme_123", "status": "active"},
            "request_id": "demo_002",
        }
        resp = client.post("/agent/propose-tool-call", json=proposal)
        pending = resp.json()
        print_response("Result (should require approval)", pending)

        approval_id = pending["approval_id"]
        print(f"  >>> Human reviewer approves {approval_id}...")
        resp = client.post(
            "/approve",
            params={"approval_id": approval_id, "approver": "yusuf@company.com", "approve": True},
        )
        print_response("After approval", resp.json())

        # Demo 5: Denied (Wrong role)
        print_separator("Demo 5: Denied (Wrong Role)")
        proposal = {
            "agent_id": "read_only_bot",
            "agent_role": "read_only",
            "tool_name": "crm.update_customer_status",
            "arguments": {"customer_id": "abc_456", "status": "inactive"},
            "request_id": "demo_003",
        }
        resp = client.post("/agent/propose-tool-call", json=proposal)
        print_response("Result (should be denied)", resp.json())

        # Demo 6: Denied (Tool not in registry)
        print_separator("Demo 6: Denied (Unknown Tool)")
        proposal = {
            "agent_id": "assistant_v1",
            "agent_role": "admin",
            "tool_name": "system.shutdown",
            "arguments": {"reason": "maintenance"},
            "request_id": "demo_004",
        }
        resp = client.post("/agent/propose-tool-call", json=proposal)
        print_response("Result (should be denied)", resp.json())

        # Demo 7: Dual Approval (Payment)
        print_separator("Demo 7: Dual Approval (Payment)")
        proposal = {
            "agent_id": "billing_agent",
            "agent_role": "admin",
            "tool_name": "payment.charge",
            "arguments": {"customer_id": "cust_789", "amount_cents": 2999, "currency": "USD"},
            "request_id": "demo_005",
        }
        resp = client.post("/agent/propose-tool-call", json=proposal)
        print_response("Result (should require approval)", resp.json())

        # Demo 8: Schema Validation Failure
        print_separator("Demo 8: Schema Validation Failure")
        proposal = {
            "agent_id": "sales_agent_v2",
            "agent_role": "account_manager",
            "tool_name": "crm.update_customer_status",
            "arguments": {"customer_id": "acme_123", "status": "vip_customer"},
            "request_id": "demo_006",
        }
        resp = client.post("/agent/propose-tool-call", json=proposal)
        print_response("Result (should be denied - invalid status)", resp.json())

        # Demo 9: View Audit Log
        print_separator("Demo 9: Audit Log")
        resp = client.get("/audit-log", params={"limit": 10})
        entries = resp.json()["entries"]
        for entry in entries[-5:]:
            print(f"  [{entry['timestamp']}] {entry['event']} - "
                  f"tool={entry.get('tool_name', 'N/A')} "
                  f"decision={entry.get('decision', 'N/A')}")
        print()

        # Demo 10: Metrics
        print_separator("Demo 10: Gateway Metrics")
        resp = client.get("/metrics")
        print_response("Metrics", resp.json())

        # Demo 11: Pending Approvals
        print_separator("Demo 11: Pending Approvals")
        resp = client.get("/approvals/pending")
        print_response("Pending approvals", resp.json())

    print()
    print("Demo complete! All gateway flows tested successfully.")
    print()


if __name__ == "__main__":
    run_demo()
