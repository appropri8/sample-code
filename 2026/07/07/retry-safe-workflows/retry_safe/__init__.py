"""Make `python -m retry_safe` and `from retry_safe import ...` work."""

from retry_safe.db import get_connection, init_schema

__all__ = ["get_connection", "init_schema"]
