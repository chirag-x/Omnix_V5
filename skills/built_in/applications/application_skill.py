"""
Omnix V5 Application Skill Base

Base class for all application-related skills.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from abc import ABC
from unittest import result

from skills.core.base_skill import BaseSkill
from skills.core.skill_context import SkillContext
from skills.core.skill_result import SkillResult


class ApplicationSkill(BaseSkill, ABC):
    """
    Base class for desktop application skills.

    All actual desktop control is delegated to the
    Automation Engine through SkillContext.
    """

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    async def open(
        self,
        context: SkillContext,
        application: str,
    ) -> bool:
        """
        Open an application.
        """
        print("=" * 80)
        print("AUTOMATION OBJECT :", context.automation)
        print("AUTOMATION TYPE   :", type(context.automation))
        print("AUTOMATION MODULE :", type(context.automation).__module__)
        print("=" * 80)

        return await context.automation.open_application(application)

    async def close(
        self,
        context: SkillContext,
        application: str,
    ) -> bool:

        result = await context.automation.close_application(application)

        return result is not False

    async def focus(
        self,
        context: SkillContext,
        application: str,
    ) -> bool:

        result = await context.automation.focus_application(application)

        return result is not False

    async def is_running(
        self,
        context: SkillContext,
        application: str,
    ) -> bool:
        """
        Returns True if application is already running.
        """
        return await context.automation.is_running(application)

    async def ensure_running(
        self,
        context: SkillContext,
        application: str,
    ) -> None:
        """
        Start application only if it isn't already running.
        """

        running = await self.is_running(
            context,
            application,
        )

        if not running:
            await self.open(
                context,
                application,
            )
