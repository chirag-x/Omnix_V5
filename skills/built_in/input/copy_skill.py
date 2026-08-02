"""
Omnix V5 Copy Skill

Copies selected content to clipboard.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from .input_skill import InputSkill


class CopySkill(InputSkill):

    metadata = SkillMetadata(
        id="builtin.input.copy",
        name="copy",
        description="Copy selected content using keyboard shortcut.",
        category="input",
        aliases=[
            "copy",
            "copy selection",
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

        copied = await self.hotkey(
            context,
            "ctrl",
            "c",
        )

        if not copied:

            return SkillResult.failure(message=("Failed to copy " "selected content."))

        return SkillResult.success_result(
            message=("Content copied."),
            data={
                "shortcut": "ctrl+c",
                "action": "copy",
            },
        )
