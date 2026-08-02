"""
Omnix V5 Create File Skill

Creates a new file through the filesystem service.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from skills.core.base_skill import BaseSkill


class CreateFileSkill(BaseSkill):

    metadata = SkillMetadata(
        id="builtin.files.create_file",

        name="create_file",

        description="Create a new file at a specified path.",

        category="files",

        aliases=[
            "create file",
            "make file",
            "new file",
        ],

        tags=[
            "file",
            "filesystem",
            "create",
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

        content = context.parameter(
            "content",
            "",
        )


        if not path:

            return SkillResult.failure(
                message=(
                    "File path is required "
                    "to create a file."
                )
            )


        try:

            created = await context.files.create_file(
                path=str(path),
                content=str(content),
            )


        except Exception as error:

            return SkillResult.failure(
                message=(
                    "Failed to create file."
                ),
                exception=error,
            )


        if created is False:

            return SkillResult.failure(
                message=(
                    f"Could not create file: {path}"
                )
            )


        return SkillResult.success_result(
            message=(
                f"File created: {path}"
            ),

            data={
                "path": str(path),
                "content_length": len(str(content)),
                "action": "create_file",
            },
        )