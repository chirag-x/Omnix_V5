"""
Omnix V5 Browser Action Skill

Executes generic browser actions.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from typing import Callable, Awaitable

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from .browser_skill import BrowserSkill


class BrowserActionSkill(BrowserSkill):

    metadata = SkillMetadata(
        id="builtin.browser.action",
        name="browser_action",
        description="Execute browser actions.",
        category="browser",
        aliases=[
            "browser command",
            "browser control",
        ],
        tags=[
            "browser",
            "actions",
        ],
        priority=20,
    )

    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        action = context.entity("action")

        if not action:

            return SkillResult.failure(message="No browser action specified.")

        if context.browser is None:
            return SkillResult.failure(message="Browser service is unavailable.")

        action = action.lower()

        handlers: dict[
            str,
            Callable[
                [SkillContext],
                Awaitable[bool],
            ],
        ] = {
            "open": self._open,
            "open_browser": self._open,
            "focus": self._focus,
            "focus_browser": self._focus,
            "search": self._search,
            "open_url": self._open_url,
            "navigate": self._open_url,
            "go_to": self._open_url,
            "refresh": self._refresh,
            "back": self._back,
            "forward": self._forward,
            "new_tab": self._new_tab,
            "close_tab": self._close_tab,
            "scroll_up": self._scroll_up,
            "scroll_down": self._scroll_down,
        }

        handler = handlers.get(action)

        if handler is None:

            return SkillResult.failure(message=f"Unsupported browser action: {action}")

        result = await handler(context)

        if result is False:
            return SkillResult.failure(message=f"Browser action '{action}' failed.")

        return SkillResult.success_result(
            message=f"Browser action '{action}' completed.",
            data={
                "action": action,
            },
        )

    # --------------------------------------------------
    # Actions
    # --------------------------------------------------

    async def _refresh(
        self,
        context: SkillContext,
    ):
        return await context.browser.refresh()

    async def _open(
        self,
        context: SkillContext,
    ):
        browser = context.entity("browser") or self.browser_name

        if not await context.browser.is_running(browser):
            return await context.browser.launch(browser=browser)

        return await context.browser.focus(browser=browser)

    async def _focus(
        self,
        context: SkillContext,
    ):
        browser = context.entity("browser") or self.browser_name
        return await context.browser.focus(browser=browser)

    async def _search(
        self,
        context: SkillContext,
    ):
        query = context.entity("query") or context.parameter("text")

        if not query:
            return False

        browser = context.entity("browser") or self.browser_name
        return await context.browser.search(query=query, browser=browser)

    async def _open_url(
        self,
        context: SkillContext,
    ):
        url = context.entity("url") or context.parameter("target")

        if not url:
            return False

        browser = context.entity("browser") or self.browser_name

        try:
            return await context.browser.open_url(url=url, browser=browser)
        except TypeError:
            return await context.browser.open_url(url)

    async def _back(
        self,
        context: SkillContext,
    ):
        return await context.browser.back()

    async def _forward(
        self,
        context: SkillContext,
    ):
        return await context.browser.forward()

    async def _new_tab(
        self,
        context: SkillContext,
    ):
        return await context.browser.new_tab()

    async def _close_tab(
        self,
        context: SkillContext,
    ):
        return await context.browser.close_tab()

    async def _scroll_up(
        self,
        context: SkillContext,
    ):
        return await context.browser.scroll(direction="up")

    async def _scroll_down(
        self,
        context: SkillContext,
    ):
        return await context.browser.scroll(direction="down")
