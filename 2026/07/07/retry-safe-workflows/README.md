# Retry-Safe Workflows: Idempotency Keys, Outbox, and Inbox Tables

Complete, runnable code samples for the article
["Designing Retry-Safe Workflows with Idempotency Keys, Outbox, and Inbox Tables"](https://github.com/appropri8/sample-code).

The whole thing runs on Python's built-in `sqlite3`, so there is nothing to
install and no broker to stand up. The patterns (a real broker, Postgres, a
queue consumer) are drop-in swaps for the demo stand-ins.

## What this demonstrates

1. **Idempotency keys at the API layer** — a retry with the same key returns
   the original response; a key reused with a different body is rejected.
2. **Transactional outbox** — the order row and the `OrderCreated` event are
   written in one transaction, then a relay publishes them.
3. **Inbox table** — the payment consumer ignores redelivered messages by
   message id.
4. **Saga compensation** — if a later step fails, earlier steps are undone.

## Run it

```bash
python -m retry_safe.demo
```

Expected output ends with the order created once, the event published, the
redelivery skipped, and stock released by compensation.

## Test it

```bash
pip install -r requirements.txt
pytest
```

## Layout

```
retry-safe-workflows/
├── schema.sql                  # tables: idempotency_keys, orders,
│                               #   outbox_events, inbox_messages, saga_*
├── requirements.txt
├── README.md
├── retry_safe/
│   ├── __init__.py
│   ├── db.py                   # connections + explicit transactions
│   ├── idempotency.py          # API handler (key + request hash)
│   ├── order_api.py            # business write + outbox in one tx
│   ├── outbox_relay.py         # sweeps pending events and publishes
│   ├── payment_consumer.py     # inbox-deduped message consumer
│   ├── saga.py                 # saga progress + compensation
│   └── demo.py                 # ties the whole flow together
└── tests/
    └── test_retry_safe.py
```

## Notes for production

- Use Postgres. Its `SERIALIZABLE` isolation and `FOR UPDATE` row locks make
  the in-flight race in `idempotency.py` even safer than SQLite here.
- The relay should publish with the `event_id` as the broker key, and the
  consumer should dedupe on that id. Two layers of dedup (outbox + inbox) is
  normal; the outbox is about *publishing once*, the inbox about *applying once*.
- Cap idempotency key lifetime (24h is common) and expire old rows with a job.

## License

MIT
