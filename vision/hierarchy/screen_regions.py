"""
Omnix V5 - Screen Region Analyzer

Assigns human-readable screen regions to VisionObjects.

Examples:
    top_left
    center
    bottom_right
"""

from __future__ import annotations

from vision.models.vision_object import VisionObject


class ScreenRegionAnalyzer:
    """
    Determines where objects are located on the screen.
    """

    def assign_regions(
        self,
        
        objects: list[VisionObject],
        frame_width: int,
        frame_height: int,
    ) -> list[VisionObject]:

        for obj in objects:

            if obj.bbox is None:
                continue

            cx = obj.bbox.center_x
            cy = obj.bbox.center_y

            horizontal = self._horizontal(
                cx,
                frame_width,
            )

            vertical = self._vertical(
                cy,
                frame_height,
            )

            region = self._combine(
                horizontal,
                vertical,
            )

            obj.screen_region = region

            obj.set_attribute(
                "horizontal_region",
                horizontal,
            )

            obj.set_attribute(
                "vertical_region",
                vertical,
            )

        return objects

    # ---------------------------------------------------------

    def _horizontal(
        self,
        x: float,
        width: int,
    ) -> str:

        ratio = x / width

        if ratio < 0.33:
            return "left"

        if ratio < 0.66:
            return "center"

        return "right"

    # ---------------------------------------------------------

    def _vertical(
        self,
        y: float,
        height: int,
    ) -> str:

        ratio = y / height

        if ratio < 0.33:
            return "top"

        if ratio < 0.66:
            return "middle"

        return "bottom"

    # ---------------------------------------------------------

    def _combine(
        self,
        horizontal: str,
        vertical: str,
    ) -> str:

        if horizontal == "center" and vertical == "middle":
            return "center"

        return f"{vertical}_{horizontal}"