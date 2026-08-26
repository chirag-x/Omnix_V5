"""
Omnix V5 - Core Error Handling

Central error handling utilities for Omnix V5.

Provides:
    - Structured Omnix exceptions
    - Error categories and severity levels
    - Safe exception conversion
    - Error reports for Core diagnostics
    - Logging integration
    - Optional callbacks/listeners
    - Backward-friendly helper functions

This module does not replace normal Python exceptions. Instead, it
provides a consistent way for Omnix subsystems to classify, report,
and handle errors.
"""

from __future__ import annotations

import logging
import threading
import traceback

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type

from core.utils.logger import get_logger

logger = get_logger("omnix.core.error_handler")


# ============================================================================
# ERROR ENUMS
# ============================================================================


class ErrorSeverity(str, Enum):
    """
    Severity level for an Omnix error.
    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """
    High-level error categories used across Omnix V5.
    """

    UNKNOWN = "unknown"

    CORE = "core"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    INITIALIZATION = "initialization"
    SHUTDOWN = "shutdown"

    SERVICE = "service"
    CAPABILITY = "capability"

    EVENT = "event"
    STATE = "state"

    COMMAND = "command"
    PLANNING = "planning"
    EXECUTION = "execution"
    AGENT = "agent"

    VISION = "vision"
    SKILL = "skill"
    AUTOMATION = "automation"

    AI = "ai"
    MEMORY = "memory"
    CONTEXT = "context"

    VOICE = "voice"
    UI = "ui"
    SYSTEM = "system"

    COMPATIBILITY = "compatibility"
    NETWORK = "network"
    IO = "io"

    TIMEOUT = "timeout"
    VALIDATION = "validation"


# ============================================================================
# BASE OMNIX EXCEPTIONS
# ============================================================================


class OmnixError(Exception):
    """
    Base exception for Omnix V5.

    All Core-specific exceptions may inherit from this class.
    """

    default_category = ErrorCategory.UNKNOWN
    default_severity = ErrorSeverity.ERROR

    def __init__(
        self,
        message: str,
        *,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[BaseException] = None,
    ) -> None:

        super().__init__(message)

        self.message = message

        self.category = category or self.default_category

        self.severity = severity or self.default_severity

        self.context = dict(context or {})

        self.cause = cause


class OmnixCoreError(OmnixError):

    default_category = ErrorCategory.CORE


class ConfigurationError(OmnixError):

    default_category = ErrorCategory.CONFIGURATION


class DependencyError(OmnixError):

    default_category = ErrorCategory.DEPENDENCY


class InitializationError(OmnixError):

    default_category = ErrorCategory.INITIALIZATION


class ShutdownError(OmnixError):

    default_category = ErrorCategory.SHUTDOWN


class ServiceError(OmnixError):

    default_category = ErrorCategory.SERVICE


class CapabilityError(OmnixError):

    default_category = ErrorCategory.CAPABILITY


class EventError(OmnixError):

    default_category = ErrorCategory.EVENT


class StateError(OmnixError):

    default_category = ErrorCategory.STATE


class CommandError(OmnixError):

    default_category = ErrorCategory.COMMAND


class PlanningError(OmnixError):

    default_category = ErrorCategory.PLANNING


class ExecutionError(OmnixError):

    default_category = ErrorCategory.EXECUTION


class AgentError(OmnixError):

    default_category = ErrorCategory.AGENT


class VisionError(OmnixError):

    default_category = ErrorCategory.VISION


class SkillError(OmnixError):

    default_category = ErrorCategory.SKILL


class AutomationError(OmnixError):

    default_category = ErrorCategory.AUTOMATION


class AIError(OmnixError):

    default_category = ErrorCategory.AI


class MemoryError(OmnixError):

    default_category = ErrorCategory.MEMORY


class ContextError(OmnixError):

    default_category = ErrorCategory.CONTEXT


class VoiceError(OmnixError):

    default_category = ErrorCategory.VOICE


class UIError(OmnixError):

    default_category = ErrorCategory.UI


class SystemError(OmnixError):

    default_category = ErrorCategory.SYSTEM


class CompatibilityError(OmnixError):

    default_category = ErrorCategory.COMPATIBILITY


class TimeoutError(OmnixError):

    default_category = ErrorCategory.TIMEOUT


class ValidationError(OmnixError):

    default_category = ErrorCategory.VALIDATION


# ============================================================================
# ERROR REPORT
# ============================================================================


@dataclass
class ErrorReport:
    """
    Structured representation of an error.

    Error reports are useful for:
        - Logging
        - Diagnostics
        - Event reporting
        - Recovery systems
        - UI error displays
    """

    message: str

    category: ErrorCategory = ErrorCategory.UNKNOWN

    severity: ErrorSeverity = ErrorSeverity.ERROR

    exception_type: Optional[str] = None

    source: Optional[str] = None

    timestamp: str = field(
        default_factory=lambda: (datetime.now(timezone.utc).isoformat())
    )

    context: Dict[str, Any] = field(default_factory=dict)

    traceback_text: Optional[str] = None

    cause_type: Optional[str] = None

    cause_message: Optional[str] = None

    recoverable: bool = True

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Convert the report into a serializable dictionary.
        """

        data = asdict(self)

        data["category"] = self.category.value

        data["severity"] = self.severity.value

        return data


