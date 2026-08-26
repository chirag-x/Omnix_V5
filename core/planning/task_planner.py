from __future__ import annotations

import inspect
from typing import Any, Optional

from loguru import logger


class TaskPlanner:
    """
    Omnix V5 Task Planner.

    This class is part of the core orchestration layer.

    It does NOT create or own:
        - BrainManager
        - AI providers
        - Skills managers
        - Vision managers
        - Automation managers
        - CommandProcessor

    All external dependencies are injected by OmnixEngine.
    """

    def __init__(
        self,
        ai_service: Optional[Any] = None,
        command_processor: Optional[Any] = None,
        context_service: Optional[Any] = None,
        memory_service: Optional[Any] = None,
    ) -> None:

        self.ai_service = ai_service
        self.command_processor = command_processor
        self.context_service = context_service
        self.memory_service = memory_service

        logger.debug(
            "TaskPlanner initialized. "
            f"ai_service={type(ai_service).__name__ if ai_service else None}, "
            f"command_processor={type(command_processor).__name__ if command_processor else None}"
        )

    # ============================================================
    # DEPENDENCY INJECTION
    # ============================================================

    def set_ai_service(self, ai_service: Any) -> None:
        self.ai_service = ai_service

    def set_command_processor(self, command_processor: Any) -> None:
        self.command_processor = command_processor

    def set_context_service(self, context_service: Any) -> None:
        self.context_service = context_service

    def set_memory_service(self, memory_service: Any) -> None:
        self.memory_service = memory_service

    # ============================================================
    # MAIN PLANNING
    # ============================================================

    def plan(
        self,
        command: str,
        *,
        context: Optional[dict] = None,
    ) -> Any:
        """
        Build a task plan.

        Fast/simple commands are first delegated to the shared
        CommandProcessor when it exposes a suitable planning API.

        Otherwise, the injected AIService is used for higher-level
        planning.
        """

        command = str(command or "").strip()

        if not command:
            return {
                "success": False,
                "error": "Cannot plan an empty command.",
                "steps": [],
            }

        context = context or {}

        # --------------------------------------------------------
        # 1. Try the shared CommandProcessor first.
        # --------------------------------------------------------

        result = self._plan_with_command_processor(
            command,
            context,
        )

        if result is not None:
            return result

        # --------------------------------------------------------
        # 2. Fall back to the real AI subsystem.
        # --------------------------------------------------------

        result = self._plan_with_ai(
            command,
            context,
        )

        if result is not None:
            return result

        # --------------------------------------------------------
        # 3. Safe fallback.
        # --------------------------------------------------------

        return {
            "success": True,
            "command": command,
            "steps": [
                {
                    "type": "command",
                    "command": command,
                }
            ],
            "source": "fallback",
        }

    # Compatibility aliases for older callers.
    create_plan = plan
    plan_task = plan

    # ============================================================
    # COMMAND PROCESSOR
    # ============================================================

    def _plan_with_command_processor(
        self,
        command: str,
        context: dict,
    ) -> Any:

        processor = self.command_processor

        if processor is None:
            return None

        for method_name in (
            "plan",
            "create_plan",
            "process",
            "process_command",
        ):

            method = getattr(
                processor,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:
                result = self._call_with_optional_context(
                    method,
                    command,
                    context,
                )

                if result is not None:
                    return result

            except Exception as error:

                logger.debug(
                    f"CommandProcessor.{method_name} "
                    f"planning attempt failed: {error}"
                )

        return None

    # ============================================================
    # AI PLANNING
    # ============================================================

    def _plan_with_ai(
        self,
        command: str,
        context: dict,
    ) -> Any:

        service = self.ai_service

        if service is None:
            return None

        prompt = self._build_planning_prompt(
            command,
            context,
        )

        for method_name in (
            "plan",
            "generate_plan",
            "process",
            "ask",
            "generate",
            "chat",
        ):

            method = getattr(
                service,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:

                result = self._call_ai_method(
                    method,
                    command,
                    prompt,
                    context,
                )

                if result is not None:
                    return result

            except Exception as error:

                logger.debug(
                    f"AIService.{method_name} " f"planning attempt failed: {error}"
                )

        return None

    # ============================================================
    # AI PROMPT
    # ============================================================

    @staticmethod
    def _build_planning_prompt(
        command: str,
        context: dict,
    ) -> str:

        context_text = ""

        if context:
            context_text = "\n\nContext:\n" f"{context}"

        return (
            "You are the planning component of Omnix. "
            "Break the user's request into a clear, executable plan. "
            "Prefer concrete actions and preserve the user's intent.\n\n"
            f"User request:\n{command}"
            f"{context_text}"
        )

    # ============================================================
    # CALL HELPERS
    # ============================================================

    def _call_with_optional_context(
        self,
        method: Any,
        command: str,
        context: dict,
    ) -> Any:

        try:
            result = method(
                command,
                context=context,
            )
        except TypeError:
            result = method(command)

        return self._resolve_if_awaitable(result)

    def _call_ai_method(
        self,
        method: Any,
        command: str,
        prompt: str,
        context: dict,
    ) -> Any:

        attempts = (
            lambda: method(
                command,
                context=context,
            ),
            lambda: method(
                prompt,
                context=context,
            ),
            lambda: method(command),
            lambda: method(prompt),
        )

        last_error = None

        for attempt in attempts:

            try:

                result = attempt()

                return self._resolve_if_awaitable(result)

            except TypeError as error:

                last_error = error

                continue

        if last_error is not None:
            raise last_error

        return None

    @staticmethod
    def _resolve_if_awaitable(
        value: Any,
    ) -> Any:

        if not inspect.isawaitable(value):
            return value

        raise RuntimeError(
            "TaskPlanner received an async dependency. "
            "Use the async execution path in the caller."
        )

    # ============================================================
    # STATUS
    # ============================================================

    def status(self) -> dict:

        return {
            "available": True,
            "ai_service": (
                type(self.ai_service).__name__ if self.ai_service is not None else None
            ),
            "command_processor": (
                type(self.command_processor).__name__
                if self.command_processor is not None
                else None
            ),
            "context_service": (
                type(self.context_service).__name__
                if self.context_service is not None
                else None
            ),
            "memory_service": (
                type(self.memory_service).__name__
                if self.memory_service is not None
                else None
            ),
        }

    def health_check(self) -> bool:
        return True
