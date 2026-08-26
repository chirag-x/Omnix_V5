"""
Omnix V5 - Capability Router

Central capability routing layer for Omnix V5.

The router provides a clean way for the engine, agent and
planning systems to discover and access subsystem capabilities
without tightly coupling themselves to concrete implementations.

Examples:

    router.register(
        "vision",
        vision_service,
        capabilities=[
            "vision",
            "screen_analysis",
            "object_detection",
            "ocr",
        ],
    )

    route = router.resolve("screen_analysis")

    result = router.execute(
        "screen_analysis",
        image=frame,
    )
"""

from __future__ import annotations

import inspect
import logging
import threading

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional

logger = logging.getLogger("omnix.core.capability_router")


# ============================================================================
# EXCEPTIONS
# ============================================================================


class CapabilityRouterError(Exception):
    """Base exception for capability routing errors."""


class CapabilityNotFoundError(CapabilityRouterError):
    """Raised when a capability has no provider."""


class CapabilityUnavailableError(CapabilityRouterError):
    """Raised when no usable provider is available."""


class CapabilityExecutionError(CapabilityRouterError):
    """Raised when a provider cannot execute a capability."""


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class CapabilityProvider:
    """
    Information about a registered capability provider.
    """

    name: str
    provider: Any
    capabilities: List[str] = field(default_factory=list)

    priority: int = 100
    enabled: bool = True

    metadata: Dict[str, Any] = field(default_factory=dict)

    availability_check: Optional[Callable[[], bool]] = None


@dataclass
class CapabilityRoute:
    """
    Resolved route for a capability.
    """

    capability: str
    provider_name: str
    provider: Any
    priority: int

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CapabilityResult:
    """
    Standard result returned by capability execution.
    """

    success: bool
    capability: str

    provider_name: Optional[str] = None

    result: Any = None

    error: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# CAPABILITY ROUTER
# ============================================================================


