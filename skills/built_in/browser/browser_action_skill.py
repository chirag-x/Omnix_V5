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

        action = action.lower()

        handlers: dict[
            str,
            Callable[
                [SkillContext],
                Awaitable[bool],
            ],
        ] = {
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
        await context.browser.refresh()

    async def _back(
        self,
        context: SkillContext,
    ):
        await context.browser.back()

    async def _forward(
        self,
        context: SkillContext,
    ):
        await context.browser.forward()

    async def _new_tab(
        self,
        context: SkillContext,
    ):
        await context.browser.new_tab()

    async def _close_tab(
        self,
        context: SkillContext,
    ):
        await context.browser.close_tab()

    async def _scroll_up(
        self,
        context: SkillContext,
    ):
        await context.browser.scroll(direction="up")

    async def _scroll_down(
        self,
        context: SkillContext,
    ):
        await context.browser.scroll(direction="down")
