"""Transactional outbox relay.

The order service wrote OrderCreated to outbox_events in its own DB tx. This
worker sweeps the pending rows, "publishes" them (here we just print; in real
life you'd send to Kafka/RabbitMQ), and marks them published. If the worker
dies between publish and mark-published, the next sweep re-publishes the same
event, so the publisher side must also be idempotent or tolerate duplicates.
"""

import json
import time

from retry_safe.db import transaction


def publish(event: dict) -> None:
    """Stand-in for a real broker publish. Swap for your producer here."""
    print(f"[broker] publish {event['event_type']} -> {event['aggregate_id']}")


def sweep_once(conn) -> int:
    """Publish every pending outbox event exactly once (best effort)."""
    pending = conn.execute(
        "SELECT * FROM outbox_events WHERE status = 'pending' ORDER BY created_at"
    ).fetchall()

    published = 0
    for row in pending:
        event = {
            "event_id": row["event_id"],
            "event_type": row["event_type"],
            "aggregate_id": row["aggregate_id"],
            "payload": json.loads(row["payload"]),
        }
        # Publish first. If we crash before the UPDATE, the next sweep retries.
        # A real broker dedupes on event_id, so re-publish is safe.
        publish(event)
        with transaction(conn):
            conn.execute(
                "UPDATE outbox_events SET status = 'published', published_at = ? WHERE event_id = ?",
                (time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), row["event_id"]),
            )
        published += 1
    return published


def run_relay(conn, *, stop_after_empty: bool = True) -> int:
    """Loop until there is nothing left to publish. Demo helper."""
    total = 0
    while True:
        n = sweep_once(conn)
        total += n
        if stop_after_empty and n == 0:
            break
    return total
