"""Tests for the retry-safe workflow pieces."""

import pytest

from retry_safe.db import get_connection, init_schema
from retry_safe.order_api import create_order
from retry_safe.outbox_relay import run_relay
from retry_safe.payment_consumer import consume_order_created


@pytest.fixture
def conn():
    c = get_connection(":memory:")
    init_schema(c)
    return c


def test_retry_returns_same_order(conn):
    kw = dict(idempotency_key="k1", user_id="u1", amount_cents=1000, items=[])
    s1, b1 = create_order(conn, **kw)
    s2, b2 = create_order(conn, **kw)
    assert s1 == 201 and s2 == 201
    assert b1["order_id"] == b2["order_id"]


def test_key_reuse_with_different_body_is_rejected(conn):
    create_order(conn, idempotency_key="k2", user_id="u1", amount_cents=1000, items=[])
    s2, _ = create_order(conn, idempotency_key="k2", user_id="OTHER", amount_cents=9999, items=[])
    assert s2 == 422


def test_outbox_published_and_marked(conn):
    create_order(conn, idempotency_key="k3", user_id="u1", amount_cents=1000, items=[])
    n = run_relay(conn)
    assert n == 1
    remaining = conn.execute("SELECT COUNT(*) c FROM outbox_events WHERE status='pending'").fetchone()["c"]
    assert remaining == 0


def test_duplicate_delivery_is_skipped(conn):
    create_order(conn, idempotency_key="k4", user_id="u1", amount_cents=1000, items=[])
    run_relay(conn)
    row = conn.execute("SELECT order_id FROM orders").fetchone()
    payload = {"order_id": row["order_id"], "user_id": "u1", "amount_cents": 1000}
    first = consume_order_created(conn, consumer="pay", message_id="m1", payload=payload)
    again = consume_order_created(conn, consumer="pay", message_id="m1", payload=payload)
    assert first["handled"] is True
    assert again["handled"] is False
