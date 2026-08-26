"""
Omnix V5 - Service Registry

Central dependency and service registry for the Omnix runtime.

The registry is intentionally independent from the rest of the core so it can
be used during early startup without creating circular imports.

Supported features:
    - Singleton services
    - Transient/factory services
    - Lazy initialization
    - Service aliases
    - Thread-safe access
    - Dependency metadata
    - Service replacement
    - Introspection and diagnostics
    - Graceful service cleanup
"""

from __future__ import annotations

import inspect
import logging
import threading

from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
)

logger = logging.getLogger("omnix.core.service_registry")


# ============================================================================
# EXCEPTIONS
# ============================================================================


class ServiceRegistryError(Exception):
    """Base exception for all service registry errors."""


class ServiceNotFoundError(ServiceRegistryError):
    """Raised when a requested service does not exist."""


class ServiceAlreadyRegisteredError(ServiceRegistryError):
    """Raised when attempting to register an existing service."""


class ServiceInitializationError(ServiceRegistryError):
    """Raised when a service factory fails."""


# ============================================================================
# ENUMS
# ============================================================================


class ServiceLifetime(str, Enum):
    """
    Defines how a registered service is created.

    SINGLETON:
        One instance is created and reused.

    TRANSIENT:
        A new instance is created every time get() is called.

    INSTANCE:
        An already-created object managed by the registry.
    """

    SINGLETON = "singleton"
    TRANSIENT = "transient"
    INSTANCE = "instance"


class ServiceStatus(str, Enum):
    """Runtime status of a service."""

    REGISTERED = "registered"
    INITIALIZING = "initializing"
    READY = "ready"
    FAILED = "failed"
    SHUTDOWN = "shutdown"


# ============================================================================
# SERVICE DESCRIPTOR
# ============================================================================


@dataclass
class ServiceDescriptor:
    """
    Internal description of a registered service.
    """

    name: str

    factory: Optional[Callable[..., Any]] = None
    instance: Any = None

    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    dependencies: List[str] = field(default_factory=list)

    aliases: Set[str] = field(default_factory=set)

    lazy: bool = True
    status: ServiceStatus = ServiceStatus.REGISTERED

    metadata: Dict[str, Any] = field(default_factory=dict)

    error: Optional[str] = None


# ============================================================================
# SERVICE REGISTRY
# ============================================================================


