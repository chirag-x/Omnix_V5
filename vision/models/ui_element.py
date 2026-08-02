"""
Omnix V5 - UI Element

Represents an interpreted UI component built from one or more VisionObjects.

Unlike VisionObject, this class describes the meaning of an interface element
rather than a raw detection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from vision.models.bounding_box import BoundingBox


@dataclass(slots=True)
class UIElement:
    """
    High-level UI component.

    Examples:
        Search Bar
        Toolbar
        Dialog
        Menu
        Sidebar
        Login Button
        File Explorer
        Video Player
    """

    # -------------------------------------------------------
    # Identity
    # -------------------------------------------------------

    id: str = field(default_factory=lambda: uuid4().hex)

    name: str = ""

    element_type: str = ""

    role: str = ""

    app: str = ""

    confidence: float = 1.0

    # -------------------------------------------------------
    # Geometry
    # -------------------------------------------------------

    bbox: BoundingBox | None = None

    screen_region: str = ""

    # -------------------------------------------------------
    # Hierarchy
    # -------------------------------------------------------

    parent_id: str | None = None

    children: list[str] = field(default_factory=list)

    # -------------------------------------------------------
    # Detection Sources
    # -------------------------------------------------------

    object_ids: list[str] = field(default_factory=list)

    text: str = ""

    # -------------------------------------------------------
    # State
    # -------------------------------------------------------

    visible: bool = True

    enabled: bool = True

    focused: bool = False

    selected: bool = False

    hovered: bool = False

    clickable: bool = False

    editable: bool = False

    scrollable: bool = False

    expanded: bool = False

    # -------------------------------------------------------
    # Semantic Information
    # -------------------------------------------------------

    attributes: dict[str, Any] = field(default_factory=dict)

    tags: list[str] = field(default_factory=list)

    # -------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------

    def add_child(self, child_id: str) -> None:
        if child_id not in self.children:
            self.children.append(child_id)

    def add_object(self, object_id: str) -> None:
        if object_id not in self.object_ids:
            self.object_ids.append(object_id)

    def add_tag(self, tag: str) -> None:
        if tag not in self.tags:
            self.tags.append(tag)

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def get_attribute(self, key: str, default: Any = None) -> Any:
        return self.attributes.get(key, default)

    @property
    def center(self) -> tuple[float, float]:
        if self.bbox is None:
            return (0.0, 0.0)

        return (
            self.bbox.center_x,
            self.bbox.center_y,
        )

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

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.element_type,
            "role": self.role,
            "app": self.app,
            "confidence": self.confidence,
            "bbox": (
                self.bbox.to_xyxy()
                if self.bbox
                else None
            ),
            "screen_region": self.screen_region,
            "text": self.text,
            "visible": self.visible,
            "enabled": self.enabled,
            "focused": self.focused,
            "selected": self.selected,
            "hovered": self.hovered,
            "clickable": self.clickable,
            "editable": self.editable,
            "scrollable": self.scrollable,
            "expanded": self.expanded,
            "parent_id": self.parent_id,
            "children": self.children,
            "object_ids": self.object_ids,
            "attributes": self.attributes,
            "tags": self.tags,
        }

    def __repr__(self) -> str:
        return (
            f"UIElement("
            f"name='{self.name}', "
            f"type='{self.element_type}', "
            f"app='{self.app}')"
        )