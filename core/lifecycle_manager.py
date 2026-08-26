"""
Omnix V5 - Lifecycle Manager

Coordinates the lifecycle of the Omnix runtime.

Responsibilities:
    - Startup phases
    - Shutdown phases
    - Lifecycle hooks
    - Ordered callbacks
    - Component initialization
    - Failure tracking
    - Graceful shutdown
    - Legacy lifecycle compatibility

Architecture:

    OmnixEngine
         |
         v
    LifecycleManager
         |
    +----+-----+-----+
    |          |     |
    v          v     v
 Before      Start   After
 Hooks       Phase   Hooks
         |
         v
    EngineManager
         |
         v
      Services
"""

from __future__ import annotations

import inspect
import logging
import threading
import time

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Optional

logger = logging.getLogger("omnix.core.lifecycle_manager")


# ============================================================================
# ENUMS
# ============================================================================


class LifecycleState(str, Enum):
    """Current lifecycle state."""

    CREATED = "created"
    INITIALIZING = "initializing"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class LifecyclePhase(str, Enum):
    """
    Lifecycle execution phases.

    Hooks registered for a phase are executed in priority order.
    """

    PRE_INITIALIZE = "pre_initialize"
    INITIALIZE = "initialize"
    POST_INITIALIZE = "post_initialize"

    PRE_START = "pre_start"
    START = "start"
    POST_START = "post_start"

    PRE_STOP = "pre_stop"
    STOP = "stop"
    POST_STOP = "post_stop"


# ============================================================================
# EXCEPTIONS
# ============================================================================


class LifecycleError(Exception):
    """Base exception for lifecycle errors."""


class LifecycleHookError(LifecycleError):
    """Raised when a required lifecycle hook fails."""


class InvalidLifecycleStateError(LifecycleError):
    """Raised when an operation is invalid in the current state."""


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class LifecycleHook:
    """
    A registered lifecycle callback.
    """

    name: str
    callback: Callable[..., Any]

    phase: LifecyclePhase

    priority: int = 100

    required: bool = False

    enabled: bool = True

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LifecycleResult:
    """
    Result of executing one lifecycle phase.
    """

    phase: LifecyclePhase

    success: bool = True

    executed: List[str] = field(default_factory=list)

    failed: List[str] = field(default_factory=list)

    errors: Dict[str, str] = field(default_factory=dict)

    duration: float = 0.0


@dataclass
class LifecycleReport:
    """
    Complete lifecycle operation report.
    """

    success: bool

    state: LifecycleState

    phases: List[LifecycleResult] = field(default_factory=list)

    errors: Dict[str, str] = field(default_factory=dict)


# ============================================================================
# LIFECYCLE MANAGER
# ============================================================================


