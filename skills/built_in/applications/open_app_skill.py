"""
Open Application Skill

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from .application_skill import ApplicationSkill


class OpenAppSkill(ApplicationSkill):

    metadata = SkillMetadata(
        id="builtin.applications.open",
        name="open_app",
        description="Open a desktop application.",
        category="applications",
        aliases=[
            "launch application",
            "start application",
            "open software",
            "run application",
        ],
        tags=[
            "desktop",
            "windows",
            "application",
        ],
        priority=10,
    )

    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        context.log_info(f"Entities={context.entities} Parameters={context.parameters}")

        application = context.entity("application")

        if not application:

            return SkillResult.failure(message="No application specified.")

        already_running = await self.is_running(
            context,
            application,
        )

        if already_running:

            await self.focus(
                context,
                application,
            )

            return SkillResult.success_result(
                message=f"{application} is already running.",
                data={
                    "application": application,
                    "action": "focused",
                },
            )

        opened = await self.open(
            context,
            application,
        )

        if not opened:
            return SkillResult.failure(message=f"Failed to open {application}.")

        return SkillResult.success_result(
            message=f"{application} opened successfully.",
            data={
                "application": application,
                "action": "opened",
            },
        )
