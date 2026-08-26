"""
Omnix V5 Skill Manager

Central execution engine for every skill.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

import asyncio
import threading
from typing import Type
from loguru import logger

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
    LEGACY_SKILL_ALIASES = {
        "open_app": "builtin.applications.open",
        "close_app": "builtin.applications.close",
        "switch_app": "builtin.applications.switch",
        "browser_action": "builtin.browser.action",
        "open_browser": "builtin.browser.open",
        "search_web": "builtin.browser.search",
        "browser_search": "builtin.browser.search",
        "create_file": "builtin.files.create_file",
        "open_file": "builtin.files.open_file",
        "search_file": "builtin.files.search_file",
        "type_text": "builtin.input.type_text",
        "press_key": "builtin.input.press_key",
        "click_mouse": "builtin.input.click",
        "click": "builtin.input.click",
        "double_click": "builtin.input.double_click",
        "right_click": "builtin.input.right_click",
        "middle_click": "builtin.input.middle_click",
        "move_mouse": "builtin.input.move_mouse",
        "drag_mouse": "builtin.input.drag",
        "hotkey": "builtin.input.hotkey",
        "copy": "builtin.input.copy",
        "cut": "builtin.input.cut",
        "paste": "builtin.input.paste",
        "undo": "builtin.input.undo",
        "redo": "builtin.input.redo",
        "select_all": "builtin.input.select_all",
        "scroll_page": "builtin.input.scroll",
        "scroll": "builtin.input.scroll",
        "click_ui": "builtin.vision.click_ui",
        "find_element": "builtin.vision.find_element",
        "wait_for_ui": "builtin.vision.wait_ui",
        "wait_ui": "builtin.vision.wait_ui",
        "system_info": "builtin.system.system_info",
        "lock": "builtin.system.lock",
        "sleep": "builtin.system.sleep",
        "restart": "builtin.system.restart",
        "shutdown": "builtin.system.shutdown",
    }

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

        if self.loaded:
            return

        logger.info("[SkillManager] initialize()")

        self.loader.load_all()

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

        skill_id = self.normalize_skill_id(skill_id)
        skill_cls = self.registry.get(skill_id)

        skill = skill_cls()

        self.running[id(skill)] = skill

        try:
            logger.info(
                f"[SkillManager] Executing {skill_id} "
                f"parameters={context.parameters}"
            )

            result = await asyncio.wait_for(
                skill.run(context),
                timeout=skill.metadata.timeout,
            )

            result.skill_name = skill.metadata.name
            logger.info(
                f"[SkillManager] Finished {skill_id} "
                f"success={result.success} "
                f"time={result.execution_time:.3f}s"
            )

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

        if not self.loaded:
            await self.initialize()

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

        if not self.loaded:
            self._run_coroutine_sync(self.initialize())

        step = self.normalize_step(step)
        skill_id = step["skill"]
        parameters = step.get("parameters", {})

        context = SkillContext(
            command=skill_id,
            entities=parameters,
            parameters=parameters,
            automation=self.dependencies.get("automation"),
            browser=self.dependencies.get("browser"),
            vision=self.dependencies.get("vision_manager"),
            input=self.dependencies.get("input"),
            memory=self.dependencies.get("memory"),
            ai=self.dependencies.get("brain"),
            system=self.dependencies.get("system"),
            planner=self.dependencies.get("planner"),
            skills=self,
            ui=self.dependencies.get("ui_controller"),
            files=self.dependencies.get("files"),
            clipboard=self.dependencies.get("clipboard"),
            events=self.dependencies.get("events"),
            logger=logger,
        )

        return self._run_coroutine_sync(
            self.execute(
                skill_id=skill_id,
                context=context,
            )
        )

    def normalize_skill_id(self, skill_id: str) -> str:
        skill_id = str(skill_id or "").strip()

        if not skill_id:
            return skill_id

        mapped = self.LEGACY_SKILL_ALIASES.get(skill_id, skill_id)

        if self.registry.exists(mapped):
            return mapped

        try:
            return self.registry.find(mapped).metadata.id
        except SkillNotFoundError:
            return mapped

    def normalize_step(self, step):
        if not isinstance(step, dict):
            raise ValueError("Skill step must be a dictionary.")

        normalized = dict(step)
        skill_id = (
            normalized.get("skill")
            or normalized.get("tool")
            or normalized.get("name")
            or normalized.get("action")
        )

        if not skill_id:
            raise SkillNotFoundError("Skill step is missing a skill id.")

        normalized["skill"] = self.normalize_skill_id(skill_id)

        params = (
            normalized.get("parameters")
            if "parameters" in normalized
            else normalized.get("params", normalized.get("args", {}))
        )

        normalized["parameters"] = params if isinstance(params, dict) else {}

        return normalized

    def _run_coroutine_sync(self, coroutine):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coroutine)

        result_box = {}

        def runner():
            try:
                result_box["result"] = asyncio.run(coroutine)
            except BaseException as exc:
                result_box["error"] = exc

        thread = threading.Thread(target=runner, daemon=True)
        thread.start()
        thread.join()

        if "error" in result_box:
            raise result_box["error"]

        return result_box.get("result")

    # --------------------------------------------------

    def get_skill(
        self,
        skill_id: str,
    ) -> Type[BaseSkill]:

        return self.registry.get(self.normalize_skill_id(skill_id))

    def has_skill(
        self,
        skill_id: str,
    ) -> bool:

        return self.registry.exists(self.normalize_skill_id(skill_id))

    def list_skills(self):

        return self.registry.ids()

    def skill_count(self):

        return self.registry.count()
