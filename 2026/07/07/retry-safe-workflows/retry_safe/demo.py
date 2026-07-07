"""End-to-end demo of a retry-safe order workflow.

Run it:  python -m retry_safe.demo

It shows the four safety layers in one flow:
  1. Idempotency key at the API (retry returns the same order).
  2. Outbox so the order event is published exactly once-ish.
  3. Inbox so the payment consumer ignores duplicate deliveries.
  4. Saga compensation if a later step fails.
"""

import json
import sys

from retry_safe.db import get_connection, init_schema
from retry_safe.order_api import create_order
from retry_safe.outbox_relay import run_relay
from retry_safe.payment_consumer import consume_order_created
from retry_safe import saga as saga_mod


def main() -> int:
    conn = get_connection(":memory:")
    init_schema(conn)

    key = "pay-req-user-42-cart-7"
    items = [{"product_id": "sku-1", "qty": 2}]

    # --- 1. Client sends the request. Payment succeeds. ---
    status1, body1 = create_order(
        conn, idempotency_key=key, user_id="user-42",
        amount_cents=5000, items=items,
    )
    print(f"[api] first call  -> {status1} {body1}")

    # --- Client times out, retries with the SAME key. No double charge. ---
    status2, body2 = create_order(
        conn, idempotency_key=key, user_id="user-42",
        amount_cents=5000, items=items,
    )
    print(f"[api] retry call  -> {status2} {body2}")
    assert body1["order_id"] == body2["order_id"], "retry created a second order!"
    print("[ok ] idempotency held: same order_id on retry")

    # --- 2. Outbox relay publishes the OrderCreated event. ---
    published = run_relay(conn)
    print(f"[relay] published {published} event(s) from the outbox")

    # --- 3. Payment consumer handles the event. Broker redelivers once. ---
    order_row = conn.execute("SELECT * FROM orders").fetchone()
    payload = {"order_id": order_row["order_id"], "user_id": "user-42", "amount_cents": 5000}

    r1 = consume_order_created(conn, consumer="payment-svc", message_id="msg-1", payload=payload)
    r2 = consume_order_created(conn, consumer="payment-svc", message_id="msg-1", payload=payload)
    print(f"[consume] first delivery  -> {r1}")
    print(f"[consume] redelivery      -> {r2}")
    assert r2["handled"] is False, "duplicate delivery was not skipped!"
    print("[ok ] inbox dedup held: redelivery ignored")

    # --- 4. Saga compensation when a later step fails. ---
    saga_id = saga_mod.start_saga(conn, order_id=order_row["order_id"],
                                  steps=["reserve_stock", "charge_card"])
    saga_mod.mark_step(conn, saga_id=saga_id, step_name="reserve_stock")
    saga_mod.mark_step(conn, saga_id=saga_id, step_name="charge_card")

    released = {"stock": False}

    def release_stock():
        released["stock"] = True

    print("[saga] charge_card failed after stock was reserved -> compensating")
    saga_mod.compensate(conn, saga_id=saga_id,
                        compensations={"reserve_stock": release_stock})
    print(f"[saga] stock released: {released['stock']}")

    # Show final state.
    final = conn.execute("SELECT order_id, status FROM orders").fetchone()
    print(f"[final] order {final['order_id']} status = {final['status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