class CapabilityRouter:
    """
    Central registry and router for Omnix V5 capabilities.

    Multiple providers can support the same capability.

    Providers are selected according to priority:

        Lower priority number = higher preference

    Example:

        vision priority = 10
        fallback_vision priority = 100

    If the first provider is unavailable, the router
    automatically tries the next provider.
    """

    def __init__(self) -> None:

        self._providers: Dict[str, CapabilityProvider] = {}

        self._capabilities: Dict[str, List[str]] = {}

        self._lock = threading.RLock()

        logger.debug("CapabilityRouter initialized")

    # ========================================================================
    # REGISTRATION
    # ========================================================================

    def register(
        self,
        name: str,
        provider: Any,
        *,
        capabilities: Iterable[str],
        priority: int = 100,
        metadata: Optional[Dict[str, Any]] = None,
        availability_check: Optional[Callable[[], bool]] = None,
        replace: bool = False,
    ) -> None:
        """
        Register a provider.

        Parameters
        ----------
        name:
            Unique provider name.

        provider:
            Object or callable that implements
            one or more capabilities.

        capabilities:
            Capability names supported by this provider.

        priority:
            Lower values are preferred.

        metadata:
            Optional provider metadata.

        availability_check:
            Optional callable returning True when
            the provider is currently available.

        replace:
            Replace an existing provider with
            the same name.
        """

        name = self._normalize_name(name)

        if provider is None:

            raise ValueError("Provider cannot be None.")

        normalized_capabilities = [
            self._normalize_capability(capability) for capability in capabilities
        ]

        normalized_capabilities = list(dict.fromkeys(normalized_capabilities))

        if not normalized_capabilities:

            raise ValueError("Provider must support at least " "one capability.")

        if availability_check is not None and not callable(availability_check):

            raise TypeError("availability_check must be callable.")

        with self._lock:

            if name in self._providers and not replace:

                raise CapabilityRouterError(
                    f"Provider '{name}' " "is already registered."
                )

            if name in self._providers:

                self._remove_provider(name)

            entry = CapabilityProvider(
                name=name,
                provider=provider,
                capabilities=(normalized_capabilities),
                priority=priority,
                metadata=dict(metadata or {}),
                availability_check=(availability_check),
            )

            self._providers[name] = entry

            for capability in normalized_capabilities:

                providers = self._capabilities.setdefault(
                    capability,
                    [],
                )

                if name not in providers:

                    providers.append(name)

                self._sort_providers(capability)

        logger.info(
            "Registered provider '%s' " "for capabilities: %s",
            name,
            ", ".join(normalized_capabilities),
        )

    def unregister(
        self,
        name: str,
    ) -> bool:
        """
        Remove a registered provider.

        Returns True when the provider existed.
        """

        name = self._normalize_name(name)

        with self._lock:

            if name not in self._providers:

                return False

            self._remove_provider(name)

            return True

    def _remove_provider(
        self,
        name: str,
    ) -> None:
        """
        Remove provider from capability mappings.

        Caller must hold the lock.
        """

        provider = self._providers.pop(
            name,
            None,
        )

        if provider is None:

            return

        for capability in provider.capabilities:

            providers = self._capabilities.get(capability)

            if providers is None:

                continue

            if name in providers:

                providers.remove(name)

            if not providers:

                self._capabilities.pop(
                    capability,
                    None,
                )

    # ========================================================================
    # PROVIDER STATE
    # ========================================================================

    def enable(
        self,
        name: str,
    ) -> bool:
        """
        Enable a provider.
        """

        return self.set_enabled(
            name,
            True,
        )

    def disable(
        self,
        name: str,
    ) -> bool:
        """
        Disable a provider.
        """

        return self.set_enabled(
            name,
            False,
        )

    def set_enabled(
        self,
        name: str,
        enabled: bool,
    ) -> bool:
        """
        Change provider enabled state.
        """

        name = self._normalize_name(name)

        with self._lock:

            provider = self._providers.get(name)

            if provider is None:

                return False

            provider.enabled = bool(enabled)

            return True

    def is_available(
        self,
        name: str,
    ) -> bool:
        """
        Check whether a provider is usable.
        """

        name = self._normalize_name(name)

        with self._lock:

            provider = self._providers.get(name)

        if provider is None:

            return False

        if not provider.enabled:

            return False

        if provider.availability_check is None:

            return True

        try:

            return bool(provider.availability_check())

        except Exception:

            logger.exception(
                "Availability check failed " "for provider '%s'",
                name,
            )

            return False

    # ========================================================================
    # RESOLUTION
    # ========================================================================

    def resolve(
        self,
        capability: str,
        *,
        exclude: Optional[Iterable[str]] = None,
    ) -> CapabilityRoute:
        """
        Resolve the best available provider
        for a capability.
        """

        capability = self._normalize_capability(capability)

        excluded = {self._normalize_name(name) for name in (exclude or [])}

        with self._lock:

            provider_names = list(
                self._capabilities.get(
                    capability,
                    [],
                )
            )

        if not provider_names:

            raise CapabilityNotFoundError(
                f"No provider registered " f"for capability '{capability}'."
            )

        for provider_name in provider_names:

            if provider_name in excluded:

                continue

            if not self.is_available(provider_name):

                continue

            with self._lock:

                provider = self._providers.get(provider_name)

                if provider is None:

                    continue

                return CapabilityRoute(
                    capability=capability,
                    provider_name=(provider.name),
                    provider=provider.provider,
                    priority=(provider.priority),
                    metadata=dict(provider.metadata),
                )

        raise CapabilityUnavailableError(
            f"No available provider for " f"capability '{capability}'."
        )

    def get_routes(
        self,
        capability: str,
    ) -> List[CapabilityRoute]:
        """
        Return all registered routes for a capability.
        """

        capability = self._normalize_capability(capability)

        with self._lock:

            provider_names = list(
                self._capabilities.get(
                    capability,
                    [],
                )
            )

            routes = []

            for name in provider_names:

                provider = self._providers.get(name)

                if provider is None:

                    continue

                routes.append(
                    CapabilityRoute(
                        capability=capability,
                        provider_name=(provider.name),
                        provider=(provider.provider),
                        priority=(provider.priority),
                        metadata=dict(provider.metadata),
                    )
                )

        return routes

    def can_handle(
        self,
        capability: str,
    ) -> bool:
        """
        Return True if an available provider
        can handle this capability.
        """

        try:

            self.resolve(capability)

            return True

        except (
            CapabilityNotFoundError,
            CapabilityUnavailableError,
        ):

            return False

    # ========================================================================
    # EXECUTION
    # ========================================================================

    def execute(
        self,
        capability: str,
        *args: Any,
        method: Optional[str] = None,
        fallback: bool = True,
        raise_on_error: bool = False,
        **kwargs: Any,
    ) -> CapabilityResult:
        """
        Resolve and execute a capability.

        The router will try fallback providers
        when execution fails if fallback=True.
        """

        capability = self._normalize_capability(capability)

        attempted: List[str] = []

        last_error: Optional[Exception] = None

        while True:

            try:

                route = self.resolve(
                    capability,
                    exclude=attempted,
                )

            except (
                CapabilityNotFoundError,
                CapabilityUnavailableError,
            ) as exc:

                if last_error is None:

                    if raise_on_error:

                        raise

                    return CapabilityResult(
                        success=False,
                        capability=capability,
                        error=str(exc),
                    )

                break

            attempted.append(route.provider_name)

            try:

                result = self._execute_route(
                    route,
                    *args,
                    method=method,
                    **kwargs,
                )

                return CapabilityResult(
                    success=True,
                    capability=capability,
                    provider_name=(route.provider_name),
                    result=result,
                    metadata=dict(route.metadata),
                )

            except Exception as exc:

                last_error = exc

                logger.exception(
                    "Capability '%s' failed " "using provider '%s'",
                    capability,
                    route.provider_name,
                )

                if not fallback:

                    break

        error_message = str(last_error)

        if raise_on_error:

            raise CapabilityExecutionError(
                f"Capability '{capability}' " f"failed: {error_message}"
            ) from last_error

        return CapabilityResult(
            success=False,
            capability=capability,
            provider_name=(attempted[-1] if attempted else None),
            error=error_message,
        )

    def _execute_route(
        self,
        route: CapabilityRoute,
        *args: Any,
        method: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Execute the selected provider.
        """

        provider = route.provider

        if method is not None:

            callback = getattr(
                provider,
                method,
                None,
            )

            if not callable(callback):

                raise CapabilityExecutionError(
                    f"Provider "
                    f"'{route.provider_name}' "
                    f"does not implement "
                    f"method '{method}'."
                )

            return self._invoke(
                callback,
                *args,
                **kwargs,
            )

        if callable(provider):

            return self._invoke(
                provider,
                *args,
                **kwargs,
            )

        callback = self._find_capability_method(
            provider,
            route.capability,
        )

        if callback is None:

            raise CapabilityExecutionError(
                f"Provider "
                f"'{route.provider_name}' "
                f"cannot execute capability "
                f"'{route.capability}'."
            )

        return self._invoke(
            callback,
            *args,
            **kwargs,
        )

    def _find_capability_method(
        self,
        provider: Any,
        capability: str,
    ) -> Optional[Callable[..., Any]]:
        """
        Find the most appropriate provider method.
        """

        candidates = [
            capability,
            capability.replace(
                "-",
                "_",
            ),
        ]

        candidates.extend(
            [
                "execute",
                "handle",
                "process",
                "run",
            ]
        )

        for method_name in candidates:

            callback = getattr(
                provider,
                method_name,
                None,
            )

            if callable(callback):

                return callback

        return None

    @staticmethod
    def _invoke(
        callback: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Invoke a synchronous provider callback.
        """

        result = callback(
            *args,
            **kwargs,
        )

        if inspect.isawaitable(result):

            raise CapabilityExecutionError(
                "Async providers are not supported "
                "by the synchronous "
                "CapabilityRouter."
            )

        return result

    # ========================================================================
    # DISCOVERY
    # ========================================================================

    def get_provider(
        self,
        name: str,
    ) -> Optional[CapabilityProvider]:
        """
        Return a provider by name.
        """

        name = self._normalize_name(name)

        with self._lock:

            provider = self._providers.get(name)

            if provider is None:

                return None

            return CapabilityProvider(
                name=provider.name,
                provider=provider.provider,
                capabilities=list(provider.capabilities),
                priority=provider.priority,
                enabled=provider.enabled,
                metadata=dict(provider.metadata),
                availability_check=(provider.availability_check),
            )

    def list_capabilities(
        self,
    ) -> List[str]:
        """
        Return all registered capabilities.
        """

        with self._lock:

            return sorted(self._capabilities.keys())

    def list_providers(
        self,
        capability: Optional[str] = None,
    ) -> List[str]:
        """
        Return registered providers.

        When capability is supplied, only providers
        supporting that capability are returned.
        """

        with self._lock:

            if capability is None:

                return sorted(self._providers.keys())

            capability = self._normalize_capability(capability)

            return list(
                self._capabilities.get(
                    capability,
                    [],
                )
            )

    # ========================================================================
    # DIAGNOSTICS
    # ========================================================================

    def diagnostics(
        self,
    ) -> Dict[str, Any]:
        """
        Return router diagnostic information.
        """

        with self._lock:

            providers = {}

            for name, provider in self._providers.items():

                providers[name] = {
                    "capabilities": list(provider.capabilities),
                    "priority": (provider.priority),
                    "enabled": (provider.enabled),
                    "available": (self.is_available(name)),
                    "metadata": dict(provider.metadata),
                }

            capabilities = {
                capability: list(providers)
                for capability, providers in self._capabilities.items()
            }

        return {
            "provider_count": len(providers),
            "capability_count": len(capabilities),
            "providers": providers,
            "capabilities": capabilities,
        }

    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================

    def _sort_providers(
        self,
        capability: str,
    ) -> None:
        """
        Sort capability providers by priority.
        """

        providers = self._capabilities.get(
            capability,
            [],
        )

        providers.sort(
            key=lambda name: (
                self._providers[name].priority
                if name in self._providers
                else float("inf")
            )
        )

    @staticmethod
    def _normalize_name(
        name: str,
    ) -> str:
        """
        Normalize provider names.
        """

        if not isinstance(
            name,
            str,
        ):

            raise TypeError("Provider name must be a string.")

        name = (
            name.strip()
            .lower()
            .replace(
                " ",
                "_",
            )
            .replace(
                "-",
                "_",
            )
        )

        if not name:

            raise ValueError("Provider name cannot be empty.")

        return name

    @staticmethod
    def _normalize_capability(
        capability: str,
    ) -> str:
        """
        Normalize capability names.
        """

        if not isinstance(
            capability,
            str,
        ):

            raise TypeError("Capability must be a string.")

        capability = (
            capability.strip()
            .lower()
            .replace(
                " ",
                "_",
            )
            .replace(
                "-",
                "_",
            )
        )

        if not capability:

            raise ValueError("Capability cannot be empty.")

        return capability

    def __contains__(
        self,
        capability: str,
    ) -> bool:

        return self.can_handle(capability)

    def __len__(
        self,
    ) -> int:

        with self._lock:

            return len(self._providers)

    def __repr__(
        self,
    ) -> str:

        return (
            f"{self.__class__.__name__}("
            f"providers={len(self)}, "
            f"capabilities="
            f"{len(self.list_capabilities())}"
            f")"
        )
