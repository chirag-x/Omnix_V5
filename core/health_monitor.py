"""
Omnix V5 - Health Monitor

Provides centralized health monitoring for the Omnix runtime.

Responsibilities:
    - Register health-check providers
    - Check individual services
    - Check the complete Omnix system
    - Support synchronous and simple callable checks
    - Track failures and recovery
    - Maintain health history
    - Provide diagnostics for UI and OmnixEngine
    - Support legacy and V5 subsystems

Typical monitored subsystems:
    - system
    - context
    - memory
    - brain / ai
    - vision
    - skills
    - automation
    - voice
    - ui
    - agent
"""

from __future__ import annotations

import inspect
import logging
import threading
import time

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("omnix.core.health_monitor")


# ============================================================================
# ENUMS
# ============================================================================


class HealthStatus(str, Enum):
    """
    Health state of a component.
    """

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNAVAILABLE = "unavailable"
    STARTING = "starting"
    STOPPING = "stopping"


# ============================================================================
# EXCEPTIONS
# ============================================================================


class HealthMonitorError(Exception):
    """Base exception for HealthMonitor errors."""


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class HealthCheck:
    """
    Definition of a health check.

    The callback may return:

        True
        False
        None
        HealthStatus
        dict
    """

    name: str

    callback: Optional[Callable[..., Any]] = None

    required: bool = False

    timeout: Optional[float] = None

    enabled: bool = True

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentHealth:
    """
    Current health information for one component.
    """

    name: str

    status: HealthStatus = HealthStatus.UNKNOWN

    healthy: bool = False

    required: bool = False

    message: Optional[str] = None

    error: Optional[str] = None

    details: Dict[str, Any] = field(default_factory=dict)

    last_check: Optional[float] = None

    last_healthy: Optional[float] = None

    consecutive_failures: int = 0

    total_checks: int = 0

    total_failures: int = 0

    duration: float = 0.0


@dataclass
class HealthReport:
    """
    Full system health report.
    """

    status: HealthStatus

    healthy: bool

    components: Dict[str, ComponentHealth] = field(default_factory=dict)

    checked_at: float = field(default_factory=time.time)

    duration: float = 0.0

    required_failures: List[str] = field(default_factory=list)

    optional_failures: List[str] = field(default_factory=list)


# ============================================================================
# HEALTH MONITOR
# ============================================================================


