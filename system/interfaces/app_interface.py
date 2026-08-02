"""
Omnix V5
Application Interface

Defines application management contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class AppInterface(ABC):
    """
    Interface for application operations.
    """

    # ---------------------------------------------------------
    # Launch
    # ---------------------------------------------------------

    @abstractmethod
    def launch(
        self,
        application: str,
    ) -> bool:
        """
        Launch an application.
        """

        pass

    # ---------------------------------------------------------
    # Close
    # ---------------------------------------------------------

    @abstractmethod
    def close(
        self,
        application: str,
    ) -> bool:
        """
        Close an application.
        """

        pass

    # ---------------------------------------------------------
    # Running Check
    # ---------------------------------------------------------

    @abstractmethod
    def is_running(
        self,
        application: str,
    ) -> bool:
        """
        Check whether application is running.
        """

        pass

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    @abstractmethod
    def information(
        self,
        application: str,
    ) -> dict:
        """
        Return application information.
        """

        pass
