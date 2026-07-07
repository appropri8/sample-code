-- Schema for the retry-safe workflow demo.
-- Kept intentionally close to what you would write for Postgres, with the
-- few SQLite-isms noted inline.

-- 1. Idempotency keys: one row per client-supplied key at the API layer.
CREATE TABLE IF NOT EXISTS idempotency_keys (
    idempotency_key TEXT PRIMARY KEY,
    request_hash    TEXT NOT NULL,          -- sha256 of method + path + body
    status          TEXT NOT NULL,          -- processing | completed | failed
    response_status INTEGER,                -- e.g. 200, 409
    response_body   TEXT,                    -- stored JSON of the first response
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at      TEXT NOT NULL            -- keys are not kept forever
);

-- 2. Orders: the business table for the demo workflow.
CREATE TABLE IF NOT EXISTS orders (
    order_id        TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL,
    amount_cents    INTEGER NOT NULL,
    status          TEXT NOT NULL,          -- created | paid | failed
    idempotency_key TEXT UNIQUE,            -- links the request to its order
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 3. Outbox: events written in the same tx as the business row.
CREATE TABLE IF NOT EXISTS outbox_events (
    event_id    TEXT PRIMARY KEY,
    event_type  TEXT NOT NULL,              -- e.g. OrderCreated
    aggregate_id TEXT NOT NULL,             -- the order_id
    payload     TEXT NOT NULL,              -- JSON
    status      TEXT NOT NULL DEFAULT 'pending',  -- pending | published
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    published_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_outbox_status ON outbox_events(status);

-- 4. Inbox: what the consumer has already processed, keyed by message id.
CREATE TABLE IF NOT EXISTS inbox_messages (
    message_id  TEXT PRIMARY KEY,
    consumer    TEXT NOT NULL,              -- which service processed it
    status      TEXT NOT NULL DEFAULT 'done',     -- done | poison
    processed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 5. Saga bookkeeping: which step we are on and whether we compensated.
CREATE TABLE IF NOT EXISTS saga_instances (
    saga_id     TEXT PRIMARY KEY,
    order_id    TEXT NOT NULL,
    status      TEXT NOT NULL,              -- in_progress | completed | compensated
    current_step TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS saga_steps (
    saga_id     TEXT NOT NULL,
    step_index  INTEGER NOT NULL,
    step_name   TEXT NOT NULL,              -- create_order | charge_payment | ...
    status      TEXT NOT NULL,              -- done | compensated
    compensated_at TEXT,
    PRIMARY KEY (saga_id, step_index)
);
