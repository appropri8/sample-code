import random
import time


class ServiceBusyError(Exception):
    """Service is temporarily at capacity."""


class TimeoutError(Exception):
    """Request timed out."""


def exponential_backoff_with_jitter(
    attempt: int,
    base_delay: float = 0.1,
    max_delay: float = 30.0,
) -> float:
    """Calculate delay with exponential backoff and full jitter.

    AWS recommendation: APIs with side effects are not safe to retry
    unless they provide idempotency keys.
    """
    delay = min(base_delay * (2 ** attempt), max_delay)
    jittered = delay * (0.5 + random.random())
    return min(jittered, max_delay)


def safe_retry_request(
    request_fn,
    max_retries: int = 3,
    idempotent_only: bool = True,
    on_backoff=None,
):
    """Retry a request safely with exponential backoff and jitter.

    Args:
        request_fn: Callable that executes the request. Should have an
            `idempotent` attribute (bool) if `idempotent_only` is True.
        max_retries: Maximum number of retry attempts.
        idempotent_only: If True, raises if request is not idempotent.
        on_backoff: Optional callback(attempt, delay) for logging backoff.

    Raises:
        ValueError: If request is not idempotent and idempotent_only is True.
        ServiceBusyError: If service is busy and retries are exhausted.
        TimeoutError: If request times out and retries are exhausted.
    """
    if idempotent_only and not getattr(request_fn, "idempotent", False):
        raise ValueError(
            "Cannot retry non-idempotent request. "
            "Use idempotency keys to mark requests as safe to retry."
        )

    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return request_fn()
        except (ServiceBusyError, TimeoutError) as exc:
            last_exception = exc
            if attempt < max_retries:
                delay = exponential_backoff_with_jitter(attempt)
                if on_backoff:
                    on_backoff(attempt, delay)
                time.sleep(delay)
                continue
            raise last_exception
