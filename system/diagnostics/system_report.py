"""
Omnix V5
System Report

Creates complete system diagnostic reports.
"""

from __future__ import annotations

import logging
from datetime import datetime
import uuid

from .health_check import HealthCheck
from .performance import PerformanceMonitor

logger = logging.getLogger(__name__)


class SystemReport:
    """
    Generates complete Omnix system reports.
    """

    def __init__(
        self,
        health_check: HealthCheck | None = None,
        performance: PerformanceMonitor | None = None,
    ) -> None:

        self._health = health_check or HealthCheck()

        self._performance = performance or PerformanceMonitor()

    # ---------------------------------------------------------
    # Generate
    # ---------------------------------------------------------

    def generate(
        self,
    ) -> dict:

        health = self._health.run()

        performance = self._performance.health_status()

        return {
            "version": "V5",
            "report_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "status": self._overall_status(
                health,
                performance,
            ),
            "health": health,
            "performance": performance,
        }

    # ---------------------------------------------------------
    # Status
    # ---------------------------------------------------------

    def _overall_status(
        self,
        health: dict,
        performance: dict,
    ) -> str:

        if health["overall"] != "healthy":

            return "warning"

        warnings = performance.get(
            "warnings",
            [],
        )

        if len(warnings) >= 2:

            return "critical"

        if warnings:

            return "warning"

        return "healthy"

    # ---------------------------------------------------------
    # Human Summary
    # ---------------------------------------------------------

    def summary(
        self,
    ) -> str:

        report = self.generate()

        resources = report["performance"]["metrics"]["resources"]

        cpu = resources.get(
            "cpu",
            "N/A",
        )

        memory = resources.get("memory", {})

        memory_percent = memory.get(
            "percent",
            "N/A",
        )

        return (
            f"Omnix Status: "
            f"{report['status']}\n"
            f"CPU: {cpu}%\n"
            f"Memory: {memory_percent}%"
        )

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "health": repr(self._health),
            "performance": repr(self._performance),
        }

    def __repr__(
        self,
    ) -> str:

        return "SystemReport()"
