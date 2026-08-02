"""
Omnix V5
Geometry Model

Provides common geometry functionality for all
screen-based models.
"""

from __future__ import annotations

from dataclasses import dataclass

from .base_model import BaseModel


@dataclass(
    slots=True,
    kw_only=True,
)
class GeometryModel(BaseModel):
    """
    Base class for any object that occupies
    a rectangular area on the screen.
    """

    # ---------------------------------------------------------
    # Position
    # ---------------------------------------------------------

    left: int = 0
    top: int = 0

    # ---------------------------------------------------------
    # Size
    # ---------------------------------------------------------

    width: int = 0
    height: int = 0

    # ---------------------------------------------------------
    # Geometry Properties
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

    @property
    def bounds(self) -> tuple[int, int, int, int]:
        """
        Returns:
            (left, top, width, height)
        """
        return (
            self.left,
            self.top,
            self.width,
            self.height,
        )

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def aspect_ratio(self) -> float:
        if self.height == 0:
            return 0.0

        return self.width / self.height

    @property
    def is_empty(self) -> bool:
        return self.width <= 0 or self.height <= 0

    # ---------------------------------------------------------
    # Geometry Helpers
    # ---------------------------------------------------------

    def contains(
        self,
        x: int,
        y: int,
    ) -> bool:
        """
        Returns True if the point lies inside
        this rectangle.
        """

        return self.left <= x <= self.right and self.top <= y <= self.bottom

    def intersects(
        self,
        other: "GeometryModel",
    ) -> bool:
        """
        Returns True if this rectangle intersects
        another geometry object.
        """

        return not (
            self.right < other.left
            or self.left > other.right
            or self.bottom < other.top
            or self.top > other.bottom
        )

    def distance_to(
        self,
        other: "GeometryModel",
    ) -> float:
        """
        Distance between center points.
        """

        x1, y1 = self.center
        x2, y2 = other.center

        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    # ---------------------------------------------------------
    # Updates
    # ---------------------------------------------------------

    def move(
        self,
        left: int,
        top: int,
    ) -> None:

        self.left = left
        self.top = top
        self.touch()

    def resize(
        self,
        width: int,
        height: int,
    ) -> None:

        self.width = width
        self.height = height
        self.touch()

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

        self.touch()

    # ---------------------------------------------------------
    # Representation
    # ---------------------------------------------------------

    def __str__(self) -> str:
        return f"{self.width}x{self.height} " f"@ ({self.left}, {self.top})"
