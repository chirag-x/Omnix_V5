"""
Omnix V5 Middle Click Skill

Performs a middle mouse click at a screen position.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from .input_skill import InputSkill


class MiddleClickSkill(InputSkill):

    metadata = SkillMetadata(
        id="builtin.input.middle_click",

        name="middle_click",

        description="Middle click at a screen position.",

        category="input",

        aliases=[
            "middle click",
            "mouse wheel click",
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
                    "Middle click requires "
                    "x and y coordinates."
                )
            )


        clicked = await context.input.click(
            x=int(x),
            y=int(y),
            button="middle",
        )


        if not clicked:
            return SkillResult.failure(
                message=(
                    f"Failed to middle click "
                    f"at ({x}, {y})."
                )
            )


        return SkillResult.success_result(
            message=(
                f"Middle clicked at "
                f"({x}, {y})."
            ),

            data={
                "x": int(x),
                "y": int(y),
                "action": "middle_click",
            },
        )