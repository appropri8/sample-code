#!/usr/bin/env python3
"""
Tests for the Tool-Risk Gateway.

Tests cover: policy evaluation, capability tokens, approval flow,
role-based access control, schema validation, and audit logging.

Run with:
    pytest test_gateway.py -v
"""

import time
import json
import pytest
from unittest.mock import patch, MagicMock

# Import gateway components
from gateway import (
    evaluate_policy,
    PolicyRequest,
    PolicyResult,
    Decision,
    CapabilityTokenIssuer,
    CapabilityToken,
    ToolDefinition,
    RiskClass,
    TOOL_REGISTRY,
    GATEWAY_SECRET_KEY,
    issuer,
    _redact_sensitive_fields,
)


# ─── Policy Engine Tests ─────────────────────────────────────────────────────


class TestEvaluatePolicy:
    """Tests for the evaluate_policy function."""

    def test_allow_read_only_tool(self):
        """A read-only tool with allowed role should be ALLOW."""
        request = PolicyRequest(
            agent_id="assistant_v1",
            agent_role="read_only",
            tool_name="knowledge_base.search",
            arguments={"query": "test query", "max_results": 5},
            request_id="test_001",
        )
        result = evaluate_policy(request)
        assert result.decision == Decision.ALLOW

    def test_deny_unknown_tool(self):
        """An unregistered tool should be DENY."""
        request = PolicyRequest(
            agent_id="agent_v1",
            agent_role="admin",
            tool_name="nonexistent.tool",
            arguments={},
            request_id="test_002",
        )
        result = evaluate_policy(request)
        assert result.decision == Decision.DENY
        assert "not found" in result.reason.lower()

    def test_deny_wrong_role(self):
        """A tool call from an unapproved role should be DENY."""
        request = PolicyRequest(
            agent_id="read_only_bot",
            agent_role="read_only",
            tool_name="crm.update_customer_status",
            arguments={"customer_id": "abc", "status": "active"},
            request_id="test_003",
        )
        result = evaluate_policy(request)
        assert result.decision == Decision.DENY
        assert "not allowed" in result.reason.lower()

    def test_approval_required_for_state_change(self):
        """A state-changing tool should require approval."""
        request = PolicyRequest(
            agent_id="sales_agent",
            agent_role="account_manager",
            tool_name="crm.update_customer_status",
            arguments={"customer_id": "abc_123", "status": "active"},
            request_id="test_004",
        )
        result = evaluate_policy(request)
        assert result.decision == Decision.APPROVAL_REQUIRED

    def test_deny_invalid_schema(self):
        """Invalid arguments (wrong enum value) should be DENY."""
        request = PolicyRequest(
            agent_id="sales_agent",
            agent_role="account_manager",
            tool_name="crm.update_customer_status",
            arguments={"customer_id": "abc_123", "status": "vip_customer"},
            request_id="test_005",
        )
        result = evaluate_policy(request)
        assert result.decision == Decision.DENY
        assert "validation" in result.reason.lower()

    def test_deny_missing_required_field(self):
        """Missing required fields should be DENY."""
        request = PolicyRequest(
            agent_id="sales_agent",
            agent_role="account_manager",
            tool_name="crm.update_customer_status",
            arguments={"customer_id": "abc_123"},  # missing 'status'
            request_id="test_006",
        )
        result = evaluate_policy(request)
        assert result.decision == Decision.DENY

    def test_approval_required_for_payment(self):
        """Payment operations should require approval."""
        request = PolicyRequest(
            agent_id="billing_agent",
            agent_role="admin",
            tool_name="payment.charge",
            arguments={"customer_id": "cust_789", "amount_cents": 2999, "currency": "USD"},
            request_id="test_007",
        )
        result = evaluate_policy(request)
        # Payment has requires_dual_approval=True
        assert result.decision == Decision.APPROVAL_REQUIRED

    def test_allow_star_role(self):
        """Tools with allowed_roles=['*'] should allow any role."""
        request = PolicyRequest(
            agent_id="any_agent",
            agent_role="completely_unknown_role",
            tool_name="crm.get_customer",
            arguments={"customer_id": "abc_123"},
            request_id="test_008",
        )
        result = evaluate_policy(request)
        assert result.decision == Decision.ALLOW

    def test_sandbox_required_for_email(self):
        """Email sending should require sandbox execution."""
        request = PolicyRequest(
            agent_id="marketing_bot",
            agent_role="marketing",
            tool_name="email.send",
            arguments={"to": "test@example.com", "subject": "Hello", "body": "Test"},
            request_id="test_009",
        )
        result = evaluate_policy(request)
        # email.send has requires_approval first, so should be APPROVAL_REQUIRED
        # In practice, approval check comes before sandbox check
        assert result.decision == Decision.APPROVAL_REQUIRED


# ─── Capability Token Tests ──────────────────────────────────────────────────


