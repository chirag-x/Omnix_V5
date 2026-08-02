"""
Omnix V5 Find Element Skill

Finds a UI element using the vision system.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.base_skill import BaseSkill
from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult


class FindElementSkill(BaseSkill):

    metadata = SkillMetadata(
        id="builtin.vision.find_element",
        name="find_element",
        description="Find a UI element on the screen using vision.",
        category="vision",
        aliases=[
            "find element",
            "locate button",
            "find ui",
        ],
        tags=[
            "vision",
            "ui",
            "screen",
        ],
        priority=20,
    )

    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        element = context.parameter("target") or context.parameter("element")

        if not element:

            return SkillResult.failure(message=("Element name is required."))

        try:

            result = await context.vision.find_element(str(element))

        except Exception as error:

            return SkillResult.failure(
                message=("Vision search failed."),
                exception=error,
            )

        if not result:

            return SkillResult.failure(
                message=(f"Could not find " f"element: {element}")
            )

        return SkillResult.success_result(
            message=(f"Found element: {element}"),
            data={
                "element": str(element),
                "result": result,
                "action": "find_element",
            },
        )
