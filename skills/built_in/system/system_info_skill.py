"""
Omnix V5 System Info Skill

Provides information about the current system state.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

import inspect

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

            if context.system is None:
                return SkillResult.failure(
                    message=("System service is unavailable."),
                )

            if hasattr(context.system, "get_information"):
                info = context.system.get_information()
            elif hasattr(context.system, "get_info"):
                info = context.system.get_info()
            elif hasattr(context.system, "statistics"):
                info = context.system.statistics()
            else:
                return SkillResult.failure(
                    message=("System information API is unavailable."),
                )

            if inspect.isawaitable(info):
                info = await info

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
