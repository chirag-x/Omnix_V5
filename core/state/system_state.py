"""
Omnix V5 - System State

Centralized, thread-safe state tracking for Omnix subsystems.

This module does not initialize, start, or stop subsystems. It only
tracks their current state and health.

Designed to support both:
    - New Omnix V5 subsystems
    - Legacy Omnix components

Typical usage:

    system_state.register("vision")
    system_state.set_starting("vision")
    system_state.set_ready("vision")

    system_state.set_error(
        "vision",
        "Camera initialization failed",
    )

The OmnixEngine and subsystem managers remain responsible for the actual
initialization and lifecycle of components.
"""

from __future__ import annotations

import threading
import time

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# ============================================================================
# SYSTEM COMPONENT STATUS
# ============================================================================


class ComponentStatus(str, Enum):
    """
    Lifecycle and health state of an Omnix component.
    """

    UNKNOWN = "unknown"

    REGISTERED = "registered"

    STARTING = "starting"

    READY = "ready"

    DEGRADED = "degraded"

    STOPPING = "stopping"

    STOPPED = "stopped"

    ERROR = "error"


# ============================================================================
# COMPONENT STATE
# ============================================================================


@dataclass
class ComponentState:
    """
    State information for a single Omnix subsystem.
    """

    name: str

    status: ComponentStatus = ComponentStatus.UNKNOWN

    registered_at: Optional[float] = None

    started_at: Optional[float] = None

    updated_at: float = field(default_factory=time.time)

    error: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_ready(self) -> bool:
        """
        Return True when the component is ready.
        """

        return self.status == ComponentStatus.READY

    @property
    def is_healthy(self) -> bool:
        """
        Return whether the component is currently healthy.

        READY and REGISTERED are considered healthy states.
        """

        return self.status in {
            ComponentStatus.REGISTERED,
            ComponentStatus.READY,
        }

    @property
    def is_active(self) -> bool:
        """
        Return True when the component is currently active.
        """

        return self.status in {
            ComponentStatus.STARTING,
            ComponentStatus.READY,
            ComponentStatus.DEGRADED,
        }

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Return a serializable representation.
        """

        return {
            "name": self.name,
            "status": self.status.value,
            "registered_at": (self.registered_at),
            "started_at": (self.started_at),
            "updated_at": (self.updated_at),
            "error": self.error,
            "is_ready": self.is_ready,
            "is_healthy": self.is_healthy,
            "is_active": self.is_active,
            "metadata": dict(self.metadata),
        }


# ============================================================================
# SYSTEM SNAPSHOT
# ============================================================================


@dataclass
class SystemSnapshot:
    """
    Snapshot of the complete Omnix system state.
    """

    components: Dict[str, ComponentState] = field(default_factory=dict)

    updated_at: float = field(default_factory=time.time)

    @property
    def total_components(
        self,
    ) -> int:

        return len(self.components)

    @property
    def ready_components(
        self,
    ) -> int:

        return sum(
            1
            for component in self.components.values()
            if component.status == ComponentStatus.READY
        )

    @property
    def degraded_components(
        self,
    ) -> int:

        return sum(
            1
            for component in self.components.values()
            if component.status == ComponentStatus.DEGRADED
        )

    @property
    def error_components(
        self,
    ) -> int:

        return sum(
            1
            for component in self.components.values()
            if component.status == ComponentStatus.ERROR
        )

    @property
    def is_healthy(
        self,
    ) -> bool:
        """
        Return True when no registered component
        is currently in an ERROR state.
        """

        if not self.components:

            return False

        return not any(
            component.status == ComponentStatus.ERROR
            for component in self.components.values()
        )

    @property
    def health_status(
        self,
    ) -> str:
        """
        Return an overall system health label.
        """

        if not self.components:

            return "unknown"

        if self.error_components > 0:

            return "error"

        if self.degraded_components > 0:

            return "degraded"

        if self.ready_components == self.total_components:

            return "healthy"

        return "initializing"

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Return a serializable snapshot.
        """

        return {
            "components": {
                name: component.to_dict() for name, component in self.components.items()
            },
            "updated_at": (self.updated_at),
            "total_components": (self.total_components),
            "ready_components": (self.ready_components),
            "degraded_components": (self.degraded_components),
            "error_components": (self.error_components),
            "is_healthy": (self.is_healthy),
            "health_status": (self.health_status),
        }


# ============================================================================
# SYSTEM STATE
# ============================================================================


