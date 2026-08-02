"""
Omnix V5
Window Interface

Defines window management contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class WindowInterface(ABC):
    """
    Interface for window operations.
    """

    # ---------------------------------------------------------
    # Focus
    # ---------------------------------------------------------

    @abstractmethod
    def focus(
        self,
        window: str,
    ) -> bool:
        """
        Focus a window.
        """

        pass

    # ---------------------------------------------------------
    # Close
    # ---------------------------------------------------------

    @abstractmethod
    def close(
        self,
        window: str,
    ) -> bool:
        """
        Close a window.
        """

        pass

    # ---------------------------------------------------------
    # Minimize
    # ---------------------------------------------------------

    @abstractmethod
    def minimize(
        self,
        window: str,
    ) -> bool:
        """
        Minimize a window.
        """

        pass

    # ---------------------------------------------------------
    # Maximize
    # ---------------------------------------------------------

    @abstractmethod
    def maximize(
        self,
        window: str,
    ) -> bool:
        """
        Maximize a window.
        """

        pass

    # ---------------------------------------------------------
    # Restore
    # ---------------------------------------------------------

    @abstractmethod
    def restore(
        self,
        window: str,
    ) -> bool:
        """
        Restore a window.
        """

        pass

    # ---------------------------------------------------------
    # Active Window
    # ---------------------------------------------------------

    @abstractmethod
    def active_window(
        self,
    ) -> dict:
        """
        Return active window information.
        """

        pass

    # ---------------------------------------------------------
    # List Windows
    # ---------------------------------------------------------

    @abstractmethod
    def list_windows(
        self,
    ) -> list:
        """
        Return available windows.
        """

        pass
