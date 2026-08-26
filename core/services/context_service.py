"""
Omnix V5 - Context Service

Provides centralized runtime context management for Omnix V5.

This service manages shared context at the application, session,
and command levels.

It does not replace ExecutionContext from core.planning.

ExecutionContext:
    Context for a single command or task execution.

ContextService:
    Shared runtime context accessible across Omnix subsystems.

The service is designed to support:

    - Core engine
    - Agent subsystem
    - Skills
    - Vision
    - Memory
    - UI
    - Voice
    - Automation
    - Legacy compatibility
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Dict, Iterable, Optional


# ============================================================================
# CONTEXT SNAPSHOT
# ============================================================================


@dataclass(frozen=True)
class ContextSnapshot:
    """
    Immutable snapshot of the current ContextService state.

    Useful for:

        - Debugging
        - Logging
        - Agent observations
        - Recovery systems
        - State inspection
    """

    global_context: Dict[str, Any]
    session_context: Dict[str, Any]
    active_context: Dict[str, Any]
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Convert the snapshot to a dictionary.
        """

        return {
            "global_context": deepcopy(
                self.global_context
            ),
            "session_context": deepcopy(
                self.session_context
            ),
            "active_context": deepcopy(
                self.active_context
            ),
            "metadata": deepcopy(
                self.metadata
            ),
        }


# ============================================================================
# CONTEXT SERVICE
# ============================================================================