class LifecycleManager:
    """
    Manages Omnix startup and shutdown lifecycle phases.

    This manager does not own services directly.

    Instead, EngineManager or OmnixEngine can be registered as
    lifecycle callbacks.

    Example:

        lifecycle = LifecycleManager()

        lifecycle.register_hook(
            "prepare_runtime",
            prepare_runtime,
            LifecyclePhase.PRE_INITIALIZE,
        )

        lifecycle.initialize()

        lifecycle.start()

        lifecycle.stop()
    """

    def __init__(self) -> None:

        self._hooks: Dict[LifecyclePhase, List[LifecycleHook]] = {
            phase: [] for phase in LifecyclePhase
        }

        self._state = LifecycleState.CREATED

        self._history: List[LifecycleResult] = []

        self._lock = threading.RLock()

        self._started_at: Optional[float] = None
        self._stopped_at: Optional[float] = None

        logger.debug("LifecycleManager initialized")

    # ========================================================================
    # PROPERTIES
    # ========================================================================

    @property
    def state(self) -> LifecycleState:
        """Return the current lifecycle state."""

        with self._lock:
            return self._state

    @property
    def is_running(self) -> bool:
        """Return True when Omnix is operational."""

        return self.state in (
            LifecycleState.RUNNING,
            LifecycleState.DEGRADED,
        )

    @property
    def uptime(self) -> Optional[float]:
        """
        Return current uptime in seconds.
        """

        with self._lock:

            started_at = self._started_at
            stopped_at = self._stopped_at

        if started_at is None:
            return None

        end_time = stopped_at if stopped_at is not None else time.time()

        return max(
            0.0,
            end_time - started_at,
        )

    # ========================================================================
    # HOOK REGISTRATION
    # ========================================================================

    def register_hook(
        self,
        name: str,
        callback: Callable[..., Any],
        phase: LifecyclePhase,
        *,
        priority: int = 100,
        required: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        replace: bool = False,
    ) -> None:
        """
        Register a lifecycle hook.

        Lower priority values execute first.

        Example:

            lifecycle.register_hook(
                "start_engine",
                engine.start,
                LifecyclePhase.START,
                priority=50,
                required=True,
            )
        """

        self._validate_name(name)

        if not callable(callback):
            raise TypeError(f"Lifecycle hook '{name}' " f"must be callable.")

        with self._lock:

            hooks = self._hooks[phase]

            existing = next(
                (hook for hook in hooks if hook.name == name),
                None,
            )

            if existing is not None:

                if not replace:
                    raise LifecycleError(
                        f"Lifecycle hook '{name}' "
                        f"already exists in phase "
                        f"'{phase.value}'."
                    )

                hooks.remove(existing)

            hook = LifecycleHook(
                name=name,
                callback=callback,
                phase=phase,
                priority=priority,
                required=required,
                metadata=dict(metadata or {}),
            )

            hooks.append(hook)

            hooks.sort(key=lambda item: item.priority)

        logger.debug(
            "Registered lifecycle hook '%s' " "for phase '%s'",
            name,
            phase.value,
        )

    def unregister_hook(
        self,
        name: str,
        phase: Optional[LifecyclePhase] = None,
    ) -> bool:
        """
        Remove a lifecycle hook.

        If phase is None, all phases are searched.
        """

        phases: Iterable[LifecyclePhase]

        if phase is not None:
            phases = [phase]
        else:
            phases = list(LifecyclePhase)

        with self._lock:

            for current_phase in phases:

                hooks = self._hooks[current_phase]

                for hook in list(hooks):

                    if hook.name == name:

                        hooks.remove(hook)

                        logger.debug(
                            "Removed lifecycle hook '%s'",
                            name,
                        )

                        return True

        return False

    def enable_hook(
        self,
        name: str,
        enabled: bool = True,
    ) -> bool:
        """
        Enable or disable a lifecycle hook.
        """

        with self._lock:

            for hooks in self._hooks.values():

                for hook in hooks:

                    if hook.name == name:

                        hook.enabled = enabled

                        return True

        return False

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    def initialize(
        self,
    ) -> LifecycleReport:
        """
        Run initialization lifecycle phases.
        """

        with self._lock:

            self._ensure_state(LifecycleState.CREATED)

            self._state = LifecycleState.INITIALIZING

        phases = [
            LifecyclePhase.PRE_INITIALIZE,
            LifecyclePhase.INITIALIZE,
            LifecyclePhase.POST_INITIALIZE,
        ]

        return self._execute_lifecycle(
            phases,
            success_state=LifecycleState.CREATED,
        )

    # ========================================================================
    # STARTUP
    # ========================================================================

    def start(
        self,
    ) -> LifecycleReport:
        """
        Execute startup lifecycle phases.
        """

        with self._lock:

            if self._state not in (
                LifecycleState.CREATED,
                LifecycleState.INITIALIZING,
            ):

                raise InvalidLifecycleStateError(
                    f"Cannot start lifecycle from " f"'{self._state.value}'."
                )

            self._state = LifecycleState.STARTING

        phases = [
            LifecyclePhase.PRE_START,
            LifecyclePhase.START,
            LifecyclePhase.POST_START,
        ]

        report = self._execute_lifecycle(
            phases,
            success_state=LifecycleState.RUNNING,
        )

        if report.success:

            with self._lock:

                self._started_at = time.time()
                self._stopped_at = None

        return report

    # ========================================================================
    # SHUTDOWN
    # ========================================================================

    def stop(
        self,
    ) -> LifecycleReport:
        """
        Execute graceful shutdown.

        Shutdown attempts all hooks even when one fails.
        """

        with self._lock:

            if self._state in (
                LifecycleState.STOPPED,
                LifecycleState.STOPPING,
            ):

                return LifecycleReport(
                    success=True,
                    state=self._state,
                )

            self._state = LifecycleState.STOPPING

        phases = [
            LifecyclePhase.PRE_STOP,
            LifecyclePhase.STOP,
            LifecyclePhase.POST_STOP,
        ]

        report = self._execute_lifecycle(
            phases,
            success_state=LifecycleState.STOPPED,
            continue_on_error=True,
        )

        with self._lock:
            self._stopped_at = time.time()

        return report

    def restart(
        self,
    ) -> LifecycleReport:
        """
        Stop and restart the lifecycle.

        Hooks remain registered.
        """

        self.stop()

        with self._lock:

            self._state = LifecycleState.CREATED
            self._history.clear()

        initialization = self.initialize()

        if not initialization.success:
            return initialization

        return self.start()

    # ========================================================================
    # PHASE EXECUTION
    # ========================================================================

    def run_phase(
        self,
        phase: LifecyclePhase,
        *,
        continue_on_error: bool = False,
    ) -> LifecycleResult:
        """
        Execute a single lifecycle phase.
        """

        started_at = time.perf_counter()

        result = LifecycleResult(phase=phase)

        with self._lock:

            hooks = list(self._hooks[phase])

        for hook in hooks:

            if not hook.enabled:
                continue

            try:

                self._invoke_hook(hook)

                result.executed.append(hook.name)

                logger.debug(
                    "Lifecycle hook completed: %s",
                    hook.name,
                )

            except Exception as exc:

                message = str(exc)

                result.success = False

                result.failed.append(hook.name)

                result.errors[hook.name] = message

                logger.exception(
                    "Lifecycle hook failed: %s",
                    hook.name,
                )

                if hook.required:

                    if not continue_on_error:
                        break

        result.duration = time.perf_counter() - started_at

        with self._lock:

            self._history.append(result)

        return result

    def _execute_lifecycle(
        self,
        phases: Iterable[LifecyclePhase],
        *,
        success_state: LifecycleState,
        continue_on_error: bool = False,
    ) -> LifecycleReport:
        """
        Execute multiple lifecycle phases.
        """

        phase_results: List[LifecycleResult] = []

        errors: Dict[str, str] = {}

        success = True

        for phase in phases:

            result = self.run_phase(
                phase,
                continue_on_error=continue_on_error,
            )

            phase_results.append(result)

            if not result.success:

                success = False

                errors.update(result.errors)

                if not continue_on_error:

                    break

        with self._lock:

            if success:

                self._state = success_state

            elif continue_on_error:

                if success_state in (
                    LifecycleState.RUNNING,
                    LifecycleState.STOPPED,
                ):

                    self._state = (
                        LifecycleState.DEGRADED
                        if success_state == LifecycleState.RUNNING
                        else LifecycleState.STOPPED
                    )

                else:

                    self._state = LifecycleState.DEGRADED

            else:

                self._state = LifecycleState.FAILED

            state = self._state

        return LifecycleReport(
            success=success,
            state=state,
            phases=phase_results,
            errors=errors,
        )

    # ========================================================================
    # HOOK INVOCATION
    # ========================================================================

    def _invoke_hook(
        self,
        hook: LifecycleHook,
    ) -> None:
        """
        Invoke a lifecycle hook.

        Supports:

            callback()
            callback(manager)
            callback(lifecycle_manager)

        Async callbacks are detected and rejected here
        because the lifecycle manager deliberately does
        not own an asyncio event loop. Async support can
        later be added through a dedicated runtime layer.
        """

        callback = hook.callback

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

            self._validate_hook_result(
                hook,
                result,
            )

            return

        if not parameters:

            result = callback()

        else:

            kwargs: Dict[str, Any] = {}

            for parameter in parameters:

                if parameter.name in (
                    "manager",
                    "lifecycle_manager",
                    "lifecycle",
                ):

                    kwargs[parameter.name] = self

                elif parameter.default is inspect.Parameter.empty:

                    raise LifecycleHookError(
                        f"Cannot resolve parameter "
                        f"'{parameter.name}' "
                        f"for lifecycle hook "
                        f"'{hook.name}'."
                    )

            result = callback(**kwargs)

        self._validate_hook_result(
            hook,
            result,
        )

    @staticmethod
    def _validate_hook_result(
        hook: LifecycleHook,
        result: Any,
    ) -> None:
        """
        Validate lifecycle hook result.
        """

        if inspect.isawaitable(result):

            raise LifecycleHookError(
                f"Lifecycle hook '{hook.name}' "
                f"returned an awaitable. "
                f"Async lifecycle hooks must be "
                f"handled by the async runtime."
            )

        if result is False:

            raise LifecycleHookError(
                f"Lifecycle hook '{hook.name}' " f"returned False."
            )

    # ========================================================================
    # LEGACY COMPATIBILITY
    # ========================================================================

    def register_component(
        self,
        name: str,
        component: Any,
        *,
        start_phase: LifecyclePhase = (LifecyclePhase.START),
        stop_phase: LifecyclePhase = (LifecyclePhase.STOP),
        required: bool = False,
        priority: int = 100,
    ) -> None:
        """
        Register an old or new Omnix component using
        conventional lifecycle methods.

        Supported startup methods:

            initialize()
            startup()
            start()

        Supported shutdown methods:

            shutdown()
            close()
            stop()
        """

        startup_method = self._find_method(
            component,
            (
                "initialize",
                "startup",
                "start",
            ),
        )

        if startup_method is not None:

            self.register_hook(
                f"{name}.startup",
                startup_method,
                start_phase,
                priority=priority,
                required=required,
            )

        shutdown_method = self._find_method(
            component,
            (
                "shutdown",
                "close",
                "stop",
            ),
        )

        if shutdown_method is not None:

            self.register_hook(
                f"{name}.shutdown",
                shutdown_method,
                stop_phase,
                priority=priority,
                required=False,
            )

    @staticmethod
    def _find_method(
        component: Any,
        method_names: Iterable[str],
    ) -> Optional[Callable[..., Any]]:
        """
        Find the first supported lifecycle method.
        """

        for method_name in method_names:

            method = getattr(
                component,
                method_name,
                None,
            )

            if callable(method):
                return method

        return None

    # ========================================================================
    # INSPECTION
    # ========================================================================

    def get_hooks(
        self,
        phase: Optional[LifecyclePhase] = None,
    ) -> List[LifecycleHook]:
        """
        Return registered hooks.
        """

        with self._lock:

            if phase is not None:

                return list(self._hooks[phase])

            hooks: List[LifecycleHook] = []

            for phase_hooks in self._hooks.values():

                hooks.extend(phase_hooks)

            return hooks

    def get_history(
        self,
    ) -> List[LifecycleResult]:
        """
        Return lifecycle execution history.
        """

        with self._lock:
            return list(self._history)

    def diagnostics(
        self,
    ) -> Dict[str, Any]:
        """
        Return lifecycle diagnostics.
        """

        with self._lock:

            hooks = {
                phase.value: [
                    {
                        "name": hook.name,
                        "priority": hook.priority,
                        "required": hook.required,
                        "enabled": hook.enabled,
                        "metadata": dict(hook.metadata),
                    }
                    for hook in phase_hooks
                ]
                for phase, phase_hooks in self._hooks.items()
            }

            history = [
                {
                    "phase": result.phase.value,
                    "success": result.success,
                    "executed": list(result.executed),
                    "failed": list(result.failed),
                    "errors": dict(result.errors),
                    "duration": result.duration,
                }
                for result in self._history
            ]

            return {
                "state": self._state.value,
                "running": self.is_running,
                "uptime": self.uptime,
                "hooks": hooks,
                "history": history,
            }

    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================

    def _ensure_state(
        self,
        *allowed_states: LifecycleState,
    ) -> None:
        """
        Ensure the current state allows an operation.
        """

        if self._state not in allowed_states:

            allowed = ", ".join(state.value for state in allowed_states)

            raise InvalidLifecycleStateError(
                f"Operation is not allowed while "
                f"state is '{self._state.value}'. "
                f"Allowed states: {allowed}."
            )

    @staticmethod
    def _validate_name(
        name: str,
    ) -> None:

        if not isinstance(name, str) or not name.strip():

            raise ValueError("Lifecycle hook name must be " "a non-empty string.")

    def __repr__(
        self,
    ) -> str:

        return (
            f"{self.__class__.__name__}("
            f"state={self.state.value}, "
            f"hooks={len(self.get_hooks())}"
            f")"
        )
