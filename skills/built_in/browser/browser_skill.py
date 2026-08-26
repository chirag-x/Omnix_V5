"""
Omnix V5 Browser Skill Base

Base class for every browser-related skill.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from abc import ABC

from skills.core.base_skill import BaseSkill
from skills.core.skill_context import SkillContext


class BrowserSkill(BaseSkill, ABC):
    """
    Base class for browser skills.

    Browser interaction is delegated to the Browser Controller
    exposed through SkillContext.
    """

    @property
    def browser_name(self) -> str:
        """
        Default browser if none is specified.
        """
        return "chrome"

    # --------------------------------------------------
    # Browser Helpers
    # --------------------------------------------------

    async def ensure_browser(
        self,
        context: SkillContext,
        browser: str | None = None,
    ):
        """
        Ensure a browser session exists.
        """

        if context.browser is None:
            raise RuntimeError("Browser service is unavailable.")

        browser = browser or self.browser_name

        if not await context.browser.is_running(browser):
            await context.browser.launch(browser=browser)

    async def open_url(
        self,
        context: SkillContext,
        url: str,
    ) -> bool:
        """
        Open a URL.
        """

        await self.ensure_browser(context)

        return await context.browser.open_url(url)

    async def search(
        self,
        context: SkillContext,
        query: str,
    ):
        """
        Perform a web search.
        """

        await self.ensure_browser(context)

        await context.browser.search(query)

    async def new_tab(
        self,
        context: SkillContext,
    ):

        await self.ensure_browser(context)

        await context.browser.new_tab()

    async def close_tab(
        self,
        context: SkillContext,
    ):

        await context.browser.close_tab()

    async def refresh(
        self,
        context: SkillContext,
    ):

        await context.browser.refresh()

    async def current_url(
        self,
        context: SkillContext,
    ) -> str:

        return await context.browser.current_url()
