"""
Omnix V5 - Detection Fuser

Fuses object detections (YOLO) with OCR detections to create
semantically richer VisionObjects.

Example:
    TextBox + "Search..." text
        ↓
    Search Box
"""

from __future__ import annotations

from vision.models.vision_object import VisionObject


class DetectionFuser:

    def __init__(
        self,
        overlap_threshold: float = 0.30,
    ):
        self.overlap_threshold = overlap_threshold

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------

    def fuse(
        self,
        objects: list[VisionObject],
        texts: list[VisionObject],
    ) -> tuple[list[VisionObject], list[VisionObject]]:
        """
        Returns:
            fused_objects,
            remaining_texts
        """

        remaining_texts = texts.copy()

        for obj in objects:

            if obj.bbox is None:
                continue

            attached_text = []

            for text in remaining_texts[:]:

                if text.bbox is None:
                    continue

                iou = obj.bbox.iou(text.bbox)

                inside = obj.bbox.contains_box(text.bbox) or text.bbox.contains_box(
                    obj.bbox
                )

                if inside or iou >= self.overlap_threshold:

                    if text.label:
                        attached_text.append(text.label)

                    obj.set_attribute(
                        "is_fused",
                        True,
                    )

                    obj.add_tag("text")

                    obj.set_attribute(
                        "text",
                        text.label,
                    )

                    remaining_texts.remove(text)

            if attached_text:

                obj.set_attribute(
                    "all_text",
                    tuple(attached_text),
                )

                obj.set_attribute(
                    "raw_text",
                    text.label,
                )

                obj.set_attribute(
                    "display_text",
                    " ".join(attached_text),
                )

                self._semantic_upgrade(obj)

        return objects, remaining_texts

    # ----------------------------------------------------------
    # Semantic Upgrade
    # ----------------------------------------------------------

    def _semantic_upgrade(
        self,
        obj: VisionObject,
    ) -> None:

        text = (
            obj.get_attribute(
                "display_text",
                "",
            )
            .lower()
            .strip()
        )

        label = obj.label.lower()

        # ----------------------------------------
        # TextBox
        # ----------------------------------------

        if label in {
            "textbox",
            "input",
            "text field",
        }:

            obj.category = "input"

            if "search" in text:

                obj.label = "search_box"

                obj.add_tag("search")

                obj.add_tag("editable")

        # ----------------------------------------
        # Button
        # ----------------------------------------

        elif label == "button":

            obj.category = "button"

            if text:

                obj.label = f"{text}_button"

                obj.add_tag("clickable")

        # ----------------------------------------
        # Menu
        # ----------------------------------------

        elif label == "menu":

            obj.category = "navigation"

        # ----------------------------------------
        # Image
        # ----------------------------------------

        elif label in {
            "image",
            "picture",
        }:

            obj.category = "media"