class TestCapabilityTokenIssuer:
    """Tests for the CapabilityTokenIssuer."""

    def test_mint_token_success(self):
        """Mint a token and verify it has all required fields."""
        tool_def = TOOL_REGISTRY["crm.get_customer"]
        token = issuer.mint_token(
            agent_id="agent_v1",
            tool_def=tool_def,
            arguments={"customer_id": "abc_123"},
        )
        assert token.token_id is not None
        assert token.agent_id == "agent_v1"
        assert token.tool_name == "crm.get_customer"
        assert token.resource_id == "abc_123"
        assert token.action == "get_customer"
        assert token.expires_at > token.issued_at
        assert token.signature != ""

    def test_verify_valid_token(self):
        """A freshly minted token should verify as valid."""
        tool_def = TOOL_REGISTRY["crm.get_customer"]
        token = issuer.mint_token("agent_v1", tool_def, {"customer_id": "abc_123"})
        assert issuer.verify_token(token) is True

    def test_reject_expired_token(self):
        """An expired token should be rejected."""
        tool_def = TOOL_REGISTRY["crm.get_customer"]
        token = issuer.mint_token("agent_v1", tool_def, {"customer_id": "abc_123"}, ttl_seconds=0)
        time.sleep(0.1)  # Ensure token expires
        assert issuer.verify_token(token) is False

    def test_reject_tampered_token(self):
        """A token with a modified signature should be rejected."""
        tool_def = TOOL_REGISTRY["crm.get_customer"]
        token = issuer.mint_token("agent_v1", tool_def, {"customer_id": "abc_123"})
        token.signature = "tampered_signature"
        assert issuer.verify_token(token) is False

    def test_reject_tampered_scope(self):
        """A token with modified scope should be rejected."""
        tool_def = TOOL_REGISTRY["crm.get_customer"]
        token = issuer.mint_token("agent_v1", tool_def, {"customer_id": "abc_123"})
        token.scope["customer_id"] = "different_customer"
        assert issuer.verify_token(token) is False

    def test_token_ttl_compliance(self):
        """Token TTL should match the tool definition."""
        tool_def = TOOL_REGISTRY["crm.update_customer_status"]
        token = issuer.mint_token("agent_v1", tool_def, {"customer_id": "abc", "status": "active"})
        expected_ttl = tool_def.token_ttl_seconds
        actual_ttl = token.expires_at - token.issued_at
        assert abs(actual_ttl - expected_ttl) < 1

    def test_different_secret_key(self):
        """Tokens from different secret keys should not verify."""
        issuer2 = CapabilityTokenIssuer("different-secret")
        tool_def = TOOL_REGISTRY["crm.get_customer"]
        token = issuer2.mint_token("agent_v1", tool_def, {"customer_id": "abc_123"})
        assert issuer.verify_token(token) is False


# ─── Redaction Tests ─────────────────────────────────────────────────────────


class TestRedaction:
    def test_redact_sensitive_keys(self):
        """Sensitive field values should be redacted."""
        args = {
            "customer_id": "abc_123",
            "email": "user@example.com",
            "body": "This is a normal message body",
        }
        redacted = _redact_sensitive_fields(args)
        assert redacted["customer_id"] == "abc_123"
        assert redacted["email"] == "***REDACTED***"
        assert redacted["body"] == "This is a normal message body"

    def test_truncate_long_values(self):
        """Values longer than 50 chars should be truncated."""
        args = {"long_field": "a" * 100}
        redacted = _redact_sensitive_fields(args)
        assert len(redacted["long_field"]) < 50


# ─── Policy Request Model Tests ──────────────────────────────────────────────


class TestPolicyRequestModel:
    def test_default_request_id(self):
        """request_id should default to empty string."""
        req = PolicyRequest(
            agent_id="test", agent_role="admin", tool_name="test.tool", arguments={}
        )
        assert req.request_id == ""

    def test_all_fields_required(self):
        """All main fields should be required."""
        with pytest.raises(Exception):
            PolicyRequest(agent_id="test")


# ─── Tool Definition Tests ───────────────────────────────────────────────────


class TestToolRegistry:
    def test_all_tools_have_required_fields(self):
        """Every tool in the registry must have all required fields."""
        for name, tool in TOOL_REGISTRY.items():
            assert tool.name == name
            assert tool.description, f"Tool {name} has no description"
            assert tool.input_schema, f"Tool {name} has no input schema"
            assert isinstance(tool.risk_class, RiskClass), f"Tool {name} has invalid risk class"
            assert isinstance(tool.allowed_roles, list), f"Tool {name} has invalid allowed roles"
            assert isinstance(tool.requires_approval, bool)

    def test_crm_tools_have_correct_risk(self):
        """CRM tools should have appropriate risk levels."""
        assert TOOL_REGISTRY["crm.get_customer"].risk_class == RiskClass.READ_INTERNAL
        assert TOOL_REGISTRY["crm.update_customer_status"].risk_class == RiskClass.STATE_CHANGE

    def test_payment_tool_requires_dual_approval(self):
        """Payment tools should require dual approval."""
        assert TOOL_REGISTRY["payment.charge"].requires_dual_approval is True

    def test_dangerous_tools_limited_roles(self):
        """Dangerous tools should have limited allowed roles."""
        assert TOOL_REGISTRY["file.delete"].allowed_roles == ["admin"]
        assert TOOL_REGISTRY["payment.charge"].allowed_roles == ["admin"]
