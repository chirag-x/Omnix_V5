"""
Omnix V5 - Semantic Summary

Generates a concise, human-readable summary of the current
screen using structured vision data.
"""

from __future__ import annotations

from vision.summary.screen_state import ScreenState
from vision.models.ui_tree import UITree


class SemanticSummaryBuilder:

    def build(
        self,
        state: ScreenState,
        tree: UITree,
    ) -> str:

        lines: list[str] = []

        # --------------------------------------------------
        # Application
        # --------------------------------------------------

        if state.active_app:
            lines.append(
                f"Active application: {state.active_app}."
            )

        if state.active_window:
            lines.append(
                f"Current window: {state.active_window}."
            )

        # --------------------------------------------------
        # Focus
        # --------------------------------------------------

        if state.focused_element:
            lines.append(
                f"Focused element: {state.focused_element}."
            )

        # --------------------------------------------------
        # Counts
        # --------------------------------------------------

        lines.append(
            f"{state.visible_elements} UI elements are visible."
        )

        if state.clickable_elements:
            lines.append(
                f"{state.clickable_elements} clickable elements detected."
            )

        if state.editable_elements:
            lines.append(
                f"{state.editable_elements} editable fields detected."
            )

        # --------------------------------------------------
        # Important UI
        # --------------------------------------------------

        important = self._important_elements(tree)

        if important:
            lines.append(
                "Important elements: "
                + ", ".join(important)
                + "."
            )

        # --------------------------------------------------
        # Status
        # --------------------------------------------------

        status = []

        if state.has_dialog:
            status.append("dialog open")

        if state.has_popup:
            status.append("popup visible")

        if state.loading:
            status.append("loading")

        if state.error:
            status.append("error detected")

        if status:
            lines.append(
                "Screen status: "
                + ", ".join(status)
                + "."
            )
        else:
            lines.append(
                "Screen appears ready for interaction."
            )

        return " ".join(lines)

    # --------------------------------------------------

    def _important_elements(
        self,
        tree: UITree,
    ) -> list[str]:

        important = []

        priority = {

            "search_box",

            "address_bar",

            "login_button",

            "send_button",

            "message_input",

            "password_field",

            "username_field",

            "terminal",

            "editor",

            "file_tree",

            "menu",

        }

        for element in tree.elements:

            label = element.element_type.lower()

            if label in priority:

                important.append(
                    element.name
                )

        return important[:10]