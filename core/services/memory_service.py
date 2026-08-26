"""
Omnix V5 - Memory Service

Core-level bridge between OmnixEngine and the real Omnix
memory architecture.

Main execution path:

    OmnixEngine
        ↓
    MemoryService
        ↓
    MemoryCoordinator
        ├── MemoryManager
        ├── BehaviorMemory
        └── SystemMemory

UIPatternMemory remains owned by VisionManager.
"""

from __future__ import annotations

import inspect

from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

# ============================================================================
# RESULT OBJECTS
# ============================================================================


@dataclass
class MemoryResult:
    """
    Normalized result returned from a memory operation.
    """

    success: bool

    value: Any = None

    provider: Optional[str] = None

    operation: Optional[str] = None

    error: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:

        if self.provider is not None:
            self.provider = str(self.provider).strip() or None

        if self.operation is not None:
            self.operation = str(self.operation).strip() or None

        if self.error is not None:
            self.error = str(self.error).strip() or None

        if not isinstance(self.metadata, dict):
            raise TypeError("metadata must be a dictionary.")

        self.metadata = dict(self.metadata)

    @property
    def failed(self) -> bool:
        return not self.success

    def to_dict(self) -> Dict[str, Any]:

        return {
            "success": self.success,
            "value": self.value,
            "provider": self.provider,
            "operation": self.operation,
            "error": self.error,
            "metadata": dict(self.metadata),
        }


@dataclass
class MemoryProviderInfo:
    """
    Information about a registered memory provider.
    """

    name: str

    capabilities: List[str] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:

        self.name = str(self.name).strip()

        if not self.name:
            raise ValueError("Provider name cannot be empty.")

        self.capabilities = [
            str(capability).strip()
            for capability in self.capabilities
            if str(capability).strip()
        ]

        if not isinstance(self.metadata, dict):
            raise TypeError("metadata must be a dictionary.")

        self.metadata = dict(self.metadata)

    def to_dict(self) -> Dict[str, Any]:

        return {
            "name": self.name,
            "capabilities": list(self.capabilities),
            "metadata": dict(self.metadata),
        }


# ============================================================================
# MEMORY SERVICE
# ============================================================================


