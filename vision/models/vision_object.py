"""
Omnix V5 - Vision Object

Standard object representation used throughout the Vision Engine.

Every detector (YOLO, OCR, UI Detector, etc.) should ultimately produce
VisionObject instances.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from vision.models.bounding_box import BoundingBox


@dataclass(slots=True)
class VisionObject:
    """
    Represents one detected object on the screen.
    """

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    id: str = field(default_factory=lambda: uuid4().hex)

    label: str = ""

    category: str = "object"

    confidence: float = 0.0

    # ------------------------------------------------------------------
    # Geometry
    # ------------------------------------------------------------------

    bbox: BoundingBox | None = None

    # ------------------------------------------------------------------
    # Source
    # ------------------------------------------------------------------

    source: str = "yolo"
    model: str = "yolo11n"

    # ------------------------------------------------------------------
    # Tracking
    # ------------------------------------------------------------------

    track_id: int | None = None

    frame_id: int = 0

    timestamp: float = 0.0

    # ------------------------------------------------------------------
    # Screen Information
    # ------------------------------------------------------------------

    screen_region: str = ""

    parent_id: str | None = None

    children: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Semantic Information
    # ------------------------------------------------------------------

    attributes: dict[str, Any] = field(default_factory=dict)

    tags: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Utility Properties
    # ------------------------------------------------------------------

    @property
    def width(self) -> float:
        if self.bbox is None:
            return 0.0
        return self.bbox.width

    @property
    def height(self) -> float:
        if self.bbox is None:
            return 0.0
        return self.bbox.height

    @property
    def area(self) -> float:
        if self.bbox is None:
            return 0.0
        return self.bbox.area

    @property
    def center(self) -> tuple[float, float]:
        if self.bbox is None:
            return (0.0, 0.0)

        return (
            self.bbox.center_x,
            self.bbox.center_y,
        )

    @property
    def aspect_ratio(self) -> float:
        if self.bbox is None:
            return 0.0
        return self.bbox.aspect_ratio

    @property
    def text(self):

        return self.get_attribute(
            "raw_text",
            self.label,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def add_tag(self, tag: str) -> None:
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        if tag in self.tags:
            self.tags.remove(tag)

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def get_attribute(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self.attributes.get(key, default)

    def add_child(self, child_id: str) -> None:
        if child_id not in self.children:
            self.children.append(child_id)

    def to_dict(self) -> dict:
        """
        Serialize object for memory or API usage.
        """

        return {
            "id": self.id,
            "label": self.label,
            "category": self.category,
            "confidence": self.confidence,
            "bbox": (self.bbox.to_xyxy() if self.bbox else None),
            "source": self.source,
            "model": self.model,
            "track_id": self.track_id,
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "screen_region": self.screen_region,
            "parent_id": self.parent_id,
            "children": self.children,
            "attributes": self.attributes,
            "tags": self.tags,
        }

    def __repr__(self) -> str:
        return (
            f"VisionObject("
            f"label='{self.label}', "
            f"confidence={self.confidence:.2f}, "
            f"region='{self.screen_region}')"
        )
