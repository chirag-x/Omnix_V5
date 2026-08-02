"""
Omnix V5 Close Application Skill

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from .application_skill import ApplicationSkill


class CloseAppSkill(ApplicationSkill):

    metadata = SkillMetadata(
        id="builtin.applications.close",
        name="close_app",
        description="Close a desktop application.",
        category="applications",
        aliases=[
            "exit application",
            "quit application",
            "terminate application",
            "close software",
        ],
        tags=[
            "application",
            "desktop",
            "windows",
        ],
        priority=10,
    )

    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        application = context.entity("application")

        if not application:
            return SkillResult.failure(message="No application specified.")

        running = await self.is_running(
            context,
            application,
        )

        if not running:
            return SkillResult.success_result(
                message=f"{application} is not running.",
                data={
                    "application": application,
                    "action": "already_closed",
                },
            )

        closed = await self.close(
            context,
            application,
        )

        if not closed:
            return SkillResult.failure(message=f"Failed to close {application}.")

        return SkillResult.success_result(
            message=f"{application} closed successfully.",
            data={
                "application": application,
                "action": "closed",
            },
        )
