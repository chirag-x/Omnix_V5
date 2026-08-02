"""
Omnix V5 Restart System Skill

Restarts the operating system through the system service.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.base_skill import BaseSkill
from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult


class RestartSkill(BaseSkill):

    metadata = SkillMetadata(
        id="builtin.system.restart",
        name="restart",
        description="Restart the computer system.",
        category="system",
        aliases=[
            "restart",
            "reboot",
            "restart computer",
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

            restarted = await context.system.restart()

        except Exception as error:

            return SkillResult.failure(
                message=("Failed to restart system."),
                exception=error,
            )

        if restarted is False:

            return SkillResult.failure(message=("System restart request failed."))

        return SkillResult.success_result(
            message=("System restart initiated."),
            data={
                "action": "restart",
            },
        )