class ContextService:
    """
    Centralized runtime context manager for Omnix V5.

    Context is divided into three levels:

        GLOBAL
            Persistent while Omnix is running.

            Examples:
                system state
                configuration
                active subsystems

        SESSION
            Context associated with the current Omnix session.

            Examples:
                conversation information
                temporary preferences
                current workflow

        ACTIVE
            Context for the currently active command or task.

            Examples:
                active command
                current goal
                active execution context
                current plan

    This service is thread-safe.
    """

    def __init__(
        self,
        *,
        global_context: Optional[
            Dict[str, Any]
        ] = None,
        session_context: Optional[
            Dict[str, Any]
        ] = None,
    ) -> None:

        self._global_context: Dict[
            str,
            Any
        ] = dict(
            global_context or {}
        )

        self._session_context: Dict[
            str,
            Any
        ] = dict(
            session_context or {}
        )

        self._active_context: Dict[
            str,
            Any
        ] = {}

        self._lock = RLock()

    # ====================================================================
    # GLOBAL CONTEXT
    # ====================================================================

    def set_global(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Store a value in global runtime context.
        """

        key = self._normalize_key(
            key
        )

        with self._lock:

            self._global_context[
                key
            ] = value

    def get_global(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Retrieve a value from global runtime context.
        """

        key = self._normalize_key(
            key
        )

        with self._lock:

            return self._global_context.get(
                key,
                default,
            )

    def remove_global(
        self,
        key: str,
    ) -> Any:
        """
        Remove and return a global value.
        """

        key = self._normalize_key(
            key
        )

        with self._lock:

            return self._global_context.pop(
                key,
                None,
            )

    def update_global(
        self,
        values: Dict[str, Any],
    ) -> None:
        """
        Update multiple global context values.
        """

        if not isinstance(
            values,
            dict,
        ):
            raise TypeError(
                "values must be a dictionary."
            )

        with self._lock:

            self._global_context.update(
                values
            )

    def clear_global(
        self,
    ) -> None:
        """
        Clear all global context.
        """

        with self._lock:

            self._global_context.clear()

    # ====================================================================
    # SESSION CONTEXT
    # ====================================================================

    def set_session(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Store a value in session context.
        """

        key = self._normalize_key(
            key
        )

        with self._lock:

            self._session_context[
                key
            ] = value

    def get_session(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Retrieve a value from session context.
        """

        key = self._normalize_key(
            key
        )

        with self._lock:

            return self._session_context.get(
                key,
                default,
            )

    def remove_session(
        self,
        key: str,
    ) -> Any:
        """
        Remove and return a session value.
        """

        key = self._normalize_key(
            key
        )

        with self._lock:

            return self._session_context.pop(
                key,
                None,
            )

    def update_session(
        self,
        values: Dict[str, Any],
    ) -> None:
        """
        Update multiple session context values.
        """

        if not isinstance(
            values,
            dict,
        ):
            raise TypeError(
                "values must be a dictionary."
            )

        with self._lock:

            self._session_context.update(
                values
            )

    def clear_session(
        self,
    ) -> None:
        """
        Clear all session context.
        """

        with self._lock:

            self._session_context.clear()

    # ====================================================================
    # ACTIVE CONTEXT
    # ====================================================================

    def set_active(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Store a value in the currently active task context.
        """

        key = self._normalize_key(
            key
        )

        with self._lock:

            self._active_context[
                key
            ] = value

    def get_active(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Retrieve a value from active context.
        """

        key = self._normalize_key(
            key
        )

        with self._lock:

            return self._active_context.get(
                key,
                default,
            )

    def remove_active(
        self,
        key: str,
    ) -> Any:
        """
        Remove and return an active context value.
        """

        key = self._normalize_key(
            key
        )

        with self._lock:

            return self._active_context.pop(
                key,
                None,
            )

    def update_active(
        self,
        values: Dict[str, Any],
    ) -> None:
        """
        Update multiple active context values.
        """

        if not isinstance(
            values,
            dict,
        ):
            raise TypeError(
                "values must be a dictionary."
            )

        with self._lock:

            self._active_context.update(
                values
            )

    def clear_active(
        self,
    ) -> None:
        """
        Clear the current active task context.
        """

        with self._lock:

            self._active_context.clear()

    # ====================================================================
    # GENERIC CONTEXT ACCESS
    # ====================================================================

    def set(
        self,
        key: str,
        value: Any,
        *,
        scope: str = "session",
    ) -> None:
        """
        Store a context value.

        Supported scopes:

            global
            session
            active
        """

        normalized_scope = (
            self._normalize_scope(
                scope
            )
        )

        if normalized_scope == "global":

            self.set_global(
                key,
                value,
            )

        elif normalized_scope == "session":

            self.set_session(
                key,
                value,
            )

        else:

            self.set_active(
                key,
                value,
            )

    def get(
        self,
        key: str,
        default: Any = None,
        *,
        scope: Optional[
            str
        ] = None,
    ) -> Any:
        """
        Retrieve a context value.

        If no scope is specified, lookup order is:

            active
                ↓
            session
                ↓
            global
        """

        key = self._normalize_key(
            key
        )

        if scope is not None:

            normalized_scope = (
                self._normalize_scope(
                    scope
                )
            )

            if normalized_scope == "global":

                return self.get_global(
                    key,
                    default,
                )

            if normalized_scope == "session":

                return self.get_session(
                    key,
                    default,
                )

            return self.get_active(
                key,
                default,
            )

        with self._lock:

            if key in self._active_context:

                return self._active_context[
                    key
                ]

            if key in self._session_context:

                return self._session_context[
                    key
                ]

            return self._global_context.get(
                key,
                default,
            )

    def remove(
        self,
        key: str,
        *,
        scope: str = "session",
    ) -> Any:
        """
        Remove a context value.
        """

        normalized_scope = (
            self._normalize_scope(
                scope
            )
        )

        if normalized_scope == "global":

            return self.remove_global(
                key
            )

        if normalized_scope == "session":

            return self.remove_session(
                key
            )

        return self.remove_active(
            key
        )

    def contains(
        self,
        key: str,
        *,
        scope: Optional[
            str
        ] = None,
    ) -> bool:
        """
        Check whether a context key exists.
        """

        sentinel = object()

        return (
            self.get(
                key,
                sentinel,
                scope=scope,
            )
            is not sentinel
        )

    # ====================================================================
    # ACTIVE EXECUTION HELPERS
    # ====================================================================

    def set_active_execution(
        self,
        execution_context: Any,
    ) -> None:
        """
        Store the currently active ExecutionContext.

        The type is intentionally Any to avoid tightly coupling the
        service layer to the Planning subsystem.
        """

        self.set_active(
            "execution_context",
            execution_context,
        )

    def get_active_execution(
        self,
        default: Any = None,
    ) -> Any:
        """
        Return the currently active execution context.
        """

        return self.get_active(
            "execution_context",
            default,
        )

    def set_active_command(
        self,
        command: Any,
    ) -> None:
        """
        Store the currently active command.
        """

        self.set_active(
            "command",
            command,
        )

    def get_active_command(
        self,
        default: Any = None,
    ) -> Any:
        """
        Return the currently active command.
        """

        return self.get_active(
            "command",
            default,
        )

    def set_active_plan(
        self,
        plan: Any,
    ) -> None:
        """
        Store the currently active task plan.
        """

        self.set_active(
            "plan",
            plan,
        )

    def get_active_plan(
        self,
        default: Any = None,
    ) -> Any:
        """
        Return the currently active task plan.
        """

        return self.get_active(
            "plan",
            default,
        )

    # ====================================================================
    # SNAPSHOTS
    # ====================================================================

    def snapshot(
        self,
        *,
        metadata: Optional[
            Dict[str, Any]
        ] = None,
        deep: bool = False,
    ) -> ContextSnapshot:
        """
        Create a snapshot of the current context.

        deep=False:
            Faster shallow copy.

        deep=True:
            Safer deep copy for mutable data.
        """

        with self._lock:

            copier = (
                deepcopy
                if deep
                else dict
            )

            return ContextSnapshot(
                global_context=copier(
                    self._global_context
                ),
                session_context=copier(
                    self._session_context
                ),
                active_context=copier(
                    self._active_context
                ),
                metadata=(
                    deepcopy(metadata)
                    if metadata
                    else {}
                ),
            )

    def to_dict(
        self,
        *,
        deep: bool = False,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Return all contexts as dictionaries.
        """

        snapshot = self.snapshot(
            deep=deep
        )

        return {
            "global": (
                snapshot.global_context
            ),
            "session": (
                snapshot.session_context
            ),
            "active": (
                snapshot.active_context
            ),
        }

    # ====================================================================
    # MERGING
    # ====================================================================

    def merge(
        self,
        *,
        scopes: Iterable[
            str
        ] = (
            "global",
            "session",
            "active",
        ),
        deep: bool = False,
    ) -> Dict[str, Any]:
        """
        Merge multiple context scopes.

        Later scopes override earlier scopes.

        Default order:

            global
                ↓
            session
                ↓
            active
        """

        result: Dict[
            str,
            Any
        ] = {}

        snapshot = self.snapshot(
            deep=deep
        )

        mapping = {
            "global": (
                snapshot.global_context
            ),
            "session": (
                snapshot.session_context
            ),
            "active": (
                snapshot.active_context
            ),
        }

        for scope in scopes:

            normalized_scope = (
                self._normalize_scope(
                    scope
                )
            )

            result.update(
                mapping[
                    normalized_scope
                ]
            )

        return result

    # ====================================================================
    # RESET
    # ====================================================================

    def reset(
        self,
        *,
        keep_global: bool = True,
    ) -> None:
        """
        Reset runtime context.

        By default global context is preserved because it may contain
        engine-level state and registered subsystem information.
        """

        with self._lock:

            self._session_context.clear()

            self._active_context.clear()

            if not keep_global:

                self._global_context.clear()

    # ====================================================================
    # STATUS
    # ====================================================================

    def status(
        self,
    ) -> Dict[str, Any]:
        """
        Return lightweight context statistics.
        """

        with self._lock:

            return {
                "global_keys": len(
                    self._global_context
                ),
                "session_keys": len(
                    self._session_context
                ),
                "active_keys": len(
                    self._active_context
                ),
                "has_active_execution": (
                    "execution_context"
                    in self._active_context
                ),
                "has_active_command": (
                    "command"
                    in self._active_context
                ),
                "has_active_plan": (
                    "plan"
                    in self._active_context
                ),
            }

    # ====================================================================
    # INTERNAL HELPERS
    # ====================================================================

    @staticmethod
    def _normalize_key(
        key: str,
    ) -> str:
        """
        Validate and normalize a context key.
        """

        normalized = str(
            key
        ).strip()

        if not normalized:

            raise ValueError(
                "Context key cannot be empty."
            )

        return normalized

    @staticmethod
    def _normalize_scope(
        scope: str,
    ) -> str:
        """
        Validate and normalize a context scope.
        """

        normalized = str(
            scope
        ).strip().lower()

        aliases = {
            "global": "global",
            "engine": "global",

            "session": "session",
            "runtime": "session",

            "active": "active",
            "task": "active",
            "execution": "active",
        }

        if normalized not in aliases:

            raise ValueError(
                "Invalid context scope: "
                f"{scope}. "
                "Supported scopes are "
                "'global', 'session', and 'active'."
            )

        return aliases[
            normalized
        ]


# ============================================================================
# SHARED CONTEXT SERVICE
# ============================================================================


_default_context_service: Optional[
    ContextService
] = None


def get_context_service(
) -> ContextService:
    """
    Return the shared Omnix V5 ContextService.
    """

    global _default_context_service

    if (
        _default_context_service
        is None
    ):

        _default_context_service = (
            ContextService()
        )

    return _default_context_service


def reset_context_service(
) -> None:
    """
    Reset the shared ContextService instance.

    Primarily useful for testing or controlled engine reinitialization.
    """

    global _default_context_service

    _default_context_service = None


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "ContextSnapshot",
    "ContextService",
    "get_context_service",
    "reset_context_service",
]