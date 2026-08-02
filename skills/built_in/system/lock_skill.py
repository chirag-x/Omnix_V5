"""
Omnix V5 Lock System Skill

Locks the current user session.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.base_skill import BaseSkill
from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult


class LockSkill(BaseSkill):

    metadata = SkillMetadata(
        id="builtin.system.lock",
        name="lock",
        description="Lock the computer session.",
        category="system",
        aliases=[
            "lock pc",
            "lock computer",
            "lock screen",
        ],
        tags=[
            "system",
            "security",
            "power",
        ],
        priority=10,
    )

    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        try:

            locked = await context.system.lock()

        except Exception as error:

            return SkillResult.failure(
                message=("Failed to lock system."),
                exception=error,
            )

        if locked is False:

            return SkillResult.failure(message=("System lock failed."))

        return SkillResult.success_result(
            message=("System locked."),
            data={
                "action": "lock",
            },
        )
