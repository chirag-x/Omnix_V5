"""
Omnix V5
Health Check

Checks subsystem health.
"""

from __future__ import annotations

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class HealthCheck:
    """
    Performs health checks across Omnix systems.
    """

    def __init__(
        self,
    ) -> None:

        self._checks = {}

    # ---------------------------------------------------------
    # Register
    # ---------------------------------------------------------

    def register(
        self,
        name: str,
        checker,
    ) -> None:
        """
        Register a subsystem health checker.
        """

        self._checks[name] = checker


    # ---------------------------------------------------------
    # Run Checks
    # ---------------------------------------------------------

    def run(
        self,
    ) -> dict:
        """
        Execute all health checks.
        """

        results = {}

        for name, checker in self._checks.items():

            try:

                results[name] = {
                    "status": "healthy"
                    if checker()
                    else "unhealthy",
                }

            except Exception as exc:

                results[name] = {
                    "status": "error",
                    "error": str(exc),
                }

        return {

            "timestamp": datetime.utcnow().isoformat(),

            "overall": self._overall_status(
                results,
            ),

            "checks": results,

        }


    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def _overall_status(
        self,
        results: dict,
    ) -> str:

        for item in results.values():

            if item["status"] != "healthy":

                return "unhealthy"

        return "healthy"


    def statistics(
        self,
    ) -> dict:

        return {

            "checks": len(
                self._checks
            )

        }


    def __repr__(
        self,
    ) -> str:

        return (
            "HealthCheck("
            f"checks={len(self._checks)})"
        )