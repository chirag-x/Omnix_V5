"""
Omnix V5 - Vision Service

Stable Core gateway for the real Omnix vision subsystem.

Primary architecture:

    OmnixEngine
         |
         v
    VisionService
         |
         v
    VisionManager
         |
         +--> ScreenObserver
         +--> VisionPipeline
         +--> UIPatternMemory
         +--> ExecutionContext synchronization
         +--> UI element detection

The service does not implement computer vision itself.
"""

from __future__ import annotations

import asyncio
import inspect

from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple

# ============================================================================
# RESULT TYPES
# ============================================================================


@dataclass
class VisionResult:
    """
    Normalized result returned from a vision operation.
    """

    success: bool

    value: Any = None

    provider: Optional[str] = None

    operation: Optional[str] = None

    error: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

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
class VisionProviderInfo:
    """
    Information about a registered vision provider.
    """

    name: str

    capabilities: List[str] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "capabilities": list(self.capabilities),
            "metadata": dict(self.metadata),
        }


# ============================================================================
# VISION SERVICE
# ============================================================================


class VisionService:
    """
    Core gateway for Omnix vision.

    The primary provider should normally be:

        VisionManager
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

        name = self._normalize_provider_name(name)

        if provider is None:
            raise ValueError("Vision provider cannot be None.")

        try:
            priority = int(priority)

        except (
            TypeError,
            ValueError,
        ):
            priority = 0

        with self._lock:

            if name in self._providers and not replace:
                raise ValueError(f"Vision provider already exists: " f"{name}")

            self._providers[name] = provider

            self._provider_priorities[name] = priority

            self._provider_metadata[name] = dict(metadata or {})

    def unregister_provider(
        self,
        name: str,
    ) -> bool:

        name = self._normalize_provider_name(name)

        with self._lock:

            if name not in self._providers:
                return False

            self._providers.pop(
                name,
                None,
            )

            self._provider_priorities.pop(
                name,
                None,
            )

            self._provider_metadata.pop(
                name,
                None,
            )

            return True

    def get_provider(
        self,
        name: str,
    ) -> Any:

        name = self._normalize_provider_name(name)

        with self._lock:
            return self._providers.get(name)

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

    def get_primary_provider(
        self,
    ) -> Optional[Any]:

        providers = self._select_providers(None)

        if not providers:
            return None

        return providers[0][1]

    def list_providers(
        self,
    ) -> List[VisionProviderInfo]:

        providers = []

        for name, _ in self._select_providers(None):

            providers.append(
                VisionProviderInfo(
                    name=name,
                    capabilities=self._get_capabilities(name),
                    metadata=dict(
                        self._provider_metadata.get(
                            name,
                            {},
                        )
                    ),
                )
            )

        return providers

    # ====================================================================
    # LIFECYCLE
    # ====================================================================

    async def start_async(
        self,
        provider: Optional[str] = None,
    ) -> VisionResult:

        return await self._call_operation_async(
            operation="start",
            method_names=(
                "start",
                "initialize",
            ),
            provider=provider,
        )

    def start(
        self,
        provider: Optional[str] = None,
    ) -> VisionResult:

        return self._run_sync(self.start_async(provider=provider))

    async def stop_async(
        self,
        provider: Optional[str] = None,
    ) -> VisionResult:

        return await self._call_operation_async(
            operation="stop",
            method_names=(
                "stop",
                "shutdown",
            ),
            provider=provider,
        )

    def stop(
        self,
        provider: Optional[str] = None,
    ) -> VisionResult:

        return self._run_sync(self.stop_async(provider=provider))

    # ====================================================================
    # FRAME ACCESS
    # ====================================================================

    async def get_latest_frame_async(
        self,
        provider: Optional[str] = None,
    ) -> VisionResult:

        return await self._call_operation_async(
            operation="get_latest_frame",
            method_names=(
                "get_latest_frame",
                "latest_frame",
            ),
            provider=provider,
        )

    def get_latest_frame(
        self,
        provider: Optional[str] = None,
    ) -> VisionResult:

        return self._run_sync(self.get_latest_frame_async(provider=provider))

    async def get_latest_analysis_async(
        self,
        provider: Optional[str] = None,
    ) -> VisionResult:

        return await self._call_operation_async(
            operation="get_latest_analysis",
            method_names=(
                "get_latest_analysis",
                "get_latest_frame",
            ),
            provider=provider,
        )

    def get_latest_analysis(
        self,
        provider: Optional[str] = None,
    ) -> VisionResult:

        return self._run_sync(self.get_latest_analysis_async(provider=provider))

    # ====================================================================
    # SCREEN / FRAME ANALYSIS
    # ====================================================================

    async def analyze_async(
        self,
        data: Any = None,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> VisionResult:

        call_args = (
            tuple(args)
            if data is None
            else (
                data,
                *args,
            )
        )

        return await self._call_operation_async(
            operation="analyze",
            method_names=(
                "analyze",
                "analyze_frame",
                "analyze_screen",
                "process",
            ),
            provider=provider,
            args=call_args,
            kwargs=kwargs,
        )

    def analyze(
        self,
        data: Any = None,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> VisionResult:

        return self._run_sync(
            self.analyze_async(
                data,
                *args,
                provider=provider,
                **kwargs,
            )
        )

    # ====================================================================
    # DETECTION
    # ====================================================================

    async def detect_async(
        self,
        data: Any = None,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> VisionResult:

        call_args = (
            tuple(args)
            if data is None
            else (
                data,
                *args,
            )
        )

        return await self._call_operation_async(
            operation="detect",
            method_names=(
                "detect",
                "detect_objects",
                "detect_elements",
                "find_objects",
            ),
            provider=provider,
            args=call_args,
            kwargs=kwargs,
        )

    def detect(
        self,
        data: Any = None,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> VisionResult:

        return self._run_sync(
            self.detect_async(
                data,
                *args,
                provider=provider,
                **kwargs,
            )
        )

    detect_objects = detect

    # ====================================================================
    # ELEMENT SEARCH
    # ====================================================================

    async def find_element_async(
        self,
        target: Any,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> VisionResult:

        return await self._call_operation_async(
            operation="find_element",
            method_names=(
                "find_element",
                "find",
                "locate_element",
                "locate",
                "search",
            ),
            provider=provider,
            args=(
                target,
                *args,
            ),
            kwargs=kwargs,
        )

    def find_element(
        self,
        target: Any,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> VisionResult:

        return self._run_sync(
            self.find_element_async(
                target,
                *args,
                provider=provider,
                **kwargs,
            )
        )

    find = find_element
    locate = find_element

    # ====================================================================
    # WAIT FOR ELEMENT
    # ====================================================================

    async def wait_for_element_async(
        self,
        target: Any,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> VisionResult:

        return await self._call_operation_async(
            operation="wait_for_element",
            method_names=("wait_for_element",),
            provider=provider,
            args=(
                target,
                *args,
            ),
            kwargs=kwargs,
        )

    def wait_for_element(
        self,
        target: Any,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> VisionResult:

        return self._run_sync(
            self.wait_for_element_async(
                target,
                *args,
                provider=provider,
                **kwargs,
            )
        )

    # ====================================================================
    # CLICK ELEMENT
    # ====================================================================

    async def click_element_async(
        self,
        target: Any,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> VisionResult:

        return await self._call_operation_async(
            operation="click_element",
            method_names=("click_element",),
            provider=provider,
            args=(
                target,
                *args,
            ),
            kwargs=kwargs,
        )

    def click_element(
        self,
        target: Any,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> VisionResult:

        return self._run_sync(
            self.click_element_async(
                target,
                *args,
                provider=provider,
                **kwargs,
            )
        )

    # ====================================================================
    # GENERIC EXECUTION
    # ====================================================================

    async def execute_async(
        self,
        operation: str,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> VisionResult:

        operation = self._normalize_operation(operation)

        return await self._call_operation_async(
            operation=operation,
            method_names=(operation,),
            provider=provider,
            args=args,
            kwargs=kwargs,
        )

    def execute(
        self,
        operation: str,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> VisionResult:

        return self._run_sync(
            self.execute_async(
                operation,
                *args,
                provider=provider,
                **kwargs,
            )
        )

    # ====================================================================
    # PROVIDER EXECUTION
    # ====================================================================

    async def _call_operation_async(
        self,
        operation: str,
        method_names: Tuple[str, ...],
        provider: Optional[str] = None,
        args: Tuple[Any, ...] = (),
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> VisionResult:

        kwargs = dict(kwargs or {})

        providers = self._select_providers(provider)

        if not providers:

            return VisionResult(
                success=False,
                operation=operation,
                error=("No vision provider is registered."),
            )

        errors = []

        for provider_name, provider_object in providers:

            try:

                raw_result = self._call_provider(
                    provider_object,
                    method_names,
                    args,
                    kwargs,
                )

                if inspect.isawaitable(raw_result):
                    raw_result = await raw_result

                result = self._normalize_result(
                    raw_result,
                    provider_name,
                    operation,
                )

                if result.success:
                    return result

                errors.append(
                    {
                        "provider": provider_name,
                        "error": result.error,
                    }
                )

            except Exception as error:

                errors.append(
                    {
                        "provider": provider_name,
                        "error": str(error),
                    }
                )

        return VisionResult(
            success=False,
            operation=operation,
            error=("No vision provider completed " "the operation."),
            metadata={
                "provider_errors": errors,
            },
        )

    @staticmethod
    def _call_provider(
        provider: Any,
        method_names: Tuple[str, ...],
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> Any:

        for method_name in method_names:

            method = getattr(
                provider,
                method_name,
                None,
            )

            if callable(method):

                return method(
                    *args,
                    **kwargs,
                )

        raise AttributeError(
            "Vision provider does not expose "
            f"any supported methods: "
            f"{method_names}"
        )

    # ====================================================================
    # RESULT NORMALIZATION
    # ====================================================================

    @staticmethod
    def _normalize_result(
        raw_result: Any,
        provider: str,
        operation: str,
    ) -> VisionResult:

        if isinstance(
            raw_result,
            VisionResult,
        ):
            return raw_result

        if raw_result is None:

            # Important:
            # start() and stop() from VisionManager
            # return None on successful completion.
            if operation in (
                "start",
                "stop",
            ):

                return VisionResult(
                    success=True,
                    provider=provider,
                    operation=operation,
                )

            return VisionResult(
                success=False,
                provider=provider,
                operation=operation,
                error="Vision operation returned no result.",
            )

        if hasattr(
            raw_result,
            "success",
        ):

            return VisionResult(
                success=bool(raw_result.success),
                value=getattr(
                    raw_result,
                    "value",
                    getattr(
                        raw_result,
                        "data",
                        getattr(
                            raw_result,
                            "result",
                            raw_result,
                        ),
                    ),
                ),
                provider=provider,
                operation=operation,
                error=getattr(
                    raw_result,
                    "error",
                    None,
                ),
                metadata=getattr(
                    raw_result,
                    "metadata",
                    {},
                )
                or {},
            )

        if isinstance(
            raw_result,
            dict,
        ):

            return VisionResult(
                success=bool(
                    raw_result.get(
                        "success",
                        True,
                    )
                ),
                value=raw_result.get(
                    "value",
                    raw_result.get(
                        "data",
                        raw_result.get(
                            "result",
                            raw_result,
                        ),
                    ),
                ),
                provider=provider,
                operation=operation,
                error=raw_result.get("error"),
                metadata=raw_result.get(
                    "metadata",
                    {},
                )
                or {},
            )

        if isinstance(
            raw_result,
            bool,
        ):

            return VisionResult(
                success=raw_result,
                value=raw_result,
                provider=provider,
                operation=operation,
            )

        return VisionResult(
            success=True,
            value=raw_result,
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

                name = self._normalize_provider_name(provider)

                provider_object = self._providers.get(name)

                if provider_object is None:
                    return []

                return [
                    (
                        name,
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
    # CAPABILITIES
    # ====================================================================

    def _get_capabilities(
        self,
        provider_name: str,
    ) -> List[str]:

        with self._lock:

            provider = self._providers.get(provider_name)

            metadata = dict(
                self._provider_metadata.get(
                    provider_name,
                    {},
                )
            )

        capabilities = metadata.get(
            "capabilities",
            [],
        )

        if capabilities:
            return [str(item) for item in capabilities]

        if provider is None:
            return []

        methods = (
            "start",
            "stop",
            "get_latest_frame",
            "get_latest_analysis",
            "find_element",
            "wait_for_element",
            "click_element",
        )

        return [
            method
            for method in methods
            if callable(
                getattr(
                    provider,
                    method,
                    None,
                )
            )
        ]

    # ====================================================================
    # SYNC / ASYNC BRIDGE
    # ====================================================================

    @staticmethod
    def _run_sync(
        awaitable: Any,
    ) -> VisionResult:

        try:

            asyncio.get_running_loop()

        except RuntimeError:

            return asyncio.run(awaitable)

        raise RuntimeError(
            "Synchronous VisionService method "
            "called inside an active event loop. "
            "Use the corresponding *_async() "
            "method instead."
        )

    # ====================================================================
    # NORMALIZATION
    # ====================================================================

    @staticmethod
    def _normalize_provider_name(
        name: Any,
    ) -> str:

        normalized = str(name or "").strip().lower()

        if not normalized:

            raise ValueError("Provider name cannot be empty.")

        return normalized

    @staticmethod
    def _normalize_operation(
        operation: Any,
    ) -> str:

        normalized = str(operation or "").strip()

        if not normalized:

            raise ValueError("Vision operation cannot be empty.")

        return normalized

    # ====================================================================
    # STATUS
    # ====================================================================

    def status(
        self,
    ) -> Dict[str, Any]:

        providers = []

        for name, provider in self._select_providers(None):

            providers.append(
                {
                    "name": name,
                    "priority": (
                        self._provider_priorities.get(
                            name,
                            0,
                        )
                    ),
                    "type": type(provider).__name__,
                    "capabilities": (self._get_capabilities(name)),
                    "metadata": dict(
                        self._provider_metadata.get(
                            name,
                            {},
                        )
                    ),
                }
            )

        return {
            "service": "vision",
            "provider_count": len(providers),
            "providers": providers,
        }


# ============================================================================
# SHARED SERVICE
# ============================================================================


_default_vision_service: Optional[VisionService] = None


def get_vision_service() -> VisionService:

    global _default_vision_service

    if _default_vision_service is None:

        _default_vision_service = VisionService()

    return _default_vision_service


def reset_vision_service() -> None:

    global _default_vision_service

    _default_vision_service = None


__all__ = [
    "VisionResult",
    "VisionProviderInfo",
    "VisionService",
    "get_vision_service",
    "reset_vision_service",
]
