"""
Omnix V5 Double Click Skill

Double clicks at a screen position.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from .input_skill import InputSkill


class DoubleClickSkill(InputSkill):

    metadata = SkillMetadata(
        id="builtin.input.double_click",
        name="double_click",
        description="Double click at a screen position.",
        category="input",
        aliases=[
            "double click",
            "double tap",
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
                message=("Double click requires " "x and y coordinates.")
            )

        clicked = await self.double_click(
            context,
            int(x),
            int(y),
        )

        if not clicked:
            return SkillResult.failure(
                message=(f"Failed to double click " f"at ({x}, {y}).")
            )

        return SkillResult.success_result(
            message=(f"Double clicked at " f"({x}, {y})."),
            data={
                "x": int(x),
                "y": int(y),
                "action": "double_click",
            },
        )
