"""Database helpers for the retry-safe workflow demo.

Uses SQLite so the whole sample runs with nothing but Python installed.
In production you would point this at PostgreSQL and use its stronger
transaction isolation, but the patterns below are the same.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"


def get_connection(db_path: str = ":memory:") -> sqlite3.Connection:
    """Open a connection and make it behave predictably.

    - isolation_level=None puts us in autocommit so we control BEGIN/COMMIT
      explicitly. That matters for the outbox + saga code, where we want a
      single transaction to touch several tables at once.
    """
    conn = sqlite3.connect(db_path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Create every table from schema.sql."""
    sql = SCHEMA_PATH.read_text()
    conn.executescript(sql)


@contextmanager
def transaction(conn: sqlite3.Connection):
    """A real transaction boundary.

    We commit on success and roll back on any exception. Callers still have
    to do their own row locking where races are possible.
    """
    conn.execute("BEGIN")
    try:
        yield conn
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
