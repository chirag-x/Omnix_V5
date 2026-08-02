"""
Omnix V5 Redo Skill

Redo last undone action using keyboard shortcut.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from .input_skill import InputSkill


class RedoSkill(InputSkill):

    metadata = SkillMetadata(
        id="builtin.input.redo",

        name="redo",

        description="Redo the last undone action using keyboard shortcut.",

        category="input",

        aliases=[
            "redo",
            "redo action",
        ],

        tags=[
            "keyboard",
            "editing",
            "input",
        ],

        priority=20,
    )


    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        redone = await self.hotkey(
            context,
            "ctrl",
            "y",
        )


        if not redone:

            return SkillResult.failure(
                message=(
                    "Failed to redo "
                    "last action."
                )
            )


        return SkillResult.success_result(
            message=(
                "Last action redone."
            ),

            data={
                "shortcut": "ctrl+y",
                "action": "redo",
            },
        )