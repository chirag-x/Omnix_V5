from __future__ import annotations

import inspect
from typing import Any, Dict, Optional

from loguru import logger


class GoalExecutor:
    """
    Omnix V5 Goal Executor.

    This class belongs to the core orchestration layer.

    It does NOT create or own:

        - SkillManager
        - VisionManager
        - VoiceManager
        - BrainManager
        - AutomationManager
        - MemoryManager

    All subsystem dependencies must be injected by OmnixEngine.

    Main execution flow:

        GoalExecutor
            ↓
        SkillsService / AutomationService / VisionService
            ↓
        Real subsystem manager
            ↓
        Result
    """

    def __init__(
        self,
        skills_service: Optional[Any] = None,
        automation_service: Optional[Any] = None,
        vision_service: Optional[Any] = None,
        ai_service: Optional[Any] = None,
        context_service: Optional[Any] = None,
        memory_service: Optional[Any] = None,
    ) -> None:

        self.skills_service = skills_service
        self.automation_service = automation_service
        self.vision_service = vision_service
        self.ai_service = ai_service
        self.context_service = context_service
        self.memory_service = memory_service

        logger.debug(
            "GoalExecutor initialized. "
            f"skills_service="
            f"{type(skills_service).__name__ if skills_service else None}"
        )

    # ============================================================
    # DEPENDENCY INJECTION
    # ============================================================

    def set_skills_service(
        self,
        skills_service: Any,
    ) -> None:
        self.skills_service = skills_service

    def set_automation_service(
        self,
        automation_service: Any,
    ) -> None:
        self.automation_service = automation_service

    def set_vision_service(
        self,
        vision_service: Any,
    ) -> None:
        self.vision_service = vision_service

    def set_ai_service(
        self,
        ai_service: Any,
    ) -> None:
        self.ai_service = ai_service

    def set_context_service(
        self,
        context_service: Any,
    ) -> None:
        self.context_service = context_service

    def set_memory_service(
        self,
        memory_service: Any,
    ) -> None:
        self.memory_service = memory_service

    # ============================================================
    # MAIN EXECUTION
    # ============================================================

    def execute(
        self,
        goal: Any,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Execute a goal using the real Omnix subsystems.

        The goal may be:

            - string
            - dictionary
            - task/goal object
        """

        context = context or {}

        if goal is None:
            return self._error_result("Cannot execute an empty goal.")

        logger.info(f"GoalExecutor executing: {goal}")

        # --------------------------------------------------------
        # Normalize the goal.
        # --------------------------------------------------------

        goal_data = self._normalize_goal(goal)

        # --------------------------------------------------------
        # Explicit subsystem routing.
        # --------------------------------------------------------

        route = self._get_route(goal_data)

        if route == "automation":

            result = self._execute_with_automation(
                goal_data,
                context,
            )

            if result is not None:
                return result

        elif route == "vision":

            result = self._execute_with_vision(
                goal_data,
                context,
            )

            if result is not None:
                return result

        elif route == "ai":

            result = self._execute_with_ai(
                goal_data,
                context,
            )

            if result is not None:
                return result

        # --------------------------------------------------------
        # Default route:
        #
        # Use the real Skills subsystem.
        # --------------------------------------------------------

        result = self._execute_with_skills(
            goal_data,
            context,
        )

        if result is not None:
            return result

        # --------------------------------------------------------
        # Automation fallback.
        # --------------------------------------------------------

        result = self._execute_with_automation(
            goal_data,
            context,
        )

        if result is not None:
            return result

        return self._error_result(
            "No available Omnix subsystem could execute " "this goal.",
            goal=goal_data,
        )

    # Compatibility aliases.
    execute_goal = execute
    run = execute

    # ============================================================
    # GOAL NORMALIZATION
    # ============================================================

    def _normalize_goal(
        self,
        goal: Any,
    ) -> Dict[str, Any]:

        if isinstance(
            goal,
            dict,
        ):
            return dict(goal)

        if isinstance(
            goal,
            str,
        ):
            return {
                "command": goal,
                "goal": goal,
            }

        data = {}

        for attribute in (
            "command",
            "goal",
            "task",
            "action",
            "intent",
            "type",
            "target",
            "parameters",
        ):

            value = getattr(
                goal,
                attribute,
                None,
            )

            if value is not None:
                data[attribute] = value

        if not data:

            data = {"goal": str(goal)}

        return data

    # ============================================================
    # ROUTING
    # ============================================================

    @staticmethod
    def _get_route(
        goal: Dict[str, Any],
    ) -> Optional[str]:

        for key in (
            "route",
            "executor",
            "service",
            "type",
        ):

            value = goal.get(key)

            if not value:
                continue

            value = str(value).lower()

            if "automation" in value:
                return "automation"

            if "vision" in value:
                return "vision"

            if value in (
                "ai",
                "chat",
                "conversation",
            ):
                return "ai"

        return None

    # ============================================================
    # SKILLS EXECUTION
    # ============================================================

    def _execute_with_skills(
        self,
        goal: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Any:

        service = self.skills_service

        if service is None:
            return None

        command = self._get_command(goal)

        methods = (
            "execute",
            "execute_skill",
            "run",
            "process",
            "handle",
        )

        return self._try_service_methods(
            service=service,
            methods=methods,
            command=command,
            goal=goal,
            context=context,
            service_name="SkillsService",
        )

    # ============================================================
    # AUTOMATION EXECUTION
    # ============================================================

    def _execute_with_automation(
        self,
        goal: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Any:

        service = self.automation_service

        if service is None:
            return None

        command = self._get_command(goal)

        methods = (
            "execute",
            "run",
            "process",
            "handle",
        )

        return self._try_service_methods(
            service=service,
            methods=methods,
            command=command,
            goal=goal,
            context=context,
            service_name="AutomationService",
        )

    # ============================================================
    # VISION EXECUTION
    # ============================================================

    def _execute_with_vision(
        self,
        goal: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Any:

        service = self.vision_service

        if service is None:
            return None

        command = self._get_command(goal)

        methods = (
            "analyze",
            "observe",
            "process",
            "execute",
        )

        return self._try_service_methods(
            service=service,
            methods=methods,
            command=command,
            goal=goal,
            context=context,
            service_name="VisionService",
        )

    # ============================================================
    # AI EXECUTION
    # ============================================================

    def _execute_with_ai(
        self,
        goal: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Any:

        service = self.ai_service

        if service is None:
            return None

        command = self._get_command(goal)

        methods = (
            "process",
            "ask",
            "generate",
            "chat",
            "execute",
        )

        return self._try_service_methods(
            service=service,
            methods=methods,
            command=command,
            goal=goal,
            context=context,
            service_name="AIService",
        )

    # ============================================================
    # GENERIC SERVICE CALLER
    # ============================================================

    def _try_service_methods(
        self,
        *,
        service: Any,
        methods,
        command: str,
        goal: Dict[str, Any],
        context: Dict[str, Any],
        service_name: str,
    ) -> Any:

        for method_name in methods:

            method = getattr(
                service,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:

                result = self._call_service_method(
                    method,
                    command,
                    goal,
                    context,
                )

                if result is not None:

                    logger.debug(
                        f"{service_name} handled goal " f"using {method_name}()."
                    )

                    return result

            except Exception as error:

                logger.debug(f"{service_name}.{method_name} " f"failed: {error}")

        return None

    def _call_service_method(
        self,
        method: Any,
        command: str,
        goal: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Any:

        attempts = (
            lambda: method(
                command,
                context=context,
            ),
            lambda: method(
                goal,
                context=context,
            ),
            lambda: method(command),
            lambda: method(goal),
        )

        last_error = None

        for attempt in attempts:

            try:

                result = attempt()

                if inspect.isawaitable(result):

                    raise RuntimeError(
                        "GoalExecutor received an async "
                        "service result. Use the async "
                        "execution path."
                    )

                return result

            except TypeError as error:

                last_error = error

                continue

        if last_error is not None:
            raise last_error

        return None

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _get_command(
        goal: Dict[str, Any],
    ) -> str:

        for key in (
            "command",
            "goal",
            "task",
            "action",
            "description",
        ):

            value = goal.get(key)

            if value:

                return str(value)

        return str(goal)

    @staticmethod
    def _error_result(
        error: str,
        **extra: Any,
    ) -> Dict[str, Any]:

        result = {
            "success": False,
            "error": error,
        }

        result.update(extra)

        return result

    # ============================================================
    # STATUS
    # ============================================================

    def status(
        self,
    ) -> Dict[str, Any]:

        return {
            "available": True,
            "skills_service": (
                type(self.skills_service).__name__
                if self.skills_service is not None
                else None
            ),
            "automation_service": (
                type(self.automation_service).__name__
                if self.automation_service is not None
                else None
            ),
            "vision_service": (
                type(self.vision_service).__name__
                if self.vision_service is not None
                else None
            ),
            "ai_service": (
                type(self.ai_service).__name__ if self.ai_service is not None else None
            ),
        }

    def health_check(
        self,
    ) -> bool:

        return True
