from __future__ import annotations

import inspect
from typing import Any, Dict, List, Optional

from loguru import logger


class AgentController:
    """
    Omnix V5 Agent Controller.

    Central orchestration layer for agent execution.

    This class does NOT create:

        - BrainManager
        - SkillManager
        - VisionManager
        - VoiceManager
        - AutomationEngine
        - MemoryManager

    All dependencies are injected by OmnixEngine.

    Execution flow:

        command
            ↓
        IntentClassifier
            ↓
        TaskPlanner
            ↓
        WorkflowPlanner
            ↓
        GoalExecutor
            ↓
        Real Omnix services/subsystems
    """

    def __init__(
        self,
        workflow_planner: Optional[Any] = None,
        goal_executor: Optional[Any] = None,
        command_processor: Optional[Any] = None,
        intent_classifier: Optional[Any] = None,
        task_planner: Optional[Any] = None,
        context_service: Optional[Any] = None,
        memory_service: Optional[Any] = None,
        ai_service: Optional[Any] = None,
    ) -> None:

        self.workflow_planner = workflow_planner
        self.goal_executor = goal_executor
        self.command_processor = command_processor
        self.intent_classifier = intent_classifier
        self.task_planner = task_planner

        self.context_service = context_service
        self.memory_service = memory_service
        self.ai_service = ai_service

        self.running = True

        logger.debug(
            "AgentController initialized. "
            f"workflow_planner="
            f"{type(workflow_planner).__name__ if workflow_planner else None}, "
            f"goal_executor="
            f"{type(goal_executor).__name__ if goal_executor else None}"
        )

    # ============================================================
    # DEPENDENCY INJECTION
    # ============================================================

    def set_workflow_planner(
        self,
        workflow_planner: Any,
    ) -> None:
        self.workflow_planner = workflow_planner

    def set_goal_executor(
        self,
        goal_executor: Any,
    ) -> None:
        self.goal_executor = goal_executor

    def set_command_processor(
        self,
        command_processor: Any,
    ) -> None:
        self.command_processor = command_processor

    def set_intent_classifier(
        self,
        intent_classifier: Any,
    ) -> None:
        self.intent_classifier = intent_classifier

    def set_task_planner(
        self,
        task_planner: Any,
    ) -> None:
        self.task_planner = task_planner

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

    def set_ai_service(
        self,
        ai_service: Any,
    ) -> None:
        self.ai_service = ai_service

    # ============================================================
    # MAIN ENTRY POINT
    # ============================================================

    def execute(
        self,
        command: Any,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Main agent execution entry point.
        """

        if not self.running:
            return self._error("AgentController is stopped.")

        command_text = self._extract_command(command)

        if not command_text:
            return self._error("Cannot execute an empty command.")

        context = dict(context or {})

        logger.info(f"Agent executing: {command_text}")

        # --------------------------------------------------------
        # 1. Analyze command.
        # --------------------------------------------------------

        analysis = self._analyze_command(
            command_text,
            context,
        )

        # --------------------------------------------------------
        # 2. Create task plan.
        # --------------------------------------------------------

        plan = self._create_plan(
            command_text,
            context,
            analysis,
        )

        if plan is None:
            return self._error(
                "Unable to create an execution plan.",
                command=command_text,
                analysis=analysis,
            )

        # --------------------------------------------------------
        # 3. Convert plan into workflow when supported.
        # --------------------------------------------------------

        workflow = self._create_workflow(plan)

        # --------------------------------------------------------
        # 4. Execute workflow or plan.
        # --------------------------------------------------------

        execution_target = workflow if workflow is not None else plan

        result = self._execute(
            execution_target,
            command_text,
            context,
        )

        # --------------------------------------------------------
        # 5. Return normalized result.
        # --------------------------------------------------------

        return self._normalize_result(
            result,
            command=command_text,
            analysis=analysis,
            plan=plan,
            workflow=workflow,
        )

    # Compatibility aliases.

    process_command = execute
    process = execute
    run = execute

    # ============================================================
    # COMMAND ANALYSIS
    # ============================================================

    def _analyze_command(
        self,
        command: str,
        context: Dict[str, Any],
    ) -> Any:

        classifier = self.intent_classifier

        if classifier is None:
            return None

        for method_name in (
            "classify",
            "analyze",
            "predict",
        ):

            method = getattr(
                classifier,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:

                result = self._call(
                    method,
                    command,
                    context=context,
                )

                if result is not None:
                    return result

            except Exception as error:

                logger.debug(
                    f"Intent classification failed " f"through {method_name}: {error}"
                )

        return None

    # ============================================================
    # TASK PLANNING
    # ============================================================

    def _create_plan(
        self,
        command: str,
        context: Dict[str, Any],
        analysis: Any,
    ) -> Any:

        planner = self.task_planner

        if planner is not None:

            for method_name in (
                "create_plan",
                "plan",
                "plan_task",
            ):

                method = getattr(
                    planner,
                    method_name,
                    None,
                )

                if not callable(method):
                    continue

                try:

                    result = self._call(
                        method,
                        command,
                        context=context,
                        analysis=analysis,
                    )

                    if result is not None:
                        return result

                except Exception as error:

                    logger.debug(
                        f"Task planning failed through " f"{method_name}: {error}"
                    )

        # --------------------------------------------------------
        # Fallback to deterministic command processing.
        # --------------------------------------------------------

        processor = self.command_processor

        if processor is not None:

            method = getattr(
                processor,
                "create_simple_plan",
                None,
            )

            if callable(method):

                try:

                    result = method(command)

                    if result:
                        return result

                except Exception as error:

                    logger.debug(f"Simple plan creation failed: " f"{error}")

        return None

    # ============================================================
    # WORKFLOW CREATION
    # ============================================================

    def _create_workflow(
        self,
        plan: Any,
    ) -> Any:

        planner = self.workflow_planner

        if planner is None:
            return None

        for method_name in (
            "create_workflow",
            "build_workflow",
            "plan_workflow",
            "from_plan",
        ):

            method = getattr(
                planner,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:

                result = method(plan)

                result = self._resolve_result(result)

                if result is not None:
                    return result

            except Exception as error:

                logger.debug(
                    f"Workflow creation failed through " f"{method_name}: {error}"
                )

        return None

    # ============================================================
    # EXECUTION
    # ============================================================

    def _execute(
        self,
        execution_target: Any,
        command: str,
        context: Dict[str, Any],
    ) -> Any:

        executor = self.goal_executor

        if executor is None:
            return self._error("GoalExecutor is unavailable.")

        # --------------------------------------------------------
        # Preferred execution methods.
        # --------------------------------------------------------

        methods = (
            "execute_workflow",
            "execute_plan",
            "execute",
            "execute_goal",
            "run",
        )

        for method_name in methods:

            method = getattr(
                executor,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:

                result = self._call_executor(
                    method,
                    execution_target,
                    command,
                    context,
                )

                if result is not None:
                    return result

            except Exception as error:

                logger.debug(
                    f"Goal execution failed through " f"{method_name}: {error}"
                )

        # --------------------------------------------------------
        # If the executor only supports one goal at a time,
        # execute each step individually.
        # --------------------------------------------------------

        steps = self._extract_steps(execution_target)

        if steps:

            results: List[Any] = []

            for step in steps:

                if not self.running:
                    return self._error("Agent execution was stopped.")

                try:

                    result = self._execute_single_goal(
                        executor,
                        step,
                        context,
                    )

                    results.append(result)

                    if self._result_failed(result):
                        return {
                            "success": False,
                            "error": "Workflow step failed.",
                            "results": results,
                        }

                except Exception as error:

                    return self._error(
                        str(error),
                        results=results,
                    )

            return {
                "success": True,
                "results": results,
            }

        return self._error("GoalExecutor could not execute the plan.")

    # ============================================================
    # SINGLE GOAL EXECUTION
    # ============================================================

    def _execute_single_goal(
        self,
        executor: Any,
        goal: Any,
        context: Dict[str, Any],
    ) -> Any:

        for method_name in (
            "execute",
            "execute_goal",
            "execute_step",
            "run",
        ):

            method = getattr(
                executor,
                method_name,
                None,
            )

            if not callable(method):
                continue

            result = self._call(
                method,
                goal,
                context=context,
            )

            if result is not None:
                return result

        return None

    # ============================================================
    # EXECUTOR CALLING
    # ============================================================

    def _call_executor(
        self,
        method: Any,
        target: Any,
        command: str,
        context: Dict[str, Any],
    ) -> Any:

        attempts = (
            lambda: method(
                target,
                context=context,
            ),
            lambda: method(
                goal=target,
                context=context,
            ),
            lambda: method(
                plan=target,
                context=context,
            ),
            lambda: method(
                workflow=target,
                context=context,
            ),
            lambda: method(target),
            lambda: method(command),
        )

        last_error = None

        for attempt in attempts:

            try:

                result = attempt()

                return self._resolve_result(result)

            except TypeError as error:

                last_error = error

        if last_error is not None:
            raise last_error

        return None

    # ============================================================
    # GENERIC CALL HELPER
    # ============================================================

    def _call(
        self,
        method: Any,
        value: Any,
        *,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:

        attempts = (
            lambda: method(
                value,
                context=context,
                **kwargs,
            ),
            lambda: method(
                value,
                context=context,
            ),
            lambda: method(value),
        )

        last_error = None

        for attempt in attempts:

            try:

                result = attempt()

                return self._resolve_result(result)

            except TypeError as error:

                last_error = error

        if last_error is not None:
            raise last_error

        return None

    @staticmethod
    def _resolve_result(
        result: Any,
    ) -> Any:

        if not inspect.isawaitable(result):
            return result

        raise RuntimeError(
            "AgentController received an async result. "
            "The caller must use the async execution path."
        )

    # ============================================================
    # STEP EXTRACTION
    # ============================================================

    @staticmethod
    def _extract_steps(
        value: Any,
    ) -> List[Any]:

        if value is None:
            return []

        if isinstance(
            value,
            list,
        ):
            return value

        if isinstance(
            value,
            tuple,
        ):
            return list(value)

        if isinstance(
            value,
            dict,
        ):

            for key in (
                "steps",
                "plan",
                "actions",
                "tasks",
            ):

                steps = value.get(key)

                if isinstance(
                    steps,
                    (list, tuple),
                ):
                    return list(steps)

        steps = getattr(
            value,
            "steps",
            None,
        )

        if isinstance(
            steps,
            (list, tuple),
        ):
            return list(steps)

        return []

    # ============================================================
    # RESULT HANDLING
    # ============================================================

    @staticmethod
    def _result_failed(
        result: Any,
    ) -> bool:

        if result is None:
            return True

        if result == "error":
            return True

        if result is False:
            return True

        if (
            isinstance(
                result,
                dict,
            )
            and result.get("success") is False
        ):

            return True

        return False

    def _normalize_result(
        self,
        result: Any,
        *,
        command: str,
        analysis: Any,
        plan: Any,
        workflow: Any,
    ) -> Dict[str, Any]:

        if isinstance(
            result,
            dict,
        ):

            normalized = dict(result)

            normalized.setdefault(
                "command",
                command,
            )

            normalized.setdefault(
                "analysis",
                analysis,
            )

            normalized.setdefault(
                "plan",
                plan,
            )

            normalized.setdefault(
                "workflow",
                workflow,
            )

            normalized.setdefault(
                "success",
                not self._result_failed(result),
            )

            return normalized

        return {
            "success": (not self._result_failed(result)),
            "command": command,
            "analysis": analysis,
            "plan": plan,
            "workflow": workflow,
            "result": result,
        }

    # ============================================================
    # COMMAND EXTRACTION
    # ============================================================

    @staticmethod
    def _extract_command(
        command: Any,
    ) -> str:

        if isinstance(
            command,
            str,
        ):
            return command.strip()

        if isinstance(
            command,
            dict,
        ):

            for key in (
                "command",
                "text",
                "goal",
                "task",
                "action",
            ):

                value = command.get(key)

                if value:
                    return str(value).strip()

        return str(command or "").strip()

    # ============================================================
    # STOP / START
    # ============================================================

    def stop(
        self,
    ) -> None:

        logger.info("Stopping AgentController.")

        self.running = False

        executor = self.goal_executor

        if executor is None:
            return

        method = getattr(
            executor,
            "stop",
            None,
        )

        if callable(method):

            try:
                method()

            except Exception as error:
                logger.debug(f"GoalExecutor stop failed: " f"{error}")

    def start(
        self,
    ) -> bool:

        self.running = True

        return True

    # ============================================================
    # STATUS
    # ============================================================

    def status(
        self,
    ) -> Dict[str, Any]:

        return {
            "available": True,
            "running": self.running,
            "workflow_planner": (
                type(self.workflow_planner).__name__
                if self.workflow_planner is not None
                else None
            ),
            "goal_executor": (
                type(self.goal_executor).__name__
                if self.goal_executor is not None
                else None
            ),
            "command_processor": (
                type(self.command_processor).__name__
                if self.command_processor is not None
                else None
            ),
            "intent_classifier": (
                type(self.intent_classifier).__name__
                if self.intent_classifier is not None
                else None
            ),
            "task_planner": (
                type(self.task_planner).__name__
                if self.task_planner is not None
                else None
            ),
        }

    def health_check(
        self,
    ) -> bool:

        return self.running and self.goal_executor is not None

    # ============================================================
    # ERROR HELPER
    # ============================================================

    @staticmethod
    def _error(
        message: str,
        **extra: Any,
    ) -> Dict[str, Any]:

        result = {
            "success": False,
            "error": message,
        }

        result.update(extra)

        return result
