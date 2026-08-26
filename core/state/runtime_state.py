"""
Omnix V5 - Runtime State

Central runtime state for the currently running Omnix process.

This module stores lightweight, thread-safe state that represents what
Omnix is doing right now.

Examples:
    - Is Omnix running?
    - Is a command currently being processed?
    - Is an agent/task active?
    - What is the current command?
    - What is the current task ID?
    - Has execution been requested to stop?

Important:
    This module intentionally does NOT directly import or control:
        - Vision
        - Skills
        - AI / Brain
        - System services
        - Agent implementations

Those subsystems update runtime state through this API.

This allows the V5 Core to support both new V5 subsystems and legacy
Omnix code without creating circular dependencies.
"""

from __future__ import annotations

import threading
import time

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

# ============================================================================
# RUNTIME STATUS
# ============================================================================


class RuntimeStatus(str, Enum):
    """
    High-level status of the Omnix runtime.
    """

    IDLE = "idle"

    STARTING = "starting"

    RUNNING = "running"

    PROCESSING = "processing"

    EXECUTING = "executing"

    STOPPING = "stopping"

    STOPPED = "stopped"

    ERROR = "error"


# ============================================================================
# RUNTIME SNAPSHOT
# ============================================================================


@dataclass
class RuntimeSnapshot:
    """
    Immutable-style snapshot of the current runtime state.
    """

    status: RuntimeStatus

    is_running: bool

    is_processing: bool

    is_executing: bool

    stop_requested: bool

    current_command: Optional[str]

    current_task_id: Optional[str]

    current_operation: Optional[str]

    started_at: Optional[float]

    updated_at: float

    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def uptime_seconds(self) -> float:
        """
        Return runtime uptime in seconds.
        """

        if self.started_at is None:
            return 0.0

        return max(0.0, time.time() - self.started_at)

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Return a serializable snapshot.
        """

        return {
            "status": self.status.value,
            "is_running": self.is_running,
            "is_processing": self.is_processing,
            "is_executing": self.is_executing,
            "stop_requested": self.stop_requested,
            "current_command": (self.current_command),
            "current_task_id": (self.current_task_id),
            "current_operation": (self.current_operation),
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "uptime_seconds": (self.uptime_seconds),
            "metadata": dict(self.metadata),
        }


# ============================================================================
# RUNTIME STATE
# ============================================================================


class RuntimeState:
    """
    Thread-safe runtime state manager for Omnix.

    RuntimeState is intended to be the single source of truth for the
    current execution state of the Omnix process.

    Example:

        runtime = RuntimeState()

        runtime.start()

        runtime.begin_processing(
            "Open Chrome"
        )

        runtime.begin_execution(
            task_id="task_123"
        )

        ...

        runtime.finish_execution()

        runtime.finish_processing()

    Legacy compatibility:

        The old Core used independent flags such as:

            GoalExecutor.running

        V5 code can instead use:

            runtime.is_running
            runtime.stop_requested
            runtime.is_executing

        This makes shutdown and execution state easier to coordinate.
    """

    def __init__(
        self,
    ) -> None:

        self._status = RuntimeStatus.IDLE

        self._is_running = False

        self._is_processing = False

        self._is_executing = False

        self._stop_requested = False

        self._current_command: Optional[str] = None

        self._current_task_id: Optional[str] = None

        self._current_operation: Optional[str] = None

        self._started_at: Optional[float] = None

        self._updated_at = time.time()

        self._metadata: Dict[str, Any] = {}

        self._lock = threading.RLock()

    # ========================================================================
    # LIFECYCLE
    # ========================================================================

    def start(
        self,
    ) -> None:
        """
        Mark the Omnix runtime as started.
        """

        with self._lock:

            if self._is_running:
                return

            self._status = RuntimeStatus.STARTING

            self._is_running = True

            self._is_processing = False

            self._is_executing = False

            self._stop_requested = False

            self._current_command = None

            self._current_task_id = None

            self._current_operation = None

            self._started_at = time.time()

            self._updated_at = self._started_at

            self._status = RuntimeStatus.RUNNING

    def stop(
        self,
    ) -> None:
        """
        Stop the runtime and clear active execution state.
        """

        with self._lock:

            self._status = RuntimeStatus.STOPPING

            self._is_running = False

            self._is_processing = False

            self._is_executing = False

            self._stop_requested = True

            self._current_command = None

            self._current_task_id = None

            self._current_operation = None

            self._status = RuntimeStatus.STOPPED

            self._touch()

    def reset(
        self,
    ) -> None:
        """
        Reset runtime state to its initial state.

        This does not delete metadata unless clear_metadata()
        is called separately.
        """

        with self._lock:

            self._status = RuntimeStatus.IDLE

            self._is_running = False

            self._is_processing = False

            self._is_executing = False

            self._stop_requested = False

            self._current_command = None

            self._current_task_id = None

            self._current_operation = None

            self._started_at = None

            self._touch()

    # ========================================================================
    # COMMAND PROCESSING
    # ========================================================================

    def begin_processing(
        self,
        command: Optional[str] = None,
    ) -> None:
        """
        Mark command processing as active.
        """

        with self._lock:

            self._ensure_running()

            self._is_processing = True

            self._current_operation = "processing"

            if command is not None:

                self._current_command = self._normalize_text(command)

            if not self._is_executing:

                self._status = RuntimeStatus.PROCESSING

            self._touch()

    def finish_processing(
        self,
        *,
        clear_command: bool = False,
    ) -> None:
        """
        Mark command processing as complete.
        """

        with self._lock:

            self._is_processing = False

            if clear_command:

                self._current_command = None

            if not self._is_executing:

                self._current_operation = None

                self._update_idle_status()

            self._touch()

    # ========================================================================
    # TASK EXECUTION
    # ========================================================================

    def begin_execution(
        self,
        task_id: Optional[str] = None,
        *,
        operation: Optional[str] = None,
    ) -> None:
        """
        Mark task or agent execution as active.
        """

        with self._lock:

            self._ensure_running()

            self._is_executing = True

            self._stop_requested = False

            self._status = RuntimeStatus.EXECUTING

            if task_id is not None:

                self._current_task_id = self._normalize_text(task_id)

            self._current_operation = (
                self._normalize_text(operation) if operation else "executing"
            )

            self._touch()

    def finish_execution(
        self,
        *,
        clear_task: bool = True,
    ) -> None:
        """
        Mark execution as complete.
        """

        with self._lock:

            self._is_executing = False

            if clear_task:

                self._current_task_id = None

            if not self._is_processing:

                self._current_operation = None

                self._update_idle_status()

            else:

                self._status = RuntimeStatus.PROCESSING

            self._touch()

    # ========================================================================
    # STOP CONTROL
    # ========================================================================

    def request_stop(
        self,
    ) -> None:
        """
        Request cancellation of the active operation.

        Execution components should periodically check:

            runtime.stop_requested

        This supports safe cancellation without directly coupling
        RuntimeState to AgentController or GoalExecutor.
        """

        with self._lock:

            self._stop_requested = True

            if self._is_running:

                self._status = RuntimeStatus.STOPPING

            self._touch()

    def clear_stop_request(
        self,
    ) -> None:
        """
        Clear a previous stop request.
        """

        with self._lock:

            self._stop_requested = False

            self._update_idle_status()

            self._touch()

    # ========================================================================
    # ERROR STATE
    # ========================================================================

    def set_error(
        self,
        error: Optional[Any] = None,
    ) -> None:
        """
        Mark the runtime as being in an error state.

        The error itself is stored as metadata rather than introducing
        a dependency on a specific error model.
        """

        with self._lock:

            self._status = RuntimeStatus.ERROR

            if error is not None:

                self._metadata["last_error"] = str(error)

            self._touch()

    def clear_error(
        self,
    ) -> None:
        """
        Clear the current error status.
        """

        with self._lock:

            self._metadata.pop(
                "last_error",
                None,
            )

            self._update_idle_status()

            self._touch()

    # ========================================================================
    # CURRENT VALUES
    # ========================================================================

    def set_current_command(
        self,
        command: Optional[str],
    ) -> None:
        """
        Update the current command.
        """

        with self._lock:

            self._current_command = (
                self._normalize_text(command) if command is not None else None
            )

            self._touch()

    def set_current_task(
        self,
        task_id: Optional[str],
    ) -> None:
        """
        Update the current task ID.
        """

        with self._lock:

            self._current_task_id = (
                self._normalize_text(task_id) if task_id is not None else None
            )

            self._touch()

    def set_operation(
        self,
        operation: Optional[str],
    ) -> None:
        """
        Update the current runtime operation.
        """

        with self._lock:

            self._current_operation = (
                self._normalize_text(operation) if operation is not None else None
            )

            self._touch()

    # ========================================================================
    # METADATA
    # ========================================================================

    def set_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Store runtime metadata.
        """

        key = self._normalize_key(key)

        with self._lock:

            self._metadata[key] = value

            self._touch()

    def get_metadata(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Get runtime metadata.
        """

        key = self._normalize_key(key)

        with self._lock:

            return self._metadata.get(
                key,
                default,
            )

    def remove_metadata(
        self,
        key: str,
    ) -> bool:
        """
        Remove a metadata value.
        """

        key = self._normalize_key(key)

        with self._lock:

            if key not in self._metadata:

                return False

            del self._metadata[key]

            self._touch()

            return True

    def clear_metadata(
        self,
    ) -> None:
        """
        Remove all runtime metadata.
        """

        with self._lock:

            self._metadata.clear()

            self._touch()

    # ========================================================================
    # SNAPSHOT
    # ========================================================================

    def snapshot(
        self,
    ) -> RuntimeSnapshot:
        """
        Return a safe snapshot of current runtime state.
        """

        with self._lock:

            return RuntimeSnapshot(
                status=self._status,
                is_running=self._is_running,
                is_processing=(self._is_processing),
                is_executing=(self._is_executing),
                stop_requested=(self._stop_requested),
                current_command=(self._current_command),
                current_task_id=(self._current_task_id),
                current_operation=(self._current_operation),
                started_at=(self._started_at),
                updated_at=(self._updated_at),
                metadata=dict(self._metadata),
            )

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Return current runtime state as a dictionary.
        """

        return self.snapshot().to_dict()

    # ========================================================================
    # PROPERTIES
    # ========================================================================

    @property
    def status(
        self,
    ) -> RuntimeStatus:

        with self._lock:

            return self._status

    @property
    def is_running(
        self,
    ) -> bool:

        with self._lock:

            return self._is_running

    @property
    def is_processing(
        self,
    ) -> bool:

        with self._lock:

            return self._is_processing

    @property
    def is_executing(
        self,
    ) -> bool:

        with self._lock:

            return self._is_executing

    @property
    def stop_requested(
        self,
    ) -> bool:

        with self._lock:

            return self._stop_requested

    @property
    def current_command(
        self,
    ) -> Optional[str]:

        with self._lock:

            return self._current_command

    @property
    def current_task_id(
        self,
    ) -> Optional[str]:

        with self._lock:

            return self._current_task_id

    @property
    def current_operation(
        self,
    ) -> Optional[str]:

        with self._lock:

            return self._current_operation

    @property
    def started_at(
        self,
    ) -> Optional[float]:

        with self._lock:

            return self._started_at

    @property
    def uptime_seconds(
        self,
    ) -> float:

        with self._lock:

            if self._started_at is None:

                return 0.0

            return max(0.0, time.time() - self._started_at)

    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================

    def _ensure_running(
        self,
    ) -> None:
        """
        Automatically start the runtime when needed.
        """

        if not self._is_running:

            self._is_running = True

            self._stop_requested = False

            self._started_at = time.time()

            self._status = RuntimeStatus.RUNNING

    def _update_idle_status(
        self,
    ) -> None:
        """
        Restore the appropriate non-active status.
        """

        if not self._is_running:

            self._status = RuntimeStatus.STOPPED

            return

        if self._stop_requested:

            self._status = RuntimeStatus.STOPPING

            return

        if self._is_executing:

            self._status = RuntimeStatus.EXECUTING

            return

        if self._is_processing:

            self._status = RuntimeStatus.PROCESSING

            return

        self._status = RuntimeStatus.RUNNING

    def _touch(
        self,
    ) -> None:
        """
        Update the last modification timestamp.
        """

        self._updated_at = time.time()

    @staticmethod
    def _normalize_text(
        value: Any,
    ) -> str:
        """
        Convert and normalize text values.
        """

        return str(value).strip()

    @staticmethod
    def _normalize_key(
        key: Any,
    ) -> str:
        """
        Validate metadata keys.
        """

        key = str(key).strip()

        if not key:

            raise ValueError("Metadata key cannot be empty.")

        return key


# ============================================================================
# GLOBAL RUNTIME STATE
# ============================================================================


_default_runtime_state = RuntimeState()


def get_runtime_state() -> RuntimeState:
    """
    Return the default Omnix runtime state.

    Most of Omnix can use this shared runtime instance:

        from core.state.runtime_state import (
            get_runtime_state,
        )

        runtime = get_runtime_state()
    """

    return _default_runtime_state


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "RuntimeStatus",
    "RuntimeSnapshot",
    "RuntimeState",
    "get_runtime_state",
]
