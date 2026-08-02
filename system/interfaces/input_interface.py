"""
Omnix V5
Input Interface

Defines keyboard and mouse operation contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class InputInterface(ABC):
    """
    Interface for input operations.
    """

    # ---------------------------------------------------------
    # Mouse Movement
    # ---------------------------------------------------------

    @abstractmethod
    def move_mouse(
        self,
        x: int,
        y: int,
    ) -> bool:
        """
        Move cursor to position.
        """

        pass

    # ---------------------------------------------------------
    # Click
    # ---------------------------------------------------------

    @abstractmethod
    def click(
        self,
        button: str = "left",
    ) -> bool:
        """
        Click mouse button.
        """

        pass

    # ---------------------------------------------------------
    # Double Click
    # ---------------------------------------------------------

    @abstractmethod
    def double_click(
        self,
        button: str = "left",
    ) -> bool:
        """
        Double click.
        """

        pass

    # ---------------------------------------------------------
    # Keyboard Typing
    # ---------------------------------------------------------

    @abstractmethod
    def type_text(
        self,
        text: str,
    ) -> bool:
        """
        Type text.
        """

        pass

    # ---------------------------------------------------------
    # Key Press
    # ---------------------------------------------------------

    @abstractmethod
    def press_key(
        self,
        key: str,
    ) -> bool:
        """
        Press keyboard key.
        """

        pass

    # ---------------------------------------------------------
    # Hotkey
    # ---------------------------------------------------------

    @abstractmethod
    def hotkey(
        self,
        *keys: str,
    ) -> bool:
        """
        Execute keyboard shortcut.
        """

        pass