class ServiceRegistry:
    """
    Thread-safe dependency and service registry.

    This registry is the central place where Omnix V5 subsystems are exposed
    to the rest of the application.

    Example:

        registry.register_instance("vision", vision_system)

        registry.register_factory(
            "skills",
            lambda: SkillsManager(),
            dependencies=["context"]
        )

        skills = registry.get("skills")
    """

    def __init__(self) -> None:
        self._services: Dict[str, ServiceDescriptor] = {}
        self._aliases: Dict[str, str] = {}

        self._lock = threading.RLock()

        self._shutdown = False

        logger.debug("ServiceRegistry initialized")

    # ========================================================================
    # REGISTRATION
    # ========================================================================

    def register(
        self,
        name: str,
        service: Any = None,
        *,
        factory: Optional[Callable[..., Any]] = None,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        dependencies: Optional[Iterable[str]] = None,
        aliases: Optional[Iterable[str]] = None,
        lazy: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        replace: bool = False,
    ) -> None:
        """
        Register a service.

        For backward compatibility, ``service`` may be:

        - an existing instance
        - a class
        - a callable factory

        Prefer register_instance() or register_factory() in new V5 code.
        """

        self._validate_name(name)

        with self._lock:
            self._ensure_not_shutdown()

            if name in self._services and not replace:
                raise ServiceAlreadyRegisteredError(
                    f"Service '{name}' is already registered."
                )

            if replace and name in self._services:
                self._remove_service_locked(name)

            resolved_factory = factory
            instance = None
            resolved_lifetime = lifetime

            if service is not None and factory is None:

                if inspect.isclass(service):
                    resolved_factory = service

                elif callable(service):
                    resolved_factory = service

                else:
                    instance = service
                    resolved_lifetime = ServiceLifetime.INSTANCE

            descriptor = ServiceDescriptor(
                name=name,
                factory=resolved_factory,
                instance=instance,
                lifetime=resolved_lifetime,
                dependencies=list(dependencies or []),
                aliases=set(aliases or []),
                lazy=lazy,
                metadata=dict(metadata or {}),
                status=(
                    ServiceStatus.READY
                    if instance is not None
                    else ServiceStatus.REGISTERED
                ),
            )

            self._services[name] = descriptor

            for alias in descriptor.aliases:
                self._register_alias_locked(alias, name)

            logger.info(
                "Registered service '%s' (%s)",
                name,
                descriptor.lifetime.value,
            )

        # Eager initialization happens outside the registration lock.
        if not lazy and descriptor.instance is None:
            self.get(name)

    def register_instance(
        self,
        name: str,
        instance: Any,
        *,
        aliases: Optional[Iterable[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        replace: bool = False,
    ) -> None:
        """Register an existing service instance."""

        self.register(
            name=name,
            service=instance,
            lifetime=ServiceLifetime.INSTANCE,
            aliases=aliases,
            metadata=metadata,
            replace=replace,
        )

    def register_factory(
        self,
        name: str,
        factory: Callable[..., Any],
        *,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        dependencies: Optional[Iterable[str]] = None,
        aliases: Optional[Iterable[str]] = None,
        lazy: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        replace: bool = False,
    ) -> None:
        """Register a service factory."""

        if not callable(factory):
            raise TypeError(f"Factory for service '{name}' must be callable.")

        self.register(
            name=name,
            factory=factory,
            lifetime=lifetime,
            dependencies=dependencies,
            aliases=aliases,
            lazy=lazy,
            metadata=metadata,
            replace=replace,
        )

    # ========================================================================
    # RESOLUTION
    # ========================================================================

    def get(
        self,
        name: str,
        default: Any = None,
        *,
        required: bool = True,
    ) -> Any:
        """
        Retrieve a service.

        Parameters
        ----------
        name:
            Service name or alias.

        default:
            Value returned when required=False and the service does not exist.

        required:
            If True, raises ServiceNotFoundError when missing.
        """

        with self._lock:

            if self._shutdown:
                raise ServiceRegistryError(
                    "Cannot resolve services after registry shutdown."
                )

            canonical_name = self._resolve_name_locked(name)

            descriptor = self._services.get(canonical_name)

            if descriptor is None:
                if required:
                    raise ServiceNotFoundError(f"Service '{name}' is not registered.")

                return default

            # Already-created service.
            if (
                descriptor.lifetime
                in (
                    ServiceLifetime.SINGLETON,
                    ServiceLifetime.INSTANCE,
                )
                and descriptor.instance is not None
            ):
                return descriptor.instance

        # Do initialization outside the first lookup section, but use
        # a second lock inside initialization to prevent duplicate singletons.
        return self._create_or_resolve(descriptor)

    def try_get(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Safely retrieve a service.

        Returns default instead of raising when the service does not exist.
        """

        return self.get(
            name,
            default=default,
            required=False,
        )

    def require(self, name: str) -> Any:
        """Alias for get(name, required=True)."""

        return self.get(name, required=True)

    # ========================================================================
    # SERVICE CREATION
    # ========================================================================

    def _create_or_resolve(
        self,
        descriptor: ServiceDescriptor,
    ) -> Any:
        """
        Create or retrieve a service instance.
        """

        with self._lock:

            if (
                descriptor.lifetime
                in (
                    ServiceLifetime.SINGLETON,
                    ServiceLifetime.INSTANCE,
                )
                and descriptor.instance is not None
            ):
                return descriptor.instance

            if descriptor.status == ServiceStatus.INITIALIZING:
                raise ServiceInitializationError(
                    f"Circular or concurrent initialization detected "
                    f"for service '{descriptor.name}'."
                )

            descriptor.status = ServiceStatus.INITIALIZING
            descriptor.error = None

        try:

            dependencies = self._resolve_dependencies(descriptor)

            instance = self._invoke_factory(
                descriptor.factory,
                dependencies,
            )

            if instance is None:
                raise ServiceInitializationError(
                    f"Factory for service '{descriptor.name}' " f"returned None."
                )

            with self._lock:

                if descriptor.lifetime in (
                    ServiceLifetime.SINGLETON,
                    ServiceLifetime.INSTANCE,
                ):
                    descriptor.instance = instance

                descriptor.status = ServiceStatus.READY

            logger.info(
                "Initialized service '%s'",
                descriptor.name,
            )

            return instance

        except Exception as exc:

            error_message = (
                f"Failed to initialize service " f"'{descriptor.name}': {exc}"
            )

            with self._lock:
                descriptor.status = ServiceStatus.FAILED
                descriptor.error = error_message

            logger.exception(error_message)

            if isinstance(exc, ServiceRegistryError):
                raise

            raise ServiceInitializationError(error_message) from exc

    def _resolve_dependencies(
        self,
        descriptor: ServiceDescriptor,
    ) -> Dict[str, Any]:
        """
        Resolve dependencies declared by a service.
        """

        resolved: Dict[str, Any] = {}

        for dependency_name in descriptor.dependencies:
            resolved[dependency_name] = self.get(
                dependency_name,
                required=True,
            )

        return resolved

    def _invoke_factory(
        self,
        factory: Optional[Callable[..., Any]],
        dependencies: Dict[str, Any],
    ) -> Any:
        """
        Call a service factory.

        Supported factory styles:

            factory()

            factory(registry)

            factory(dependency1, dependency2)

            factory(
                vision=...,
                memory=...
            )
        """

        if factory is None:
            raise ServiceInitializationError("Service has no instance or factory.")

        try:
            signature = inspect.signature(factory)
            parameters = list(signature.parameters.values())

        except (TypeError, ValueError):
            return factory()

        if not parameters:
            return factory()

        kwargs: Dict[str, Any] = {}

        for parameter in parameters:

            if parameter.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue

            parameter_name = parameter.name

            if parameter_name in (
                "registry",
                "service_registry",
                "services",
            ):
                kwargs[parameter_name] = self

            elif parameter_name in dependencies:
                kwargs[parameter_name] = dependencies[parameter_name]

            elif parameter.default is inspect.Parameter.empty:
                raise ServiceInitializationError(
                    f"Unable to resolve factory parameter " f"'{parameter_name}'."
                )

        return factory(**kwargs)

    # ========================================================================
    # ALIASES
    # ========================================================================

    def add_alias(
        self,
        alias: str,
        service_name: str,
    ) -> None:
        """Add an alias for an existing service."""

        self._validate_name(alias)

        with self._lock:

            canonical_name = self._resolve_name_locked(service_name)

            if canonical_name not in self._services:
                raise ServiceNotFoundError(
                    f"Cannot alias unknown service " f"'{service_name}'."
                )

            self._register_alias_locked(
                alias,
                canonical_name,
            )

            self._services[canonical_name].aliases.add(alias)

    def _register_alias_locked(
        self,
        alias: str,
        service_name: str,
    ) -> None:

        if alias in self._services:
            raise ServiceRegistryError(
                f"Alias '{alias}' conflicts with a service name."
            )

        existing = self._aliases.get(alias)

        if existing is not None and existing != service_name:
            raise ServiceRegistryError(
                f"Alias '{alias}' already belongs to " f"service '{existing}'."
            )

        self._aliases[alias] = service_name

    # ========================================================================
    # SERVICE REMOVAL
    # ========================================================================

    def unregister(
        self,
        name: str,
        *,
        shutdown: bool = False,
    ) -> bool:
        """
        Remove a service from the registry.

        Returns True when a service was removed.
        """

        instance = None

        with self._lock:

            canonical_name = self._resolve_name_locked(name)

            descriptor = self._services.get(canonical_name)

            if descriptor is None:
                return False

            instance = descriptor.instance

            self._remove_service_locked(canonical_name)

        if shutdown and instance is not None:
            self._shutdown_instance(
                canonical_name,
                instance,
            )

        logger.info(
            "Unregistered service '%s'",
            canonical_name,
        )

        return True

    def _remove_service_locked(
        self,
        name: str,
    ) -> None:

        descriptor = self._services.pop(
            name,
            None,
        )

        if descriptor is None:
            return

        aliases_to_remove = [
            alias for alias, target in self._aliases.items() if target == name
        ]

        for alias in aliases_to_remove:
            self._aliases.pop(alias, None)

    # ========================================================================
    # INSPECTION
    # ========================================================================

    def contains(self, name: str) -> bool:
        """Return True if a service or alias exists."""

        with self._lock:
            canonical_name = self._resolve_name_locked(name)

            return canonical_name in self._services

    def is_registered(self, name: str) -> bool:
        """Backward-compatible alias for contains()."""

        return self.contains(name)

    def list_services(
        self,
        *,
        include_aliases: bool = False,
    ) -> List[str]:
        """Return registered service names."""

        with self._lock:

            names = sorted(self._services.keys())

            if include_aliases:
                names.extend(sorted(self._aliases.keys()))

            return names

    def get_descriptor(
        self,
        name: str,
    ) -> Optional[ServiceDescriptor]:
        """
        Return a copy-safe descriptor reference.

        The descriptor itself should be treated as read-only by callers.
        """

        with self._lock:

            canonical_name = self._resolve_name_locked(name)

            return self._services.get(canonical_name)

    def get_status(
        self,
        name: str,
    ) -> Optional[ServiceStatus]:
        """Return the runtime status of a service."""

        descriptor = self.get_descriptor(name)

        if descriptor is None:
            return None

        return descriptor.status

    def diagnostics(self) -> Dict[str, Any]:
        """
        Return registry diagnostics.

        This method is designed for HealthMonitor,
        EngineManager, debugging, and UI diagnostics.
        """

        with self._lock:

            services: Dict[str, Any] = {}

            for name, descriptor in self._services.items():

                services[name] = {
                    "status": descriptor.status.value,
                    "lifetime": descriptor.lifetime.value,
                    "initialized": (descriptor.instance is not None),
                    "dependencies": list(descriptor.dependencies),
                    "aliases": sorted(descriptor.aliases),
                    "error": descriptor.error,
                    "metadata": dict(descriptor.metadata),
                }

            return {
                "shutdown": self._shutdown,
                "service_count": len(self._services),
                "alias_count": len(self._aliases),
                "services": services,
            }

    # ========================================================================
    # SHUTDOWN
    # ========================================================================

    def shutdown(self) -> None:
        """
        Gracefully shut down all initialized services.

        Supported cleanup methods:

            shutdown()
            close()
            stop()
        """

        with self._lock:

            if self._shutdown:
                return

            self._shutdown = True

            services = list(self._services.items())

        # Reverse order is safer because services registered later often
        # depend on services registered earlier.
        for name, descriptor in reversed(services):

            instance = descriptor.instance

            if instance is not None:

                self._shutdown_instance(
                    name,
                    instance,
                )

            with self._lock:
                descriptor.status = ServiceStatus.SHUTDOWN

        logger.info("ServiceRegistry shutdown complete.")

    def _shutdown_instance(
        self,
        name: str,
        instance: Any,
    ) -> None:
        """
        Attempt to gracefully stop a service.
        """

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

                result = method()

                # Support async cleanup methods without forcing the
                # registry to own an event loop.
                if inspect.isawaitable(result):
                    logger.warning(
                        "Async shutdown returned by '%s'. "
                        "The caller should await service cleanup.",
                        name,
                    )

                logger.debug(
                    "Service '%s' cleaned up using %s()",
                    name,
                    method_name,
                )

                return

            except Exception:

                logger.exception(
                    "Failed to clean up service '%s'",
                    name,
                )

                return

    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================

    def _resolve_name_locked(
        self,
        name: str,
    ) -> str:

        if not isinstance(name, str):
            return name

        return self._aliases.get(
            name,
            name,
        )

    def _ensure_not_shutdown(self) -> None:

        if self._shutdown:
            raise ServiceRegistryError("ServiceRegistry has already been shut down.")

    @staticmethod
    def _validate_name(name: str) -> None:

        if not isinstance(name, str) or not name.strip():
            raise ValueError("Service name must be a non-empty string.")

    # ========================================================================
    # PYTHON CONVENIENCE METHODS
    # ========================================================================

    def __contains__(
        self,
        name: str,
    ) -> bool:
        return self.contains(name)

    def __getitem__(
        self,
        name: str,
    ) -> Any:
        return self.get(name)

    def __len__(self) -> int:
        with self._lock:
            return len(self._services)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"services={len(self)}, "
            f"shutdown={self._shutdown}"
            f")"
        )