# ============================================================================
# ERROR HANDLER
# ============================================================================


ErrorListener = Callable[
    [ErrorReport],
    None,
]


class ErrorHandler:
    """
    Central error handler for Omnix V5.

    The handler converts exceptions into structured ErrorReport objects,
    logs them, stores a bounded error history, and notifies registered
    listeners.

    Example:

        handler = ErrorHandler()

        try:
            ...
        except Exception as exc:
            report = handler.handle(
                exc,
                source="vision_service",
            )
    """

    def __init__(
        self,
        *,
        max_history: int = 500,
        logger_instance: Optional[logging.Logger] = None,
    ) -> None:

        if max_history < 1:

            raise ValueError("max_history must be at least 1.")

        self._max_history = max_history

        self._history: List[ErrorReport] = []

        self._listeners: List[ErrorListener] = []

        self._lock = threading.RLock()

        self._logger = logger_instance or logger

    # ========================================================================
    # HANDLING
    # ========================================================================

    def handle(
        self,
        error: BaseException,
        *,
        source: Optional[str] = None,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
        context: Optional[Dict[str, Any]] = None,
        recoverable: Optional[bool] = None,
        include_traceback: bool = True,
    ) -> ErrorReport:
        """
        Convert and process an exception.

        Returns the generated ErrorReport.
        """

        report = self.create_report(
            error,
            source=source,
            category=category,
            severity=severity,
            context=context,
            recoverable=recoverable,
            include_traceback=(include_traceback),
        )

        self._store(report)

        self._log(report)

        self._notify(report)

        return report

    def create_report(
        self,
        error: BaseException,
        *,
        source: Optional[str] = None,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
        context: Optional[Dict[str, Any]] = None,
        recoverable: Optional[bool] = None,
        include_traceback: bool = True,
    ) -> ErrorReport:
        """
        Create an ErrorReport without storing or logging it.
        """

        if isinstance(
            error,
            OmnixError,
        ):

            resolved_category = category or error.category

            resolved_severity = severity or error.severity

            merged_context = dict(error.context)

            if context:

                merged_context.update(context)

            cause = error.cause

        else:

            resolved_category = category or self._infer_category(error)

            resolved_severity = severity or self._infer_severity(error)

            merged_context = dict(context or {})

            cause = error.__cause__

        if recoverable is None:

            recoverable = self._is_recoverable(
                error,
                resolved_severity,
            )

        traceback_text = None

        if include_traceback:

            traceback_text = "".join(
                traceback.format_exception(
                    type(error),
                    error,
                    error.__traceback__,
                )
            )

        return ErrorReport(
            message=str(error) or error.__class__.__name__,
            category=resolved_category,
            severity=resolved_severity,
            exception_type=(error.__class__.__name__),
            source=source,
            context=merged_context,
            traceback_text=traceback_text,
            cause_type=(cause.__class__.__name__ if cause is not None else None),
            cause_message=(str(cause) if cause is not None else None),
            recoverable=bool(recoverable),
        )

    # ========================================================================
    # HISTORY
    # ========================================================================

    def history(
        self,
        *,
        limit: Optional[int] = None,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
    ) -> List[ErrorReport]:
        """
        Return stored error reports.

        Results can optionally be filtered by category and severity.
        """

        with self._lock:

            reports = list(self._history)

        if category is not None:

            reports = [report for report in reports if report.category == category]

        if severity is not None:

            reports = [report for report in reports if report.severity == severity]

        if limit is not None:

            if limit < 1:

                return []

            reports = reports[-limit:]

        return reports

    def latest(
        self,
    ) -> Optional[ErrorReport]:
        """
        Return the latest stored error.
        """

        with self._lock:

            if not self._history:

                return None

            return self._history[-1]

    def clear_history(
        self,
    ) -> None:
        """
        Remove all stored error reports.
        """

        with self._lock:

            self._history.clear()

    def count(
        self,
        *,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
    ) -> int:
        """
        Count matching errors.
        """

        return len(
            self.history(
                category=category,
                severity=severity,
            )
        )

    # ========================================================================
    # LISTENERS
    # ========================================================================

    def add_listener(
        self,
        listener: ErrorListener,
    ) -> None:
        """
        Register an error listener.
        """

        if not callable(listener):

            raise TypeError("Error listener must be callable.")

        with self._lock:

            if listener not in (self._listeners):

                self._listeners.append(listener)

    def remove_listener(
        self,
        listener: ErrorListener,
    ) -> bool:
        """
        Remove an error listener.
        """

        with self._lock:

            if listener not in (self._listeners):

                return False

            self._listeners.remove(listener)

            return True

    # ========================================================================
    # INTERNAL PROCESSING
    # ========================================================================

    def _store(
        self,
        report: ErrorReport,
    ) -> None:
        """
        Store an error report.
        """

        with self._lock:

            self._history.append(report)

            overflow = len(self._history) - self._max_history

            if overflow > 0:

                del self._history[:overflow]

    def _notify(
        self,
        report: ErrorReport,
    ) -> None:
        """
        Notify registered listeners.

        Listener failures are isolated so an error-reporting callback
        cannot crash the Core.
        """

        with self._lock:

            listeners = list(self._listeners)

        for listener in listeners:

            try:

                listener(report)

            except Exception:

                self._logger.exception("Error listener failed.")

    def _log(
        self,
        report: ErrorReport,
    ) -> None:
        """
        Log an error report according to its severity.
        """

        message = "[%s] %s: %s" % (
            report.category.value,
            report.source or "unknown",
            report.message,
        )

        if report.severity == ErrorSeverity.DEBUG:

            self._logger.debug(message)

        elif report.severity == ErrorSeverity.INFO:

            self._logger.info(message)

        elif report.severity == ErrorSeverity.WARNING:

            self._logger.warning(message)

        elif report.severity == ErrorSeverity.CRITICAL:

            self._logger.critical(message)

        else:

            if report.traceback_text:

                self._logger.error(
                    "%s\n%s",
                    message,
                    report.traceback_text,
                )

            else:

                self._logger.error(message)

    # ========================================================================
    # ERROR INFERENCE
    # ========================================================================

    @staticmethod
    def _infer_category(
        error: BaseException,
    ) -> ErrorCategory:
        """
        Infer a category for standard Python exceptions.
        """

        if isinstance(
            error,
            (ImportError, ModuleNotFoundError),
        ):

            return ErrorCategory.DEPENDENCY

        if isinstance(
            error,
            (ValueError, TypeError, KeyError),
        ):

            return ErrorCategory.VALIDATION

        if isinstance(
            error,
            (FileNotFoundError, PermissionError, OSError),
        ):

            return ErrorCategory.IO

        if isinstance(
            error,
            TimeoutError,
        ):

            return ErrorCategory.TIMEOUT

        return ErrorCategory.UNKNOWN

    @staticmethod
    def _infer_severity(
        error: BaseException,
    ) -> ErrorSeverity:
        """
        Infer a reasonable severity level.
        """

        if isinstance(
            error,
            (SystemExit, KeyboardInterrupt),
        ):

            return ErrorSeverity.CRITICAL

        if isinstance(
            error,
            (
                ImportError,
                ModuleNotFoundError,
                RuntimeError,
            ),
        ):

            return ErrorSeverity.ERROR

        if isinstance(
            error,
            (
                ValueError,
                TypeError,
                KeyError,
            ),
        ):

            return ErrorSeverity.WARNING

        return ErrorSeverity.ERROR

    @staticmethod
    def _is_recoverable(
        error: BaseException,
        severity: ErrorSeverity,
    ) -> bool:
        """
        Determine whether an error is likely recoverable.
        """

        if isinstance(
            error,
            (SystemExit, KeyboardInterrupt),
        ):

            return False

        if severity == ErrorSeverity.CRITICAL:

            return False

        return True


