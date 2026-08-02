"""
Omnix V5 Cut Skill

Cuts selected content to clipboard.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from .input_skill import InputSkill


class CutSkill(InputSkill):

    metadata = SkillMetadata(
        id="builtin.input.cut",
        name="cut",
        description="Cut selected content using keyboard shortcut.",
        category="input",
        aliases=[
            "cut",
            "cut selection",
        ],
        tags=[
            "keyboard",
            "clipboard",
            "input",
        ],
        priority=20,
    )

    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        cut = await self.hotkey(
            context,
            "ctrl",
            "x",
        )

        if not cut:

            return SkillResult.failure(message=("Failed to cut " "selected content."))

        return SkillResult.success_result(
            message=("Content cut."),
            data={
                "shortcut": "ctrl+x",
                "action": "cut",
            },
        )
