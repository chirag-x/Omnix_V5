"""
Omnix V5 Skill Loader

Automatically discovers and loads skills.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from pathlib import Path
from types import ModuleType
from typing import Iterable, Type
from loguru import logger

from skills.core.base_skill import BaseSkill
from skills.manager.skill_registry import SkillRegistry


class SkillLoader:
    """
    Automatically discovers skill classes
    and registers them.
    """

    DEFAULT_PACKAGES = (
        "skills.built_in",
        "skills.generated.generated_skills",
    )

    def __init__(
        self,
        registry: SkillRegistry,
    ):

        self.registry = registry

        self.loaded_skills = []

        self.failed_modules = {}

    # --------------------------------------------------
    # Public
    # --------------------------------------------------

    def load_all(self) -> None:

        print("=" * 60)
        print("LOAD_ALL EXECUTED")
        print("=" * 60)

        logger.info("[SkillLoader] Discovering skills...")

        for package in self.DEFAULT_PACKAGES:

            try:

                logger.info(f"[SkillLoader] Loading package: {package}")

                self.load_package(package)

            except Exception as e:

                logger.exception(f"[SkillLoader] Failed to load package {package}: {e}")

        logger.info(f"[SkillLoader] Loaded {self.successful} skills")

        if self.failed:

            logger.warning(f"[SkillLoader] Failed modules: {self.failed}")

            for module, error in self.failed_modules.items():

                logger.error(f"{module} -> {error}")

    def load_package(
        self,
        package_name: str,
    ) -> None:

        try:

            package = importlib.import_module(package_name)

        except Exception as e:

            self.failed_modules[package_name] = str(e)

            return

        for module_name in self._walk_package(package):

            self.load_module(module_name)

    def load_module(
        self,
        module_name: str,
    ) -> None:

        try:

            module = importlib.import_module(module_name)

            for skill in self._find_skills(module):

                self.registry.register(skill)
                logger.success(f"[SkillLoader] Registered: {skill.metadata.id}")

                self.loaded_skills.append(skill.metadata.id)

        except Exception as e:

            self.failed_modules[module_name] = str(e)

    # --------------------------------------------------
    # Discovery
    # --------------------------------------------------

    def _walk_package(
        self,
        package: ModuleType,
    ) -> Iterable[str]:

        if not hasattr(package, "__path__"):
            return

        for module in pkgutil.walk_packages(
            package.__path__,
            package.__name__ + ".",
        ):

            yield module.name

    def _find_skills(
        self,
        module: ModuleType,
    ) -> Iterable[Type[BaseSkill]]:

        for _, obj in inspect.getmembers(
            module,
            inspect.isclass,
        ):

            # Must inherit from BaseSkill
            if not issubclass(
                obj,
                BaseSkill,
            ):
                continue

            # Skip BaseSkill itself
            if obj is BaseSkill:
                continue

            # Skip imported classes from other modules
            if obj.__module__ != module.__name__:
                continue

            # Skip abstract classes
            if inspect.isabstract(obj):
                continue

            # Skip classes without metadata
            if not hasattr(
                obj,
                "metadata",
            ):
                continue

            yield obj

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    @property
    def successful(self):

        return len(self.loaded_skills)

    @property
    def failed(self):

        return len(self.failed_modules)

    def summary(self):

        return {
            "loaded": self.successful,
            "failed": self.failed,
            "skills": self.loaded_skills,
            "errors": self.failed_modules,
        }
