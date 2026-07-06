import time
import threading
import pytest

from adaptive_load_shedding.adaptive_limiter import AdaptiveConcurrencyLimiter
from adaptive_load_shedding.middleware import ConcurrencyLimitMiddleware
from adaptive_load_shedding.retry import exponential_backoff_with_jitter, safe_retry_request, ServiceBusyError


class TestAdaptiveConcurrencyLimiter:
    def test_initial_limit_is_half_max(self):
        limiter = AdaptiveConcurrencyLimiter(max_concurrency=100)
        assert limiter.current == 50.0

    def test_rejects_when_at_capacity(self):
        limiter = AdaptiveConcurrencyLimiter(min_concurrency=1, max_concurrency=2)
        assert limiter.allow_request() is True
        assert limiter.allow_request() is False

    def test_releases_and_allows_again(self):
        limiter = AdaptiveConcurrencyLimiter(min_concurrency=1, max_concurrency=2)
        limiter.allow_request()
        limiter.allow_request()
        assert limiter.allow_request() is False
        limiter.release_request()
        assert limiter.allow_request() is True

    def test_decreases_limit_when_latency_high(self):
        limiter = AdaptiveConcurrencyLimiter(
            min_concurrency=10,
            max_concurrency=100,
            target_latency_seconds=0.05,
        )
        for _ in range(10):
            limiter.record_latency(0.2)
        assert limiter.current < limiter.max

    def test_increases_limit_when_latency_low(self):
        limiter = AdaptiveConcurrencyLimiter(
            min_concurrency=10,
            max_concurrency=100,
            target_latency_seconds=0.1,
        )
        limiter.current = 20.0
        for _ in range(10):
            limiter.record_latency(0.01)
        assert limiter.current > 20.0

    def test_respects_min_and_max(self):
        limiter = AdaptiveConcurrencyLimiter(min_concurrency=5, max_concurrency=10)
        limiter.current = 5.0
        for _ in range(20):
            limiter.record_latency(1.0)
        assert limiter.current >= 5.0

        limiter.current = 10.0
        for _ in range(20):
            limiter.record_latency(0.001)
        assert limiter.current <= 10.0


class FakeHandler:
    def __init__(self, block_event, response="ok"):
        self.block_event = block_event
        self.response = response
        self.calls = []

    def send_response(self, code, message=None):
        pass

    def send_header(self, keyword, value):
        pass

    def end_headers(self):
        pass

    def wfile(self):
        return type('obj', (object,), {'write': lambda x: None})()

    def __call__(self, *args, **kwargs):
        self.calls.append(1)
        self.block_event.wait(0.05)
        return self.response


class TestConcurrencyLimitMiddleware:
    def test_rejects_over_limit(self):
        block_event = threading.Event()
        middleware = ConcurrencyLimitMiddleware(max_concurrency=1)

        def blocking_handler():
            block_event.wait(0.05)
            return "ok"

        wrapped = middleware.wrap(blocking_handler)
        t = threading.Thread(target=wrapped)
        t.start()

        time.sleep(0.01)
        result = wrapped()
        assert result is None

        block_event.set()
        t.join()

    def test_tracks_stats(self):
        middleware = ConcurrencyLimitMiddleware(max_concurrency=1)
        events = [threading.Event() for _ in range(2)]

        def handler1():
            events[0].wait(0.05)
            return "ok"

        def handler2():
            events[1].wait(0.05)
            return "ok"

        wrapped1 = middleware.wrap(handler1)
        wrapped2 = middleware.wrap(handler2)

        t1 = threading.Thread(target=wrapped1)
        t2 = threading.Thread(target=wrapped2)
        t1.start()
        t2.start()

        time.sleep(0.02)
        assert middleware.stats["accepted"] == 1
        assert middleware.stats["rejected"] == 1

        events[0].set()
        events[1].set()
        t1.join()
        t2.join()


class TestRetryBehavior:
    def test_backoff_increases_exponentially(self):
        for _ in range(20):
            delay0 = exponential_backoff_with_jitter(0)
            delay1 = exponential_backoff_with_jitter(1)
            delay2 = exponential_backoff_with_jitter(2)
            assert delay1 >= delay0 * 0.5
            assert delay2 >= delay1 * 0.5

    def test_respects_max_delay(self):
        for _ in range(50):
            delay = exponential_backoff_with_jitter(10, base_delay=0.1, max_delay=1.0)
            assert delay <= 1.0

    def test_successful_retry(self):
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ServiceBusyError("busy")
            return "ok"
        flaky.idempotent = True

        result = safe_retry_request(flaky, max_retries=3)
        assert result == "ok"
        assert call_count == 2

    def test_raises_after_max_retries(self):
        def always_fails():
            raise ServiceBusyError("always")
        always_fails.idempotent = True

        with pytest.raises(ServiceBusyError):
            safe_retry_request(always_fails, max_retries=2)

    def test_non_idempotent_rejected(self):
        def non_idempotent():
            return "ok"
        non_idempotent.idempotent = False

        with pytest.raises(ValueError, match="non-idempotent"):
            safe_retry_request(non_idempotent, idempotent_only=True)
