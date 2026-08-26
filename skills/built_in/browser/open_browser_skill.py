"""
Omnix V5 Open Browser Skill

Launches or focuses a browser and optionally opens a URL.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from .browser_skill import BrowserSkill


class OpenBrowserSkill(BrowserSkill):

    metadata = SkillMetadata(
        id="builtin.browser.open",
        name="open_browser",
        description="Launch or focus a web browser.",
        category="browser",
        aliases=[
            "launch browser",
            "start browser",
            "open chrome",
            "open edge",
            "open firefox",
        ],
        tags=[
            "browser",
            "internet",
            "navigation",
        ],
        priority=10,
    )

    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        browser = context.entity("browser") or self.browser_name

        url = context.entity("url")

        if context.browser is None:
            return SkillResult.failure(message="Browser service is unavailable.")

        # -----------------------------------------
        # Launch browser if necessary
        # -----------------------------------------

        if not await context.browser.is_running(browser):

            launched = await context.browser.launch(browser=browser)

            if launched is False:
                return SkillResult.failure(message=f"Failed to launch {browser}.")

            action = "opened"

        else:

            await context.browser.focus(browser=browser)

            action = "focused"

        # -----------------------------------------
        # Open URL if supplied
        # -----------------------------------------

        if url:

            try:
                opened = await context.browser.open_url(url, browser=browser)
            except TypeError:
                opened = await context.browser.open_url(url)

            if opened is False:
                return SkillResult.failure(message=f"Failed to open {url}.")

        return SkillResult.success_result(
            message=f"{browser} {action} successfully.",
            data={
                "browser": browser,
                "action": action,
                "url": url,
            },
        )
