"""
Omnix V5 Skill Manager

Central execution engine for every skill.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

import asyncio
from typing import Type
from loguru import logger
from matplotlib.pyplot import step

from skills.core.base_skill import BaseSkill
from skills.core.skill_context import SkillContext
from skills.core.skill_result import SkillResult
from skills.core.exceptions import (
    SkillNotFoundError,
)

from skills.manager.skill_registry import SkillRegistry
from skills.manager.skill_loader import SkillLoader
from skills.manager.skill_validator import SkillValidator


class SkillManager:

    def __init__(self, dependencies=None):

        self.dependencies = dependencies or {}

        self.registry = SkillRegistry()

        self.validator = SkillValidator()

        self.loader = SkillLoader(self.registry)

        self.loaded = False

        self.running = {}

    # --------------------------------------------------

    # async def initialize(self):

    #     self.loader.load_all()

    #     self.loaded = True

    async def initialize(self):

        print("=" * 60)
        print("SKILL MANAGER INITIALIZE CALLED")
        print("=" * 60)

        logger.info("[SkillManager] initialize()")

        print("Loader object:", self.loader)

        self.loader.load_all()

        print("Registry Count:", self.registry.count())

        print("Loader Summary:", self.loader.summary())

        self.loaded = True

    # --------------------------------------------------

    async def shutdown(self):

        self.running.clear()

        self.loaded = False

    # --------------------------------------------------

    async def execute(
        self,
        skill_id: str,
        context: SkillContext,
    ) -> SkillResult:

        if not self.loaded:

            await self.initialize()

        skill_cls = self.registry.get(skill_id)

        skill = skill_cls()

        self.running[id(skill)] = skill

        try:

            result = await asyncio.wait_for(
                skill.run(context),
                timeout=skill.metadata.timeout,
            )

            result.skill_name = skill.metadata.name

            return result

        finally:

            self.running.pop(
                id(skill),
                None,
            )

    # --------------------------------------------------

    async def execute_by_alias(
        self,
        alias: str,
        context: SkillContext,
    ) -> SkillResult:

        skill_cls = self.registry.find(alias)

        return await self.execute(
            skill_cls.metadata.id,
            context,
        )

    # --------------------------------------------------

    def execute_skill(self, step):
        """
        Compatibility wrapper for GoalExecutor.
        """

        skill_id = step["skill"]
        parameters = step.get("parameters", {})

        context = SkillContext(
            command=skill_id,
            entities=parameters,
            parameters=parameters,
            automation=self.dependencies.get("automation"),
            browser=self.dependencies.get("browser"),
            vision=self.dependencies.get("vision_manager"),
            memory=self.dependencies.get("memory"),
            ai=self.dependencies.get("brain"),
            system=self.dependencies.get("system"),
            planner=self.dependencies.get("planner"),
            skills=self,
            ui=self.dependencies.get("ui_controller"),
            logger=logger,
        )

        return asyncio.run(
            self.execute(
                skill_id=skill_id,
                context=context,
            )
        )

    # --------------------------------------------------

    def get_skill(
        self,
        skill_id: str,
    ) -> Type[BaseSkill]:

        return self.registry.get(skill_id)

    def has_skill(
        self,
        skill_id: str,
    ) -> bool:

        return self.registry.exists(skill_id)

    def list_skills(self):

        return self.registry.all()

    def skill_count(self):

        return self.registry.count()
