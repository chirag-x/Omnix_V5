"""
Omnix V5 Skill Result

Standard result object returned by every skill.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class SkillResult:
    """
    Standard return object for every Omnix skill.
    """

    # -----------------------------
    # Status
    # -----------------------------

    success: bool

    message: str = ""

    # -----------------------------
    # Returned Data
    # -----------------------------

    data: dict[str, Any] = field(default_factory=dict)

    # -----------------------------
    # Error Information
    # -----------------------------

    error: str | None = None

    exception: Exception | None = None

    # -----------------------------
    # Warnings
    # -----------------------------

    warnings: list[str] = field(default_factory=list)

    # -----------------------------
    # Metadata
    # -----------------------------

    execution_time: float = 0.0

    skill_name: str = ""

    timestamp: datetime = field(default_factory=datetime.utcnow)

    # -----------------------------
    # Helper Properties
    # -----------------------------

    @property
    def failed(self) -> bool:
        return not self.success

    # -----------------------------
    # Factory Methods
    # -----------------------------

    @classmethod
    def success_result(
        cls,
        message: str = "",
        data: dict[str, Any] | None = None,
        execution_time: float = 0.0,
        skill_name: str = "",
    ) -> "SkillResult":

        return cls(
            success=True,
            message=message,
            data=data or {},
            execution_time=execution_time,
            skill_name=skill_name,
        )

    @classmethod
    def failure(
        cls,
        message: str = "",
        error: str | None = None,
        exception: Exception | None = None,
        execution_time: float = 0.0,
        skill_name: str = "",
    ) -> "SkillResult":

        return cls(
            success=False,
            message=message,
            error=error or message,
            exception=exception,
            execution_time=execution_time,
            skill_name=skill_name,
        )

    # -----------------------------
    # Utility
    # -----------------------------

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)

    def update_data(self, **kwargs: Any) -> None:
        self.data.update(kwargs)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert result to JSON-safe dictionary.
        """

        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error": self.error,
            "warnings": self.warnings,
            "execution_time": self.execution_time,
            "skill_name": self.skill_name,
            "timestamp": self.timestamp.isoformat(),
        }

    def __bool__(self) -> bool:
        return self.success

    def __str__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return f"[{status}] {self.message}"