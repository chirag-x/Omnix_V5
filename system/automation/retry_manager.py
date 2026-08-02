"""
Omnix V5
Retry Manager

Handles retry policies for failed automation actions.
"""

from __future__ import annotations

import logging
import time
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryManager:
    """
    Executes retry policies for automation operations.
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 0.5,
    ) -> None:

        self._max_retries = max_retries

        self._retry_delay = retry_delay

        self._enabled = True

    # ---------------------------------------------------------
    # State
    # ---------------------------------------------------------

    @property
    def enabled(
        self,
    ) -> bool:

        return self._enabled

    def enable(
        self,
    ) -> None:

        self._enabled = True

    def disable(
        self,
    ) -> None:

        self._enabled = False

    # ---------------------------------------------------------
    # Retry
    # ---------------------------------------------------------

    def execute(
        self,
        operation: Callable[[], T],
    ) -> T:

        if not self._enabled:

            return operation()

        last_exception: Exception | None = None

        for attempt in range(

            self._max_retries + 1,

        ):

            try:

                return operation()

            except Exception as exc:

                last_exception = exc

                logger.warning(

                    "Retry %s/%s failed: %s",

                    attempt + 1,

                    self._max_retries,

                    exc,

                )

                if attempt < self._max_retries:

                    time.sleep(

                        self._retry_delay,

                    )

        assert last_exception is not None

        raise last_exception

    # ---------------------------------------------------------
    # Configuration
    # ---------------------------------------------------------

    @property
    def max_retries(
        self,
    ) -> int:

        return self._max_retries

    @property
    def retry_delay(
        self,
    ) -> float:

        return self._retry_delay

    def configure(
        self,
        *,
        max_retries: int | None = None,
        retry_delay: float | None = None,
    ) -> None:

        if max_retries is not None:

            self._max_retries = max_retries

        if retry_delay is not None:

            self._retry_delay = retry_delay

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {

            "enabled": self._enabled,

            "max_retries": self._max_retries,

            "retry_delay": self._retry_delay,

        }

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return (

            "RetryManager("

            f"enabled={self._enabled}, "

            f"max_retries={self._max_retries}, "

            f"retry_delay={self._retry_delay})"

        )