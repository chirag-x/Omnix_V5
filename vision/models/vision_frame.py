"""
Omnix V5 - Vision Frame

Represents one complete understanding of the current screen.

This object is the ONLY vision object passed to:
- Planner
- Memory
- Automation
- AI Brain
- Skills
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vision.models.ui_element import UIElement
from vision.models.ui_tree import UITree
from vision.models.vision_object import VisionObject
from vision.summary.screen_state import ScreenState


@dataclass(slots=True)
class VisionFrame:

    # =====================================================
    # Frame Metadata
    # =====================================================

    frame_id: int = 0
    timestamp: float = 0.0

    frame_width: int = 0
    frame_height: int = 0

    # =====================================================
    # Context
    # =====================================================

    active_window: str = ""
    active_app: str = ""

    # =====================================================
    # Raw Detection Data
    # =====================================================

    objects: list[VisionObject] = field(default_factory=list)

    texts: list[VisionObject] = field(default_factory=list)

    # =====================================================
    # Structured UI
    # =====================================================

    ui_tree: UITree = field(default_factory=UITree)

    ui_elements: list[UIElement] = field(default_factory=list)

    # =====================================================
    # Relationships
    # =====================================================

    relationships: list[Any] = field(default_factory=list)

    # =====================================================
    # Semantic Understanding
    # =====================================================

    screen_state: ScreenState | None = None

    summary: str = ""

    focused_element: str | None = None

    # =====================================================
    # Performance
    # =====================================================

    timings: dict[str, float] = field(default_factory=dict)

    # =====================================================
    # Metadata
    # =====================================================

    metadata: dict[str, Any] = field(default_factory=dict)

    # =====================================================
    # Add Helpers
    # =====================================================

    def add_object(self, obj: VisionObject):

        self.objects.append(obj)

    def add_text(self, text: VisionObject):

        self.texts.append(text)

    def add_ui_element(self, element: UIElement):

        self.ui_elements.append(element)

    def add_relationship(self, relation):

        self.relationships.append(relation)

    # =====================================================
    # Timing
    # =====================================================

    def set_timing(
        self,
        stage: str,
        milliseconds: float,
    ):

        self.timings[stage] = milliseconds

    def get_timing(
        self,
        stage: str,
    ) -> float:

        return self.timings.get(stage, 0.0)

    # =====================================================
    # Query Helpers
    # =====================================================

    def get_object(
        self,
        object_id: str,
    ) -> VisionObject | None:

        for obj in self.objects:

            if obj.id == object_id:
                return obj

        return None

    def get_element(
        self,
        element_id: str,
    ) -> UIElement | None:

        return self.ui_tree.get(element_id)

    def find_element(
        self,
        name: str,
    ) -> UIElement | None:

        return self.ui_tree.find(name)

    # =====================================================
    # Statistics
    # =====================================================

    @property
    def object_count(self):

        return len(self.objects)

    @property
    def text_count(self):

        return len(self.texts)

    @property
    def ui_count(self):

        return len(self.ui_tree)

    @property
    def total_elements(self):

        return self.object_count + self.text_count + self.ui_count

    # =====================================================
    # Export
    # =====================================================

    def to_dict(self):

        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "frame_size": {
                "width": self.frame_width,
                "height": self.frame_height,
            },
            "active_window": self.active_window,
            "active_app": self.active_app,
            "summary": self.summary,
            "screen_state": (self.screen_state.summary if self.screen_state else ""),
            "focused_element": self.focused_element,
            "objects": [obj.to_dict() for obj in self.objects],
            "texts": [obj.to_dict() for obj in self.texts],
            "ui_tree": self.ui_tree.to_dict(),
            "relationships": self.relationships,
            "timings": self.timings,
            "metadata": self.metadata,
        }

    # =====================================================

    def clear(self):

        self.objects.clear()

        self.texts.clear()

        self.ui_elements.clear()

        self.relationships.clear()

        self.ui_tree = UITree()

        self.summary = ""

        self.screen_state = None

        self.timings.clear()

        self.metadata.clear()

    # =====================================================

    def __repr__(self):

        return (
            f"VisionFrame("
            f"id={self.frame_id}, "
            f"objects={self.object_count}, "
            f"texts={self.text_count}, "
            f"ui={self.ui_count}, "
            f"app='{self.active_app}')"
        )
