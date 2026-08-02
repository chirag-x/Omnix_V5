"""
Omnix V5 - Duplicate Detection Filter

Removes duplicate VisionObjects using IoU (Intersection over Union).

The detector with the highest confidence is kept.
"""

from __future__ import annotations

from vision.models.vision_object import VisionObject


class DuplicateFilter:
    """
    Removes overlapping duplicate detections.
    """

    def __init__(
        self,
        iou_threshold: float = 0.50,
    ):
        self.iou_threshold = iou_threshold

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def filter(
        self,
        detections: list[VisionObject],
    ) -> list[VisionObject]:

        if len(detections) <= 1:
            return detections

        # Highest confidence first
        detections = sorted(
            detections,
            key=lambda obj: obj.confidence,
            reverse=True,
        )

        kept: list[VisionObject] = []

        for candidate in detections:

            duplicate = False

            for existing in kept:

                # Only compare same class
                if candidate.label != existing.label:
                    continue

                iou = candidate.bbox.iou(existing.bbox)

                if iou >= self.iou_threshold:
                    duplicate = True
                    break

            if not duplicate:
                kept.append(candidate)

        return kept