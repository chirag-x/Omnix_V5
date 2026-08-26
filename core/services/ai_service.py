"""
Omnix V5 - AI Service

Stable Core-level bridge between Omnix Core and AI providers.

Primary provider:
    Omnix V5 BrainManager

Fallback providers:
    Legacy brain systems
    LLM providers
    Agent systems
    Custom AI providers

The service normalizes provider APIs, supports provider priority,
sync/async providers, fallback execution, and result normalization.
"""

from __future__ import annotations

import asyncio
import inspect

from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple

# ============================================================================
# RESULT
# ============================================================================


@dataclass
class AIResult:

    success: bool

    value: Any = None

    provider: Optional[str] = None

    operation: Optional[str] = None

    error: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:

        self.success = bool(self.success)

        if self.provider is not None:
            self.provider = str(self.provider).strip() or None

        if self.operation is not None:
            self.operation = str(self.operation).strip() or None

        if self.error is not None:
            self.error = str(self.error).strip() or None

        if not isinstance(
            self.metadata,
            dict,
        ):
            self.metadata = {"value": self.metadata}

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


# ============================================================================
# PROVIDER INFORMATION
# ============================================================================


@dataclass
class AIProviderInfo:

    name: str

    priority: int = 0

    capabilities: List[str] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:

        return {
            "name": self.name,
            "priority": self.priority,
            "capabilities": list(self.capabilities),
            "metadata": dict(self.metadata),
        }


# ============================================================================
# AI SERVICE
# ============================================================================


