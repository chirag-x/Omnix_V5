"""
Omnix V5 - Screen State

Creates a high-level representation of the current screen.

This module converts raw detections and UI hierarchy into a
compact state object that the planner, memory and LLM can
reason about.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from vision.models.ui_tree import UITree
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vision.models.vision_frame import VisionFrame


@dataclass(slots=True)
class ScreenState:

    # Window information
    active_app: str = ""
    active_window: str = ""

    # UI overview
    focused_element: str | None = None

    visible_elements: int = 0

    clickable_elements: int = 0

    editable_elements: int = 0

    text_elements: int = 0

    # Screen status
    has_dialog: bool = False

    has_popup: bool = False

    has_notification: bool = False

    loading: bool = False

    error: bool = False

    # Human-readable summary
    summary: str = ""

    metadata: dict = field(default_factory=dict)


class ScreenStateBuilder:

    def build(
        self,
        frame: VisionFrame,
        tree: UITree,
    ) -> ScreenState:

        state = ScreenState()

        state.active_app = frame.active_app
        state.active_window = frame.active_window

        state.visible_elements = len(tree.elements)

        # ----------------------------------------------------
        # Count element types
        # ----------------------------------------------------

        for element in tree.elements:

            if element.clickable:
                state.clickable_elements += 1

            if element.editable:
                state.editable_elements += 1

            if element.text:
                state.text_elements += 1

            if element.focused:
                state.focused_element = element.name

            label = element.element_type.lower()

            if "dialog" in label:
                state.has_dialog = True

            if "popup" in label:
                state.has_popup = True

            if "notification" in label:
                state.has_notification = True

            if "spinner" in label:
                state.loading = True

            if "error" in label:
                state.error = True

        # ----------------------------------------------------
        # Human Summary
        # ----------------------------------------------------

        state.summary = self._build_summary(state)

        return state

    # --------------------------------------------------------

    def _build_summary(
        self,
        state: ScreenState,
    ) -> str:

        parts = []

        if state.active_app:
            parts.append(f"Application: {state.active_app}")

        if state.active_window:
            parts.append(f"Window: {state.active_window}")

        parts.append(f"{state.visible_elements} UI elements detected")

        if state.focused_element:
            parts.append(f"Focused: {state.focused_element}")

        if state.has_dialog:
            parts.append("Dialog open")

        if state.has_popup:
            parts.append("Popup visible")

        if state.loading:
            parts.append("Loading")

        if state.error:
            parts.append("Error detected")

        return " | ".join(parts)