class MemoryService:
    """
    Stable Core-level interface for Omnix memory.

    The main V5 provider is MemoryCoordinator.

    Additional providers may still be registered for future
    extensions or compatibility.
    """

    DEFAULT_PROVIDER = "omnix_memory"

    def __init__(
        self,
        memory: Optional[Any] = None,
        auto_initialize: bool = True,
    ) -> None:

        self._lock = RLock()

        self._providers: Dict[str, Any] = {}

        self._provider_info: Dict[
            str,
            MemoryProviderInfo,
        ] = {}

        self._initialized = False

        self.memory = memory

        if auto_initialize:
            self.initialize()

    # ====================================================================
    # INITIALIZATION
    # ====================================================================

    def initialize(self) -> bool:
        """
        Initialize the main Omnix V5 memory provider.
        """

        if self._initialized:
            return self.has_provider(self.DEFAULT_PROVIDER)

        try:

            if self.memory is None:

                from memory.memory_coordinator import (
                    MemoryCoordinator,
                )

                self.memory = MemoryCoordinator(
                    auto_initialize=True,
                )

            self.register_provider(
                self.DEFAULT_PROVIDER,
                self.memory,
                capabilities=[
                    "semantic_memory",
                    "behavior_memory",
                    "system_memory",
                    "remember",
                    "recall",
                    "search",
                    "clear",
                ],
                metadata={
                    "type": "memory_coordinator",
                    "primary": True,
                },
                replace=True,
            )

            self._initialized = True

            logger.info("MemoryService connected to " "MemoryCoordinator.")

            return True

        except Exception as error:

            logger.exception("Failed to initialize MemoryService: " f"{error}")

            self._initialized = True

            return False

    # Compatibility alias
    start = initialize

    def shutdown(self) -> None:
        """
        Shutdown memory service safely.
        """

        with self._lock:

            providers = list(self._providers.items())

        for provider_name, provider in providers:

            for method_name in (
                "shutdown",
                "close",
                "stop",
            ):

                method = getattr(
                    provider,
                    method_name,
                    None,
                )

                if not callable(method):
                    continue

                try:

                    result = method()

                    if inspect.isawaitable(result):

                        logger.warning(
                            "Async shutdown is not supported "
                            f"for memory provider: "
                            f"{provider_name}"
                        )

                    break

                except Exception as error:

                    logger.warning(
                        f"Memory provider shutdown failed "
                        f"({provider_name}): {error}"
                    )

        with self._lock:

            self._providers.clear()

            self._provider_info.clear()

        self.memory = None

        self._initialized = False

        logger.info("MemoryService shutdown complete.")

    stop = shutdown
    close = shutdown

    # ====================================================================
    # PROVIDER REGISTRATION
    # ====================================================================

    def register_provider(
        self,
        name: str,
        provider: Any,
        *,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        replace: bool = False,
    ) -> None:
        """
        Register a memory provider.
        """

        normalized_name = self._normalize_provider_name(name)

        if provider is None:
            raise ValueError("Memory provider cannot be None.")

        with self._lock:

            if normalized_name in self._providers and not replace:
                raise ValueError(
                    f"Memory provider already exists: " f"{normalized_name}"
                )

            self._providers[normalized_name] = provider

            self._provider_info[normalized_name] = MemoryProviderInfo(
                name=normalized_name,
                capabilities=(capabilities or self._get_capabilities(provider)),
                metadata=metadata or {},
            )

    # Compatibility aliases
    add_provider = register_provider

    def unregister_provider(
        self,
        name: str,
    ) -> Optional[Any]:

        normalized_name = self._normalize_provider_name(name)

        with self._lock:

            self._provider_info.pop(
                normalized_name,
                None,
            )

            return self._providers.pop(
                normalized_name,
                None,
            )

    remove_provider = unregister_provider

    def get_provider(
        self,
        name: Optional[str] = None,
    ) -> Optional[Any]:

        self._ensure_initialized()

        provider_name = (
            self._normalize_provider_name(name)
            if name is not None
            else self.DEFAULT_PROVIDER
        )

        with self._lock:

            return self._providers.get(provider_name)

    def has_provider(
        self,
        name: str,
    ) -> bool:

        normalized_name = self._normalize_provider_name(name)

        with self._lock:

            return normalized_name in self._providers

    # ====================================================================
    # PROVIDER INFORMATION
    # ====================================================================

    def list_providers(
        self,
    ) -> List[MemoryProviderInfo]:

        with self._lock:

            return list(self._provider_info.values())

    # ====================================================================
    # SEMANTIC MEMORY
    # ====================================================================

    def remember(
        self,
        memory: Any,
        value: Any = None,
        *args: Any,
        provider: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> MemoryResult:
        """
        Store information in semantic memory.

        Supports both:

            remember("Some information")

        and legacy-style:

            remember("key", "value")
        """

        self._ensure_initialized()

        if value is not None:

            if isinstance(memory, str):

                memory_text = f"{memory}: {value}"

            else:

                memory_text = {
                    "key": memory,
                    "value": value,
                }

        else:

            memory_text = memory

        return self._call_operation(
            operation="remember",
            method_names=(
                "remember",
                "add_memory",
                "store",
                "save",
                "add",
            ),
            provider=provider,
            args=(
                memory_text,
                *args,
            ),
            kwargs={
                "metadata": metadata,
                **kwargs,
            },
        )

    store = remember
    save = remember
    add_memory = remember

    def recall(
        self,
        query: Any,
        default: Any = None,
        *args: Any,
        provider: Optional[str] = None,
        limit: int = 5,
        **kwargs: Any,
    ) -> MemoryResult:
        """
        Recall semantically relevant memories.
        """

        self._ensure_initialized()

        result = self._call_operation(
            operation="recall",
            method_names=(
                "recall",
                "search",
                "search_memory",
                "find",
            ),
            provider=provider,
            args=(
                query,
                *args,
            ),
            kwargs={
                "limit": limit,
                **kwargs,
            },
        )

        if result.success and result.value is None and default is not None:
            result.value = default

        return result

    retrieve = recall
    load = recall

    def search(
        self,
        query: Any,
        *args: Any,
        provider: Optional[str] = None,
        limit: int = 5,
        **kwargs: Any,
    ) -> MemoryResult:
        """
        Search semantic memory.
        """

        self._ensure_initialized()

        return self._call_operation(
            operation="search",
            method_names=(
                "search",
                "recall",
                "search_memory",
                "find",
                "query",
            ),
            provider=provider,
            args=(
                query,
                *args,
            ),
            kwargs={
                "limit": limit,
                **kwargs,
            },
        )

    query = search
    find = search

    # ====================================================================
    # BEHAVIOR MEMORY
    # ====================================================================

    def remember_behavior(
        self,
        command: str,
        plan: Any,
        **kwargs: Any,
    ) -> MemoryResult:

        return self._call_operation(
            operation="remember_behavior",
            method_names=(
                "remember_behavior",
                "learn_behavior",
            ),
            provider=self.DEFAULT_PROVIDER,
            args=(
                command,
                plan,
            ),
            kwargs=kwargs,
        )

    def recall_behavior(
        self,
        command: str,
        **kwargs: Any,
    ) -> MemoryResult:

        return self._call_operation(
            operation="recall_behavior",
            method_names=(
                "recall_behavior",
                "get_learned_behavior",
            ),
            provider=self.DEFAULT_PROVIDER,
            args=(command,),
            kwargs=kwargs,
        )

    learn_behavior = remember_behavior

    get_learned_behavior = recall_behavior

    # ====================================================================
    # SYSTEM MEMORY
    # ====================================================================

    def remember_system(
        self,
        key: str,
        value: Any,
        **kwargs: Any,
    ) -> MemoryResult:

        return self._call_operation(
            operation="remember_system",
            method_names=("remember_system",),
            provider=self.DEFAULT_PROVIDER,
            args=(
                key,
                value,
            ),
            kwargs=kwargs,
        )

    def recall_system(
        self,
        key: str,
        default: Any = None,
        **kwargs: Any,
    ) -> MemoryResult:

        result = self._call_operation(
            operation="recall_system",
            method_names=("recall_system",),
            provider=self.DEFAULT_PROVIDER,
            args=(key,),
            kwargs=kwargs,
        )

        if result.success and result.value is None:
            result.value = default

        return result

    def add_recent_app(
        self,
        app_name: str,
        **kwargs: Any,
    ) -> MemoryResult:

        return self._call_operation(
            operation="add_recent_app",
            method_names=("add_recent_app",),
            provider=self.DEFAULT_PROVIDER,
            args=(app_name,),
            kwargs=kwargs,
        )

    def get_recent_apps(
        self,
        **kwargs: Any,
    ) -> MemoryResult:

        return self._call_operation(
            operation="get_recent_apps",
            method_names=("get_recent_apps",),
            provider=self.DEFAULT_PROVIDER,
            args=(),
            kwargs=kwargs,
        )

    def remember_alias(
        self,
        alias: str,
        target: str,
        **kwargs: Any,
    ) -> MemoryResult:

        return self._call_operation(
            operation="remember_alias",
            method_names=("remember_alias",),
            provider=self.DEFAULT_PROVIDER,
            args=(
                alias,
                target,
            ),
            kwargs=kwargs,
        )

    def resolve_alias(
        self,
        alias: str,
        default: Any = None,
        **kwargs: Any,
    ) -> MemoryResult:

        result = self._call_operation(
            operation="resolve_alias",
            method_names=("resolve_alias",),
            provider=self.DEFAULT_PROVIDER,
            args=(alias,),
            kwargs=kwargs,
        )

        if result.success and result.value is None:
            result.value = default

        return result

    def record_failure(
        self,
        failure: Any,
        **kwargs: Any,
    ) -> MemoryResult:

        return self._call_operation(
            operation="record_failure",
            method_names=("record_failure",),
            provider=self.DEFAULT_PROVIDER,
            args=(failure,),
            kwargs=kwargs,
        )

    # ====================================================================
    # CLEAR
    # ====================================================================

    def clear(
        self,
        memory_type: Optional[str] = None,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> MemoryResult:
        """
        Clear memory.

        Examples:

            clear()
            clear("semantic")
            clear("behavior")
            clear("system")
        """

        return self._call_operation(
            operation="clear",
            method_names=(
                "clear",
                "reset",
                "clear_memory",
            ),
            provider=(provider or self.DEFAULT_PROVIDER),
            args=(
                (
                    memory_type,
                    *args,
                )
                if memory_type is not None
                else args
            ),
            kwargs=kwargs,
        )

    reset = clear

    # ====================================================================
    # GENERIC EXECUTION
    # ====================================================================

    def execute(
        self,
        operation: str,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> MemoryResult:
        """
        Execute a custom memory operation.
        """

        normalized_operation = self._normalize_operation(operation)

        return self._call_operation(
            operation=normalized_operation,
            method_names=(normalized_operation,),
            provider=provider,
            args=args,
            kwargs=kwargs,
        )

    # ====================================================================
    # STATUS / HEALTH
    # ====================================================================

    def status(
        self,
    ) -> Dict[str, Any]:

        self._ensure_initialized()

        provider = self.get_provider(self.DEFAULT_PROVIDER)

        memory_status = None

        if provider is not None:

            method = getattr(
                provider,
                "status",
                None,
            )

            if callable(method):

                try:
                    memory_status = method()

                except Exception as error:

                    memory_status = {
                        "error": str(error),
                    }

        return {
            "initialized": self._initialized,
            "primary_provider": (
                self.DEFAULT_PROVIDER
                if self.has_provider(self.DEFAULT_PROVIDER)
                else None
            ),
            "providers": [item.to_dict() for item in self.list_providers()],
            "memory": memory_status,
        }

    def health(
        self,
    ) -> Dict[str, Any]:

        provider = self.get_provider(self.DEFAULT_PROVIDER)

        if provider is None:

            return {
                "healthy": False,
                "reason": ("MemoryCoordinator is unavailable."),
            }

        method = getattr(
            provider,
            "health",
            None,
        )

        if callable(method):

            try:
                result = method()

                if isinstance(result, dict):
                    return result

                return {
                    "healthy": bool(result),
                }

            except Exception as error:

                return {
                    "healthy": False,
                    "error": str(error),
                }

        return {
            "healthy": True,
        }

    # ====================================================================
    # INTERNAL ROUTING
    # ====================================================================

    def _ensure_initialized(
        self,
    ) -> None:

        if not self._initialized:
            self.initialize()

    def _call_operation(
        self,
        *,
        operation: str,
        method_names: Tuple[str, ...],
        provider: Optional[str],
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> MemoryResult:

        self._ensure_initialized()

        providers = self._select_providers(provider)

        if not providers:

            return MemoryResult(
                success=False,
                operation=operation,
                error=("No memory providers are " "registered."),
            )

        errors: List[str] = []

        for (
            provider_name,
            provider_object,
        ) in providers:

            try:

                result = self._call_provider(
                    provider_object,
                    method_names,
                    *args,
                    **kwargs,
                )

                if inspect.isawaitable(result):

                    raise RuntimeError(
                        "Async memory execution is not "
                        "supported by this synchronous "
                        "service."
                    )

                return self._normalize_result(
                    result,
                    provider=provider_name,
                    operation=operation,
                )

            except Exception as error:

                errors.append(f"{provider_name}: {error}")

        return MemoryResult(
            success=False,
            operation=operation,
            error=("; ".join(errors) or "Memory operation failed."),
        )

    @staticmethod
    def _call_provider(
        provider: Any,
        method_names: Tuple[str, ...],
        *args: Any,
        **kwargs: Any,
    ) -> Any:

        last_error = None

        for method_name in method_names:

            method = getattr(
                provider,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:

                return method(
                    *args,
                    **kwargs,
                )

            except TypeError as error:

                last_error = error

                try:

                    return method(*args)

                except TypeError as retry_error:

                    last_error = retry_error

                    continue

        if last_error is not None:
            raise last_error

        raise AttributeError(
            "Provider does not support any of "
            f"these methods: "
            f"{', '.join(method_names)}"
        )

    def _select_providers(
        self,
        provider: Optional[str],
    ) -> List[Tuple[str, Any]]:

        with self._lock:

            if provider is not None:

                provider_name = self._normalize_provider_name(provider)

                provider_object = self._providers.get(provider_name)

                if provider_object is None:
                    return []

                return [
                    (
                        provider_name,
                        provider_object,
                    )
                ]

            primary = self._providers.get(self.DEFAULT_PROVIDER)

            others = [
                (
                    name,
                    provider_object,
                )
                for (
                    name,
                    provider_object,
                ) in self._providers.items()
                if name != self.DEFAULT_PROVIDER
            ]

            result: List[Tuple[str, Any]] = []

            if primary is not None:

                result.append(
                    (
                        self.DEFAULT_PROVIDER,
                        primary,
                    )
                )

            result.extend(others)

            return result

    @staticmethod
    def _normalize_result(
        result: Any,
        *,
        provider: str,
        operation: str,
    ) -> MemoryResult:

        if isinstance(
            result,
            MemoryResult,
        ):

            if result.provider is None:
                result.provider = provider

            if result.operation is None:
                result.operation = operation

            return result

        if isinstance(
            result,
            bool,
        ):

            return MemoryResult(
                success=result,
                value=result,
                provider=provider,
                operation=operation,
            )

        if isinstance(
            result,
            dict,
        ):

            success = result.get(
                "success",
                result.get(
                    "ok",
                    True,
                ),
            )

            return MemoryResult(
                success=bool(success),
                value=result.get(
                    "value",
                    result.get(
                        "result",
                        result,
                    ),
                ),
                provider=result.get(
                    "provider",
                    provider,
                ),
                operation=result.get(
                    "operation",
                    operation,
                ),
                error=result.get("error"),
                metadata=dict(
                    result.get(
                        "metadata",
                        {},
                    )
                ),
            )

        return MemoryResult(
            success=True,
            value=result,
            provider=provider,
            operation=operation,
        )

    @staticmethod
    def _normalize_provider_name(
        name: str,
    ) -> str:

        normalized = str(name or "").strip().lower()

        if not normalized:

            raise ValueError("Provider name cannot be empty.")

        return normalized

    @staticmethod
    def _normalize_operation(
        operation: str,
    ) -> str:

        normalized = str(operation or "").strip()

        if not normalized:

            raise ValueError("Operation cannot be empty.")

        return normalized

    @staticmethod
    def _get_capabilities(
        provider: Any,
    ) -> List[str]:

        capabilities = getattr(
            provider,
            "capabilities",
            None,
        )

        if capabilities is None:

            capabilities = []

            for name in (
                "remember",
                "recall",
                "search",
                "clear",
                "remember_behavior",
                "recall_behavior",
                "status",
                "health",
            ):

                if callable(
                    getattr(
                        provider,
                        name,
                        None,
                    )
                ):

                    capabilities.append(name)

        return [
            str(capability).strip()
            for capability in capabilities
            if str(capability).strip()
        ]


__all__ = [
    "MemoryService",
    "MemoryResult",
    "MemoryProviderInfo",
]
