import threading


class ConcurrencyLimitMiddleware:
    """In-flight request limiter middleware."""

    def __init__(self, max_concurrency=50):
        self.max = max_concurrency
        self.in_flight = 0
        self.lock = threading.Lock()
        self.stats = {"rejected": 0, "accepted": 0}

    def wrap(self, handler):
        """Wrap a callable with concurrency limiting."""

        def limited_handler(*args, **kwargs):
            with self.lock:
                if self.in_flight >= self.max:
                    self.stats["rejected"] += 1
                    return None
                self.in_flight += 1
                self.stats["accepted"] += 1

            try:
                return handler(*args, **kwargs)
            finally:
                with self.lock:
                    self.in_flight -= 1

        return limited_handler
