import time
import threading
from adaptive_load_shedding.adaptive_limiter import AdaptiveConcurrencyLimiter
from adaptive_load_shedding.retry import safe_retry_request, ServiceBusyError


def simulate_slow_service(limiter: AdaptiveConcurrencyLimiter, duration_seconds: float):
    """Simulate a service that becomes slow under load."""
    try:
        time.sleep(duration_seconds)
        limiter.record_latency(duration_seconds)
    finally:
        limiter.release_request()


def run_demo():
    limiter = AdaptiveConcurrencyLimiter(
        min_concurrency=5,
        max_concurrency=50,
        target_latency_seconds=0.05,
    )

    print("Initial concurrency limit:", limiter.current)
    print("Target latency: 50ms")

    normal_latencies = [0.02, 0.03, 0.025, 0.04, 0.03]
    for lat in normal_latencies:
        limiter.record_latency(lat)
        time.sleep(0.01)

    print("After normal traffic - limit:", round(limiter.current, 2), "avg latency:", round(limiter.avg_latency * 1000, 1), "ms")

    print("\nSimulating traffic spike with slow requests...")
    threads = []
    for i in range(20):
        accepted = limiter.allow_request()
        if accepted:
            t = threading.Thread(target=simulate_slow_service, args=(limiter, 0.2))
            threads.append(t)
            t.start()

    for t in threads:
        t.join()

    print("After spike - limit:", round(limiter.current, 2), "avg latency:", round(limiter.avg_latency * 1000, 1), "ms")

    print("\nSimulating recovery...")
    for _ in range(30):
        accepted = limiter.allow_request()
        if accepted:
            # Simulate fast request latency
            time.sleep(0.01)
            limiter.record_latency(0.03)
            limiter.release_request()
        time.sleep(0.02)

    print("After recovery - limit:", round(limiter.current, 2), "avg latency:", round(limiter.avg_latency * 1000, 1), "ms")


def run_retry_demo():
    attempt_log = []

    def flaky_request():
        if len(attempt_log) < 2:
            attempt_log.append(1)
            raise ServiceBusyError("Busy")
        return "success"
    flaky_request.idempotent = True

    def log_backoff(attempt, delay):
        print(f"  Backoff attempt {attempt}: {delay:.3f}s")

    print("\n--- Retry Demo ---")
    result = safe_retry_request(
        flaky_request,
        max_retries=3,
        on_backoff=log_backoff,
    )
    print("Result:", result)
    print("Total attempts:", len(attempt_log) + 1)


if __name__ == "__main__":
    run_demo()
    run_retry_demo()
