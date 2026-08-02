"""
Omnix V5 Scroll Skill

Controls mouse scrolling.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult

from .input_skill import InputSkill


class ScrollSkill(InputSkill):

    metadata = SkillMetadata(
        id="builtin.input.scroll",
        name="scroll",
        description="Scrolls the mouse wheel.",
        category="input",
        aliases=[
            "scroll",
            "scroll page",
            "mouse wheel",
        ],
        tags=[
            "mouse",
            "scroll",
            "input",
        ],
        priority=20,
    )

    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        amount = context.parameter("amount")

        if amount is None:

            return SkillResult.failure(message=("Scroll amount " "is required."))

        try:
            amount = int(amount)

        except ValueError:

            return SkillResult.failure(message=("Scroll amount " "must be a number."))

        scrolled = await self.scroll(
            context,
            amount,
        )

        if not scrolled:

            return SkillResult.failure(message=("Failed to scroll."))

        return SkillResult.success_result(
            message=(f"Scrolled by {amount}."),
            data={
                "amount": amount,
                "action": "scroll",
            },
        )
