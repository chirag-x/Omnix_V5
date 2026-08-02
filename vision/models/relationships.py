"""
Omnix V5 - Relationship Engine

Computes spatial relationships between VisionObjects.

Example:
    Search Box is LEFT_OF Search Button
    Login Button is BELOW Password Field
    Icon is INSIDE Button
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from vision.models.vision_object import VisionObject


class RelationType(str, Enum):
    LEFT_OF = "left_of"
    RIGHT_OF = "right_of"
    ABOVE = "above"
    BELOW = "below"
    INSIDE = "inside"
    CONTAINS = "contains"
    OVERLAPS = "overlaps"
    NEAR = "near"


@dataclass(slots=True)
class Relationship:
    source_id: str
    target_id: str
    relation: RelationType
    confidence: float = 1.0


class RelationshipEngine:

    def __init__(
        self,
        near_distance: float = 120.0,
        overlap_iou: float = 0.20,
    ):
        self.near_distance = near_distance
        self.overlap_iou = overlap_iou

    # ---------------------------------------------------------

    def build(
        self,
        objects: list[VisionObject],
    ) -> list[Relationship]:

        relationships: list[Relationship] = []

        for i, first in enumerate(objects):

            if first.bbox is None:
                continue

            for second in objects[i + 1:]:

                if second.bbox is None:
                    continue

                relationships.extend(
                    self._compare(first, second)
                )

        return relationships

    # ---------------------------------------------------------

    def _compare(
        self,
        a: VisionObject,
        b: VisionObject,
    ) -> list[Relationship]:

        relations: list[Relationship] = []

        ax = a.bbox.center_x
        ay = a.bbox.center_y

        bx = b.bbox.center_x
        by = b.bbox.center_y

        # -------------------------
        # LEFT / RIGHT
        # -------------------------

        if ax < bx:
            relations.append(
                Relationship(
                    a.id,
                    b.id,
                    RelationType.LEFT_OF,
                )
            )

            relations.append(
                Relationship(
                    b.id,
                    a.id,
                    RelationType.RIGHT_OF,
                )
            )

        else:

            relations.append(
                Relationship(
                    a.id,
                    b.id,
                    RelationType.RIGHT_OF,
                )
            )

            relations.append(
                Relationship(
                    b.id,
                    a.id,
                    RelationType.LEFT_OF,
                )
            )

        # -------------------------
        # ABOVE / BELOW
        # -------------------------

        if ay < by:

            relations.append(
                Relationship(
                    a.id,
                    b.id,
                    RelationType.ABOVE,
                )
            )

            relations.append(
                Relationship(
                    b.id,
                    a.id,
                    RelationType.BELOW,
                )
            )

        else:

            relations.append(
                Relationship(
                    a.id,
                    b.id,
                    RelationType.BELOW,
                )
            )

            relations.append(
                Relationship(
                    b.id,
                    a.id,
                    RelationType.ABOVE,
                )
            )

        # -------------------------
        # INSIDE
        # -------------------------

        if a.bbox.contains_box(b.bbox):

            relations.append(
                Relationship(
                    b.id,
                    a.id,
                    RelationType.INSIDE,
                )
            )

            relations.append(
                Relationship(
                    a.id,
                    b.id,
                    RelationType.CONTAINS,
                )
            )

        elif b.bbox.contains_box(a.bbox):

            relations.append(
                Relationship(
                    a.id,
                    b.id,
                    RelationType.INSIDE,
                )
            )

            relations.append(
                Relationship(
                    b.id,
                    a.id,
                    RelationType.CONTAINS,
                )
            )

        # -------------------------
        # OVERLAP
        # -------------------------

        if a.bbox.iou(b.bbox) >= self.overlap_iou:

            relations.append(
                Relationship(
                    a.id,
                    b.id,
                    RelationType.OVERLAPS,
                )
            )

            relations.append(
                Relationship(
                    b.id,
                    a.id,
                    RelationType.OVERLAPS,
                )
            )

        # -------------------------
        # NEAR
        # -------------------------

        if (
            a.bbox.distance_to(b.bbox)
            <= self.near_distance
        ):

            relations.append(
                Relationship(
                    a.id,
                    b.id,
                    RelationType.NEAR,
                )
            )

            relations.append(
                Relationship(
                    b.id,
                    a.id,
                    RelationType.NEAR,
                )
            )

        return relations