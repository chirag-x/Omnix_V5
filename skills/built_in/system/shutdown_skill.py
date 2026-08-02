"""
Omnix V5 Shutdown System Skill

Shuts down the operating system through the system service.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.base_skill import BaseSkill
from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult


class ShutdownSkill(BaseSkill):

    metadata = SkillMetadata(
        id="builtin.system.shutdown",
        name="shutdown",
        description="Shutdown the computer system.",
        category="system",
        aliases=[
            "shutdown",
            "turn off computer",
            "power off",
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

            shutdown = await context.system.shutdown()

        except Exception as error:

            return SkillResult.failure(
                message=("Failed to shutdown system."),
                exception=error,
            )

        if shutdown is False:

            return SkillResult.failure(message=("System shutdown request failed."))

        return SkillResult.success_result(
            message=("System shutdown initiated."),
            data={
                "action": "shutdown",
            },
        )