class AIService:
    """
    Core-level AI provider bridge.

    Supported operations:

        generate()
        ask()
        chat()
        reason()
        think()
        analyze()
        plan()
        create_plan()
        classify()
        execute()

    Example:

        service.register_provider(
            "v5_brain",
            brain_manager,
            priority=100,
        )

        result = service.ask(
            "Hello Omnix"
        )

        result = service.plan(
            "Open Chrome"
        )
    """

    def __init__(self) -> None:

        self._providers: Dict[
            str,
            Any,
        ] = {}

        self._provider_priorities: Dict[
            str,
            int,
        ] = {}

        self._provider_metadata: Dict[
            str,
            Dict[str, Any],
        ] = {}

        self._lock = RLock()

    # ====================================================================
    # PROVIDER MANAGEMENT
    # ====================================================================

    def register_provider(
        self,
        name: str,
        provider: Any,
        *,
        replace: bool = False,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:

        normalized_name = self._normalize_provider_name(name)

        if provider is None:
            raise ValueError("AI provider cannot be None.")

        try:
            priority = int(priority)
        except (
            TypeError,
            ValueError,
        ):
            priority = 0

        with self._lock:

            if normalized_name in self._providers and not replace:
                raise ValueError(f"AI provider already exists: " f"{normalized_name}")

            self._providers[normalized_name] = provider

            self._provider_priorities[normalized_name] = priority

            self._provider_metadata[normalized_name] = dict(metadata or {})

    def unregister_provider(
        self,
        name: str,
    ) -> bool:

        normalized_name = self._normalize_provider_name(name)

        with self._lock:

            if normalized_name not in self._providers:
                return False

            del self._providers[normalized_name]

            self._provider_priorities.pop(
                normalized_name,
                None,
            )

            self._provider_metadata.pop(
                normalized_name,
                None,
            )

            return True

    def get_provider(
        self,
        name: str,
        default: Any = None,
    ) -> Any:

        normalized_name = self._normalize_provider_name(name)

        with self._lock:

            return self._providers.get(
                normalized_name,
                default,
            )

    def has_provider(
        self,
        name: str,
    ) -> bool:

        return self.get_provider(name) is not None

    def get_provider_names(
        self,
    ) -> List[str]:

        with self._lock:

            return list(self._providers.keys())

    def clear_providers(
        self,
    ) -> None:

        with self._lock:

            self._providers.clear()

            self._provider_priorities.clear()

            self._provider_metadata.clear()

    # ====================================================================
    # PROVIDER INFORMATION
    # ====================================================================

    def list_providers(
        self,
    ) -> List[AIProviderInfo]:

        with self._lock:

            providers = list(self._providers.items())

            priorities = dict(self._provider_priorities)

            metadata_map = dict(self._provider_metadata)

        results = []

        for name, provider in providers:

            capabilities = getattr(
                provider,
                "capabilities",
                [],
            )

            metadata = dict(
                metadata_map.get(
                    name,
                    {},
                )
            )

            provider_metadata = getattr(
                provider,
                "metadata",
                None,
            )

            if isinstance(
                provider_metadata,
                dict,
            ):
                metadata.update(provider_metadata)

            results.append(
                AIProviderInfo(
                    name=name,
                    priority=priorities.get(
                        name,
                        0,
                    ),
                    capabilities=list(capabilities or []),
                    metadata=metadata,
                )
            )

        results.sort(
            key=lambda item: (
                item.priority,
                item.name,
            ),
            reverse=True,
        )

        return results

    # ====================================================================
    # GENERATION
    # ====================================================================

    def generate(
        self,
        prompt: Any,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> AIResult:

        return self._execute_sync(
            operation="generate",
            method_names=(
                "generate",
                "chat",
                "ask",
                "complete",
                "respond",
            ),
            provider=provider,
            args=(
                prompt,
                *args,
            ),
            kwargs=kwargs,
        )

    ask = generate
    chat = generate
    complete = generate

    async def generate_async(
        self,
        prompt: Any,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> AIResult:

        return await self._execute_async(
            operation="generate",
            method_names=(
                "generate",
                "chat",
                "ask",
                "complete",
                "respond",
            ),
            provider=provider,
            args=(
                prompt,
                *args,
            ),
            kwargs=kwargs,
        )

    ask_async = generate_async
    chat_async = generate_async

    # ====================================================================
    # REASONING
    # ====================================================================

    def reason(
        self,
        input_data: Any,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> AIResult:

        return self._execute_sync(
            operation="reason",
            method_names=(
                "reason",
                "think",
                "analyze",
                "process",
                "ask",
            ),
            provider=provider,
            args=(
                input_data,
                *args,
            ),
            kwargs=kwargs,
        )

    think = reason
    analyze = reason

    async def reason_async(
        self,
        input_data: Any,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> AIResult:

        return await self._execute_async(
            operation="reason",
            method_names=(
                "reason",
                "think",
                "analyze",
                "process",
                "ask",
            ),
            provider=provider,
            args=(
                input_data,
                *args,
            ),
            kwargs=kwargs,
        )

    think_async = reason_async
    analyze_async = reason_async

    # ====================================================================
    # PLANNING
    # ====================================================================

    def plan(
        self,
        goal: Any,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> AIResult:

        return self._execute_sync(
            operation="plan",
            method_names=(
                "generate_plan",
                "plan",
                "create_plan",
                "build_plan",
                "make_plan",
            ),
            provider=provider,
            args=(
                goal,
                *args,
            ),
            kwargs=kwargs,
        )

    create_plan = plan
    build_plan = plan
    generate_plan = plan

    async def plan_async(
        self,
        goal: Any,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> AIResult:

        return await self._execute_async(
            operation="plan",
            method_names=(
                "generate_plan",
                "plan",
                "create_plan",
                "build_plan",
                "make_plan",
            ),
            provider=provider,
            args=(
                goal,
                *args,
            ),
            kwargs=kwargs,
        )

    create_plan_async = plan_async
    build_plan_async = plan_async
    generate_plan_async = plan_async

    # ====================================================================
    # CLASSIFICATION
    # ====================================================================

    def classify(
        self,
        input_data: Any,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> AIResult:

        return self._execute_sync(
            operation="classify",
            method_names=(
                "classify",
                "classify_intent",
                "detect_intent",
                "ask",
            ),
            provider=provider,
            args=(
                input_data,
                *args,
            ),
            kwargs=kwargs,
        )

    classify_intent = classify

    async def classify_async(
        self,
        input_data: Any,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> AIResult:

        return await self._execute_async(
            operation="classify",
            method_names=(
                "classify",
                "classify_intent",
                "detect_intent",
                "ask",
            ),
            provider=provider,
            args=(
                input_data,
                *args,
            ),
            kwargs=kwargs,
        )

    classify_intent_async = classify_async

    # ====================================================================
    # GENERIC EXECUTION
    # ====================================================================

    def execute(
        self,
        operation: str,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> AIResult:

        normalized_operation = self._normalize_operation(operation)

        return self._execute_sync(
            operation=normalized_operation,
            method_names=(
                normalized_operation,
                "execute",
                "process",
                "run",
            ),
            provider=provider,
            args=args,
            kwargs=kwargs,
        )

    async def execute_async(
        self,
        operation: str,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> AIResult:

        normalized_operation = self._normalize_operation(operation)

        return await self._execute_async(
            operation=normalized_operation,
            method_names=(
                normalized_operation,
                "execute",
                "process",
                "run",
            ),
            provider=provider,
            args=args,
            kwargs=kwargs,
        )

    # ====================================================================
    # SYNCHRONOUS ROUTING
    # ====================================================================

    def _execute_sync(
        self,
        *,
        operation: str,
        method_names: Tuple[str, ...],
        provider: Optional[str],
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> AIResult:

        try:
            asyncio.get_running_loop()

            raise RuntimeError(
                "AIService synchronous methods "
                "cannot be used inside an active "
                "event loop. Use the *_async() "
                "version instead."
            )

        except RuntimeError as error:

            if "cannot be used" in str(error):
                raise

        return asyncio.run(
            self._execute_async(
                operation=operation,
                method_names=method_names,
                provider=provider,
                args=args,
                kwargs=kwargs,
            )
        )

    # ====================================================================
    # ASYNCHRONOUS ROUTING
    # ====================================================================

    async def _execute_async(
        self,
        *,
        operation: str,
        method_names: Tuple[str, ...],
        provider: Optional[str],
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> AIResult:

        providers = self._select_providers(provider)

        if not providers:

            return AIResult(
                success=False,
                operation=operation,
                error=("No AI providers " "are registered."),
            )

        errors = []

        for (
            provider_name,
            provider_object,
        ) in providers:

            try:

                result = self._call_provider(
                    provider_object,
                    method_names,
                    operation,
                    *args,
                    **kwargs,
                )

                if inspect.isawaitable(result):
                    result = await result

                normalized = self._normalize_result(
                    result,
                    provider=provider_name,
                    operation=operation,
                )

                if normalized.success:
                    return normalized

                errors.append(
                    {
                        "provider": provider_name,
                        "error": normalized.error,
                    }
                )

            except Exception as error:

                errors.append(
                    {
                        "provider": provider_name,
                        "error": str(error),
                    }
                )

        return AIResult(
            success=False,
            operation=operation,
            error=("No AI provider completed " "the operation."),
            metadata={"provider_errors": errors},
        )

    # ====================================================================
    # PROVIDER CALLING
    # ====================================================================

    @staticmethod
    def _call_provider(
        provider: Any,
        method_names: Tuple[str, ...],
        operation: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:

        for method_name in method_names:

            method = getattr(
                provider,
                method_name,
                None,
            )

            if not callable(method):
                continue

            if method_name in (
                "execute",
                "process",
                "run",
            ):

                return method(
                    operation,
                    *args,
                    **kwargs,
                )

            return method(
                *args,
                **kwargs,
            )

        if callable(provider):

            return provider(
                operation,
                *args,
                **kwargs,
            )

        raise AttributeError(
            "Provider does not support "
            f"any compatible method for "
            f"operation: {operation}"
        )

    # ====================================================================
    # RESULT NORMALIZATION
    # ====================================================================

    @staticmethod
    def _normalize_result(
        result: Any,
        *,
        provider: str,
        operation: str,
    ) -> AIResult:

        if isinstance(
            result,
            AIResult,
        ):

            if result.provider is None:
                result.provider = provider

            if result.operation is None:
                result.operation = operation

            return result

        if result is None:

            return AIResult(
                success=False,
                provider=provider,
                operation=operation,
                error=("AI provider returned " "no result."),
            )

        if isinstance(
            result,
            bool,
        ):

            return AIResult(
                success=result,
                value=result,
                provider=provider,
                operation=operation,
                error=(None if result else "AI operation returned False."),
            )

        if isinstance(
            result,
            dict,
        ):

            success = result.get(
                "success",
                result.get(
                    "ok",
                    not bool(result.get("error")),
                ),
            )

            return AIResult(
                success=bool(success),
                value=result.get(
                    "value",
                    result.get(
                        "result",
                        result.get(
                            "response",
                            result.get(
                                "data",
                                result,
                            ),
                        ),
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
                    or {}
                ),
            )

        success = getattr(
            result,
            "success",
            None,
        )

        if success is not None:

            return AIResult(
                success=bool(success),
                value=getattr(
                    result,
                    "value",
                    getattr(
                        result,
                        "result",
                        result,
                    ),
                ),
                provider=getattr(
                    result,
                    "provider",
                    provider,
                ),
                operation=getattr(
                    result,
                    "operation",
                    operation,
                ),
                error=getattr(
                    result,
                    "error",
                    None,
                ),
                metadata=getattr(
                    result,
                    "metadata",
                    {},
                )
                or {},
            )

        return AIResult(
            success=True,
            value=result,
            provider=provider,
            operation=operation,
        )

    # ====================================================================
    # PROVIDER SELECTION
    # ====================================================================

    def _select_providers(
        self,
        provider: Optional[str],
    ) -> List[Tuple[str, Any]]:

        with self._lock:

            if provider is not None:

                normalized_name = self._normalize_provider_name(provider)

                provider_object = self._providers.get(normalized_name)

                if provider_object is None:
                    return []

                return [
                    (
                        normalized_name,
                        provider_object,
                    )
                ]

            providers = list(self._providers.items())

            priorities = dict(self._provider_priorities)

        providers.sort(
            key=lambda item: (
                priorities.get(
                    item[0],
                    0,
                ),
                item[0],
            ),
            reverse=True,
        )

        return providers

    # ====================================================================
    # STATUS
    # ====================================================================

    def status(
        self,
    ) -> Dict[str, Any]:

        providers = self.list_providers()

        return {
            "service": "ai",
            "provider_count": len(providers),
            "providers": [provider.to_dict() for provider in providers],
        }

    # ====================================================================
    # UTILITIES
    # ====================================================================

    @staticmethod
    def _normalize_provider_name(
        name: str,
    ) -> str:

        normalized = str(name).strip().lower()

        if not normalized:
            raise ValueError("Provider name cannot be empty.")

        return normalized

    @staticmethod
    def _normalize_operation(
        operation: str,
    ) -> str:

        normalized = str(operation).strip().lower()

        if not normalized:
            raise ValueError("AI operation cannot be empty.")

        return normalized


# ============================================================================
# SHARED SERVICE
# ============================================================================

_default_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:

    global _default_ai_service

    if _default_ai_service is None:
        _default_ai_service = AIService()

    return _default_ai_service


def reset_ai_service() -> None:

    global _default_ai_service

    _default_ai_service = None


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "AIResult",
    "AIProviderInfo",
    "AIService",
    "get_ai_service",
    "reset_ai_service",
]
