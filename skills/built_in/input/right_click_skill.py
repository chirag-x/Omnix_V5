"""
Omnix V5 Right Click Skill

Performs a right mouse click at a screen position.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from .input_skill import InputSkill


class RightClickSkill(InputSkill):

    metadata = SkillMetadata(
        id="builtin.input.right_click",

        name="right_click",

        description="Right click at a screen position.",

        category="input",

        aliases=[
            "right click",
            "context click",
        ],

        tags=[
            "mouse",
            "click",
            "input",
        ],

        priority=20,
    )


    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        x = context.parameter("x")
        y = context.parameter("y")


        if x is None or y is None:
            return SkillResult.failure(
                message=(
                    "Right click requires "
                    "x and y coordinates."
                )
            )


        clicked = await self.right_click(
            context,
            int(x),
            int(y),
        )


        if not clicked:
            return SkillResult.failure(
                message=(
                    f"Failed to right click "
                    f"at ({x}, {y})."
                )
            )


        return SkillResult.success_result(
            message=(
                f"Right clicked at "
                f"({x}, {y})."
            ),

            data={
                "x": int(x),
                "y": int(y),
                "action": "right_click",
            },
        )