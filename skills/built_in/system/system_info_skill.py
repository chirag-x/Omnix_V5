"""
Omnix V5 System Info Skill

Provides information about the current system state.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.base_skill import BaseSkill
from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult


class SystemInfoSkill(BaseSkill):

    metadata = SkillMetadata(
        id="builtin.system.system_info",
        name="system_info",
        description="Get current system information.",
        category="system",
        aliases=[
            "system info",
            "computer info",
            "pc status",
        ],
        tags=[
            "system",
            "information",
            "status",
        ],
        priority=10,
    )

    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        try:

            info = await context.system.get_information()

        except Exception as error:

            return SkillResult.failure(
                message=("Failed to get system information."),
                exception=error,
            )

        return SkillResult.success_result(
            message=("System information retrieved."),
            data={
                "system": info,
                "action": "system_info",
            },
        )
