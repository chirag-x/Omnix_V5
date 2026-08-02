"""
Omnix V5 Move Mouse Skill

Moves the mouse cursor to a specific position.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_context import SkillContext
from skills.core.skill_result import SkillResult

from .input_skill import InputSkill


class MoveMouseSkill(InputSkill):

    metadata = SkillMetadata(
        id="builtin.input.move_mouse",

        name="move_mouse",

        description="Move mouse cursor to a screen position.",

        category="input",

        aliases=[
            "move mouse",
            "move cursor",
            "place cursor",
        ],

        tags=[
            "mouse",
            "cursor",
            "input",
        ],

        priority=20,
    )


    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        x = context.parameter(
            "x"
        )

        y = context.parameter(
            "y"
        )


        if x is None or y is None:
            return SkillResult.failure(
                message=(
                    "Mouse position "
                    "requires x and y coordinates."
                )
            )


        moved = await self.move_mouse(
            context,
            int(x),
            int(y),
        )


        if not moved:
            return SkillResult.failure(
                message=(
                    f"Failed to move mouse "
                    f"to ({x}, {y})."
                )
            )


        return SkillResult.success_result(
            message=(
                f"Mouse moved to "
                f"({x}, {y})."
            ),

            data={
                "x": int(x),
                "y": int(y),
                "action": "move_mouse",
            },
        )