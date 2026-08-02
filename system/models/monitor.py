"""
Omnix V5
Monitor Model

Represents a physical display connected to the system.
"""

from __future__ import annotations

from dataclasses import dataclass

from .geometry_model import GeometryModel

@dataclass(
    slots=True,
    kw_only=True,
)
class Monitor(GeometryModel):
    """
    Represents a display monitor.
    """

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    id: int

    name: str

    # ---------------------------------------------------------
    # Geometry
    # ---------------------------------------------------------

    left: int

    top: int

    width: int

    height: int

    # ---------------------------------------------------------
    # Display
    # ---------------------------------------------------------

    primary: bool = False

    dpi_scale: float = 1.0

    refresh_rate: float = 60.0

    orientation: str = "landscape"

    # ---------------------------------------------------------
    # Work Area
    # ---------------------------------------------------------

    work_left: int = 0
    work_top: int = 0
    work_width: int = 0
    work_height: int = 0

    # ---------------------------------------------------------
    # State
    # ---------------------------------------------------------

    connected: bool = True

    enabled: bool = True

    # ---------------------------------------------------------
    # Geometry Helpers
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
    def resolution(self) -> tuple[int, int]:
        return (
            self.width,
            self.height,
        )

    @property
    def work_area(self) -> tuple[int, int, int, int]:
        """
        Returns:

        (left, top, width, height)
        """

        return (
            self.work_left,
            self.work_top,
            self.work_width,
            self.work_height,
        )

    @property
    def area(self) -> int:
        return self.width * self.height

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def contains(
        self,
        x: int,
        y: int,
    ) -> bool:
        """
        Returns True if the coordinate belongs to
        this monitor.
        """

        return (
            self.left <= x <= self.right
            and self.top <= y <= self.bottom
        )

    def contains_window(self, window) -> bool:
        """
        Returns True if most of the supplied
        window lies on this monitor.
        """

        return self.contains(
            window.center[0],
            window.center[1],
        )

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

    def update_work_area(
        self,
        left: int,
        top: int,
        width: int,
        height: int,
    ) -> None:

        self.work_left = left
        self.work_top = top
        self.work_width = width
        self.work_height = height

    @property
    def is_available(self) -> bool:
        """
        Returns True if the monitor can currently
        be used.
        """

        return (
            self.connected
            and self.enabled
        )

    def __str__(self) -> str:

        role = "Primary" if self.primary else "Secondary"

        return (
            f"{self.name} "
            f"({self.width}x{self.height}, {role})"
        )