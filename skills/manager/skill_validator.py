"""
Omnix V5 Skill Validator

Validates skills before they are registered.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

import inspect
from typing import Type

from skills.core.base_skill import BaseSkill
from skills.core.skill_metadata import SkillMetadata
from skills.core.exceptions import (
    SkillValidationError,
)


class SkillValidator:
    """
    Validates Skill classes before registration.
    """

    REQUIRED_METADATA = (
        "id",
        "name",
        "description",
    )

    def validate(
        self,
        skill_cls: Type[BaseSkill],
    ) -> None:

        self._validate_inheritance(skill_cls)

        metadata = self._validate_metadata(skill_cls)

        self._validate_execute(skill_cls)

        self._validate_timeout(metadata)

        self._validate_priority(metadata)

        self._validate_aliases(metadata)

        self._validate_dependencies(metadata)

    # --------------------------------------------------
    # Base Class
    # --------------------------------------------------

    def _validate_inheritance(
        self,
        skill_cls: Type[BaseSkill],
    ) -> None:

        if not issubclass(skill_cls, BaseSkill):

            raise SkillValidationError(
                f"{skill_cls.__name__} "
                "does not inherit BaseSkill."
            )

    # --------------------------------------------------
    # Metadata
    # --------------------------------------------------

    def _validate_metadata(
        self,
        skill_cls: Type[BaseSkill],
    ) -> SkillMetadata:

        if not hasattr(skill_cls, "metadata"):

            raise SkillValidationError(
                f"{skill_cls.__name__} "
                "is missing metadata."
            )

        metadata = skill_cls.metadata

        for field in self.REQUIRED_METADATA:

            value = getattr(metadata, field, None)

            if not value:

                raise SkillValidationError(
                    f"{skill_cls.__name__}: "
                    f"metadata.{field} is required."
                )

        return metadata

    # --------------------------------------------------
    # Execute
    # --------------------------------------------------

    def _validate_execute(
        self,
        skill_cls: Type[BaseSkill],
    ) -> None:

        if skill_cls.execute is BaseSkill.execute:

            raise SkillValidationError(
                f"{skill_cls.__name__} "
                "does not implement execute()."
            )

        if not inspect.iscoroutinefunction(
            skill_cls.execute
        ):

            raise SkillValidationError(
                f"{skill_cls.__name__}.execute "
                "must be async."
            )

    # --------------------------------------------------
    # Metadata Checks
    # --------------------------------------------------

    def _validate_timeout(
        self,
        metadata: SkillMetadata,
    ) -> None:

        if metadata.timeout <= 0:

            raise SkillValidationError(
                "Timeout must be > 0."
            )

    def _validate_priority(
        self,
        metadata: SkillMetadata,
    ) -> None:

        if metadata.priority < 0:

            raise SkillValidationError(
                "Priority cannot be negative."
            )

    def _validate_aliases(
        self,
        metadata: SkillMetadata,
    ) -> None:

        aliases = [
            alias.lower()
            for alias in metadata.aliases
        ]

        if len(aliases) != len(set(aliases)):

            raise SkillValidationError(
                f"Duplicate aliases "
                f"in '{metadata.name}'."
            )

    def _validate_dependencies(
        self,
        metadata: SkillMetadata,
    ) -> None:

        if metadata.id in metadata.dependencies:

            raise SkillValidationError(
                "Skill cannot depend on itself."
            )