"""Idempotency key logic for the API layer.

The handler does three things:
  1. Hash the request (method + path + body) so we can catch key reuse.
  2. On a new key, store a 'processing' row and let the work run.
  3. On a repeat key, return the stored response instead of doing the work again.

This mirrors how Stripe behaves: the first response for a key is cached and
replayed on later requests that carry the same key.
"""

import hashlib
import json
import time

from retry_safe.db import transaction


def request_hash(method: str, path: str, body: dict) -> str:
    raw = f"{method}\n{path}\n{json.dumps(body, sort_keys=True)}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _expiry(days: int = 1) -> str:
    # SQLite has no date math in strftime across days, so we compute it.
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() + days * 86400))


def handle(
    conn,
    *,
    idempotency_key: str,
    method: str,
    path: str,
    body: dict,
    work,
):
    """Run `work()` once per idempotency key.

    `work` is a callable that returns (status_code, response_dict). It should
    perform the real business write. It only ever runs once per key.
    """
    r_hash = request_hash(method, path, body)
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

    # Fast path: key already seen. Replay the stored response, but first
    # make sure the caller reused the key for the SAME request. Reusing a key
    # with a different body is a client bug we must reject (Stripe does too).
    row = conn.execute(
        "SELECT status, response_status, response_body, request_hash FROM idempotency_keys WHERE idempotency_key = ?",
        (idempotency_key,),
    ).fetchone()

    if row is not None:
        if row["request_hash"] != r_hash:
            return 422, {"error": "idempotency key reused with a different request"}
        if row["status"] == "processing":
            # A previous request is still in flight. Tell the client to wait
            # and retry rather than start a second execution.
            return 409, {"error": "request in progress", "idempotency_key": idempotency_key}
        # completed or failed: replay the original response.
        return row["response_status"], json.loads(row["response_body"])

    # New key. Reserve it atomically. The UNIQUE constraint on the key is our
    # guard against two in-flight requests with the same key.
    try:
        with transaction(conn):
            conn.execute(
                """INSERT INTO idempotency_keys
                   (idempotency_key, request_hash, status, created_at, expires_at)
                   VALUES (?, ?, 'processing', ?, ?)""",
                (idempotency_key, r_hash, now, _expiry()),
            )
    except sqlite3.IntegrityError:  # another request grabbed the key first
        return 409, {"error": "request in progress", "idempotency_key": idempotency_key}

    # Do the real work once.
    try:
        status_code, response = work()
        new_status = "completed" if 200 <= status_code < 300 else "failed"
        with transaction(conn):
            conn.execute(
                """UPDATE idempotency_keys
                   SET status = ?, response_status = ?, response_body = ?
                   WHERE idempotency_key = ?""",
                (new_status, status_code, json.dumps(response), idempotency_key),
            )
        return status_code, response
    except Exception as exc:
        with transaction(conn):
            conn.execute(
                """UPDATE idempotency_keys
                   SET status = 'failed', response_status = 500, response_body = ?
                   WHERE idempotency_key = ?""",
                (json.dumps({"error": str(exc)}), idempotency_key),
            )
        raise


import sqlite3  # noqa: E402  (kept at bottom to avoid clutter above)
