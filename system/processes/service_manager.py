"""
Omnix V5
Service Manager
"""

from __future__ import annotations

import logging
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class ServiceManager:
    """
    Manage Windows services.

    Responsibilities
    ----------------
    • Enumerate services
    • Query service status
    • Start services
    • Stop services
    • Restart services
    """

    def services(self) -> list[Any]:
        """
        Return all Windows services.
        """

        try:

            return list(psutil.win_service_iter())

        except Exception:

            logger.exception(
                "Unable to enumerate services."
            )

            return []

    def get(
        self,
        name: str,
    ) -> Any | None:
        """
        Get one Windows service.
        """

        try:

            return psutil.win_service_get(name)

        except Exception:

            return None

    def exists(
        self,
        name: str,
    ) -> bool:

        return self.get(name) is not None

    def status(
        self,
        name: str,
    ) -> str | None:
        """
        Return service status.
        """

        service = self.get(name)

        if service is None:

            return None

        try:

            return service.status()

        except Exception:

            return None

    def start(
        self,
        name: str,
    ) -> bool:
        """
        Start a service.
        """

        service = self.get(name)

        if service is None:

            return False

        try:

            service.start()

            return True

        except Exception:

            logger.exception(
                "Failed to start service '%s'.",
                name,
            )

            return False

    def stop(
        self,
        name: str,
    ) -> bool:
        """
        Stop a service.
        """

        service = self.get(name)

        if service is None:

            return False

        try:

            service.stop()

            return True

        except Exception:

            logger.exception(
                "Failed to stop service '%s'.",
                name,
            )

            return False

    def restart(
        self,
        name: str,
    ) -> bool:
        """
        Restart a service.
        """

        if not self.stop(name):

            return False

        return self.start(name)

    def information(
        self,
        name: str,
    ) -> dict | None:
        """
        Return service information.
        """

        service = self.get(name)

        if service is None:

            return None

        try:

            return service.as_dict()

        except Exception:

            logger.exception(
                "Failed reading service information."
            )

            return None

    def running(self) -> list[Any]:
        """
        Return running services.
        """

        running = []

        for service in self.services():

            try:

                if service.status() == "running":

                    running.append(service)

            except Exception:

                continue

        return running

    def stopped(self) -> list[Any]:
        """
        Return stopped services.
        """

        stopped = []

        for service in self.services():

            try:

                if service.status() == "stopped":

                    stopped.append(service)

            except Exception:

                continue

        return stopped

    def statistics(self) -> dict:

        services = self.services()

        return {
            "total": len(services),
            "running": len(self.running()),
            "stopped": len(self.stopped()),
        }

    def __len__(self) -> int:

        return len(self.services())

    def __repr__(self) -> str:

        return (
            f"{self.__class__.__name__}"
            f"(services={len(self)})"
        )