"""
Omnix V5
Resource Controller

Low-level system resource information.
"""

from __future__ import annotations

import logging

import psutil

logger = logging.getLogger(__name__)


class ResourceController:
    """
    Provides direct access to system resources.

    Responsible only for collecting system data.
    """

    def __init__(
        self,
    ) -> None:

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
    # CPU
    # ---------------------------------------------------------

    def cpu_usage(
        self,
    ) -> float | None:

        if not self._enabled:

            return None

        try:

            return psutil.cpu_percent(
                interval=0.1,
            )

        except Exception as exc:

            logger.error(
                "CPU reading failed: %s",
                exc,
            )

            return None

    # ---------------------------------------------------------
    # Memory
    # ---------------------------------------------------------

    def memory_usage(
        self,
    ) -> dict | None:

        try:

            data = psutil.virtual_memory()

            return {
                "total": data.total,
                "available": data.available,
                "used": data.used,
                "percent": data.percent,
            }

        except Exception as exc:

            logger.error(
                "Memory reading failed: %s",
                exc,
            )

            return None

    # ---------------------------------------------------------
    # Disk
    # ---------------------------------------------------------

    def disk_usage(
        self,
        path: str = "/",
    ) -> dict | None:

        try:

            data = psutil.disk_usage(
                path,
            )

            return {
                "total": data.total,
                "used": data.used,
                "free": data.free,
                "percent": data.percent,
            }

        except Exception as exc:

            logger.error(
                "Disk reading failed: %s",
                exc,
            )

            return None

    # ---------------------------------------------------------
    # Battery
    # ---------------------------------------------------------

    def battery_status(
        self,
    ) -> dict | None:

        try:

            battery = psutil.sensors_battery()

            if battery is None:

                return None

            return {
                "percent": battery.percent,
                "plugged": battery.power_plugged,
                "seconds_left": battery.secsleft,
            }

        except Exception as exc:

            logger.error(
                "Battery reading failed: %s",
                exc,
            )

            return None

    # ---------------------------------------------------------
    # Network
    # ---------------------------------------------------------

    def network_usage(
        self,
    ) -> dict | None:

        try:

            data = psutil.net_io_counters()

            return {
                "bytes_sent": data.bytes_sent,
                "bytes_received": data.bytes_recv,
            }

        except Exception as exc:

            logger.error(
                "Network reading failed: %s",
                exc,
            )

            return None

    # ---------------------------------------------------------
    # GPU
    # ---------------------------------------------------------

    def gpu_usage(
        self,
    ) -> dict | None:
        """
        GPU monitoring.

        Future:
        NVIDIA NVML integration.
        """

        return None

    # ---------------------------------------------------------
    # Complete Snapshot
    # ---------------------------------------------------------

    def snapshot(
        self,
    ) -> dict:

        return {
            "cpu": self.cpu_usage(),
            "memory": self.memory_usage(),
            "disk": self.disk_usage(),
            "battery": self.battery_status(),
            "network": self.network_usage(),
            "gpu": self.gpu_usage(),
        }

    # ---------------------------------------------------------
    # Diagnostics
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "enabled": self._enabled,
        }

    def __repr__(
        self,
    ) -> str:

        return "ResourceController(" f"enabled={self._enabled})"
