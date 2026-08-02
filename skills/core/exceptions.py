"""
Omnix V5 Skill Exceptions

Custom exceptions used by the Skill Framework.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from typing import Any


class SkillError(Exception):
    """
    Base exception for all skill-related errors.
    """

    def __init__(
        self,
        message: str,
        *,
        skill: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)

        self.message = message
        self.skill = skill
        self.details = details or {}

    def __str__(self) -> str:
        if self.skill:
            return f"[{self.skill}] {self.message}"
        return self.message


# =====================================================
# Loading
# =====================================================

class SkillLoadError(SkillError):
    """Raised when a skill cannot be loaded."""


class SkillRegistrationError(SkillError):
    """Raised when registration fails."""


class SkillNotFoundError(SkillError):
    """Raised when a requested skill does not exist."""


# =====================================================
# Validation
# =====================================================

class SkillValidationError(SkillError):
    """Raised when validation fails."""


class SkillDependencyError(SkillError):
    """Raised when dependencies are missing."""


class SkillPermissionError(SkillError):
    """Raised when permissions are insufficient."""


class SkillConfigurationError(SkillError):
    """Raised when configuration is invalid."""


# =====================================================
# Execution
# =====================================================

class SkillExecutionError(SkillError):
    """Raised when execution fails."""


class SkillTimeoutError(SkillError):
    """Raised when execution exceeds timeout."""


class SkillCancelledError(SkillError):
    """Raised when execution is cancelled."""


# =====================================================
# Vision
# =====================================================

class VisionError(SkillExecutionError):
    """Vision service failed."""


class UIElementNotFoundError(VisionError):
    """Requested UI element was not found."""


class OCRFailureError(VisionError):
    """OCR processing failed."""


# =====================================================
# Browser
# =====================================================

class BrowserError(SkillExecutionError):
    """Browser service failed."""


class BrowserNotRunningError(BrowserError):
    """No browser instance available."""


class NavigationError(BrowserError):
    """Navigation failed."""


# =====================================================
# Automation
# =====================================================

class AutomationError(SkillExecutionError):
    """Automation service failed."""


class ApplicationNotFoundError(AutomationError):
    """Requested application not found."""


class WindowNotFoundError(AutomationError):
    """Requested window not found."""


# =====================================================
# Generator
# =====================================================

class SkillGenerationError(SkillError):
    """AI skill generation failed."""


class SkillCompilationError(SkillGenerationError):
    """Generated skill could not be compiled."""


class SkillTestFailedError(SkillGenerationError):
    """Generated skill failed automated tests."""