# ============================================================================
# GLOBAL DEFAULT HANDLER
# ============================================================================


_default_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """
    Return the default Core error handler.
    """

    return _default_handler


def handle_error(
    error: BaseException,
    **kwargs: Any,
) -> ErrorReport:
    """
    Handle an exception using the default ErrorHandler.

    Example:

        try:
            ...
        except Exception as exc:
            handle_error(
                exc,
                source="skills_service",
            )
    """

    return _default_handler.handle(
        error,
        **kwargs,
    )


def create_error(
    message: str,
    *,
    error_type: Type[OmnixError] = OmnixError,
    category: Optional[ErrorCategory] = None,
    severity: Optional[ErrorSeverity] = None,
    context: Optional[Dict[str, Any]] = None,
    cause: Optional[BaseException] = None,
) -> OmnixError:
    """
    Create a structured Omnix error.
    """

    return error_type(
        message,
        category=category,
        severity=severity,
        context=context,
        cause=cause,
    )


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorReport",
    "ErrorHandler",
    "OmnixError",
    "OmnixCoreError",
    "ConfigurationError",
    "DependencyError",
    "InitializationError",
    "ShutdownError",
    "ServiceError",
    "CapabilityError",
    "EventError",
    "StateError",
    "CommandError",
    "PlanningError",
    "ExecutionError",
    "AgentError",
    "VisionError",
    "SkillError",
    "AutomationError",
    "AIError",
    "MemoryError",
    "ContextError",
    "VoiceError",
    "UIError",
    "SystemError",
    "CompatibilityError",
    "TimeoutError",
    "ValidationError",
    "get_error_handler",
    "handle_error",
    "create_error",
]
