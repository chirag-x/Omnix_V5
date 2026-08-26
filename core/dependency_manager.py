"""
Omnix V5 - Dependency Manager

Manages dependencies between Omnix services and validates optional
Python modules required by V5 and legacy subsystems.

This module does not initialize services itself. Its responsibility is to:

    - Register dependency requirements
    - Validate service dependencies
    - Validate Python package availability
    - Build dependency graphs
    - Detect circular dependencies
    - Calculate safe startup order
    - Provide diagnostics for EngineManager and HealthMonitor

Designed to work with:
    - ServiceRegistry
    - EngineManager
    - LifecycleManager
    - Legacy compatibility modules
"""

from __future__ import annotations

import importlib.util
import logging
import threading

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Set

logger = logging.getLogger("omnix.core.dependency_manager")


# ============================================================================
# EXCEPTIONS
# ============================================================================


class DependencyError(Exception):
    """Base exception for dependency-related errors."""


class MissingDependencyError(DependencyError):
    """Raised when a required dependency is missing."""


class CircularDependencyError(DependencyError):
    """Raised when a circular dependency is detected."""


# ============================================================================
# ENUMS
# ============================================================================


class DependencyType(str, Enum):
    """
    Type of dependency.

    SERVICE:
        Another Omnix service registered in ServiceRegistry.

    MODULE:
        A Python module/package available through importlib.

    OPTIONAL:
        A dependency that improves functionality but is not required
        for the system to continue running.
    """

    SERVICE = "service"
    MODULE = "module"
    OPTIONAL = "optional"


class DependencyStatus(str, Enum):
    """Current availability status."""

    UNKNOWN = "unknown"
    AVAILABLE = "available"
    MISSING = "missing"
    FAILED = "failed"


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class Dependency:
    """
    Represents one dependency.

    Example:

        Dependency(
            name="vision",
            dependency_type=DependencyType.SERVICE,
            required=True,
        )
    """

    name: str

    dependency_type: DependencyType = DependencyType.SERVICE

    required: bool = True

    description: Optional[str] = None

    status: DependencyStatus = DependencyStatus.UNKNOWN

    error: Optional[str] = None


@dataclass
class ServiceDependencies:
    """
    Dependency configuration for one service.
    """

    service_name: str

    dependencies: List[Dependency] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DependencyReport:
    """
    Validation result for a dependency set.
    """

    valid: bool = True

    missing_required: List[str] = field(default_factory=list)

    missing_optional: List[str] = field(default_factory=list)

    available: List[str] = field(default_factory=list)

    errors: List[str] = field(default_factory=list)


# ============================================================================
# DEPENDENCY MANAGER
# ============================================================================


