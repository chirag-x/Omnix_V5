"""
Omnix V5 - Engine Manager

Central runtime manager responsible for coordinating Omnix services.

Responsibilities:
    - Service registration
    - Dependency registration
    - Dependency validation
    - Safe service startup
    - Startup ordering
    - Partial startup handling
    - Service access
    - Service shutdown
    - Runtime diagnostics

This class sits above ServiceRegistry and DependencyManager but below
OmnixEngine.

Architecture:

    OmnixEngine
         |
         v
    EngineManager
      /        \
     v          v
ServiceRegistry DependencyManager
     |
     v
Omnix V5 Services
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Optional, Set

from .service_registry import (
    ServiceRegistry,
    ServiceLifetime,
    ServiceStatus,
    ServiceNotFoundError,
    ServiceRegistryError,
)

from .dependency_manager import (
    DependencyManager,
    DependencyReport,
    MissingDependencyError,
    CircularDependencyError,
)

logger = logging.getLogger("omnix.core.engine_manager")


# ============================================================================
# ENUMS
# ============================================================================


class EngineState(str, Enum):
    """Current state of the Omnix runtime."""

    CREATED = "created"
    CONFIGURING = "configuring"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class StartupMode(str, Enum):
    """
    Controls how startup failures are handled.

    STRICT:
        Required service failure stops the engine.

    TOLERANT:
        Failed services are recorded and startup continues.

    OPTIONAL:
        Only explicitly required services cause startup failure.
    """

    STRICT = "strict"
    TOLERANT = "tolerant"
    OPTIONAL = "optional"


class ServiceStartupState(str, Enum):
    """Detailed startup state for an individual service."""

    PENDING = "pending"
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    SKIPPED = "skipped"
    STOPPED = "stopped"


# ============================================================================
# EXCEPTIONS
# ============================================================================


class EngineManagerError(Exception):
    """Base exception for EngineManager errors."""


class EngineStartupError(EngineManagerError):
    """Raised when engine startup fails."""


class InvalidEngineStateError(EngineManagerError):
    """Raised when an operation is invalid for the current state."""


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class ServiceStartupRecord:
    """
    Stores startup information for one service.
    """

    name: str

    required: bool = True

    state: ServiceStartupState = ServiceStartupState.PENDING

    error: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StartupResult:
    """
    Result returned after startup.
    """

    success: bool

    engine_state: EngineState

    started: List[str] = field(default_factory=list)

    failed: List[str] = field(default_factory=list)

    skipped: List[str] = field(default_factory=list)

    errors: Dict[str, str] = field(default_factory=dict)


# ============================================================================
# ENGINE MANAGER
# ============================================================================


class EngineManager:
    """
    Coordinates the lifecycle of Omnix V5 services.

    Example:

        manager = EngineManager()

        manager.register_service(
            "memory",
            MemoryService,
        )

        manager.register_service(
            "context",
            ContextService,
            required_services=["memory"],
        )

        result = manager.start()

        memory = manager.get("memory")
    """

    def __init__(
        self,
        registry: Optional[ServiceRegistry] = None,
        dependency_manager: Optional[DependencyManager] = None,
    ) -> None:

        self._registry = registry if registry is not None else ServiceRegistry()

        self._dependencies = (
            dependency_manager
            if dependency_manager is not None
            else DependencyManager(self._registry)
        )

        self._state = EngineState.CREATED

        self._service_records: Dict[str, ServiceStartupRecord] = {}

        self._started_services: List[str] = []

        self._required_services: Set[str] = set()

        self._lock = threading.RLock()

        logger.debug("EngineManager initialized")

    # ========================================================================
    # PROPERTIES
    # ========================================================================

    @property
    def registry(self) -> ServiceRegistry:
        """Return the underlying ServiceRegistry."""

        return self._registry

    @property
    def dependencies(self) -> DependencyManager:
        """Return the DependencyManager."""

        return self._dependencies

    @property
    def state(self) -> EngineState:
        """Return current engine state."""

        with self._lock:
            return self._state

    @property
    def is_running(self) -> bool:
        """Return True when engine is operational."""

        return self.state in (
            EngineState.RUNNING,
            EngineState.DEGRADED,
        )

    # ========================================================================
    # SERVICE REGISTRATION
    # ========================================================================

    def register_service(
        self,
        name: str,
        service: Any = None,
        *,
        factory: Optional[Callable[..., Any]] = None,
        lifetime: ServiceLifetime = (ServiceLifetime.SINGLETON),
        required: bool = True,
        required_services: Optional[Iterable[str]] = None,
        optional_services: Optional[Iterable[str]] = None,
        required_modules: Optional[Iterable[str]] = None,
        optional_modules: Optional[Iterable[str]] = None,
        aliases: Optional[Iterable[str]] = None,
        lazy: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        replace: bool = False,
    ) -> None:
        """
        Register an Omnix service and its dependencies.

        New V5 code should register through this method
        instead of registering separately with the registry
        and dependency manager.
        """

        with self._lock:

            self._ensure_registration_allowed()

            self._registry.register(
                name=name,
                service=service,
                factory=factory,
                lifetime=lifetime,
                aliases=aliases,
                lazy=True,
                metadata=metadata,
                replace=replace,
            )

            self._dependencies.register(
                name,
                required_services=(required_services),
                optional_services=(optional_services),
                required_modules=(required_modules),
                optional_modules=(optional_modules),
                metadata=metadata,
                replace=True,
            )

            record = ServiceStartupRecord(
                name=name,
                required=required,
                metadata=dict(metadata or {}),
            )

            self._service_records[name] = record

            if required:
                self._required_services.add(name)
            else:
                self._required_services.discard(name)

            logger.info(
                "Engine service registered: %s " "(required=%s)",
                name,
                required,
            )

    def register_instance(
        self,
        name: str,
        instance: Any,
        **kwargs: Any,
    ) -> None:
        """
        Convenience method for registering
        an existing service instance.
        """

        self.register_service(
            name,
            service=instance,
            lifetime=ServiceLifetime.INSTANCE,
            **kwargs,
        )

    def register_factory(
        self,
        name: str,
        factory: Callable[..., Any],
        **kwargs: Any,
    ) -> None:
        """
        Convenience method for registering
        a service factory.
        """

        self.register_service(
            name,
            factory=factory,
            **kwargs,
        )

    # ========================================================================
    # SERVICE ACCESS
    # ========================================================================

    def get(
        self,
        name: str,
        default: Any = None,
        *,
        required: bool = True,
    ) -> Any:
        """
        Retrieve a registered service.
        """

        return self._registry.get(
            name,
            default=default,
            required=required,
        )

    def try_get(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Retrieve a service safely.
        """

        return self._registry.try_get(
            name,
            default=default,
        )

    def has_service(
        self,
        name: str,
    ) -> bool:
        """Return True if a service exists."""

        return self._registry.contains(name)

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def validate(
        self,
        *,
        raise_on_error: bool = False,
    ) -> Dict[str, DependencyReport]:
        """
        Validate all service dependencies.
        """

        with self._lock:

            if self._state == EngineState.CREATED:
                self._state = EngineState.CONFIGURING

        self._dependencies.validate_graph(raise_on_cycle=raise_on_error)

        reports = self._dependencies.validate_all(raise_on_error=False)

        failures = []

        for name, report in reports.items():

            if not report.valid:

                failures.append(f"{name}: " f"{', '.join(report.missing_required)}")

        if failures and raise_on_error:

            raise MissingDependencyError("; ".join(failures))

        return reports

    # ========================================================================
    # STARTUP
    # ========================================================================

    def start(
        self,
        *,
        mode: StartupMode = (StartupMode.OPTIONAL),
        services: Optional[Iterable[str]] = None,
    ) -> StartupResult:
        """
        Start Omnix services.

        Startup order is calculated from the dependency graph.

        Parameters
        ----------
        mode:
            Defines how startup failures are handled.

        services:
            Optional subset of services to start.
        """

        with self._lock:

            if self._state in (
                EngineState.STARTING,
                EngineState.RUNNING,
                EngineState.DEGRADED,
            ):

                raise InvalidEngineStateError(
                    f"Cannot start engine while in " f"state '{self._state.value}'."
                )

            if self._state == EngineState.STOPPING:

                raise InvalidEngineStateError(
                    "Cannot start while shutdown " "is in progress."
                )

            self._state = EngineState.STARTING

        logger.info("Starting Omnix EngineManager...")

        started: List[str] = []
        failed: List[str] = []
        skipped: List[str] = []
        errors: Dict[str, str] = {}

        try:

            validation_reports = self.validate(raise_on_error=False)

            startup_order = self._dependencies.get_startup_order(raise_on_cycle=True)

            registered = set(self._registry.list_services())

            # Include registered services that have no
            # dependency definition.
            for name in sorted(registered):

                if name not in startup_order:
                    startup_order.append(name)

            if services is not None:

                requested = set(services)

                startup_order = [name for name in startup_order if name in requested]

            for name in startup_order:

                if name not in registered:
                    continue

                record = self._service_records.setdefault(
                    name,
                    ServiceStartupRecord(name=name),
                )

                report = validation_reports.get(name)

                if report is not None and not report.valid:

                    error = "Missing required dependencies: " + ", ".join(
                        report.missing_required
                    )

                    if self._should_abort(
                        name,
                        mode,
                    ):

                        record.state = ServiceStartupState.FAILED

                        record.error = error

                        failed.append(name)
                        errors[name] = error

                        raise EngineStartupError(
                            f"Required service " f"'{name}' cannot start: " f"{error}"
                        )

                    record.state = ServiceStartupState.SKIPPED

                    record.error = error

                    skipped.append(name)

                    logger.warning(
                        "Skipping service '%s': %s",
                        name,
                        error,
                    )

                    continue

                self._start_service(
                    name,
                    record,
                    started,
                    failed,
                    errors,
                    mode,
                )

        except Exception as exc:

            logger.exception("Engine startup failed")

            with self._lock:

                self._state = EngineState.FAILED

            if isinstance(
                exc,
                EngineStartupError,
            ):
                raise

            raise EngineStartupError(str(exc)) from exc

        with self._lock:

            self._started_services = list(started)

            if failed or skipped:

                self._state = EngineState.DEGRADED

            else:

                self._state = EngineState.RUNNING

        result = StartupResult(
            success=(
                self._state
                in (
                    EngineState.RUNNING,
                    EngineState.DEGRADED,
                )
            ),
            engine_state=self._state,
            started=started,
            failed=failed,
            skipped=skipped,
            errors=errors,
        )

        logger.info(
            "Engine startup completed "
            "(state=%s, started=%d, "
            "failed=%d, skipped=%d)",
            self._state.value,
            len(started),
            len(failed),
            len(skipped),
        )

        return result

    def _start_service(
        self,
        name: str,
        record: ServiceStartupRecord,
        started: List[str],
        failed: List[str],
        errors: Dict[str, str],
        mode: StartupMode,
    ) -> None:
        """
        Start one service safely.
        """

        record.state = ServiceStartupState.STARTING

        try:

            instance = self._registry.get(
                name,
                required=True,
            )

            self._invoke_start(
                name,
                instance,
            )

            record.state = ServiceStartupState.RUNNING

            record.error = None

            started.append(name)

            logger.info(
                "Service started: %s",
                name,
            )

        except Exception as exc:

            error = str(exc)

            record.state = ServiceStartupState.FAILED

            record.error = error

            failed.append(name)
            errors[name] = error

            logger.exception(
                "Service failed to start: %s",
                name,
            )

            if self._should_abort(
                name,
                mode,
            ):

                raise EngineStartupError(
                    f"Service '{name}' " f"failed to start: {error}"
                ) from exc

    @staticmethod
    def _invoke_start(
        name: str,
        instance: Any,
    ) -> None:
        """
        Invoke a supported startup method.

        Service constructors may already perform all
        initialization, so lifecycle methods are optional.
        """

        for method_name in (
            "start",
            "initialize",
            "startup",
        ):

            method = getattr(
                instance,
                method_name,
                None,
            )

            if not callable(method):
                continue

            result = method()

            if result is False:

                raise EngineManagerError(
                    f"Service '{name}' returned " f"False from {method_name}()."
                )

            return

    def _should_abort(
        self,
        name: str,
        mode: StartupMode,
    ) -> bool:
        """
        Determine whether a service failure should
        stop engine startup.
        """

        if mode == StartupMode.STRICT:
            return True

        if mode == StartupMode.TOLERANT:
            return False

        return name in self._required_services

    # ========================================================================
    # INDIVIDUAL SERVICE CONTROL
    # ========================================================================

    def start_service(
        self,
        name: str,
        *,
        mode: StartupMode = (StartupMode.OPTIONAL),
    ) -> Any:
        """
        Start a single service.

        Dependencies should already be available.
        """

        with self._lock:

            if not self._registry.contains(name):

                raise ServiceNotFoundError(f"Unknown service '{name}'.")

            record = self._service_records.setdefault(
                name,
                ServiceStartupRecord(
                    name=name,
                    required=(name in self._required_services),
                ),
            )

        report = self._dependencies.validate(name)

        if not report.valid:

            message = "Missing dependencies: " + ", ".join(report.missing_required)

            record.state = ServiceStartupState.FAILED

            record.error = message

            raise MissingDependencyError(message)

        instance = self._registry.get(name)

        record.state = ServiceStartupState.STARTING

        try:

            self._invoke_start(
                name,
                instance,
            )

            record.state = ServiceStartupState.RUNNING

            record.error = None

            with self._lock:

                if name not in self._started_services:
                    self._started_services.append(name)

            return instance

        except Exception:

            record.state = ServiceStartupState.FAILED

            logger.exception(
                "Failed starting service '%s'",
                name,
            )

            if self._should_abort(
                name,
                mode,
            ):
                raise

            return None

    def stop_service(
        self,
        name: str,
    ) -> bool:
        """
        Stop one service without removing it
        from the registry.
        """

        instance = self._registry.try_get(name)

        if instance is None:
            return False

        for method_name in (
            "shutdown",
            "close",
            "stop",
        ):

            method = getattr(
                instance,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:

                method()

                with self._lock:

                    record = self._service_records.get(name)

                    if record is not None:

                        record.state = ServiceStartupState.STOPPED

                    if name in self._started_services:

                        self._started_services.remove(name)

                logger.info(
                    "Service stopped: %s",
                    name,
                )

                return True

            except Exception:

                logger.exception(
                    "Failed stopping service '%s'",
                    name,
                )

                return False

        return False

    # ========================================================================
    # SHUTDOWN
    # ========================================================================

    def shutdown(
        self,
        *,
        clear_registry: bool = True,
    ) -> None:
        """
        Shut down Omnix services.

        Services are stopped in reverse dependency
        order whenever possible.
        """

        with self._lock:

            if self._state in (
                EngineState.STOPPED,
                EngineState.STOPPING,
            ):
                return

            self._state = EngineState.STOPPING

            started_services = list(self._started_services)

        logger.info("Shutting down EngineManager...")

        try:

            shutdown_order = self._dependencies.get_shutdown_order()

        except Exception:

            logger.warning(
                "Could not calculate dependency " "shutdown order.",
                exc_info=True,
            )

            shutdown_order = list(reversed(started_services))

        for name in shutdown_order:

            if name not in started_services:
                continue

            self.stop_service(name)

        # Any service that was initialized but was
        # not tracked as started is still handled by
        # ServiceRegistry shutdown.
        if clear_registry:

            try:

                self._registry.shutdown()

            except Exception:

                logger.exception("ServiceRegistry shutdown failed")

        with self._lock:

            self._started_services.clear()

            self._state = EngineState.STOPPED

        logger.info("EngineManager shutdown complete")

    # ========================================================================
    # DIAGNOSTICS
    # ========================================================================

    def health_status(
        self,
    ) -> Dict[str, Any]:
        """
        Return a lightweight health summary.

        This will later be consumed by
        HealthMonitor and OmnixEngine.
        """

        with self._lock:

            services = {}

            for name, record in self._service_records.items():

                registry_status = self._registry.get_status(name)

                services[name] = {
                    "required": (record.required),
                    "startup_state": (record.state.value),
                    "registry_status": (
                        registry_status.value if registry_status else None
                    ),
                    "error": record.error,
                }

            return {
                "state": self._state.value,
                "running": self.is_running,
                "service_count": len(self._service_records),
                "started_services": list(self._started_services),
                "services": services,
            }

    def diagnostics(
        self,
    ) -> Dict[str, Any]:
        """
        Return full runtime diagnostics.
        """

        return {
            "engine": self.health_status(),
            "registry": (self._registry.diagnostics()),
            "dependencies": (self._dependencies.diagnostics()),
        }

    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================

    def _ensure_registration_allowed(
        self,
    ) -> None:
        """
        Prevent structural changes while running.
        """

        if self._state in (
            EngineState.STARTING,
            EngineState.RUNNING,
            EngineState.STOPPING,
        ):

            raise InvalidEngineStateError(
                f"Cannot register services while "
                f"engine state is "
                f"'{self._state.value}'."
            )

        if self._state == EngineState.STOPPED:

            raise InvalidEngineStateError(
                "Cannot register services after " "EngineManager shutdown."
            )

    def __contains__(
        self,
        name: str,
    ) -> bool:
        return self.has_service(name)

    def __getitem__(
        self,
        name: str,
    ) -> Any:
        return self.get(name)

    def __repr__(
        self,
    ) -> str:
        return (
            f"{self.__class__.__name__}("
            f"state={self._state.value}, "
            f"services="
            f"{len(self._service_records)}"
            f")"
        )
