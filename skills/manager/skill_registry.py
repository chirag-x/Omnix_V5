"""
Omnix V5 Skill Registry

Central registry for every available skill.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from collections import defaultdict
from typing import Type

from skills.core.base_skill import BaseSkill
from skills.core.exceptions import (
    SkillNotFoundError,
    SkillRegistrationError,
)


class SkillRegistry:
    """
    Stores and indexes every skill.

    Provides fast lookup by:

    - id
    - name
    - alias
    - category
    - tag
    """

    def __init__(self):

        self._skills: dict[str, Type[BaseSkill]] = {}

        self._aliases: dict[str, str] = {}

        self._categories: defaultdict[str, set[str]] = defaultdict(set)

        self._tags: defaultdict[str, set[str]] = defaultdict(set)

    # =====================================================
    # Registration
    # =====================================================

    def register(
        self,
        skill_cls: Type[BaseSkill],
    ) -> None:

        metadata = skill_cls.metadata

        skill_id = metadata.id

        if skill_id in self._skills:
            raise SkillRegistrationError(
                f"Skill '{skill_id}' already exists."
            )

        self._skills[skill_id] = skill_cls

        for alias in metadata.aliases:
            self._aliases[alias.lower()] = skill_id

        self._categories[
            metadata.category.lower()
        ].add(skill_id)

        for tag in metadata.tags:
            self._tags[
                tag.lower()
            ].add(skill_id)

    # =====================================================
    # Lookup
    # =====================================================

    def get(
        self,
        skill_id: str,
    ) -> Type[BaseSkill]:

        skill = self._skills.get(skill_id)

        if skill is None:

            raise SkillNotFoundError(
                f"Skill '{skill_id}' not found."
            )

        return skill

    def find(
        self,
        name: str,
    ) -> Type[BaseSkill]:

        name = name.lower()

        if name in self._skills:
            return self._skills[name]

        if name in self._aliases:
            return self._skills[
                self._aliases[name]
            ]

        raise SkillNotFoundError(name)

    # =====================================================
    # Search
    # =====================================================

    def by_category(
        self,
        category: str,
    ) -> list[Type[BaseSkill]]:

        ids = self._categories.get(
            category.lower(),
            set(),
        )

        return [
            self._skills[i]
            for i in ids
        ]

    def by_tag(
        self,
        tag: str,
    ) -> list[Type[BaseSkill]]:

        ids = self._tags.get(
            tag.lower(),
            set(),
        )

        return [
            self._skills[i]
            for i in ids
        ]

    # =====================================================
    # Utilities
    # =====================================================

    def exists(
        self,
        skill_id: str,
    ) -> bool:

        return skill_id in self._skills

    def unregister(
        self,
        skill_id: str,
    ) -> None:

        if skill_id not in self._skills:
            return

        metadata = self._skills[
            skill_id
        ].metadata

        del self._skills[skill_id]

        for alias in metadata.aliases:
            self._aliases.pop(
                alias.lower(),
                None,
            )

        self._categories[
            metadata.category.lower()
        ].discard(skill_id)

        for tag in metadata.tags:
            self._tags[
                tag.lower()
            ].discard(skill_id)

    def all(self):

        return list(
            self._skills.values()
        )

    def count(self):

        return len(self._skills)

    def clear(self):

        self._skills.clear()

        self._aliases.clear()

        self._categories.clear()

        self._tags.clear()