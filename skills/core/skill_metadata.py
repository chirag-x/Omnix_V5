"""
Omnix V5 Skill Metadata

Defines metadata for every Omnix skill.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SkillMetadata:
    """
    Metadata describing a skill.

    Used by:

    - Skill Loader
    - Registry
    - Validator
    - Planner
    - Skill Generator
    
    """
    # --------------------------------------------------
    # Identity
    # --------------------------------------------------

    id: str

    name: str

    description: str

    version: str = "1.0.0"

    author: str = "Omnix"

    # --------------------------------------------------
    # Organization
    # --------------------------------------------------

    category: str = "general"

    subcategory: str = ""

    tags: list[str] = field(default_factory=list)

    aliases: list[str] = field(default_factory=list)

    # --------------------------------------------------
    # Priority
    # --------------------------------------------------

    priority: int = 100

    enabled: bool = True

    # --------------------------------------------------
    # Requirements
    # --------------------------------------------------

    dependencies: list[str] = field(default_factory=list)

    permissions: list[str] = field(default_factory=list)

    supported_os: list[str] = field(default_factory=lambda: ["windows", "linux", "mac"])

    # --------------------------------------------------
    # AI
    # --------------------------------------------------

    ai_generated: bool = False

    built_in: bool = True

    experimental: bool = False

    # --------------------------------------------------
    # Planner
    # --------------------------------------------------

    supports_parallel_execution: bool = False

    timeout: float = 30.0

    retry_count: int = 0

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    usage_count: int = 0

    success_count: int = 0

    failure_count: int = 0

    average_execution_time: float = 0.0

    # --------------------------------------------------
    # Custom
    # --------------------------------------------------

    extra: dict[str, Any] = field(default_factory=dict)

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    @property
    def success_rate(self) -> float:

        total = self.success_count + self.failure_count

        if total == 0:
            return 0.0

        return (self.success_count / total) * 100

    def increment_success(self) -> None:

        self.usage_count += 1
        self.success_count += 1

    def increment_failure(self) -> None:

        self.usage_count += 1
        self.failure_count += 1

    def supports_platform(self, os_name: str) -> bool:

        return os_name.lower() in (
            supported_platform.lower() for supported_platform in self.supported_os
        )

    def matches(self, query: str) -> bool:
        """
        Used by SkillRegistry search.
        """

        query = query.lower()

        if query == self.name.lower():
            return True

        if query in self.description.lower():
            return True

        if any(query == alias.lower() for alias in self.aliases):
            return True

        if any(query == tag.lower() for tag in self.tags):
            return True

        return False

    def to_dict(self) -> dict[str, Any]:

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "category": self.category,
            "subcategory": self.subcategory,
            "aliases": self.aliases,
            "tags": self.tags,
            "priority": self.priority,
            "enabled": self.enabled,
            "dependencies": self.dependencies,
            "permissions": self.permissions,
            "supported_os": self.supported_os,
            "ai_generated": self.ai_generated,
            "built_in": self.built_in,
            "experimental": self.experimental,
            "supports_parallel_execution": self.supports_parallel_execution,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "usage_count": self.usage_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "average_execution_time": self.average_execution_time,
            "success_rate": self.success_rate,
            "extra": self.extra,
        }
