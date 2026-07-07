"""Saga bookkeeping with compensation.

A saga is just a list of local steps. Each step commits on its own database.
If a later step fails, we run compensating actions for the steps that already
succeeded, in reverse order. The saga_instances / saga_steps tables store
where we are so a crashed coordinator can resume.

This module is intentionally small: it tracks progress and runs compensations.
It does not decide business rules; the caller supplies the compensations.
"""

import time
import uuid

from retry_safe.db import transaction


def start_saga(conn, *, order_id: str, steps: list[str]) -> str:
    saga_id = str(uuid.uuid4())
    with transaction(conn):
        conn.execute(
            "INSERT INTO saga_instances (saga_id, order_id, status, current_step) VALUES (?, ?, 'in_progress', ?)",
            (saga_id, order_id, steps[0] if steps else ""),
        )
        for i, name in enumerate(steps):
            conn.execute(
                "INSERT INTO saga_steps (saga_id, step_index, step_name, status) VALUES (?, ?, ?, 'done')",
                (saga_id, i, name),
            )
    return saga_id


def mark_step(conn, *, saga_id: str, step_name: str) -> None:
    with transaction(conn):
        conn.execute(
            "UPDATE saga_steps SET status = 'done' WHERE saga_id = ? AND step_name = ?",
            (saga_id, step_name),
        )
        conn.execute(
            "UPDATE saga_instances SET current_step = ?, updated_at = ? WHERE saga_id = ?",
            (step_name, _now(), saga_id),
        )


def compensate(conn, *, saga_id: str, compensations: dict[str, callable]) -> None:
    """Run compensations for done steps, newest first.

    `compensations` maps a step_name to a zero-arg callable that undoes it.
    """
    steps = conn.execute(
        "SELECT step_index, step_name FROM saga_steps WHERE saga_id = ? AND status = 'done' ORDER BY step_index DESC",
        (saga_id,),
    ).fetchall()

    for step in steps:
        fn = compensations.get(step["step_name"])
        if fn:
            fn()
        with transaction(conn):
            conn.execute(
                "UPDATE saga_steps SET status = 'compensated', compensated_at = ? WHERE saga_id = ? AND step_index = ?",
                (_now(), saga_id, step["step_index"]),
            )

    with transaction(conn):
        conn.execute(
            "UPDATE saga_instances SET status = 'compensated', updated_at = ? WHERE saga_id = ?",
            (_now(), saga_id),
        )


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
