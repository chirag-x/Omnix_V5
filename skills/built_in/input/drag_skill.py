"""
Omnix V5 Drag Mouse Skill

Drags the mouse from one position to another.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from .input_skill import InputSkill


class DragSkill(InputSkill):

    metadata = SkillMetadata(
        id="builtin.input.drag",

        name="drag",

        description="Drag mouse from one screen position to another.",

        category="input",

        aliases=[
            "drag mouse",
            "drag from",
            "move and drag",
        ],

        tags=[
            "mouse",
            "drag",
            "input",
        ],

        priority=20,
    )


    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        start_x = context.parameter("start_x")
        start_y = context.parameter("start_y")

        end_x = context.parameter("end_x")
        end_y = context.parameter("end_y")


        if (
            start_x is None
            or start_y is None
            or end_x is None
            or end_y is None
        ):
            return SkillResult.failure(
                message=(
                    "Drag requires "
                    "start_x, start_y, "
                    "end_x and end_y."
                )
            )


        dragged = await self.drag(
            context,

            int(start_x),
            int(start_y),

            int(end_x),
            int(end_y),
        )


        if not dragged:
            return SkillResult.failure(
                message=(
                    "Failed to drag mouse "
                    f"from ({start_x},{start_y}) "
                    f"to ({end_x},{end_y})."
                )
            )


        return SkillResult.success_result(
            message=(
                "Mouse drag completed."
            ),

            data={
                "start": {
                    "x": int(start_x),
                    "y": int(start_y),
                },

                "end": {
                    "x": int(end_x),
                    "y": int(end_y),
                },

                "action": "drag",
            },
        )