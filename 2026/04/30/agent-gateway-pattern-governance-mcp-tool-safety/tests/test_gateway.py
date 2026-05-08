import unittest
from pathlib import Path

from agent_gateway import AgentGateway


ROOT = Path(__file__).resolve().parents[1]


class AgentGatewayTests(unittest.TestCase):
    def make_gateway(self):
        return AgentGateway.from_config(ROOT)

    def test_low_risk_read_runs_without_approval(self):
        gateway = self.make_gateway()
        response = gateway.invoke(
            {
                "traceId": "tr_read",
                "agentId": "support-agent-v3",
                "toolName": "read_order_history",
                "arguments": {"customerId": "cus_42"},
                "context": {
                    "roles": ["support_agent"],
                    "scopes": ["orders:read"],
                },
            }
        )

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"]["customerId"], "cus_42")
        self.assertEqual(gateway.audit.records[-1]["decision"], "allow")

    def test_refund_above_threshold_requires_approval_then_executes(self):
        gateway = self.make_gateway()
        request = {
            "traceId": "tr_refund",
            "agentId": "support-agent-v3",
            "toolName": "refund_customer",
            "arguments": {
                "customerId": "cus_42",
                "orderId": "ord_7781",
                "amount": 250.0,
                "reason": "Duplicate charge confirmed by support case.",
            },
            "context": {
                "roles": ["support_agent"],
                "scopes": ["payments:refund"],
            },
        }

        pending = gateway.invoke(request)
        self.assertEqual(pending["status"], "pending_approval")
        self.assertEqual(pending["approverRole"], "finance_approver")

        gateway.approve(
            pending["approvalId"],
            approver="maya.finance@example.com",
            reason="Case evidence confirmed.",
        )

        approved = gateway.invoke({**request, "approvalId": pending["approvalId"]})
        self.assertEqual(approved["status"], "success")
        self.assertEqual(approved["data"]["refundId"], "rf_10291")
        self.assertEqual(gateway.audit.records[-1]["approver"], "maya.finance@example.com")

    def test_missing_scope_is_denied_and_audited(self):
        gateway = self.make_gateway()
        response = gateway.invoke(
            {
                "traceId": "tr_denied",
                "agentId": "support-agent-v3",
                "toolName": "read_order_history",
                "arguments": {"customerId": "cus_42"},
                "context": {"roles": ["support_agent"], "scopes": []},
            }
        )

        self.assertEqual(response["status"], "denied")
        self.assertIn("missing scope", response["reason"])
        self.assertEqual(gateway.audit.records[-1]["decision"], "deny")

    def test_unknown_input_field_is_denied_before_execution(self):
        gateway = self.make_gateway()
        response = gateway.invoke(
            {
                "traceId": "tr_bad_schema",
                "agentId": "support-agent-v3",
                "toolName": "read_order_history",
                "arguments": {"customerId": "cus_42", "rawSql": "select * from orders"},
                "context": {
                    "roles": ["support_agent"],
                    "scopes": ["orders:read"],
                },
            }
        )

        self.assertEqual(response["status"], "denied")
        self.assertIn("unknown field", response["reason"])

    def test_approval_cannot_be_reused_for_changed_payload(self):
        gateway = self.make_gateway()
        request = {
            "traceId": "tr_reuse",
            "agentId": "support-agent-v3",
            "toolName": "refund_customer",
            "arguments": {
                "customerId": "cus_42",
                "orderId": "ord_7781",
                "amount": 250.0,
                "reason": "Duplicate charge confirmed by support case.",
            },
            "context": {
                "roles": ["support_agent"],
                "scopes": ["payments:refund"],
            },
        }
        pending = gateway.invoke(request)
        gateway.approve(pending["approvalId"], "maya.finance@example.com", "Confirmed.")

        changed_request = {
            **request,
            "approvalId": pending["approvalId"],
            "arguments": {**request["arguments"], "amount": 450.0},
        }
        response = gateway.invoke(changed_request)

        self.assertEqual(response["status"], "denied")
        self.assertIn("does not match", response["reason"])


if __name__ == "__main__":
    unittest.main()

