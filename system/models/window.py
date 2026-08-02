"""
Omnix V5
Window Model

Represents a desktop application window.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .geometry_model import GeometryModel


@dataclass(
    slots=True,
    kw_only=True,
)
class Window(GeometryModel):
    """
    Represents a desktop window.

    Every visible application window should be represented
    by this model.
    """

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    handle: int
    title: str
    thread_id: int | None = None
    executable: str | None = None
    desktop_name: str | None = None
    owner: str | None = None
    created_at: datetime | None = None
    # ---------------------------------------------------------
    # Process
    # ---------------------------------------------------------

    process_id: int | None = None
    process_name: str | None = None

    application: str | None = None

    # ---------------------------------------------------------
    # Position
    # ---------------------------------------------------------

    left: int = 0
    top: int = 0

    width: int = 0
    height: int = 0

    # ---------------------------------------------------------
    # Window State
    # ---------------------------------------------------------

    visible: bool = True
    enabled: bool = True

    minimized: bool = False
    maximized: bool = False

    focused: bool = False

    always_on_top: bool = False

    # ---------------------------------------------------------
    # Monitor
    # ---------------------------------------------------------

    monitor_id: int | None = None

    # ---------------------------------------------------------
    # Misc
    # ---------------------------------------------------------

    class_name: str | None = None

    # ---------------------------------------------------------
    # Geometry
    # ---------------------------------------------------------

    @property
    def right(self) -> int:
        """
        Right edge.
        """
        return self.left + self.width

    @property
    def bottom(self) -> int:
        """
        Bottom edge.
        """
        return self.top + self.height

    @property
    def center(self) -> tuple[int, int]:
        """
        Center point.
        """
        return (
            self.left + self.width // 2,
            self.top + self.height // 2,
        )

    @property
    def area(self) -> int:
        """
        Window area.
        """
        return self.width * self.height

    @property
    def rectangle(self) -> tuple[int, int, int, int]:
        """
        Returns:

        (left, top, right, bottom)
        """

        return (
            self.left,
            self.top,
            self.right,
            self.bottom,
        )

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def contains(self, x: int, y: int) -> bool:
        """
        Returns True if point is inside window.
        """

        return (
            self.left <= x <= self.right
            and
            self.top <= y <= self.bottom
        )

    def move(self, left: int, top: int) -> None:
        """
        Updates window position.
        """

        self.left = left
        self.top = top

    def resize(
        self,
        width: int,
        height: int,
    ) -> None:
        """
        Updates window size.
        """

        self.width = width
        self.height = height

    def update_geometry(
        self,
        left: int,
        top: int,
        width: int,
        height: int,
    ) -> None:
        """
        Updates complete geometry.
        """

        self.left = left
        self.top = top
        self.width = width
        self.height = height

    # ---------------------------------------------------------
    # Window State
    # ---------------------------------------------------------

    def focus(self) -> None:
        self.focused = True

    def unfocus(self) -> None:
        self.focused = False

    def minimize(self) -> None:
        self.minimized = True
        self.maximized = False

    def maximize(self) -> None:
        self.maximized = True
        self.minimized = False

    def restore(self) -> None:
        self.minimized = False
        self.maximized = False

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    @property
    def is_normal(self) -> bool:
        """
        True if neither minimized nor maximized.
        """

        return (
            not self.minimized
            and
            not self.maximized
        )

    @property
    def is_interactable(self) -> bool:
        """
        True if Omnix can interact with this window.
        """

        return (
            self.visible
            and
            self.enabled
            and
            not self.minimized
        )

    def __str__(self) -> str:

        return (
            f"{self.title} "
            f"({self.width}x{self.height})"
        )