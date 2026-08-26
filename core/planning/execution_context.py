"""
Omnix V5 - Execution Context

Shared runtime context for command planning and execution.

ExecutionContext represents the state of one command as it moves through
the Omnix V5 pipeline:

    Command
        ↓
    Intent Classification
        ↓
    Target Resolution
        ↓
    Task Planning
        ↓
    Execution
        ↓
    Result / Recovery

The context is intentionally lightweight and subsystem-independent.

It can carry references or metadata for:

    - Planning
    - Agent execution
    - Skills
    - Vision
    - System control
    - Recovery
    - Legacy V4 compatibility

This prevents every subsystem from requiring long parameter lists and
provides one shared state object for a command execution lifecycle.
"""

from __future__ import annotations

import time
import uuid

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .command_schema import Command

# ============================================================================
# EXECUTION STATE
# ============================================================================


class ExecutionState(str, Enum):
    """
    Current state of an Omnix command execution.
    """

    CREATED = "created"

    PREPARING = "preparing"

    READY = "ready"

    PLANNING = "planning"

    PLANNED = "planned"

    EXECUTING = "executing"

    WAITING = "waiting"

    RECOVERING = "recovering"

    COMPLETED = "completed"

    FAILED = "failed"

    CANCELLED = "cancelled"


# ============================================================================
# EXECUTION RESULT
# ============================================================================


