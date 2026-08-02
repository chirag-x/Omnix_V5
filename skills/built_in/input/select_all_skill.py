"""
Omnix V5 Select All Skill

Selects all available content using keyboard shortcut.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from .input_skill import InputSkill


class SelectAllSkill(InputSkill):

    metadata = SkillMetadata(
        id="builtin.input.select_all",
        name="select_all",
        description="Select all content using keyboard shortcut.",
        category="input",
        aliases=[
            "select all",
            "select everything",
        ],
        tags=[
            "keyboard",
            "selection",
            "input",
        ],
        priority=20,
    )

    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        selected = await self.hotkey(
            context,
            "ctrl",
            "a",
        )

        if not selected:

            return SkillResult.failure(message=("Failed to select all content."))

        return SkillResult.success_result(
            message=("All content selected."),
            data={
                "shortcut": "ctrl+a",
                "action": "select_all",
            },
        )
