"""
Omnix V5 - UI Service

Provides a stable Core-level interface between Omnix Core and UI systems.

The UIService does not implement a graphical interface itself. Instead,
it acts as a bridge between the Omnix Core and one or more UI providers.

Supported providers may include:

    - Omnix V5 UI subsystem
    - Legacy Omnix UI controller
    - Desktop GUI
    - Web UI
    - CLI interface
    - Custom UI providers

The service normalizes common UI operations so that the Core remains
independent from the actual UI implementation.
"""

from __future__ import annotations

import inspect

from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple

# ============================================================================
# RESULT OBJECTS
# ============================================================================


@dataclass
class UIResult:
    """
    Normalized result returned from a UI operation.
    """

    success: bool

    value: Any = None

    provider: Optional[str] = None

    operation: Optional[str] = None

    error: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(
        self,
    ) -> None:

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

            raise TypeError("metadata must be a dictionary.")

        self.metadata = dict(self.metadata)

    @property
    def failed(
        self,
    ) -> bool:
        """
        Return True when the operation failed.
        """

        return not self.success

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Convert the result to a dictionary.
        """

        return {
            "success": self.success,
            "value": self.value,
            "provider": self.provider,
            "operation": self.operation,
            "error": self.error,
            "metadata": dict(self.metadata),
        }


@dataclass
class UIProviderInfo:
    """
    Information about a registered UI provider.
    """

    name: str

    capabilities: List[str] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(
        self,
    ) -> None:

        self.name = str(self.name).strip()

        if not self.name:

            raise ValueError("Provider name cannot be empty.")

        self.capabilities = [
            str(capability).strip()
            for capability in self.capabilities
            if str(capability).strip()
        ]

        if not isinstance(
            self.metadata,
            dict,
        ):

            raise TypeError("metadata must be a dictionary.")

        self.metadata = dict(self.metadata)

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Convert provider information to a dictionary.
        """

        return {
            "name": self.name,
            "capabilities": list(self.capabilities),
            "metadata": dict(self.metadata),
        }


# ============================================================================
# UI SERVICE
# ============================================================================


