"""
Omnix V5 Automation Service

Thin integration gateway between the V5 core and the real
automation subsystem.

Real implementation:

    automation/automation_engine.py

This service does not implement desktop automation itself.
It delegates actions to registered automation providers,
primarily AutomationEngine.
"""

from __future__ import annotations

import asyncio
import inspect

from dataclasses import dataclass, field
from threading import RLock

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
)

# ============================================================================
# RESULT
# ============================================================================


@dataclass
class AutomationResult:
    """
    Normalized result returned by AutomationService.
    """

    success: bool

    value: Any = None

    provider: Optional[str] = None

    action: Optional[str] = None

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
            "action": self.action,
            "error": self.error,
            "metadata": dict(self.metadata),
        }


# ============================================================================
# AUTOMATION SERVICE
# ============================================================================


class AutomationService:
    """
    V5 gateway for the real automation subsystem.

    Architecture:

        OmnixEngine
             |
             v
        AutomationService
             |
             v
        AutomationEngine
             |
             +--> SystemManager
             +--> InputManager
             +--> BrowserManager
             +--> GoalExecutor

    The primary provider should normally be:

        automation.AutomationEngine
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
            raise ValueError("Automation provider cannot be None.")

        try:
            priority = int(priority)

        except (
            TypeError,
            ValueError,
        ):
            priority = 0

        with self._lock:

            if name in self._providers and not replace:
                raise ValueError(f"Automation provider already exists: " f"{name}")

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
    ) -> Any:

        name = self._normalize_provider_name(name)

        with self._lock:

            return self._providers.get(name)

    def has_provider(
        self,
        name: str,
    ) -> bool:

        return self.get_provider(name) is not None

    def get_primary_provider(
        self,
    ) -> Optional[Any]:

        providers = self._get_ordered_providers()

        if not providers:
            return None

        return providers[0][1]

    def get_provider_names(
        self,
    ) -> List[str]:

        with self._lock:

            return list(self._providers.keys())

    # ====================================================================
    # EXECUTION
    # ====================================================================

    async def execute_async(
        self,
        action: str,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> AutomationResult:
        """
        Execute an automation action.

        Example:

            await automation_service.execute_async(
                "open_application",
                app="chrome",
            )
        """

        action = self._normalize_action(action)

        if not action:

            return AutomationResult(
                success=False,
                error="Automation action is required.",
            )

        providers = self._select_providers(provider)

        if not providers:

            return AutomationResult(
                success=False,
                action=action,
                error=("No automation provider is registered."),
            )

        errors = []

        for provider_name, provider_object in providers:

            try:

                raw_result = self._call_provider(
                    provider_object,
                    action,
                    args,
                    kwargs,
                )

                if inspect.isawaitable(raw_result):
                    raw_result = await raw_result

                result = self._normalize_result(
                    raw_result,
                    action,
                    provider_name,
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

        return AutomationResult(
            success=False,
            action=action,
            error=("No automation provider completed " "the action."),
            metadata={
                "provider_errors": errors,
            },
        )

    def execute(
        self,
        action: str,
        *args: Any,
        provider: Optional[str] = None,
        **kwargs: Any,
    ) -> AutomationResult:
        """
        Synchronous compatibility wrapper.

        Do not call this inside an already running
        asyncio event loop.

        Use execute_async() there.
        """

        try:

            asyncio.get_running_loop()

        except RuntimeError:

            return asyncio.run(
                self.execute_async(
                    action,
                    *args,
                    provider=provider,
                    **kwargs,
                )
            )

        raise RuntimeError(
            "AutomationService.execute() cannot be "
            "used inside an active event loop. "
            "Use await execute_async()."
        )

    execute_action = execute
    run_action = execute

    async def execute_action_async(
        self,
        action: str,
        *args: Any,
        **kwargs: Any,
    ) -> AutomationResult:

        return await self.execute_async(
            action,
            *args,
            **kwargs,
        )

    # ====================================================================
    # PLAN EXECUTION
    # ====================================================================

    async def execute_plan(
        self,
        plan: Any,
        *,
        provider: Optional[str] = None,
    ) -> AutomationResult:
        """
        Execute a complete automation plan.

        If AutomationEngine exposes execute_plan(),
        the full plan is delegated directly.
        """

        providers = self._select_providers(provider)

        if not providers:

            return AutomationResult(
                success=False,
                action="execute_plan",
                error=("No automation provider is registered."),
            )

        errors = []

        for provider_name, provider_object in providers:

            method = getattr(
                provider_object,
                "execute_plan",
                None,
            )

            if not callable(method):
                continue

            try:

                raw_result = method(plan)

                if inspect.isawaitable(raw_result):
                    raw_result = await raw_result

                result = self._normalize_result(
                    raw_result,
                    "execute_plan",
                    provider_name,
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

        return AutomationResult(
            success=False,
            action="execute_plan",
            error=("No automation provider could " "execute the plan."),
            metadata={
                "provider_errors": errors,
            },
        )

    # ====================================================================
    # PROVIDER CALLING
    # ====================================================================

    def _call_provider(
        self,
        provider: Any,
        action: str,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> Any:
        """
        Call the real AutomationEngine.

        First tries direct action methods.
        Then falls back to generic provider APIs.
        """

        aliases = self._get_action_aliases(action)

        # ------------------------------------------------
        # Direct AutomationEngine methods
        # ------------------------------------------------

        for method_name in aliases:

            method = getattr(
                provider,
                method_name,
                None,
            )

            if callable(method):

                return self._invoke_method(
                    method,
                    action,
                    args,
                    kwargs,
                )

        # ------------------------------------------------
        # Generic compatibility methods
        # ------------------------------------------------

        for method_name in (
            "execute_action",
            "execute",
            "run_action",
            "run",
            "perform",
            "process",
        ):

            method = getattr(
                provider,
                method_name,
                None,
            )

            if callable(method):

                return self._invoke_generic(
                    method,
                    action,
                    args,
                    kwargs,
                )

        # ------------------------------------------------
        # Callable provider
        # ------------------------------------------------

        if callable(provider):

            return provider(
                action,
                *args,
                **kwargs,
            )

        raise AttributeError(
            f"Automation provider does not support " f"action: {action}"
        )

    # ====================================================================
    # METHOD INVOCATION
    # ====================================================================

    @staticmethod
    def _invoke_method(
        method: Any,
        action: str,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> Any:

        parameters = dict(kwargs)

        # ------------------------------------------------
        # Application compatibility
        # ------------------------------------------------

        if action in (
            "open_application",
            "close_application",
            "focus_application",
            "is_running",
        ):

            if "app" not in parameters and "application" in parameters:
                parameters["app"] = parameters.pop("application")

            if "app" not in parameters and "target" in parameters:
                parameters["app"] = parameters.pop("target")

        # ------------------------------------------------
        # Browser compatibility
        # ------------------------------------------------

        elif action == "open_browser":

            if "browser" not in parameters and "app" in parameters:
                parameters["browser"] = parameters.pop("app")

        elif action == "search_web":

            if "query" not in parameters and "text" in parameters:
                parameters["query"] = parameters.pop("text")

        elif action == "navigate":

            if "url" not in parameters and "target" in parameters:
                parameters["url"] = parameters.pop("target")

        # ------------------------------------------------
        # Input compatibility
        # ------------------------------------------------

        elif action == "type_text":

            if "text" not in parameters and "value" in parameters:
                parameters["text"] = parameters.pop("value")

        elif action == "press_key":

            if "key" not in parameters and "keys" in parameters:
                parameters["key"] = parameters.pop("keys")

        elif action == "drag":

            aliases = {
                "start_x": "x1",
                "start_y": "y1",
                "end_x": "x2",
                "end_y": "y2",
            }

            for target, source in aliases.items():

                if target not in parameters and source in parameters:
                    parameters[target] = parameters.pop(source)

        return method(
            *args,
            **parameters,
        )

    @staticmethod
    def _invoke_generic(
        method: Any,
        action: str,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> Any:

        attempts = (
            lambda: method(
                action,
                *args,
                **kwargs,
            ),
            lambda: method(
                action=action,
                *args,
                **kwargs,
            ),
            lambda: method(
                {
                    "action": action,
                    "parameters": dict(kwargs),
                }
            ),
        )

        last_error = None

        for attempt in attempts:

            try:
                return attempt()

            except TypeError as error:
                last_error = error

        if last_error is not None:
            raise last_error

        raise RuntimeError("Unable to invoke automation provider.")

    # ====================================================================
    # ACTION ALIASES
    # ====================================================================

    @staticmethod
    def _get_action_aliases(
        action: str,
    ) -> Tuple[str, ...]:

        mapping = {
            # Applications
            "open_application": (
                "open_application",
                "open_app",
                "launch_application",
                "launch",
            ),
            "open_app": (
                "open_application",
                "open_app",
                "launch_application",
                "launch",
            ),
            "close_application": (
                "close_application",
                "close_app",
                "quit_application",
            ),
            "close_app": (
                "close_application",
                "close_app",
                "quit_application",
            ),
            "focus_application": (
                "focus_application",
                "focus_app",
            ),
            "is_running": (
                "is_running",
                "application_running",
            ),
            # Browser
            "open_browser": (
                "open_browser",
                "launch_browser",
            ),
            "search_web": (
                "search_web",
                "browser_search",
                "search",
            ),
            "navigate": (
                "navigate",
                "open_url",
                "go_to",
            ),
            "new_tab": ("new_tab",),
            "close_tab": ("close_tab",),
            "refresh_browser": (
                "refresh_browser",
                "refresh",
            ),
            "browser_back": (
                "browser_back",
                "back",
            ),
            "browser_forward": (
                "browser_forward",
                "forward",
            ),
            "scroll_browser": (
                "scroll_browser",
                "scroll",
            ),
            "focus_browser": ("focus_browser",),
            "browser_action": ("browser_action",),
            # Input
            "move_mouse": ("move_mouse",),
            "click": (
                "click",
                "click_mouse",
            ),
            "click_mouse": (
                "click",
                "click_mouse",
            ),
            "double_click": ("double_click",),
            "right_click": ("right_click",),
            "middle_click": ("middle_click",),
            "drag": (
                "drag",
                "drag_mouse",
            ),
            "drag_mouse": (
                "drag",
                "drag_mouse",
            ),
            "type_text": (
                "type_text",
                "write_text",
            ),
            "press_key": (
                "press_key",
                "key_press",
            ),
            "hotkey": (
                "hotkey",
                "press_hotkey",
            ),
            "scroll": ("scroll",),
            "scroll_page": (
                "scroll",
                "scroll_page",
            ),
        }

        return mapping.get(
            action,
            (action,),
        )

    # ====================================================================
    # RESULT NORMALIZATION
    # ====================================================================

    @staticmethod
    def _normalize_result(
        raw_result: Any,
        action: str,
        provider: str,
    ) -> AutomationResult:

        if isinstance(
            raw_result,
            AutomationResult,
        ):

            if raw_result.action is None:
                raw_result.action = action

            if raw_result.provider is None:
                raw_result.provider = provider

            return raw_result

        if raw_result is None:

            return AutomationResult(
                success=True,
                value=None,
                provider=provider,
                action=action,
            )

        if hasattr(
            raw_result,
            "success",
        ):

            return AutomationResult(
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
                            None,
                        ),
                    ),
                ),
                provider=provider,
                action=action,
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

            return AutomationResult(
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
                action=action,
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

            return AutomationResult(
                success=raw_result,
                value=raw_result,
                provider=provider,
                action=action,
            )

        if isinstance(
            raw_result,
            str,
        ):

            lowered = raw_result.strip().lower()

            if lowered in (
                "error",
                "failed",
                "failure",
            ):

                return AutomationResult(
                    success=False,
                    value=raw_result,
                    provider=provider,
                    action=action,
                    error=raw_result,
                )

        return AutomationResult(
            success=True,
            value=raw_result,
            provider=provider,
            action=action,
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

    def _get_ordered_providers(
        self,
    ) -> List[Tuple[str, Any]]:

        return self._select_providers(None)

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
    def _normalize_action(
        action: Any,
    ) -> str:

        normalized = str(action or "").strip().lower()

        return normalized

    # ====================================================================
    # STATUS
    # ====================================================================

    def status(
        self,
    ) -> Dict[str, Any]:

        providers = []

        for name, provider in self._get_ordered_providers():

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
                    "metadata": dict(
                        self._metadata.get(
                            name,
                            {},
                        )
                    ),
                }
            )

        return {
            "service": "automation",
            "provider_count": len(providers),
            "providers": providers,
        }


__all__ = [
    "AutomationResult",
    "AutomationService",
]