class HealthMonitor:
    """
    Central health monitoring system for Omnix V5.

    Example:

        monitor = HealthMonitor()

        monitor.register(
            "vision",
            lambda: vision.is_ready(),
            required=False,
        )

        monitor.register_component(
            "memory",
            memory_system,
            required=True,
        )

        report = monitor.check_all()
    """

    def __init__(
        self,
        *,
        history_limit: int = 100,
    ) -> None:

        self._checks: Dict[str, HealthCheck] = {}

        self._health: Dict[str, ComponentHealth] = {}

        self._history: List[HealthReport] = []

        self._history_limit = max(
            1,
            history_limit,
        )

        self._lock = threading.RLock()

        self._started_at = time.time()

        logger.debug("HealthMonitor initialized")

    # ========================================================================
    # REGISTRATION
    # ========================================================================

    def register(
        self,
        name: str,
        callback: Optional[Callable[..., Any]] = None,
        *,
        required: bool = False,
        timeout: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        replace: bool = False,
    ) -> None:
        """
        Register a health check.

        If callback is None, the component can still
        have its health updated manually using:

            set_status()
            mark_healthy()
            mark_unhealthy()
        """

        self._validate_name(name)

        if callback is not None and not callable(callback):
            raise TypeError(f"Health callback for '{name}' " f"must be callable.")

        with self._lock:

            if name in self._checks and not replace:
                raise HealthMonitorError(
                    f"Health check '{name}' " f"is already registered."
                )

            self._checks[name] = HealthCheck(
                name=name,
                callback=callback,
                required=required,
                timeout=timeout,
                metadata=dict(metadata or {}),
            )

            existing = self._health.get(name)

            if existing is None:

                self._health[name] = ComponentHealth(
                    name=name,
                    required=required,
                )

            else:
                existing.required = required

        logger.debug(
            "Registered health check '%s' " "(required=%s)",
            name,
            required,
        )

    def unregister(
        self,
        name: str,
    ) -> bool:
        """
        Remove a health check.
        """

        with self._lock:

            if name not in self._checks:
                return False

            self._checks.pop(
                name,
                None,
            )

            self._health.pop(
                name,
                None,
            )

        return True

    # ========================================================================
    # COMPONENT COMPATIBILITY
    # ========================================================================

    def register_component(
        self,
        name: str,
        component: Any,
        *,
        required: bool = False,
        replace: bool = False,
    ) -> None:
        """
        Register a V5 or legacy component automatically.

        Supported health methods:

            health_check()
            health_status()
            is_healthy()
            is_ready()
            status()

        If none are available, component existence
        itself is considered the health signal.
        """

        callback = self._create_component_check(component)

        self.register(
            name,
            callback,
            required=required,
            replace=replace,
        )

    def _create_component_check(
        self,
        component: Any,
    ) -> Callable[..., Any]:
        """
        Build a compatible health callback for
        old and new Omnix components.
        """

        method_names = (
            "health_check",
            "health_status",
            "is_healthy",
            "is_ready",
            "status",
        )

        for method_name in method_names:

            method = getattr(
                component,
                method_name,
                None,
            )

            if callable(method):
                return method

        return lambda: component is not None

    # ========================================================================
    # INDIVIDUAL CHECKING
    # ========================================================================

    def check(
        self,
        name: str,
    ) -> ComponentHealth:
        """
        Run one health check.
        """

        with self._lock:

            check = self._checks.get(name)

            health = self._health.get(name)

            if health is None:

                raise HealthMonitorError(f"Unknown health component " f"'{name}'.")

            if check is None:
                return health

            if not check.enabled:

                health.status = HealthStatus.UNKNOWN

                health.healthy = False

                health.message = "Health check is disabled."

                return health

            callback = check.callback

        if callback is None:

            return self.get_component_health(name)

        started_at = time.perf_counter()

        try:

            result = self._invoke_check(callback)

            duration = time.perf_counter() - started_at

            status, healthy, message, details = self._normalize_result(result)

            if check.timeout is not None and duration > check.timeout:

                status = HealthStatus.DEGRADED

                healthy = False

                timeout_message = (
                    f"Health check exceeded "
                    f"{check.timeout:.2f}s timeout "
                    f"({duration:.2f}s)."
                )

                if message:
                    message = f"{message} " f"{timeout_message}"
                else:
                    message = timeout_message

            return self._update_health(
                name=name,
                status=status,
                healthy=healthy,
                message=message,
                details=details,
                duration=duration,
                error=None,
            )

        except Exception as exc:

            duration = time.perf_counter() - started_at

            logger.exception(
                "Health check failed for '%s'",
                name,
            )

            return self._update_health(
                name=name,
                status=HealthStatus.UNHEALTHY,
                healthy=False,
                message="Health check failed.",
                details={},
                duration=duration,
                error=str(exc),
            )

    # ========================================================================
    # FULL SYSTEM CHECK
    # ========================================================================

    def check_all(
        self,
    ) -> HealthReport:
        """
        Run all registered health checks.
        """

        started_at = time.perf_counter()

        with self._lock:

            names = list(self._checks.keys())

        components: Dict[str, ComponentHealth] = {}

        required_failures: List[str] = []
        optional_failures: List[str] = []

        for name in names:

            health = self.check(name)

            components[name] = health

            if not health.healthy:

                if health.required:

                    required_failures.append(name)

                else:

                    optional_failures.append(name)

        if required_failures:

            status = HealthStatus.UNHEALTHY
            healthy = False

        elif optional_failures:

            status = HealthStatus.DEGRADED
            healthy = True

        elif components:

            status = HealthStatus.HEALTHY
            healthy = True

        else:

            status = HealthStatus.UNKNOWN
            healthy = False

        report = HealthReport(
            status=status,
            healthy=healthy,
            components=components,
            duration=(time.perf_counter() - started_at),
            required_failures=required_failures,
            optional_failures=optional_failures,
        )

        with self._lock:

            self._history.append(report)

            if len(self._history) > self._history_limit:

                self._history = self._history[-self._history_limit :]

        return report

    # ========================================================================
    # MANUAL STATUS MANAGEMENT
    # ========================================================================

    def set_status(
        self,
        name: str,
        status: HealthStatus,
        *,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> ComponentHealth:
        """
        Manually update component health.
        """

        healthy = status == HealthStatus.HEALTHY

        return self._update_health(
            name=name,
            status=status,
            healthy=healthy,
            message=message,
            details=dict(details or {}),
            duration=0.0,
            error=error,
        )

    def mark_healthy(
        self,
        name: str,
        *,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> ComponentHealth:
        """
        Mark a component healthy.
        """

        return self.set_status(
            name,
            HealthStatus.HEALTHY,
            message=message,
            details=details,
        )

    def mark_degraded(
        self,
        name: str,
        *,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> ComponentHealth:
        """
        Mark a component degraded.
        """

        return self.set_status(
            name,
            HealthStatus.DEGRADED,
            message=message,
            details=details,
        )

    def mark_unhealthy(
        self,
        name: str,
        *,
        message: Optional[str] = None,
        error: Optional[str] = None,
    ) -> ComponentHealth:
        """
        Mark a component unhealthy.
        """

        return self.set_status(
            name,
            HealthStatus.UNHEALTHY,
            message=message,
            error=error,
        )

    # ========================================================================
    # INTERNAL HEALTH UPDATE
    # ========================================================================

    def _update_health(
        self,
        *,
        name: str,
        status: HealthStatus,
        healthy: bool,
        message: Optional[str],
        details: Dict[str, Any],
        duration: float,
        error: Optional[str],
    ) -> ComponentHealth:
        """
        Update and return component health.
        """

        with self._lock:

            health = self._health.get(name)

            if health is None:

                check = self._checks.get(name)

                required = check.required if check is not None else False

                health = ComponentHealth(
                    name=name,
                    required=required,
                )

                self._health[name] = health

            now = time.time()

            health.status = status
            health.healthy = healthy
            health.message = message
            health.details = dict(details)
            health.error = error
            health.duration = duration
            health.last_check = now

            health.total_checks += 1

            if healthy:

                health.last_healthy = now
                health.consecutive_failures = 0

            else:

                health.total_failures += 1
                health.consecutive_failures += 1

            return health

    # ========================================================================
    # RESULT NORMALIZATION
    # ========================================================================

    @staticmethod
    def _normalize_result(
        result: Any,
    ) -> tuple[
        HealthStatus,
        bool,
        Optional[str],
        Dict[str, Any],
    ]:
        """
        Convert different health-check return styles
        into a consistent result.
        """

        if isinstance(
            result,
            ComponentHealth,
        ):

            return (
                result.status,
                result.healthy,
                result.message,
                dict(result.details),
            )

        if isinstance(
            result,
            HealthStatus,
        ):

            healthy = result == HealthStatus.HEALTHY

            return (
                result,
                healthy,
                None,
                {},
            )

        if isinstance(result, bool):

            return (
                (HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY),
                result,
                None,
                {},
            )

        if result is None:

            return (
                HealthStatus.HEALTHY,
                True,
                None,
                {},
            )

        if isinstance(result, dict):

            raw_status = result.get("status")

            raw_healthy = result.get("healthy")

            status = HealthStatus.UNKNOWN

            if isinstance(
                raw_status,
                HealthStatus,
            ):

                status = raw_status

            elif isinstance(
                raw_status,
                str,
            ):

                try:

                    status = HealthStatus(raw_status.lower())

                except ValueError:

                    status = HealthStatus.UNKNOWN

            if raw_healthy is None:

                healthy = status == HealthStatus.HEALTHY

                if status == HealthStatus.UNKNOWN:

                    healthy = bool(
                        result.get(
                            "ok",
                            False,
                        )
                    )

                    status = HealthStatus.HEALTHY if healthy else HealthStatus.UNHEALTHY

            else:

                healthy = bool(raw_healthy)

                if status == HealthStatus.UNKNOWN:

                    status = HealthStatus.HEALTHY if healthy else HealthStatus.UNHEALTHY

            details = dict(result)

            details.pop(
                "status",
                None,
            )

            details.pop(
                "healthy",
                None,
            )

            details.pop(
                "message",
                None,
            )

            details.pop(
                "error",
                None,
            )

            return (
                status,
                healthy,
                result.get("message"),
                details,
            )

        return (
            HealthStatus.HEALTHY,
            bool(result),
            None,
            {},
        )

    # ========================================================================
    # CALLBACK INVOCATION
    # ========================================================================

    def _invoke_check(
        self,
        callback: Callable[..., Any],
    ) -> Any:
        """
        Execute a health callback.

        Supported forms:

            callback()

            callback(monitor)

            callback(health_monitor)
        """

        try:

            signature = inspect.signature(callback)

            parameters = [
                parameter
                for parameter in signature.parameters.values()
                if parameter.kind
                not in (
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                )
            ]

        except (
            TypeError,
            ValueError,
        ):

            result = callback()

            return self._validate_result(result)

        if not parameters:

            result = callback()

            return self._validate_result(result)

        kwargs: Dict[str, Any] = {}

        for parameter in parameters:

            if parameter.name in (
                "monitor",
                "health_monitor",
                "health",
            ):

                kwargs[parameter.name] = self

            elif parameter.default is inspect.Parameter.empty:

                raise HealthMonitorError(
                    f"Cannot resolve health check " f"parameter " f"'{parameter.name}'."
                )

        result = callback(**kwargs)

        return self._validate_result(result)

    @staticmethod
    def _validate_result(
        result: Any,
    ) -> Any:
        """
        Reject async health results.

        Async monitoring will later belong to a
        dedicated background monitoring layer.
        """

        if inspect.isawaitable(result):

            raise HealthMonitorError(
                "Async health checks are not supported "
                "by the synchronous HealthMonitor."
            )

        return result

    # ========================================================================
    # STATUS ACCESS
    # ========================================================================

    def get_component_health(
        self,
        name: str,
    ) -> ComponentHealth:
        """
        Get the last known health of a component.
        """

        with self._lock:

            health = self._health.get(name)

            if health is None:

                raise HealthMonitorError(f"Unknown component '{name}'.")

            return ComponentHealth(
                name=health.name,
                status=health.status,
                healthy=health.healthy,
                required=health.required,
                message=health.message,
                error=health.error,
                details=dict(health.details),
                last_check=health.last_check,
                last_healthy=health.last_healthy,
                consecutive_failures=(health.consecutive_failures),
                total_checks=(health.total_checks),
                total_failures=(health.total_failures),
                duration=health.duration,
            )

    def get_all_health(
        self,
    ) -> Dict[str, ComponentHealth]:
        """
        Return the latest health state of all components.
        """

        with self._lock:

            names = list(self._health.keys())

        return {name: self.get_component_health(name) for name in names}

    def get_history(
        self,
        *,
        limit: Optional[int] = None,
    ) -> List[HealthReport]:
        """
        Return health report history.
        """

        with self._lock:

            history = list(self._history)

        if limit is not None:

            return history[-max(0, limit) :]

        return history

    # ========================================================================
    # ENABLE / DISABLE
    # ========================================================================

    def enable(
        self,
        name: str,
        enabled: bool = True,
    ) -> bool:
        """
        Enable or disable a health check.
        """

        with self._lock:

            check = self._checks.get(name)

            if check is None:
                return False

            check.enabled = enabled

            return True

    # ========================================================================
    # DIAGNOSTICS
    # ========================================================================

    def diagnostics(
        self,
    ) -> Dict[str, Any]:
        """
        Return health-monitor diagnostics.
        """

        with self._lock:

            components = {}

            for name, health in self._health.items():

                components[name] = {
                    "status": (health.status.value),
                    "healthy": health.healthy,
                    "required": health.required,
                    "message": health.message,
                    "error": health.error,
                    "details": dict(health.details),
                    "last_check": (health.last_check),
                    "last_healthy": (health.last_healthy),
                    "consecutive_failures": (health.consecutive_failures),
                    "total_checks": (health.total_checks),
                    "total_failures": (health.total_failures),
                    "duration": (health.duration),
                }

            return {
                "uptime": (time.time() - self._started_at),
                "component_count": len(components),
                "components": components,
                "history_count": len(self._history),
            }

    # ========================================================================
    # HELPERS
    # ========================================================================

    @staticmethod
    def _validate_name(
        name: str,
    ) -> None:

        if not isinstance(name, str) or not name.strip():

            raise ValueError("Health component name must be " "a non-empty string.")

    def __contains__(
        self,
        name: str,
    ) -> bool:

        with self._lock:

            return name in self._checks

    def __len__(
        self,
    ) -> int:

        with self._lock:

            return len(self._checks)

    def __repr__(
        self,
    ) -> str:

        return f"{self.__class__.__name__}(" f"components={len(self)}" f")"
