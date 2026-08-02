"""
Omnix V5 Switch Application Skill

Brings an already-running application to the foreground.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from .application_skill import ApplicationSkill


class SwitchAppSkill(ApplicationSkill):

    metadata = SkillMetadata(
        id="builtin.applications.switch",
        name="switch_app",
        description="Switch to an already running application.",
        category="applications",
        aliases=[
            "focus application",
            "switch application",
            "activate application",
            "bring application",
        ],
        tags=[
            "desktop",
            "window",
            "application",
            "focus",
        ],
        priority=20,
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

            return SkillResult.failure(message=f"{application} is not running.")

        focused = await self.focus(
            context,
            application,
        )

        if not focused:
            return SkillResult.failure(message=f"Failed to focus {application}.")

        return SkillResult.success_result(
            message=f"Switched to {application}.",
            data={
                "application": application,
                "action": "focused",
            },
        )
