"""
Omnix V5 Undo Skill

Undo last action using keyboard shortcut.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from .input_skill import InputSkill


class UndoSkill(InputSkill):

    metadata = SkillMetadata(
        id="builtin.input.undo",
        name="undo",
        description="Undo the last action using keyboard shortcut.",
        category="input",
        aliases=[
            "undo",
            "undo action",
            "go back",
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

        undone = await self.hotkey(
            context,
            "ctrl",
            "z",
        )

        if not undone:

            return SkillResult.failure(message=("Failed to undo " "last action."))

        return SkillResult.success_result(
            message=("Last action undone."),
            data={
                "shortcut": "ctrl+z",
                "action": "undo",
            },
        )