class DependencyManager:
    """
    Manages Omnix service and module dependencies.

    The manager can operate with or without a ServiceRegistry.

    Example:

        dependencies = DependencyManager(registry)

        dependencies.register(
            "skills",
            required_services=[
                "context",
                "memory",
            ],
            optional_services=[
                "vision",
            ],
        )

        dependencies.validate("skills")

        order = dependencies.get_startup_order()
    """

    def __init__(
        self,
        registry: Optional[Any] = None,
    ) -> None:

        self._registry = registry

        self._dependencies: Dict[str, ServiceDependencies] = {}

        self._lock = threading.RLock()

        logger.debug("DependencyManager initialized")

    # ========================================================================
    # REGISTRATION
    # ========================================================================

    def register(
        self,
        service_name: str,
        *,
        required_services: Optional[Iterable[str]] = None,
        optional_services: Optional[Iterable[str]] = None,
        required_modules: Optional[Iterable[str]] = None,
        optional_modules: Optional[Iterable[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        replace: bool = True,
    ) -> None:
        """
        Register dependencies for a service.

        Parameters
        ----------
        service_name:
            Name of the service.

        required_services:
            Services that must exist before this service can start.

        optional_services:
            Services that may be used when available.

        required_modules:
            Python modules/packages required for operation.

        optional_modules:
            Python modules/packages that enable extra features.

        replace:
            Replace an existing dependency definition.
        """

        self._validate_name(service_name)

        dependencies: List[Dependency] = []

        for name in required_services or []:
            dependencies.append(
                Dependency(
                    name=name,
                    dependency_type=(DependencyType.SERVICE),
                    required=True,
                )
            )

        for name in optional_services or []:
            dependencies.append(
                Dependency(
                    name=name,
                    dependency_type=(DependencyType.OPTIONAL),
                    required=False,
                )
            )

        for name in required_modules or []:
            dependencies.append(
                Dependency(
                    name=name,
                    dependency_type=(DependencyType.MODULE),
                    required=True,
                )
            )

        for name in optional_modules or []:
            dependencies.append(
                Dependency(
                    name=name,
                    dependency_type=(DependencyType.MODULE),
                    required=False,
                )
            )

        with self._lock:

            if service_name in self._dependencies and not replace:
                raise DependencyError(
                    f"Dependencies already registered for " f"'{service_name}'."
                )

            self._dependencies[service_name] = ServiceDependencies(
                service_name=service_name,
                dependencies=dependencies,
                metadata=dict(metadata or {}),
            )

        logger.debug(
            "Registered %d dependencies for '%s'",
            len(dependencies),
            service_name,
        )

    def register_service(
        self,
        service_name: str,
        dependencies: Iterable[str],
        *,
        optional: bool = False,
        replace: bool = True,
    ) -> None:
        """
        Convenience method for registering service dependencies.
        """

        if optional:
            self.register(
                service_name,
                optional_services=dependencies,
                replace=replace,
            )
        else:
            self.register(
                service_name,
                required_services=dependencies,
                replace=replace,
            )

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def validate(
        self,
        service_name: str,
        *,
        raise_on_error: bool = False,
    ) -> DependencyReport:
        """
        Validate dependencies for a service.
        """

        report = DependencyReport()

        with self._lock:

            definition = self._dependencies.get(service_name)

            if definition is None:
                return report

            dependencies = list(definition.dependencies)

        for dependency in dependencies:

            available = self._check_dependency(dependency)

            if available:

                dependency.status = DependencyStatus.AVAILABLE

                report.available.append(dependency.name)

                continue

            dependency.status = DependencyStatus.MISSING

            message = (
                f"Missing dependency "
                f"'{dependency.name}' "
                f"for service '{service_name}'."
            )

            dependency.error = message

            if dependency.required:

                report.valid = False

                report.missing_required.append(dependency.name)

                report.errors.append(message)

            else:

                report.missing_optional.append(dependency.name)

        if raise_on_error and not report.valid:

            raise MissingDependencyError("; ".join(report.errors))

        return report

    def validate_all(
        self,
        *,
        raise_on_error: bool = False,
    ) -> Dict[str, DependencyReport]:
        """
        Validate all registered dependency definitions.
        """

        with self._lock:

            services = list(self._dependencies.keys())

        reports: Dict[str, DependencyReport] = {}

        for service_name in services:

            reports[service_name] = self.validate(
                service_name,
                raise_on_error=False,
            )

        if raise_on_error:

            failures = []

            for name, report in reports.items():

                if not report.valid:

                    failures.extend(f"{name}: {error}" for error in report.errors)

            if failures:

                raise MissingDependencyError("\n".join(failures))

        return reports

    def _check_dependency(
        self,
        dependency: Dependency,
    ) -> bool:
        """
        Check whether one dependency is available.
        """

        if dependency.dependency_type in (
            DependencyType.SERVICE,
            DependencyType.OPTIONAL,
        ):

            return self._service_exists(dependency.name)

        if dependency.dependency_type == DependencyType.MODULE:

            return self._module_exists(dependency.name)

        return False

    # ========================================================================
    # SERVICE CHECKING
    # ========================================================================

    def _service_exists(
        self,
        service_name: str,
    ) -> bool:
        """
        Check whether a service exists.

        Supports the V5 ServiceRegistry and legacy
        registry implementations.
        """

        registry = self._registry

        if registry is None:
            return False

        try:

            contains = getattr(
                registry,
                "contains",
                None,
            )

            if callable(contains):
                return bool(contains(service_name))

            is_registered = getattr(
                registry,
                "is_registered",
                None,
            )

            if callable(is_registered):
                return bool(is_registered(service_name))

            return service_name in registry

        except Exception:

            logger.debug(
                "Failed checking service '%s'",
                service_name,
                exc_info=True,
            )

            return False

    @staticmethod
    def _module_exists(
        module_name: str,
    ) -> bool:
        """
        Check whether a Python module can be found
        without importing it.
        """

        try:

            return importlib.util.find_spec(module_name) is not None

        except (
            ModuleNotFoundError,
            ValueError,
            ImportError,
        ):

            return False

    # ========================================================================
    # DEPENDENCY GRAPH
    # ========================================================================

    def get_dependency_graph(
        self,
        *,
        include_optional: bool = False,
    ) -> Dict[str, Set[str]]:
        """
        Build a graph of internal service dependencies.

        Only service dependencies are included.
        Python modules are not startup nodes.
        """

        graph: Dict[str, Set[str]] = {}

        with self._lock:

            definitions = dict(self._dependencies)

        for service_name, definition in definitions.items():

            graph.setdefault(
                service_name,
                set(),
            )

            for dependency in definition.dependencies:

                is_service = dependency.dependency_type == DependencyType.SERVICE

                is_optional = dependency.dependency_type == DependencyType.OPTIONAL

                if not is_service:

                    if not (include_optional and is_optional):
                        continue

                graph[service_name].add(dependency.name)

                graph.setdefault(
                    dependency.name,
                    set(),
                )

        return graph

    # ========================================================================
    # CIRCULAR DEPENDENCY DETECTION
    # ========================================================================

    def detect_cycles(
        self,
    ) -> List[List[str]]:
        """
        Detect circular service dependencies.

        Returns a list of cycles.
        """

        graph = self.get_dependency_graph()

        visited: Set[str] = set()
        visiting: Set[str] = set()

        path: List[str] = []

        cycles: List[List[str]] = []

        def visit(
            node: str,
        ) -> None:

            if node in visiting:

                try:
                    start = path.index(node)

                    cycle = path[start:] + [node]

                    if cycle not in cycles:
                        cycles.append(cycle)

                except ValueError:
                    pass

                return

            if node in visited:
                return

            visiting.add(node)
            path.append(node)

            for dependency in graph.get(
                node,
                set(),
            ):
                visit(dependency)

            path.pop()

            visiting.remove(node)

            visited.add(node)

        for node in graph:
            visit(node)

        return cycles

    def validate_graph(
        self,
        *,
        raise_on_cycle: bool = False,
    ) -> List[List[str]]:
        """
        Validate the dependency graph and optionally
        raise when cycles are found.
        """

        cycles = self.detect_cycles()

        if cycles:

            formatted = []

            for cycle in cycles:
                formatted.append(" -> ".join(cycle))

            message = "Circular dependencies detected: " + "; ".join(formatted)

            logger.error(message)

            if raise_on_cycle:
                raise CircularDependencyError(message)

        return cycles

    # ========================================================================
    # STARTUP ORDER
    # ========================================================================

    def get_startup_order(
        self,
        *,
        raise_on_cycle: bool = True,
    ) -> List[str]:
        """
        Calculate dependency-safe startup order.

        Example:

            memory
                ↓
            context
                ↓
            skills

        Returns:

            ["memory", "context", "skills"]
        """

        graph = self.get_dependency_graph()

        cycles = self.validate_graph(raise_on_cycle=False)

        if cycles and raise_on_cycle:

            formatted = [" -> ".join(cycle) for cycle in cycles]

            raise CircularDependencyError(
                "Cannot calculate startup order due to "
                "circular dependencies: " + "; ".join(formatted)
            )

        # In-degree represents how many dependencies
        # must be initialized before a node.
        in_degree: Dict[str, int] = {
            node: len(dependencies) for node, dependencies in graph.items()
        }

        dependents: Dict[str, Set[str]] = {node: set() for node in graph}

        for service, dependencies in graph.items():

            for dependency in dependencies:

                dependents.setdefault(
                    dependency,
                    set(),
                ).add(service)

        ready = sorted(node for node, degree in in_degree.items() if degree == 0)

        result: List[str] = []

        while ready:

            node = ready.pop(0)

            result.append(node)

            for dependent in sorted(
                dependents.get(
                    node,
                    set(),
                )
            ):

                in_degree[dependent] -= 1

                if in_degree[dependent] == 0:

                    ready.append(dependent)

                    ready.sort()

        if len(result) != len(graph):

            unresolved = [node for node in graph if node not in result]

            if raise_on_cycle:

                raise CircularDependencyError(
                    "Unable to resolve startup order: " + ", ".join(unresolved)
                )

            result.extend(unresolved)

        return result

    def get_shutdown_order(
        self,
    ) -> List[str]:
        """
        Return reverse dependency order for shutdown.
        """

        return list(reversed(self.get_startup_order()))

    # ========================================================================
    # DYNAMIC DEPENDENCIES
    # ========================================================================

    def add_dependency(
        self,
        service_name: str,
        dependency_name: str,
        *,
        dependency_type: DependencyType = (DependencyType.SERVICE),
        required: bool = True,
    ) -> None:
        """
        Add a dependency to an existing service definition.
        """

        self._validate_name(service_name)
        self._validate_name(dependency_name)

        with self._lock:

            definition = self._dependencies.get(service_name)

            if definition is None:

                definition = ServiceDependencies(service_name=service_name)

                self._dependencies[service_name] = definition

            for dependency in definition.dependencies:

                if (
                    dependency.name == dependency_name
                    and dependency.dependency_type == dependency_type
                ):
                    return

            definition.dependencies.append(
                Dependency(
                    name=dependency_name,
                    dependency_type=dependency_type,
                    required=required,
                )
            )

    def remove_dependency(
        self,
        service_name: str,
        dependency_name: str,
    ) -> bool:
        """
        Remove a dependency.

        Returns True when something was removed.
        """

        with self._lock:

            definition = self._dependencies.get(service_name)

            if definition is None:
                return False

            original_count = len(definition.dependencies)

            definition.dependencies = [
                dependency
                for dependency in definition.dependencies
                if dependency.name != dependency_name
            ]

            return len(definition.dependencies) != original_count

    # ========================================================================
    # INSPECTION
    # ========================================================================

    def get_dependencies(
        self,
        service_name: str,
    ) -> List[Dependency]:
        """
        Return dependencies for a service.
        """

        with self._lock:

            definition = self._dependencies.get(service_name)

            if definition is None:
                return []

            return list(definition.dependencies)

    def list_services(
        self,
    ) -> List[str]:
        """Return services with dependency definitions."""

        with self._lock:

            return sorted(self._dependencies.keys())

    def diagnostics(
        self,
    ) -> Dict[str, Any]:
        """
        Return diagnostics for debugging and health monitoring.
        """

        with self._lock:

            definitions = dict(self._dependencies)

        services: Dict[str, Any] = {}

        for name, definition in definitions.items():

            services[name] = {
                "dependencies": [
                    {
                        "name": dependency.name,
                        "type": (dependency.dependency_type.value),
                        "required": (dependency.required),
                        "status": (dependency.status.value),
                        "error": dependency.error,
                    }
                    for dependency in definition.dependencies
                ],
                "metadata": dict(definition.metadata),
            }

        cycles = self.detect_cycles()

        return {
            "service_count": len(services),
            "services": services,
            "cycles": cycles,
            "valid": not bool(cycles),
        }

    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================

    @staticmethod
    def _validate_name(
        name: str,
    ) -> None:

        if not isinstance(name, str) or not name.strip():
            raise ValueError("Dependency names must be " "non-empty strings.")

    def __contains__(
        self,
        service_name: str,
    ) -> bool:

        with self._lock:
            return service_name in self._dependencies

    def __len__(self) -> int:

        with self._lock:
            return len(self._dependencies)

    def __repr__(
        self,
    ) -> str:

        return f"{self.__class__.__name__}(" f"services={len(self)}" f")"
