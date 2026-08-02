"""
Omnix V5
UI Element Model

Represents a UI element detected using Windows UI Automation,
Vision OCR, YOLO, or any future detection backend.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .geometry_model import GeometryModel


@dataclass(
    slots=True,
    kw_only=True,
)
class UIElement(GeometryModel):
    """
    Represents an interactable UI element.
    """

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    text: str | None = None

    control_type: str | None = None

    automation_id: str | None = None

    class_name: str | None = None

    # ---------------------------------------------------------
    # Geometry
    # ---------------------------------------------------------

    left: int = 0
    top: int = 0

    width: int = 0
    height: int = 0

    # ---------------------------------------------------------
    # Detection
    # ---------------------------------------------------------

    confidence: float = 1.0

    source: str = "uia"
    # uia
    # vision
    # ocr
    # yolo
    # template
    # accessibility

    # ---------------------------------------------------------
    # State
    # ---------------------------------------------------------

    visible: bool = True

    enabled: bool = True

    focused: bool = False

    selected: bool = False

    checked: bool | None = None

    expanded: bool | None = None

    clickable: bool = True

    editable: bool = False

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------

    parent_id: str | None = None

    window_handle: int | None = None

    monitor_index: int | None = None

    # ---------------------------------------------------------
    # OCR
    # ---------------------------------------------------------

    detected_text: str | None = None

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
    def rectangle(self) -> tuple[int, int, int, int]:
        return (
            self.left,
            self.top,
            self.right,
            self.bottom,
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
        Returns True if the point lies inside the element.
        """

        return (
            self.left <= x <= self.right
            and
            self.top <= y <= self.bottom
        )

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

    @property
    def is_interactable(self) -> bool:
        """
        Returns True if Omnix can interact with this element.
        """

        return (
            self.visible
            and self.enabled
            and self.clickable
        )

    def __str__(self) -> str:

        label = self.text or self.detected_text or "Unnamed"

        return (
            f"{self.control_type} "
            f"('{label}')"
        )