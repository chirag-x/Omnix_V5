"""
Omnix V5 Paste Skill

Pastes clipboard content using keyboard shortcut.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from .input_skill import InputSkill


class PasteSkill(InputSkill):

    metadata = SkillMetadata(
        id="builtin.input.paste",
        name="paste",
        description="Paste clipboard content using keyboard shortcut.",
        category="input",
        aliases=[
            "paste",
            "paste text",
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

        pasted = await self.hotkey(
            context,
            "ctrl",
            "v",
        )

        if not pasted:

            return SkillResult.failure(
                message=("Failed to paste " "clipboard content.")
            )

        return SkillResult.success_result(
            message=("Content pasted."),
            data={
                "shortcut": "ctrl+v",
                "action": "paste",
            },
        )
