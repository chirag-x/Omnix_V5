"""
Omnix V5
Retry Utility

Reusable retry mechanism.
"""

from __future__ import annotations

import logging
import time

from functools import wraps


from .constants import (
    DEFAULT_RETRY_COUNT,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Retry Decorator
# ---------------------------------------------------------


def retry(
    attempts: int = DEFAULT_RETRY_COUNT,
    delay: float = 1.0,
    exceptions: tuple = (Exception,),
):
    """
    Retry function on failure.
    """

    def decorator(
        function,
    ):

        @wraps(
            function,
        )
        def wrapper(
            *args,
            **kwargs,
        ):

            last_error = None

            for attempt in range(
                1,
                attempts + 1,
            ):

                try:

                    return function(
                        *args,
                        **kwargs,
                    )

                except exceptions as exc:

                    last_error = exc

                    logger.warning(
                        "Attempt %s/%s failed for %s: %s",
                        attempt,
                        attempts,
                        function.__name__,
                        exc,
                    )

                    if attempt < attempts:

                        time.sleep(
                            delay,
                        )

            logger.error(
                "All retry attempts failed: %s",
                function.__name__,
            )

            raise last_error

        return wrapper

    return decorator


# ---------------------------------------------------------
# Manual Retry
# ---------------------------------------------------------


def execute_with_retry(
    function,
    attempts: int = DEFAULT_RETRY_COUNT,
    delay: float = 1.0,
    *args,
    **kwargs,
):
    """
    Execute function with retry.
    """

    last_error = None

    for attempt in range(
        1,
        attempts + 1,
    ):

        try:

            return function(
                *args,
                **kwargs,
            )

        except Exception as exc:

            last_error = exc

            logger.warning(
                "Retry %s/%s failed: %s",
                attempt,
                attempts,
                exc,
            )

            if attempt < attempts:

                time.sleep(
                    delay,
                )

    raise last_error
