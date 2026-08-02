"""
Omnix V5
UI Interface

Defines UI interaction contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class UIInterface(ABC):
    """
    Interface for UI operations.
    """

    # ---------------------------------------------------------
    # Find Element
    # ---------------------------------------------------------

    @abstractmethod
    def find(
        self,
        element: str,
    ) -> dict | None:
        """
        Find UI element.
        """

        pass

    # ---------------------------------------------------------
    # Check Exists
    # ---------------------------------------------------------

    @abstractmethod
    def exists(
        self,
        element: str,
    ) -> bool:
        """
        Check if UI element exists.
        """

        pass

    # ---------------------------------------------------------
    # Click
    # ---------------------------------------------------------

    @abstractmethod
    def click(
        self,
        element: str,
    ) -> bool:
        """
        Click UI element.
        """

        pass

    # ---------------------------------------------------------
    # Type
    # ---------------------------------------------------------

    @abstractmethod
    def type_text(
        self,
        text: str,
    ) -> bool:
        """
        Type text into UI.
        """

        pass

    # ---------------------------------------------------------
    # Wait
    # ---------------------------------------------------------

    @abstractmethod
    def wait_for(
        self,
        element: str,
        timeout: float = 5.0,
    ) -> bool:
        """
        Wait for UI element.
        """

        pass

    # ---------------------------------------------------------
    # Snapshot
    # ---------------------------------------------------------

    @abstractmethod
    def snapshot(
        self,
    ) -> dict:
        """
        Return current UI state.
        """

        pass