class SystemState:
    """
    Thread-safe registry and state manager for Omnix components.

    Example:

        state = SystemState()

        state.register("vision")
        state.set_starting("vision")

        try:
            initialize_vision()

            state.set_ready("vision")

        except Exception as error:
            state.set_error(
                "vision",
                error,
            )
    """

    def __init__(
        self,
    ) -> None:

        self._components: Dict[str, ComponentState] = {}

        self._updated_at = time.time()

        self._lock = threading.RLock()

    # ========================================================================
    # COMPONENT REGISTRATION
    # ========================================================================

    def register(
        self,
        name: str,
        *,
        metadata: Optional[Dict[str, Any]] = None,
        overwrite: bool = False,
    ) -> ComponentState:
        """
        Register a subsystem.

        If the component already exists and overwrite=False,
        the existing component is returned.
        """

        name = self._normalize_name(name)

        with self._lock:

            existing = self._components.get(name)

            if existing is not None and not overwrite:

                return self._copy_component(existing)

            now = time.time()

            component = ComponentState(
                name=name,
                status=(ComponentStatus.REGISTERED),
                registered_at=now,
                updated_at=now,
                metadata=dict(metadata or {}),
            )

            self._components[name] = component

            self._touch()

            return self._copy_component(component)

    def unregister(
        self,
        name: str,
    ) -> bool:
        """
        Remove a component from system state.
        """

        name = self._normalize_name(name)

        with self._lock:

            if name not in self._components:

                return False

            del self._components[name]

            self._touch()

            return True

    def ensure_registered(
        self,
        name: str,
    ) -> ComponentState:
        """
        Return an existing component or register it automatically.
        """

        name = self._normalize_name(name)

        with self._lock:

            component = self._components.get(name)

            if component is None:

                return self.register(name)

            return self._copy_component(component)

    # ========================================================================
    # STATUS UPDATES
    # ========================================================================

    def set_status(
        self,
        name: str,
        status: ComponentStatus | str,
        *,
        error: Optional[Any] = None,
    ) -> ComponentState:
        """
        Update a component status.

        Components are automatically registered when they do not exist.
        """

        name = self._normalize_name(name)

        status = self._normalize_status(status)

        with self._lock:

            component = self._components.get(name)

            if component is None:

                self.register(name)

                component = self._components[name]

            component.status = status

            component.updated_at = time.time()

            if status == ComponentStatus.STARTING and component.started_at is None:

                component.started_at = component.updated_at

            if error is not None:

                component.error = str(error)

            elif status != ComponentStatus.ERROR:

                component.error = None

            self._touch()

            return self._copy_component(component)

    def set_starting(
        self,
        name: str,
    ) -> ComponentState:
        """
        Mark a component as starting.
        """

        return self.set_status(
            name,
            ComponentStatus.STARTING,
        )

    def set_ready(
        self,
        name: str,
    ) -> ComponentState:
        """
        Mark a component as ready.
        """

        return self.set_status(
            name,
            ComponentStatus.READY,
        )

    def set_degraded(
        self,
        name: str,
        error: Optional[Any] = None,
    ) -> ComponentState:
        """
        Mark a component as degraded.

        Degraded means the component is still partially usable.
        """

        return self.set_status(
            name,
            ComponentStatus.DEGRADED,
            error=error,
        )

    def set_error(
        self,
        name: str,
        error: Any,
    ) -> ComponentState:
        """
        Mark a component as failed.
        """

        return self.set_status(
            name,
            ComponentStatus.ERROR,
            error=error,
        )

    def set_stopping(
        self,
        name: str,
    ) -> ComponentState:
        """
        Mark a component as stopping.
        """

        return self.set_status(
            name,
            ComponentStatus.STOPPING,
        )

    def set_stopped(
        self,
        name: str,
    ) -> ComponentState:
        """
        Mark a component as stopped.
        """

        return self.set_status(
            name,
            ComponentStatus.STOPPED,
        )

    # ========================================================================
    # COMPONENT METADATA
    # ========================================================================

    def set_metadata(
        self,
        name: str,
        key: str,
        value: Any,
    ) -> None:
        """
        Store metadata for a component.
        """

        name = self._normalize_name(name)

        key = self._normalize_key(key)

        with self._lock:

            if name not in self._components:

                self.register(name)

            component = self._components[name]

            component.metadata[key] = value

            component.updated_at = time.time()

            self._touch()

    def update_metadata(
        self,
        name: str,
        values: Dict[str, Any],
    ) -> None:
        """
        Update multiple metadata values.
        """

        if not isinstance(
            values,
            dict,
        ):

            raise TypeError("values must be a dictionary.")

        name = self._normalize_name(name)

        with self._lock:

            if name not in self._components:

                self.register(name)

            component = self._components[name]

            for key, value in values.items():

                normalized_key = self._normalize_key(key)

                component.metadata[normalized_key] = value

            component.updated_at = time.time()

            self._touch()

    def get_metadata(
        self,
        name: str,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Get component metadata.
        """

        name = self._normalize_name(name)

        key = self._normalize_key(key)

        with self._lock:

            component = self._components.get(name)

            if component is None:

                return default

            return component.metadata.get(
                key,
                default,
            )

    # ========================================================================
    # LOOKUPS
    # ========================================================================

    def get(
        self,
        name: str,
    ) -> Optional[ComponentState]:
        """
        Return a safe copy of component state.
        """

        name = self._normalize_name(name)

        with self._lock:

            component = self._components.get(name)

            if component is None:

                return None

            return self._copy_component(component)

    def exists(
        self,
        name: str,
    ) -> bool:
        """
        Check whether a component is registered.
        """

        name = self._normalize_name(name)

        with self._lock:

            return name in self._components

    def is_ready(
        self,
        name: str,
    ) -> bool:
        """
        Check whether a component is ready.
        """

        component = self.get(name)

        return bool(component and component.is_ready)

    def is_healthy(
        self,
        name: str,
    ) -> bool:
        """
        Check whether a component is healthy.
        """

        component = self.get(name)

        return bool(component and component.is_healthy)

    def names(
        self,
    ) -> List[str]:
        """
        Return registered component names.
        """

        with self._lock:

            return list(self._components.keys())

    # ========================================================================
    # SYSTEM HEALTH
    # ========================================================================

    def snapshot(
        self,
    ) -> SystemSnapshot:
        """
        Return a complete system snapshot.
        """

        with self._lock:

            components = {
                name: self._copy_component(component)
                for name, component in self._components.items()
            }

            return SystemSnapshot(
                components=components,
                updated_at=(self._updated_at),
            )

    def health_status(
        self,
    ) -> Dict[str, Any]:
        """
        Return a compact health dictionary.

        This method is intentionally compatible with the type of
        health status reporting used by legacy OmnixEngine code.
        """

        snapshot = self.snapshot()

        return {
            name: (component.status == ComponentStatus.READY)
            for name, component in snapshot.components.items()
        }

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Return the full system state as a dictionary.
        """

        return self.snapshot().to_dict()

    # ========================================================================
    # RESET
    # ========================================================================

    def clear(
        self,
    ) -> None:
        """
        Remove all component states.
        """

        with self._lock:

            self._components.clear()

            self._touch()

    def reset_component(
        self,
        name: str,
    ) -> ComponentState:
        """
        Reset one component back to REGISTERED.
        """

        name = self._normalize_name(name)

        with self._lock:

            if name not in self._components:

                return self.register(name)

            component = self._components[name]

            component.status = ComponentStatus.REGISTERED

            component.started_at = None

            component.error = None

            component.updated_at = time.time()

            self._touch()

            return self._copy_component(component)

    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================

    def _touch(
        self,
    ) -> None:
        """
        Update system modification time.
        """

        self._updated_at = time.time()

    @staticmethod
    def _copy_component(
        component: ComponentState,
    ) -> ComponentState:
        """
        Create a safe copy of component state.
        """

        return ComponentState(
            name=component.name,
            status=component.status,
            registered_at=(component.registered_at),
            started_at=(component.started_at),
            updated_at=(component.updated_at),
            error=component.error,
            metadata=dict(component.metadata),
        )

    @staticmethod
    def _normalize_name(
        name: Any,
    ) -> str:
        """
        Validate component names.
        """

        value = str(name).strip()

        if not value:

            raise ValueError("Component name cannot be empty.")

        return value

    @staticmethod
    def _normalize_key(
        key: Any,
    ) -> str:
        """
        Validate metadata keys.
        """

        value = str(key).strip()

        if not value:

            raise ValueError("Metadata key cannot be empty.")

        return value

    @staticmethod
    def _normalize_status(
        status: ComponentStatus | str,
    ) -> ComponentStatus:
        """
        Convert a string or enum into ComponentStatus.
        """

        if isinstance(
            status,
            ComponentStatus,
        ):

            return status

        try:

            return ComponentStatus(str(status).strip().lower())

        except ValueError as error:

            valid = ", ".join(item.value for item in ComponentStatus)

            raise ValueError(
                f"Invalid component status: " f"{status!r}. " f"Valid values: {valid}"
            ) from error


# ============================================================================
# GLOBAL SYSTEM STATE
# ============================================================================


_default_system_state = SystemState()


def get_system_state() -> SystemState:
    """
    Return the shared Omnix system state.
    """

    return _default_system_state


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "ComponentStatus",
    "ComponentState",
    "SystemSnapshot",
    "SystemState",
    "get_system_state",
]
