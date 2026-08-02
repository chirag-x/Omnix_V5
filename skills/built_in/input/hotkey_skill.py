"""
Omnix V5 Hotkey Skill

Executes keyboard shortcuts.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from .input_skill import InputSkill


class HotkeySkill(InputSkill):

    metadata = SkillMetadata(
        id="builtin.input.hotkey",
        name="hotkey",
        description="Execute a keyboard shortcut combination.",
        category="input",
        aliases=[
            "hotkey",
            "keyboard shortcut",
            "shortcut",
        ],
        tags=[
            "keyboard",
            "shortcut",
            "input",
        ],
        priority=20,
    )

    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        keys = context.parameter("keys")

        if not keys:

            return SkillResult.failure(message=("No keys provided " "for hotkey."))

        if isinstance(keys, str):

            keys = [key.strip() for key in keys.split("+") if key.strip()]

        if not isinstance(keys, (list, tuple)):

            return SkillResult.failure(
                message=("Hotkey keys must be " "a list or string.")
            )

        pressed = await self.hotkey(
            context,
            *keys,
        )

        if not pressed:

            return SkillResult.failure(
                message=("Failed to execute " f"hotkey: {'+'.join(keys)}")
            )

        return SkillResult.success_result(
            message=(f"Executed hotkey " f"{'+'.join(keys)}."),
            data={
                "keys": list(keys),
                "action": "hotkey",
            },
        )
