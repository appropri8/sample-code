"""The order API handler.

This is the function the HTTP layer would call. It opens one transaction that
writes the order row AND the outbox event together, then returns. The outbox
relay (see outbox_relay.py) is what actually publishes later.
"""

import json
import time
import uuid

from retry_safe.db import transaction
from retry_safe.idempotency import handle as idempotent_handle


def create_order(conn, *, idempotency_key: str, user_id: str, amount_cents: int, items):
    """Idempotent order creation: business write + outbox in one tx."""

    def work():
        order_id = str(uuid.uuid4())
        with transaction(conn):
            conn.execute(
                """INSERT INTO orders (order_id, user_id, amount_cents, status, idempotency_key)
                   VALUES (?, ?, ?, 'created', ?)""",
                (order_id, user_id, amount_cents, idempotency_key),
            )
            conn.execute(
                """INSERT INTO outbox_events (event_id, event_type, aggregate_id, payload)
                   VALUES (?, 'OrderCreated', ?, ?)""",
                (str(uuid.uuid4()), order_id,
                 json.dumps({"order_id": order_id, "user_id": user_id,
                             "amount_cents": amount_cents, "items": items})),
            )
        return 201, {"order_id": order_id, "status": "created", "amount_cents": amount_cents}

    return idempotent_handle(
        conn,
        idempotency_key=idempotency_key,
        method="POST",
        path="/api/orders",
        body={"user_id": user_id, "amount_cents": amount_cents, "items": items},
        work=work,
    )
