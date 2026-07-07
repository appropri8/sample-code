"""Idempotent message consumer using an inbox table.

The broker may deliver OrderCreated more than once. Before touching business
state we check the inbox. If the message_id is already there, we skip the work
but still ack the message, so the broker stops redelivering.
"""

import json
import time

from retry_safe.db import transaction


def consume_order_created(conn, *, consumer: str, message_id: str, payload: dict):
    """Process an OrderCreated event exactly once per message_id."""
    existing = conn.execute(
        "SELECT status FROM inbox_messages WHERE message_id = ? AND consumer = ?",
        (message_id, consumer),
    ).fetchone()

    if existing is not None:
        # Already handled. Ack and move on.
        return {"handled": False, "reason": f"duplicate ({existing['status']})"}

    # Not seen before: do the work and record it in the same transaction.
    order_id = payload["order_id"]
    try:
        with transaction(conn):
            # Simulate charging the customer.
            conn.execute(
                "UPDATE orders SET status = 'paid' WHERE order_id = ?",
                (order_id,),
            )
            # Write the next outbox event for downstream services.
            conn.execute(
                """INSERT INTO outbox_events (event_id, event_type, aggregate_id, payload)
                   VALUES (?, 'PaymentCaptured', ?, ?)""",
                (f"pay-{message_id}", order_id,
                 json.dumps({"order_id": order_id, "status": "paid"})),
            )
            conn.execute(
                "INSERT INTO inbox_messages (message_id, consumer, status) VALUES (?, ?, 'done')",
                (message_id, consumer),
            )
        return {"handled": True, "order_id": order_id}
    except Exception as exc:
        # Poison message: record it so we stop retrying forever.
        with transaction(conn):
            conn.execute(
                "INSERT OR REPLACE INTO inbox_messages (message_id, consumer, status) VALUES (?, ?, 'poison')",
                (message_id, consumer),
            )
        raise RuntimeError(f"poison message {message_id}: {exc}")
