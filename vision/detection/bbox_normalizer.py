"""
Omnix V5 - Bounding Box Normalizer

Converts raw detector outputs into standardized VisionObjects.

This module ensures every detector (YOLO, OCR, future detectors)
produces objects in exactly the same format.
"""

from __future__ import annotations

from vision.models.bounding_box import BoundingBox
from vision.models.vision_object import VisionObject


class BoundingBoxNormalizer:
    """
    Converts raw detections into VisionObjects.

    Responsibilities
    ----------------
    - Standardize coordinates
    - Create BoundingBox objects
    - Calculate screen region
    - Attach metadata
    """

    def __init__(self):
        pass

    # -----------------------------------------------------
    # Public API
    # -----------------------------------------------------

    def normalize(
        self,
        *,
        label: str,
        confidence: float,
        bbox: list | tuple,
        frame_width: int,
        frame_height: int,
        source: str = "yolo",
        model: str = "yolo11n",
        frame_id: int = 0,
        timestamp: float = 0.0,
    ) -> VisionObject:

        x1, y1, x2, y2 = map(float, bbox)

        box = BoundingBox(
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
        )

        return VisionObject(
            label=label,
            category=self._infer_category(label),
            confidence=confidence,
            bbox=box,
            screen_region=self._screen_region(
                box,
                frame_width,
                frame_height,
            ),
            source=source,
            model=model,
            frame_id=frame_id,
            timestamp=timestamp,
        )

    # -----------------------------------------------------
    # Helpers
    # -----------------------------------------------------

    def _screen_region(
        self,
        bbox: BoundingBox,
        frame_width: int,
        frame_height: int,
    ) -> str:

        cx = bbox.center_x / frame_width
        cy = bbox.center_y / frame_height

        horizontal = (
            "left"
            if cx < 0.33
            else "right"
            if cx > 0.66
            else "center"
        )

        vertical = (
            "top"
            if cy < 0.33
            else "bottom"
            if cy > 0.66
            else "middle"
        )

        if horizontal == "center" and vertical == "middle":
            return "center"

        return f"{vertical}_{horizontal}"

    def _infer_category(self, label: str) -> str:

        label = label.lower()

        mapping = {

            # Human
            "person": "human",

            # Electronics
            "tv": "display",
            "monitor": "display",
            "laptop": "computer",
            "cell phone": "mobile",
            "keyboard": "input",
            "mouse": "input",

            # Furniture
            "chair": "furniture",
            "couch": "furniture",
            "bed": "furniture",
            "table": "furniture",

            # Vehicles
            "car": "vehicle",
            "truck": "vehicle",
            "bus": "vehicle",

            # Animals
            "dog": "animal",
            "cat": "animal",

        }

        return mapping.get(label, "object")