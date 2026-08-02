"""
Omnix V5 Web Search Skill

Search the web using the configured browser and search engine.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from .browser_skill import BrowserSkill


class SearchWebSkill(BrowserSkill):

    metadata = SkillMetadata(
        id="builtin.browser.search",
        name="search_web",
        description="Search the web using the active browser.",
        category="browser",
        aliases=[
            "google search",
            "web search",
            "search internet",
            "search online",
        ],
        tags=[
            "browser",
            "internet",
            "search",
        ],
        priority=30,
    )

    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        query = context.entity("query")

        if not query:
            return SkillResult.failure(message="No search query provided.")

        browser = context.entity("browser") or self.browser_name

        new_tab = context.parameter(
            "new_tab",
            default=False,
        )

        await self.ensure_browser(context)

        if new_tab:
            await context.browser.new_tab()

        try:

            await context.browser.search(
                query=query,
                browser=browser,
            )

        except Exception as error:

            return SkillResult.failure(
                message="Web search failed.",
                exception=error,
            )

        url = None

        try:
            url = await context.browser.current_url()
        except Exception:
            pass

        return SkillResult.success_result(
            message=f'Search completed for "{query}".',
            data={
                "query": query,
                "browser": browser,
                "url": url,
                "new_tab": new_tab,
            },
        )
