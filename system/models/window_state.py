"""
Omnix V5
Window Runtime State Model

Stores the current runtime state of a window.

Unlike Window, this object changes frequently while
Omnix is running.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .geometry_model import GeometryModel


@dataclass(
    slots=True,
    kw_only=True,
)
class WindowState(GeometryModel):
    """
    Represents the live state of a desktop window.
    """

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    handle: int

    # ---------------------------------------------------------
    # State
    # ---------------------------------------------------------

    exists: bool = True
    visible: bool = True
    enabled: bool = True

    focused: bool = False

    minimized: bool = False
    maximized: bool = False

    always_on_top: bool = False

    responding: bool = True

    # ---------------------------------------------------------
    # Geometry
    # ---------------------------------------------------------

    left: int = 0
    top: int = 0

    width: int = 0
    height: int = 0

    # ---------------------------------------------------------
    # Runtime
    # ---------------------------------------------------------

    monitor_id: int | None = None

    z_order: int = 0

    opacity: float = 1.0

    last_active: datetime | None = None

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    @property
    def center(self) -> tuple[int, int]:
        return (
            self.left + self.width // 2,
            self.top + self.height // 2,
        )

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def rectangle(self) -> tuple[int, int, int, int]:
        return (
            self.left,
            self.top,
            self.right,
            self.bottom,
        )

    @property
    def is_interactable(self) -> bool:
        """
        Returns True if Omnix can safely interact with
        this window.
        """

        return (
            self.exists
            and self.visible
            and self.enabled
            and self.responding
            and not self.minimized
        )

    # ---------------------------------------------------------
    # State Updates
    # ---------------------------------------------------------

    def activate(self) -> None:
        self.focused = True
        self.last_active = datetime.now()

    def deactivate(self) -> None:
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

    def move(
        self,
        left: int,
        top: int,
    ) -> None:
        self.left = left
        self.top = top

    def resize(
        self,
        width: int,
        height: int,
    ) -> None:
        self.width = width
        self.height = height

    def update_geometry(
        self,
        left: int,
        top: int,
        width: int,
        height: int,
    ) -> None:
        self.left = left
        self.top = top
        self.width = width
        self.height = height

    def close(self) -> None:
        self.exists = False
        self.focused = False
        self.responding = False

    def __str__(self) -> str:

        if not self.exists:
            return "Closed"

        if self.focused:
            state = "Focused"

        elif self.minimized:
            state = "Minimized"

        elif self.maximized:
            state = "Maximized"

        else:
            state = "Normal"

        return (
            f"{state} "
            f"({self.width}x{self.height})"
        )