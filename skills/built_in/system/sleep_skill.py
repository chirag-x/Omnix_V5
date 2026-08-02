"""
Omnix V5 Sleep System Skill

Puts the computer into sleep mode.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.base_skill import BaseSkill
from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult


class SleepSkill(BaseSkill):

    metadata = SkillMetadata(
        id="builtin.system.sleep",
        name="sleep",
        description="Put the computer into sleep mode.",
        category="system",
        aliases=[
            "sleep pc",
            "sleep computer",
            "go to sleep",
        ],
        tags=[
            "system",
            "power",
        ],
        priority=10,
    )

    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        try:

            slept = await context.system.sleep()

        except Exception as error:

            return SkillResult.failure(
                message=("Failed to put system " "into sleep mode."),
                exception=error,
            )

        if slept is False:

            return SkillResult.failure(message=("System sleep failed."))

        return SkillResult.success_result(
            message=("System entering sleep mode."),
            data={
                "action": "sleep",
            },
        )
