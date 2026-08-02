"""
Omnix V5 Press Key Skill

Presses a single keyboard key.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from .input_skill import InputSkill


class PressKeySkill(InputSkill):

    metadata = SkillMetadata(
        id="builtin.input.press_key",

        name="press_key",

        description="Press a keyboard key.",

        category="input",

        aliases=[
            "press key",
            "hit key",
            "keyboard key",
        ],

        tags=[
            "keyboard",
            "key",
            "input",
        ],

        priority=20,
    )


    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        key = context.parameter(
            "key"
        )


        if not key:

            return SkillResult.failure(
                message=(
                    "No key provided "
                    "to press."
                )
            )


        pressed = await self.press_key(
            context,
            str(key),
        )


        if not pressed:

            return SkillResult.failure(
                message=(
                    f"Failed to press key "
                    f"'{key}'."
                )
            )


        return SkillResult.success_result(
            message=(
                f"Pressed key '{key}'."
            ),

            data={
                "key": str(key),
                "action": "press_key",
            },
        )