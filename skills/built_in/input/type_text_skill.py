"""
Omnix V5 Type Text Skill

Types text using the keyboard input system.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from .input_skill import InputSkill


class TypeTextSkill(InputSkill):

    metadata = SkillMetadata(
        id="builtin.input.type_text",

        name="type_text",

        description="Types text using keyboard input.",

        category="input",

        aliases=[
            "type text",
            "write text",
            "enter text",
        ],

        tags=[
            "keyboard",
            "typing",
            "input",
        ],

        priority=20,
    )


    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        text = context.parameter(
            "text"
        )


        if not text:

            return SkillResult.failure(
                message=(
                    "No text provided "
                    "for typing."
                )
            )


        typed = await self.type_text(
            context,
            str(text),
        )


        if not typed:

            return SkillResult.failure(
                message=(
                    "Failed to type text."
                )
            )


        return SkillResult.success_result(
            message=(
                "Text typed successfully."
            ),

            data={
                "text": str(text),
                "action": "type_text",
            },
        )