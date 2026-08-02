"""
Omnix V5 Open File Skill

Opens a file through the filesystem service.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from skills.core.base_skill import BaseSkill


class OpenFileSkill(BaseSkill):

    metadata = SkillMetadata(
        id="builtin.files.open_file",

        name="open_file",

        description="Open a file using the filesystem system.",

        category="files",

        aliases=[
            "open file",
            "launch file",
            "show file",
        ],

        tags=[
            "file",
            "filesystem",
            "open",
        ],

        priority=20,
    )


    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        path = context.parameter(
            "path"
        )


        if not path:

            return SkillResult.failure(
                message=(
                    "File path is required "
                    "to open a file."
                )
            )


        try:

            opened = await context.files.open_file(
                path=str(path),
            )


        except Exception as error:

            return SkillResult.failure(
                message=(
                    "Failed to open file."
                ),
                exception=error,
            )


        if opened is False:

            return SkillResult.failure(
                message=(
                    f"Could not open file: {path}"
                )
            )


        return SkillResult.success_result(
            message=(
                f"File opened: {path}"
            ),

            data={
                "path": str(path),
                "action": "open_file",
            },
        )