@dataclass
class ExecutionResult:
    """
    Represents the result of a single execution step or operation.

    This is intentionally generic so it can be used by:

        - Skills
        - Vision actions
        - System actions
        - Agent actions
        - Legacy actions
    """

    success: bool

    value: Any = None

    message: Optional[str] = None

    error: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    created_at: float = field(default_factory=time.time)

    def __post_init__(
        self,
    ) -> None:
        if not isinstance(
            self.metadata,
            dict,
        ):
            raise TypeError("metadata must be a dictionary.")

        self.metadata = dict(self.metadata)

        if self.message is not None:
            self.message = str(self.message).strip() or None

        if self.error is not None:
            self.error = str(self.error).strip() or None

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Convert the result into a serializable dictionary.
        """

        return {
            "success": self.success,
            "value": self.value,
            "message": self.message,
            "error": self.error,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


# ============================================================================
# EXECUTION CONTEXT
# ============================================================================


@dataclass
class ExecutionContext:
    """
    Shared context for one Omnix command execution.

    Example:

        context = ExecutionContext(
            command=command
        )

        context.set_intent(
            "open_application"
        )

        context.set_target(
            "Chrome"
        )

        context.set_state(
            ExecutionState.EXECUTING
        )
    """

    command: Command

    context_id: str = field(default_factory=lambda: (f"context_{uuid.uuid4().hex}"))

    state: ExecutionState | str = ExecutionState.CREATED

    intent: Optional[str] = None

    target: Any = None

    plan: Any = None

    current_step: int = 0

    results: List[ExecutionResult] = field(default_factory=list)

    errors: List[Dict[str, Any]] = field(default_factory=list)

    data: Dict[str, Any] = field(default_factory=dict)

    metadata: Dict[str, Any] = field(default_factory=dict)

    services: Dict[str, Any] = field(default_factory=dict)

    created_at: float = field(default_factory=time.time)

    updated_at: float = field(default_factory=time.time)

    completed_at: Optional[float] = None

    def __post_init__(
        self,
    ) -> None:
        """
        Normalize and validate context data.
        """

        if not isinstance(
            self.command,
            Command,
        ):
            raise TypeError("command must be a Command instance.")

        self.context_id = self._normalize_context_id(self.context_id)

        self.state = self._normalize_state(self.state)

        self.intent = self._normalize_optional_string(self.intent)

        if not isinstance(
            self.current_step,
            int,
        ):
            raise TypeError("current_step must be an integer.")

        if self.current_step < 0:
            self.current_step = 0

        if not isinstance(
            self.results,
            list,
        ):
            raise TypeError("results must be a list.")

        normalized_results = []

        for result in self.results:

            if isinstance(
                result,
                ExecutionResult,
            ):
                normalized_results.append(result)

            elif isinstance(
                result,
                dict,
            ):
                normalized_results.append(
                    ExecutionResult(
                        success=bool(
                            result.get(
                                "success",
                                False,
                            )
                        ),
                        value=result.get("value"),
                        message=result.get("message"),
                        error=result.get("error"),
                        metadata=dict(
                            result.get(
                                "metadata",
                                {},
                            )
                        ),
                    )
                )

            else:
                raise TypeError(
                    "results must contain " "ExecutionResult or dictionary objects."
                )

        self.results = normalized_results

        self.errors = self._normalize_dict_list(
            self.errors,
            "errors",
        )

        self.data = self._normalize_dict(
            self.data,
            "data",
        )

        self.metadata = self._normalize_dict(
            self.metadata,
            "metadata",
        )

        self.services = self._normalize_dict(
            self.services,
            "services",
        )

    # ====================================================================
    # STATE MANAGEMENT
    # ====================================================================

    def set_state(
        self,
        state: ExecutionState | str,
    ) -> None:
        """
        Update the execution state.
        """

        self.state = self._normalize_state(state)

        self._touch()

        if self.is_finished:
            self.completed_at = time.time()

    def mark_preparing(
        self,
    ) -> None:
        self.set_state(ExecutionState.PREPARING)

    def mark_ready(
        self,
    ) -> None:
        self.set_state(ExecutionState.READY)

    def mark_planning(
        self,
    ) -> None:
        self.set_state(ExecutionState.PLANNING)

    def mark_planned(
        self,
    ) -> None:
        self.set_state(ExecutionState.PLANNED)

    def mark_executing(
        self,
    ) -> None:
        self.set_state(ExecutionState.EXECUTING)

    def mark_waiting(
        self,
    ) -> None:
        self.set_state(ExecutionState.WAITING)

    def mark_recovering(
        self,
    ) -> None:
        self.set_state(ExecutionState.RECOVERING)

    def mark_completed(
        self,
    ) -> None:
        self.set_state(ExecutionState.COMPLETED)

        self.command.mark_completed()

    def mark_failed(
        self,
        error: Any = None,
    ) -> None:
        """
        Mark execution as failed.

        An optional error can also be recorded.
        """

        if error is not None:

            self.add_error(error)

        self.set_state(ExecutionState.FAILED)

        self.command.mark_failed()

    def mark_cancelled(
        self,
    ) -> None:
        self.set_state(ExecutionState.CANCELLED)

        self.command.mark_cancelled()

    # ====================================================================
    # INTENT / TARGET
    # ====================================================================

    def set_intent(
        self,
        intent: Optional[str],
    ) -> None:
        """
        Store the resolved command intent.
        """

        self.intent = self._normalize_optional_string(intent)

        if self.intent is not None:

            self.command.set_intent(self.intent)

        self._touch()

    def set_target(
        self,
        target: Any,
    ) -> None:
        """
        Store the resolved command target.
        """

        self.target = target

        if isinstance(
            target,
            str,
        ):

            normalized = target.strip()

            if normalized:

                self.command.set_target(normalized)

        self._touch()

    # ====================================================================
    # PLAN
    # ====================================================================

    def set_plan(
        self,
        plan: Any,
    ) -> None:
        """
        Attach an execution plan to this context.
        """

        self.plan = plan

        self.current_step = 0

        self._touch()

    def clear_plan(
        self,
    ) -> None:
        """
        Remove the current plan.
        """

        self.plan = None

        self.current_step = 0

        self._touch()

    def set_current_step(
        self,
        step: int,
    ) -> None:
        """
        Update the current plan step.
        """

        if not isinstance(
            step,
            int,
        ):
            raise TypeError("step must be an integer.")

        if step < 0:
            raise ValueError("step cannot be negative.")

        self.current_step = step

        self._touch()

    def advance_step(
        self,
    ) -> int:
        """
        Advance to the next execution step.

        Returns the new step index.
        """

        self.current_step += 1

        self._touch()

        return self.current_step

    # ====================================================================
    # RESULTS
    # ====================================================================

    def add_result(
        self,
        success: bool,
        *,
        value: Any = None,
        message: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Add an execution result.
        """

        result = ExecutionResult(
            success=bool(success),
            value=value,
            message=message,
            error=error,
            metadata=dict(metadata or {}),
        )

        self.results.append(result)

        self._touch()

        return result

    def add_result_object(
        self,
        result: ExecutionResult,
    ) -> None:
        """
        Add an existing ExecutionResult.
        """

        if not isinstance(
            result,
            ExecutionResult,
        ):
            raise TypeError("result must be an ExecutionResult.")

        self.results.append(result)

        self._touch()

    def get_last_result(
        self,
    ) -> Optional[ExecutionResult]:
        """
        Return the latest execution result.
        """

        if not self.results:
            return None

        return self.results[-1]

    @property
    def successful_results(
        self,
    ) -> List[ExecutionResult]:
        """
        Return successful results.
        """

        return [result for result in self.results if result.success]

    @property
    def failed_results(
        self,
    ) -> List[ExecutionResult]:
        """
        Return failed results.
        """

        return [result for result in self.results if not result.success]

    # ====================================================================
    # ERROR MANAGEMENT
    # ====================================================================

    def add_error(
        self,
        error: Any,
        *,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Record an execution error.

        Errors are stored in normalized dictionary form so that
        Recovery, Health, Logging, and legacy systems can consume them.
        """

        error_entry = {
            "message": str(error),
            "error_type": (type(error).__name__),
            "source": (str(source).strip() if source is not None else None),
            "metadata": dict(metadata or {}),
            "timestamp": time.time(),
        }

        self.errors.append(error_entry)

        self._touch()

        return error_entry

    def get_last_error(
        self,
    ) -> Optional[Dict[str, Any]]:
        """
        Return the most recent error.
        """

        if not self.errors:
            return None

        return self.errors[-1]

    def clear_errors(
        self,
    ) -> None:
        """
        Remove all recorded errors.
        """

        self.errors.clear()

        self._touch()

    @property
    def has_errors(
        self,
    ) -> bool:
        return bool(self.errors)

    # ====================================================================
    # SHARED DATA
    # ====================================================================

    def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Store shared runtime data.

        Example:

            context.set(
                "vision_result",
                detection_result
            )
        """

        key = self._normalize_key(key)

        self.data[key] = value

        self._touch()

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Retrieve shared runtime data.
        """

        return self.data.get(
            key,
            default,
        )

    def pop(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Remove and return shared runtime data.
        """

        result = self.data.pop(
            key,
            default,
        )

        self._touch()

        return result

    def update(
        self,
        values: Dict[str, Any],
    ) -> None:
        """
        Update multiple shared values.
        """

        if not isinstance(
            values,
            dict,
        ):
            raise TypeError("values must be a dictionary.")

        self.data.update(values)

        self._touch()

    # ====================================================================
    # METADATA
    # ====================================================================

    def set_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Store context metadata.
        """

        key = self._normalize_key(key)

        self.metadata[key] = value

        self._touch()

    def get_metadata(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Retrieve context metadata.
        """

        return self.metadata.get(
            key,
            default,
        )

    # ====================================================================
    # SERVICE REFERENCES
    # ====================================================================

    def register_service(
        self,
        name: str,
        service: Any,
        *,
        replace: bool = True,
    ) -> None:
        """
        Register a subsystem reference.

        This can hold references to:

            vision
            skills
            agent
            system
            memory
            recovery
            legacy services
        """

        normalized_name = self._normalize_key(name)

        if normalized_name in self.services and not replace:
            raise ValueError(f"Service already exists: " f"{normalized_name}")

        self.services[normalized_name] = service

        self._touch()

    def get_service(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Retrieve a registered subsystem.
        """

        return self.services.get(
            name,
            default,
        )

    def remove_service(
        self,
        name: str,
    ) -> bool:
        """
        Remove a registered subsystem reference.
        """

        if name not in self.services:
            return False

        del self.services[name]

        self._touch()

        return True

    # ====================================================================
    # CONVENIENCE PROPERTIES
    # ====================================================================

    @property
    def is_finished(
        self,
    ) -> bool:
        """
        Return True when execution has ended.
        """

        return self.state in {
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
        }

    @property
    def is_successful(
        self,
    ) -> bool:
        """
        Return True when execution completed successfully.
        """

        return self.state == ExecutionState.COMPLETED

    @property
    def is_failed(
        self,
    ) -> bool:
        """
        Return True when execution failed.
        """

        return self.state == ExecutionState.FAILED

    @property
    def duration(
        self,
    ) -> float:
        """
        Return current or final execution duration.
        """

        end_time = self.completed_at if self.completed_at is not None else time.time()

        return max(
            0.0,
            end_time - self.created_at,
        )

    # ====================================================================
    # SERIALIZATION
    # ====================================================================

    def to_dict(
        self,
        *,
        include_services: bool = False,
    ) -> Dict[str, Any]:
        """
        Convert context into a serializable dictionary.

        Service references are excluded by default because they may
        contain live Python objects.
        """

        data = {
            "context_id": (self.context_id),
            "command": (self.command.to_dict()),
            "state": (self.state.value),
            "intent": self.intent,
            "target": self.target,
            "plan": self.plan,
            "current_step": (self.current_step),
            "results": [result.to_dict() for result in self.results],
            "errors": [dict(error) for error in self.errors],
            "data": dict(self.data),
            "metadata": dict(self.metadata),
            "created_at": (self.created_at),
            "updated_at": (self.updated_at),
            "completed_at": (self.completed_at),
        }

        if include_services:

            data["services"] = dict(self.services)

        return data

    # ====================================================================
    # INTERNAL HELPERS
    # ====================================================================

    def _touch(
        self,
    ) -> None:
        """
        Update the modification timestamp.
        """

        self.updated_at = time.time()

    @staticmethod
    def _normalize_context_id(
        context_id: Any,
    ) -> str:
        """
        Validate context ID.
        """

        value = str(context_id).strip()

        if not value:

            raise ValueError("context_id cannot be empty.")

        return value

    @staticmethod
    def _normalize_state(
        state: ExecutionState | str,
    ) -> ExecutionState:
        """
        Normalize execution state.
        """

        if isinstance(
            state,
            ExecutionState,
        ):
            return state

        try:

            return ExecutionState(str(state).strip().lower())

        except ValueError as error:

            valid = ", ".join(item.value for item in ExecutionState)

            raise ValueError(
                f"Invalid execution state: " f"{state!r}. " f"Valid values: {valid}"
            ) from error

    @staticmethod
    def _normalize_optional_string(
        value: Optional[Any],
    ) -> Optional[str]:
        """
        Normalize an optional string.
        """

        if value is None:
            return None

        result = str(value).strip()

        return result or None

    @staticmethod
    def _normalize_key(
        key: Any,
    ) -> str:
        """
        Validate a dictionary key.
        """

        value = str(key).strip()

        if not value:

            raise ValueError("Key cannot be empty.")

        return value

    @staticmethod
    def _normalize_dict(
        value: Any,
        name: str,
    ) -> Dict[str, Any]:
        """
        Validate dictionary fields.
        """

        if not isinstance(
            value,
            dict,
        ):
            raise TypeError(f"{name} must be a dictionary.")

        return dict(value)

    @staticmethod
    def _normalize_dict_list(
        value: Any,
        name: str,
    ) -> List[Dict[str, Any]]:
        """
        Validate lists containing dictionaries.
        """

        if not isinstance(
            value,
            list,
        ):
            raise TypeError(f"{name} must be a list.")

        normalized = []

        for item in value:

            if not isinstance(
                item,
                dict,
            ):
                raise TypeError(f"{name} must contain " "dictionary objects.")

            normalized.append(dict(item))

        return normalized


# ============================================================================
# CONVENIENCE FACTORY
# ============================================================================


def create_execution_context(
    command: Command,
    *,
    services: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ExecutionContext:
    """
    Create a new ExecutionContext.
    """

    return ExecutionContext(
        command=command,
        services=dict(services or {}),
        metadata=dict(metadata or {}),
    )


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "ExecutionState",
    "ExecutionResult",
    "ExecutionContext",
    "create_execution_context",
]