class UIService:
    """
    Core-level interface for Omnix UI systems.

    Providers may expose different APIs.

    Common operations include:

        show_message()
        display_message()
        add_message()

        show_status()
        update_status()
        set_status()

        show_notification()
        notify()

        show_error()
        display_error()

        update()
        refresh()

        emit()
        send_event()
    """

    def __init__(
        self,
    ) -> None:

        self._providers: Dict[str, Any] = {}

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
    ) -> None:
        """
        Register a UI provider.
        """

        normalized_name = self._normalize_provider_name(name)

        if provider is None:

            raise ValueError("UI provider cannot be None.")

        with self._lock:

            if normalized_name in self._providers and not replace:

                raise ValueError(f"UI provider already " f"exists: {normalized_name}")

            self._providers[normalized_name] = provider

    def unregister_provider(
        self,
        name: str,
    ) -> bool:
        """
        Remove a UI provider.
        """

        normalized_name = self._normalize_provider_name(name)

        with self._lock:

            if normalized_name not in self._providers:

                return False

            del self._providers[normalized_name]

            return True

    def get_provider(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Return a registered UI provider.
        """

        normalized_name = self._normalize_provider_name(name)

        with self._lock:

            return self._providers.get(
                normalized_name,
                default,
            )

    def get_provider_names(
        self,
    ) -> List[str]:
        """
        Return registered provider names.
        """

        with self._lock:

            return list(self._providers.keys())

    def has_provider(
        self,
        name: str,
    ) -> bool:
        """
        Check whether a provider exists.
        """

        normalized_name = self._normalize_provider_name(name)

        with self._lock:

            return normalized_name in self._providers

    def clear_providers(
        self,
    ) -> None:
        """
        Remove all UI providers.
        """

        with self._lock:

            self._providers.clear()

    # ====================================================================
    # PROVIDER INFORMATION
    # ====================================================================

    def list_providers(
        self,
    ) -> List[UIProviderInfo]:
        """
        Return information about registered UI providers.
        """

        with self._lock:

            items = list(self._providers.items())

        results: List[UIProviderInfo] = []

        for name, provider in items:

            capabilities = getattr(
                provider,
                "capabilities",
                [],
            )

            metadata = getattr(
                provider,
                "metadata",
                {},
            )

            results.append(
                UIProviderInfo(
                    name=name,
                    capabilities=list(capabilities or []),
                    metadata=dict(metadata or {}),
                )
            )

        return results

    # ====================================================================
    # MESSAGES
    # ====================================================================

    def show_message(
        self,
        message: Any,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> UIResult:
        """
        Display a message in the UI.
        """

        return self._call_operation(
            operation="show_message",
            method_names=(
                "show_message",
                "display_message",
                "add_message",
                "append_message",
                "message",
            ),
            provider=provider,
            args=(
                message,
                *args,
            ),
            kwargs=kwargs,
        )

    display_message = show_message
    add_message = show_message

    def show_user_message(
        self,
        message: Any,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> UIResult:
        """
        Display a user message.
        """

        kwargs.setdefault(
            "role",
            "user",
        )

        return self.show_message(
            message,
            *args,
            provider=provider,
            **kwargs,
        )

    def show_assistant_message(
        self,
        message: Any,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> UIResult:
        """
        Display an Omnix assistant message.
        """

        kwargs.setdefault(
            "role",
            "assistant",
        )

        return self.show_message(
            message,
            *args,
            provider=provider,
            **kwargs,
        )

    # ====================================================================
    # STATUS
    # ====================================================================

    def show_status(
        self,
        status: Any,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> UIResult:
        """
        Display or update Omnix status.
        """

        return self._call_operation(
            operation="show_status",
            method_names=(
                "show_status",
                "update_status",
                "set_status",
                "display_status",
            ),
            provider=provider,
            args=(
                status,
                *args,
            ),
            kwargs=kwargs,
        )

    update_status = show_status
    set_status = show_status

    # ====================================================================
    # NOTIFICATIONS
    # ====================================================================

    def notify(
        self,
        message: Any,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> UIResult:
        """
        Display a notification.
        """

        return self._call_operation(
            operation="notify",
            method_names=(
                "notify",
                "show_notification",
                "notification",
                "show_message",
            ),
            provider=provider,
            args=(
                message,
                *args,
            ),
            kwargs=kwargs,
        )

    show_notification = notify

    # ====================================================================
    # ERRORS
    # ====================================================================

    def show_error(
        self,
        error: Any,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> UIResult:
        """
        Display an error.
        """

        return self._call_operation(
            operation="show_error",
            method_names=(
                "show_error",
                "display_error",
                "report_error",
                "show_message",
            ),
            provider=provider,
            args=(
                error,
                *args,
            ),
            kwargs=kwargs,
        )

    display_error = show_error

    # ====================================================================
    # UI UPDATE / REFRESH
    # ====================================================================

    def update(
        self,
        data: Any = None,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> UIResult:
        """
        Send an update to the UI.
        """

        return self._call_operation(
            operation="update",
            method_names=(
                "update",
                "refresh",
                "render",
                "set_data",
            ),
            provider=provider,
            args=(
                data,
                *args,
            ),
            kwargs=kwargs,
        )

    refresh = update

    # ====================================================================
    # EVENTS
    # ====================================================================

    def emit(
        self,
        event: str,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> UIResult:
        """
        Send an event to the UI.
        """

        normalized_event = self._normalize_operation(event)

        return self._call_operation(
            operation=normalized_event,
            method_names=(
                "emit",
                "send_event",
                "handle_event",
                "on_event",
            ),
            provider=provider,
            args=(
                normalized_event,
                *args,
            ),
            kwargs=kwargs,
        )

    send_event = emit

    # ====================================================================
    # GENERIC EXECUTION
    # ====================================================================

    def execute(
        self,
        operation: str,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> UIResult:
        """
        Execute a custom UI operation.
        """

        normalized_operation = self._normalize_operation(operation)

        return self._call_operation(
            operation=normalized_operation,
            method_names=(
                normalized_operation,
                "execute",
                "process",
                "handle",
            ),
            provider=provider,
            args=args,
            kwargs=kwargs,
        )

    # ====================================================================
    # INTERNAL ROUTING
    # ====================================================================

    def _call_operation(
        self,
        *,
        operation: str,
        method_names: Tuple[str, ...],
        provider: Optional[str],
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> UIResult:
        """
        Execute a UI operation using compatible providers.
        """

        providers = self._select_providers(provider)

        if not providers:

            return UIResult(
                success=False,
                operation=operation,
                error=("No UI providers " "are registered."),
            )

        errors: List[str] = []

        for provider_name, provider_object in providers:

            try:

                result = self._call_provider(
                    provider_object,
                    operation,
                    method_names,
                    *args,
                    **kwargs,
                )

                if inspect.isawaitable(result):

                    raise RuntimeError(
                        "Async UI execution is "
                        "not supported by this "
                        "synchronous service."
                    )

                return self._normalize_result(
                    result,
                    provider=provider_name,
                    operation=operation,
                )

            except Exception as error:

                errors.append(f"{provider_name}: {error}")

        return UIResult(
            success=False,
            operation=operation,
            error=("; ".join(errors) or "UI operation failed."),
        )

    @staticmethod
    def _call_provider(
        provider: Any,
        operation: str,
        method_names: Tuple[str, ...],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Find and call a compatible provider method.
        """

        for method_name in method_names:

            method = getattr(
                provider,
                method_name,
                None,
            )

            if not callable(method):

                continue

            if method_name == operation:

                return method(
                    *args,
                    **kwargs,
                )

            if method_name in (
                "execute",
                "process",
                "handle",
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
            f"any of these methods: "
            f"{', '.join(method_names)}"
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
    ) -> UIResult:
        """
        Normalize UI provider results.
        """

        if isinstance(
            result,
            UIResult,
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

            return UIResult(
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

            return UIResult(
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

        return UIResult(
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
        """
        Select providers for an operation.
        """

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

            return list(self._providers.items())

    # ====================================================================
    # STATUS
    # ====================================================================

    def status(
        self,
    ) -> Dict[str, Any]:
        """
        Return lightweight service status.
        """

        with self._lock:

            provider_names = list(self._providers.keys())

        return {
            "provider_count": len(provider_names),
            "providers": provider_names,
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

        normalized = str(operation).strip()

        if not normalized:

            raise ValueError("UI operation cannot be empty.")

        return normalized


# ============================================================================
# SHARED UI SERVICE
# ============================================================================


_default_ui_service: Optional[UIService] = None


def get_ui_service() -> UIService:
    """
    Return the shared Omnix V5 UIService.
    """

    global _default_ui_service

    if _default_ui_service is None:

        _default_ui_service = UIService()

    return _default_ui_service


def reset_ui_service() -> None:
    """
    Reset the shared UIService.

    Primarily useful for testing or controlled engine reinitialization.
    """

    global _default_ui_service

    _default_ui_service = None


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "UIResult",
    "UIProviderInfo",
    "UIService",
    "get_ui_service",
    "reset_ui_service",
]
