"""
Omnix V5 Click UI Skill

Finds and clicks a UI element using the vision system.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.base_skill import BaseSkill
from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult


class ClickUISkill(BaseSkill):

    metadata = SkillMetadata(
        id="builtin.vision.click_ui",
        name="click_ui",
        description="Find and click a UI element using vision.",
        category="vision",
        aliases=[
            "click ui",
            "click button",
            "click element",
        ],
        tags=[
            "vision",
            "ui",
            "click",
        ],
        priority=20,
    )

    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        element = context.parameter("target") or context.parameter("element")

        if not element:

            return SkillResult.failure(message=("UI element name is required."))

        try:

            result = await context.vision.click_element(str(element))

        except Exception as error:

            return SkillResult.failure(
                message=("UI click failed."),
                exception=error,
            )

        if result is False or result is None:

            return SkillResult.failure(
                message=(f"Could not click " f"element: {element}")
            )

        return SkillResult.success_result(
            message=(f"Clicked element: {element}"),
            data={
                "element": str(element),
                "result": result,
                "action": "click_ui",
            },
        )
