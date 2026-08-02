"""
Omnix V5 Execution Manager

Responsible for executing skills safely.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from skills.core.skill_result import SkillResult

if TYPE_CHECKING:
    from skills.core.base_skill import BaseSkill
    from skills.core.skill_context import SkillContext


class ExecutionManager:
    """
    Executes skills with timeout support.

    Future responsibilities:

    • Timeouts
    • Retries
    • Queueing
    • Metrics
    • Events
    """

    def __init__(self):

        self.running: dict[int, BaseSkill] = {}

    async def execute(
        self,
        skill: BaseSkill,
        context: SkillContext,
    ) -> SkillResult:

        task_id = id(skill)

        self.running[task_id] = skill

        try:

            timeout = skill.metadata.timeout

            result = await asyncio.wait_for(
                skill.run(context),
                timeout=timeout,
            )

            result.skill_name = skill.metadata.name

            return result

        finally:

            self.running.pop(task_id, None)

    # -----------------------------------------

    def is_running(
        self,
        skill: BaseSkill,
    ) -> bool:

        return id(skill) in self.running

    # -----------------------------------------

    @property
    def running_count(self) -> int:

        return len(self.running)

    # -----------------------------------------

    def cancel_all(self) -> None:

        self.running.clear()