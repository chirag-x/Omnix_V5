"""
Omnix V5
Process Interface

Defines process management contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class ProcessInterface(ABC):
    """
    Interface for process operations.
    """

    # ---------------------------------------------------------
    # Start
    # ---------------------------------------------------------

    @abstractmethod
    def start(
        self,
        process: str,
    ) -> bool:
        """
        Start a process.
        """

        pass

    # ---------------------------------------------------------
    # Stop
    # ---------------------------------------------------------

    @abstractmethod
    def stop(
        self,
        process: str,
    ) -> bool:
        """
        Stop a process.
        """

        pass

    # ---------------------------------------------------------
    # Running Check
    # ---------------------------------------------------------

    @abstractmethod
    def is_running(
        self,
        process: str,
    ) -> bool:
        """
        Check whether process is running.
        """

        pass

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    @abstractmethod
    def information(
        self,
        process: str,
    ) -> dict:
        """
        Return process information.
        """

        pass

    # ---------------------------------------------------------
    # List
    # ---------------------------------------------------------

    @abstractmethod
    def list_processes(
        self,
    ) -> list:
        """
        Return running processes.
        """

        pass
