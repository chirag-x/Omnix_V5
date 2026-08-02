"""
Omnix V5 Wait UI Skill

Waits until a UI element appears on screen.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

import asyncio

from skills.core.base_skill import BaseSkill
from skills.core.skill_context import SkillContext
from skills.core.skill_metadata import SkillMetadata
from skills.core.skill_result import SkillResult


class WaitUISkill(BaseSkill):

    metadata = SkillMetadata(
        id="builtin.vision.wait_ui",
        name="wait_ui",
        description="Wait until a UI element appears.",
        category="vision",
        aliases=[
            "wait for ui",
            "wait for element",
            "wait until button appears",
        ],
        tags=[
            "vision",
            "ui",
            "wait",
        ],
        priority=20,
    )

    async def execute(
        self,
        context: SkillContext,
    ) -> SkillResult:

        element = context.parameter("target") or context.parameter("element")

        timeout = context.parameter(
            "timeout",
            10,
        )

        if not element:

            return SkillResult.failure(message=("UI element name is required."))

        try:

            timeout = float(timeout)

        except ValueError:

            timeout = 10

        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:

            try:

                found = await context.vision.find_element(str(element))

                if found:

                    return SkillResult.success_result(
                        message=(f"UI element found: {element}"),
                        data={
                            "element": str(element),
                            "result": found,
                            "action": "wait_ui",
                        },
                    )

            except Exception:
                pass

            await asyncio.sleep(0.5)

        return SkillResult.failure(
            message=(f"Timed out waiting for " f"UI element: {element}"),
            data={
                "element": str(element),
                "timeout": timeout,
                "action": "wait_ui",
            },
        )
