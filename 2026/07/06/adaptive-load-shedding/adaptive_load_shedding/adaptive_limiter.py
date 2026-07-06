import collections
import threading
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LatencySample:
    """A single latency observation."""

    route: str
    latency_seconds: float
    timestamp: float
    was_rejected: bool = False


class AdaptiveConcurrencyLimiter:
    """Dynamically adjusts concurrency limit based on observed latency."""

    def __init__(
        self,
        min_concurrency: int = 10,
        max_concurrency: int = 100,
        target_latency_seconds: float = 0.1,
        history_size: int = 20,
    ):
        self.min = min_concurrency
        self.max = max_concurrency
        self.target = target_latency_seconds
        self.history_size = history_size

        self.current = max_concurrency / 2
        self._latencies: collections.deque = collections.deque(maxlen=history_size)
        self.in_flight = 0
        self.lock = threading.Lock()
        self.rejection_count = 0
        self.acceptance_count = 0

    def allow_request(self, route: str = "default") -> bool:
        """Check if a new request can be accepted."""
        with self.lock:
            if self.in_flight < self.current:
                self.in_flight += 1
                self.acceptance_count += 1
                return True
            self.rejection_count += 1
            return False

    def release_request(self):
        """Mark a request as completed."""
        with self.lock:
            self.in_flight -= 1

    def record_latency(self, latency_seconds: float):
        """Record a latency observation and adjust the limit if needed."""
        self._latencies.append(latency_seconds)

        if len(self._latencies) < 5:
            return

        avg_latency = sum(self._latencies) / len(self._latencies)

        if avg_latency > self.target * 1.5:
            new_limit = max(self.min, self.current * 0.9)
            self.current = new_limit
        elif avg_latency < self.target * 0.8:
            new_limit = min(self.max, self.current * 1.05)
            self.current = new_limit

    @property
    def utilization(self) -> float:
        """Current concurrency utilization percentage."""
        with self.lock:
            return (self.in_flight / self.current) * 100 if self.current > 0 else 0.0

    @property
    def avg_latency(self) -> float:
        """Average observed latency."""
        with self.lock:
            if not self._latencies:
                return 0.0
            return sum(self._latencies) / len(self._latencies)
