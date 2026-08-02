"""
Omnix V5 - Bounding Box Model

Standard bounding box representation used throughout the Vision Engine.
All coordinates are stored in pixel space, while normalized coordinates
are computed dynamically.

Author: Omnix V5
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(slots=True)
class BoundingBox:
    """
    Represents a rectangular region on the screen.

    Coordinates:
        x1,y1 -------- x2,y1
          |              |
          |              |
        x1,y2 -------- x2,y2
    """

    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return max(0.0, self.x2 - self.x1)

    @property
    def height(self) -> float:
        return max(0.0, self.y2 - self.y1)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center_x(self) -> float:
        return self.x1 + self.width / 2

    @property
    def center_y(self) -> float:
        return self.y1 + self.height / 2

    @property
    def center(self):
        return (self.center_x, self.center_y)

    @property
    def aspect_ratio(self) -> float:
        if self.height == 0:
            return 0.0
        return self.width / self.height

    def to_xyxy(self) -> list[float]:
        return [self.x1, self.y1, self.x2, self.y2]

    def to_xywh(self) -> tuple[float, float, float, float]:
        return self.x1, self.y1, self.width, self.height

    def contains(self, x: float, y: float) -> bool:
        return (
            self.x1 <= x <= self.x2
            and
            self.y1 <= y <= self.y2
        )

    def contains_box(self, other: "BoundingBox") -> bool:
        return (
            other.x1 >= self.x1
            and other.y1 >= self.y1
            and other.x2 <= self.x2
            and other.y2 <= self.y2
        )

    def intersects(self, other: "BoundingBox") -> bool:
        return not (
            self.x2 < other.x1
            or self.x1 > other.x2
            or self.y2 < other.y1
            or self.y1 > other.y2
        )

    def intersection_area(self, other: "BoundingBox") -> float:

        if not self.intersects(other):
            return 0.0

        x_left = max(self.x1, other.x1)
        y_top = max(self.y1, other.y1)
        x_right = min(self.x2, other.x2)
        y_bottom = min(self.y2, other.y2)

        return max(0.0, x_right - x_left) * max(
            0.0,
            y_bottom - y_top,
        )

    def iou(self, other: "BoundingBox") -> float:
        """
        Intersection over Union.
        """

        intersection = self.intersection_area(other)

        union = self.area + other.area - intersection

        if union == 0:
            return 0.0

        return intersection / union

    def distance_to(self, other: "BoundingBox") -> float:
        dx = self.center_x - other.center_x
        dy = self.center_y - other.center_y
        return sqrt(dx * dx + dy * dy)

    def normalized(
        self,
        frame_width: int,
        frame_height: int,
    ) -> tuple[float, float, float, float]:

        return (
            self.x1 / frame_width,
            self.y1 / frame_height,
            self.x2 / frame_width,
            self.y2 / frame_height,
        )

    def center_normalized(
        self,
        frame_width: int,
        frame_height: int,
    ) -> tuple[float, float]:

        return (
            self.center_x / frame_width,
            self.center_y / frame_height,
        )