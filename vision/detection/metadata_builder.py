"""
Omnix V5 - Metadata Builder

Enriches VisionObjects with additional metadata useful for
reasoning, planning and automation.
"""

from __future__ import annotations

from vision.models.vision_object import VisionObject


class MetadataBuilder:

    def enrich(
        self,
        objects: list[VisionObject],
        frame_width: int,
        frame_height: int,
    ) -> list[VisionObject]:

        frame_area = frame_width * frame_height

        for obj in objects:

            if obj.bbox is None:
                continue

            bbox = obj.bbox

            # -----------------------------
            # Basic Geometry
            # -----------------------------

            obj.set_attribute("center_x", bbox.center_x)
            obj.set_attribute("center_y", bbox.center_y)

            obj.set_attribute("width", bbox.width)
            obj.set_attribute("height", bbox.height)

            obj.set_attribute("area", bbox.area)

            obj.set_attribute(
                "aspect_ratio",
                round(bbox.aspect_ratio, 3),
            )

            # -----------------------------
            # Relative Screen Size
            # -----------------------------

            percent = (
                bbox.area / frame_area
                if frame_area > 0
                else 0
            )

            obj.set_attribute("screen_percent", percent)

            if percent < 0.01:
                size = "tiny"
            elif percent < 0.05:
                size = "small"
            elif percent < 0.20:
                size = "medium"
            else:
                size = "large"

            obj.set_attribute("size", size)

            # -----------------------------
            # Orientation
            # -----------------------------

            if bbox.width > bbox.height:
                orientation = "landscape"

            elif bbox.height > bbox.width:
                orientation = "portrait"

            else:
                orientation = "square"

            obj.set_attribute(
                "orientation",
                orientation,
            )

            # -----------------------------
            # Edge Detection
            # -----------------------------

            margin = 25

            edges = []

            if bbox.x1 <= margin:
                edges.append("left")

            if bbox.y1 <= margin:
                edges.append("top")

            if bbox.x2 >= frame_width - margin:
                edges.append("right")

            if bbox.y2 >= frame_height - margin:
                edges.append("bottom")

            obj.set_attribute("edges", edges)

            # -----------------------------
            # Center Distance
            # -----------------------------

            dx = abs(
                bbox.center_x - frame_width / 2
            )

            dy = abs(
                bbox.center_y - frame_height / 2
            )

            obj.set_attribute(
                "distance_from_center",
                round((dx * dx + dy * dy) ** 0.5, 2),
            )

        return objects