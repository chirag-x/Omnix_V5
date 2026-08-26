"""
Omnix V5 - Voice Service

Stable gateway between OmnixEngine and the real voice subsystem.

The real implementation is normally:

    voice.voice_manager.VoiceManager

Architecture:

    OmnixEngine
         |
         v
    VoiceService
         |
         v
    VoiceManager
         |
         +--> WakeListener
         +--> SpeechRecognizer
         +--> OfflineTTS
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
class VoiceResult:

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
class VoiceProviderInfo:

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
# VOICE SERVICE
# ============================================================================


class VoiceService:
    """
    Stable V5 gateway for voice providers.

    Primary provider:

        VoiceManager
    """

    def __init__(self) -> None:

        self._providers: Dict[
            str,
            Any,
        ] = {}

        self._priorities: Dict[
            str,
            int,
        ] = {}

        self._metadata: Dict[
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

            raise ValueError("Voice provider cannot be None.")

        try:
            priority = int(priority)

        except (
            TypeError,
            ValueError,
        ):
            priority = 0

        with self._lock:

            if name in self._providers and not replace:
                raise ValueError(f"Voice provider already exists: " f"{name}")

            self._providers[name] = provider

            self._priorities[name] = priority

            self._metadata[name] = dict(metadata or {})

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

            self._priorities.pop(
                name,
                None,
            )

            self._metadata.pop(
                name,
                None,
            )

            return True

    def get_provider(
        self,
        name: str,
        default: Any = None,
    ) -> Any:

        name = self._normalize_provider_name(name)

        with self._lock:

            return self._providers.get(
                name,
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

    def get_primary_provider(
        self,
    ) -> Optional[Any]:

        providers = self._select_providers(None)

        if not providers:
            return None

        return providers[0][1]

    def list_providers(
        self,
    ) -> List[VoiceProviderInfo]:

        result = []

        for name, provider in self._select_providers(None):

            result.append(
                VoiceProviderInfo(
                    name=name,
                    capabilities=self._get_capabilities(provider),
                    metadata=dict(
                        self._metadata.get(
                            name,
                            {},
                        )
                    ),
                )
            )

        return result

    # ====================================================================
    # LIFECYCLE
    # ====================================================================

    async def start_async(
        self,
        provider: Optional[str] = None,
    ) -> VoiceResult:

        return await self._execute_async(
            "start",
            (
                "start",
                "initialize",
            ),
            provider=provider,
        )

    def start(
        self,
        provider: Optional[str] = None,
    ) -> VoiceResult:

        return self._run_sync(self.start_async(provider=provider))

    async def stop_async(
        self,
        provider: Optional[str] = None,
    ) -> VoiceResult:

        return await self._execute_async(
            "stop",
            (
                "stop",
                "shutdown",
            ),
            provider=provider,
        )

    def stop(
        self,
        provider: Optional[str] = None,
    ) -> VoiceResult:

        return self._run_sync(self.stop_async(provider=provider))

    shutdown = stop

    # ====================================================================
    # SPEAK
    # ====================================================================

    async def speak_async(
        self,
        text: str,
        *,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> VoiceResult:

        return await self._execute_async(
            "speak",
            (
                "speak",
                "say",
                "text_to_speech",
                "synthesize",
            ),
            provider=provider,
            args=(text,),
            kwargs=kwargs,
        )

    def speak(
        self,
        text: str,
        *,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> VoiceResult:

        return self._run_sync(
            self.speak_async(
                text,
                provider=provider,
                **kwargs,
            )
        )

    say = speak
    text_to_speech = speak
    synthesize = speak

    # ====================================================================
    # LISTEN / RECOGNITION
    # ====================================================================

    async def listen_async(
        self,
        *,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> VoiceResult:

        return await self._execute_async(
            "listen",
            (
                "listen",
                "listen_command",
                "recognize",
                "transcribe",
                "speech_to_text",
            ),
            provider=provider,
            kwargs=kwargs,
        )

    def listen(
        self,
        *,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> VoiceResult:

        return self._run_sync(
            self.listen_async(
                provider=provider,
                **kwargs,
            )
        )

    recognize = listen
    transcribe = listen
    speech_to_text = listen

    # ====================================================================
    # PAUSE / RESUME
    # ====================================================================

    async def pause_async(
        self,
        provider: Optional[str] = None,
    ) -> VoiceResult:

        return await self._execute_async(
            "pause",
            ("pause",),
            provider=provider,
        )

    def pause(
        self,
        provider: Optional[str] = None,
    ) -> VoiceResult:

        return self._run_sync(self.pause_async(provider=provider))

    async def resume_async(
        self,
        provider: Optional[str] = None,
    ) -> VoiceResult:

        return await self._execute_async(
            "resume",
            (
                "resume",
                "start",
            ),
            provider=provider,
        )

    def resume(
        self,
        provider: Optional[str] = None,
    ) -> VoiceResult:

        return self._run_sync(self.resume_async(provider=provider))

    # ====================================================================
    # GENERIC EXECUTION
    # ====================================================================

    async def execute_async(
        self,
        operation: str,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> VoiceResult:

        operation = self._normalize_operation(operation)

        return await self._execute_async(
            operation,
            (operation,),
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
    ) -> VoiceResult:

        return self._run_sync(
            self.execute_async(
                operation,
                *args,
                provider=provider,
                **kwargs,
            )
        )

    process = execute
    run = execute

    # ====================================================================
    # INTERNAL EXECUTION
    # ====================================================================

    async def _execute_async(
        self,
        operation: str,
        method_names: Tuple[str, ...],
        *,
        provider: Optional[str] = None,
        args: Tuple[Any, ...] = (),
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> VoiceResult:

        kwargs = dict(kwargs or {})

        providers = self._select_providers(provider)

        if not providers:

            return VoiceResult(
                success=False,
                operation=operation,
                error=("No voice provider is registered."),
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

        return VoiceResult(
            success=False,
            operation=operation,
            error=("No voice provider completed " "the operation."),
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
            "Voice provider does not expose "
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
    ) -> VoiceResult:

        if isinstance(
            raw_result,
            VoiceResult,
        ):

            if raw_result.provider is None:
                raw_result.provider = provider

            if raw_result.operation is None:
                raw_result.operation = operation

            return raw_result

        # VoiceManager.start(), shutdown()
        # and speak() may successfully return None.
        if raw_result is None:

            return VoiceResult(
                success=True,
                provider=provider,
                operation=operation,
            )

        if hasattr(
            raw_result,
            "success",
        ):

            return VoiceResult(
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

            return VoiceResult(
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

            return VoiceResult(
                success=raw_result,
                value=raw_result,
                provider=provider,
                operation=operation,
            )

        return VoiceResult(
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
        requested_provider: Optional[str],
    ) -> List[Tuple[str, Any]]:

        with self._lock:

            if requested_provider:

                name = self._normalize_provider_name(requested_provider)

                provider = self._providers.get(name)

                if provider is None:
                    return []

                return [
                    (
                        name,
                        provider,
                    )
                ]

            return sorted(
                self._providers.items(),
                key=lambda item: (
                    self._priorities.get(
                        item[0],
                        0,
                    ),
                    item[0],
                ),
                reverse=True,
            )

    # ====================================================================
    # CAPABILITIES
    # ====================================================================

    @staticmethod
    def _get_capabilities(
        provider: Any,
    ) -> List[str]:

        methods = (
            "start",
            "stop",
            "shutdown",
            "speak",
            "listen",
            "listen_command",
            "pause",
            "resume",
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
    ) -> VoiceResult:

        try:

            asyncio.get_running_loop()

        except RuntimeError:

            return asyncio.run(awaitable)

        raise RuntimeError(
            "Synchronous VoiceService method "
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

            raise ValueError("Voice operation cannot be empty.")

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
                        self._priorities.get(
                            name,
                            0,
                        )
                    ),
                    "type": type(provider).__name__,
                    "capabilities": (self._get_capabilities(provider)),
                    "metadata": dict(
                        self._metadata.get(
                            name,
                            {},
                        )
                    ),
                }
            )

        return {
            "service": "voice",
            "provider_count": len(providers),
            "providers": providers,
        }


# ============================================================================
# SHARED SERVICE
# ============================================================================


_default_voice_service: Optional[VoiceService] = None


def get_voice_service() -> VoiceService:

    global _default_voice_service

    if _default_voice_service is None:

        _default_voice_service = VoiceService()

    return _default_voice_service


def reset_voice_service() -> None:

    global _default_voice_service

    _default_voice_service = None


__all__ = [
    "VoiceResult",
    "VoiceProviderInfo",
    "VoiceService",
    "get_voice_service",
    "reset_voice_service",
]
