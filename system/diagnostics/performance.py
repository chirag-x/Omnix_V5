"""
Omnix V5
Performance Monitor

Collects system performance metrics.
"""

from __future__ import annotations

import logging
from datetime import datetime

from system.services.resource_controller import (
    ResourceController,
)

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Collects and evaluates system performance.

    Uses ResourceController as the
    low-level resource provider.
    """

    def __init__(
        self,
        resource_controller: ResourceController | None = None,
    ) -> None:

        self._resource = resource_controller or ResourceController()

    # ---------------------------------------------------------
    # Collect
    # ---------------------------------------------------------

    def collect(
        self,
    ) -> dict:
        """
        Collect current system metrics.
        """

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "resources": self._resource.snapshot(),
        }

    # ---------------------------------------------------------
    # Health Evaluation
    # ---------------------------------------------------------

    def health_status(
        self,
    ) -> dict:
        """
        Evaluate basic resource health.
        """

        metrics = self.collect()

        warnings = []

        resources = metrics.get(
            "resources",
            {},
        )

        # CPU check

        cpu = resources.get(
            "cpu",
        )

        if cpu is not None and cpu > 90:

            warnings.append("High CPU usage")

        # Memory check

        memory = resources.get(
            "memory",
        )

        if memory:

            if (
                memory.get(
                    "percent",
                    0,
                )
                > 90
            ):

                warnings.append("High memory usage")

        # Disk check

        disk = resources.get(
            "disk",
        )

        if disk:

            if (
                disk.get(
                    "percent",
                    0,
                )
                > 90
            ):

                warnings.append("High disk usage")

        return {
            "healthy": len(warnings) == 0,
            "warnings": warnings,
            "metrics": metrics,
        }

    # ---------------------------------------------------------
    # Resource Access
    # ---------------------------------------------------------

    def snapshot(
        self,
    ) -> dict:

        return self._resource.snapshot()

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "resource_controller": repr(self._resource),
        }

    def __repr__(
        self,
    ) -> str:

        return "PerformanceMonitor()"
