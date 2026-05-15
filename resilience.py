from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TypeVar

from tenacity import RetryError, retry, stop_after_attempt, wait_exponential

from config import (
    RETRY_BASE_DELAY_SECONDS,
    RETRY_MAX_ATTEMPTS,
    RETRY_MAX_DELAY_SECONDS,
)

T = TypeVar("T")

log = logging.getLogger(__name__)


class RetryOperationError(RuntimeError):
    """Raised when a retried operation exhausts all attempts."""


def run_with_retry(operation_name: str, operation: Callable[[], T]) -> T:
    """
    Execute `operation` with exponential backoff.

    This is intended for transient failures in network/LLM/tool calls.
    """

    @retry(
        stop=stop_after_attempt(max(1, RETRY_MAX_ATTEMPTS)),
        wait=wait_exponential(
            multiplier=max(0.01, RETRY_BASE_DELAY_SECONDS),
            max=max(RETRY_BASE_DELAY_SECONDS, RETRY_MAX_DELAY_SECONDS),
        ),
        reraise=True,
    )
    def _runner() -> T:
        return operation()

    try:
        return _runner()
    except RetryError as exc:
        # Defensive guard in case tenacity raises RetryError in edge modes.
        log.error("retry_exhausted", extra={"operation": operation_name})
        raise RetryOperationError(
            f"{operation_name} failed after retry attempts"
        ) from exc
    except Exception as exc:
        # reraise=True usually surfaces the last exception directly.
        raise RetryOperationError(
            f"{operation_name} failed after retry attempts: {exc}"
        ) from exc
