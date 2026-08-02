"""
Omnix V5 Search File Skill

Searches for files using the filesystem service.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from skills.core.base_skill import BaseSkill


class SearchFileSkill(BaseSkill):

    metadata = SkillMetadata(
        id="builtin.files.search_file",

        name="search_file",

        description="Search for files using a query.",

        category="files",

        aliases=[
            "search file",
            "find file",
            "look for file",
        ],

        tags=[
            "file",
            "filesystem",
            "search",
        ],

        priority=20,
    )


    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        query = context.parameter(
            "query"
        )

        path = context.parameter(
            "path",
            None,
        )


        if not query:

            return SkillResult.failure(
                message=(
                    "Search query is required."
                )
            )


        try:

            results = await context.files.search(
                query=str(query),
                path=path,
            )


        except Exception as error:

            return SkillResult.failure(
                message=(
                    "File search failed."
                ),
                exception=error,
            )


        if results is None:

            results = []


        return SkillResult.success_result(
            message=(
                f"Found {len(results)} "
                "matching file(s)."
            ),

            data={
                "query": str(query),
                "path": path,
                "results": results,
                "action": "search_file",
            },
        )