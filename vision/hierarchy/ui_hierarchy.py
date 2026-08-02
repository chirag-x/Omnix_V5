"""
Omnix V5 - UI Hierarchy Builder

Builds a structured UITree from VisionObjects.

Responsibilities
----------------
- Build parent/child hierarchy
- Convert VisionObjects → UIElements
- Create lookup tables
- Return UITree
"""

from __future__ import annotations

from vision.models.ui_element import UIElement
from vision.models.ui_tree import UITree
from vision.models.vision_object import VisionObject


class UIHierarchyBuilder:

    def build(
        self,
        objects: list[VisionObject],
    ) -> UITree:

        if not objects:
            return UITree()

        # Largest objects become parents first
        ordered = sorted(
            objects,
            key=lambda obj: obj.area,
            reverse=True,
        )

        # ---------------------------------------------
        # Build Parent → Child relationships
        # ---------------------------------------------

        for parent in ordered:

            if parent.bbox is None:
                continue

            for child in ordered:

                if parent.id == child.id:
                    continue

                if child.bbox is None:
                    continue

                if parent.bbox.contains_box(child.bbox):

                    child.parent_id = parent.id

                    parent.add_child(child.id)

        # ---------------------------------------------
        # Convert to UI Elements
        # ---------------------------------------------

        elements = []

        for obj in ordered:

            ui = UIElement(
                name=self._display_name(obj),
                element_type=obj.label,
                role=obj.category,
                confidence=obj.confidence,
                bbox=obj.bbox,
                screen_region=obj.screen_region,
                parent_id=obj.parent_id,
                children=obj.children.copy(),
                object_ids=[obj.id],
                text=obj.get_attribute("display_text", ""),
                attributes=obj.attributes.copy(),
                tags=obj.tags.copy(),
            )

            elements.append(ui)

        # ---------------------------------------------
        # Build UITree
        # ---------------------------------------------

        tree = UITree.from_elements(elements)

        return tree

    # ------------------------------------------------

    def _display_name(
        self,
        obj: VisionObject,
    ) -> str:

        text = obj.get_attribute(
            "display_text",
            "",
        )

        if text:
            return text

        return obj.label.replace(
            "_",
            " ",
        ).title()
