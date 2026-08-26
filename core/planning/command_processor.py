from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from loguru import logger


class CommandProcessor:
    """
    Omnix V5 Command Processor.

    This component is intentionally lightweight.

    It does NOT create or own:
        - BrainManager
        - AIService
        - SkillManager
        - VisionManager
        - VoiceManager
        - AutomationManager

    Its responsibilities are:

        1. Clean and normalize user commands.
        2. Detect simple deterministic commands.
        3. Convert simple commands into executable action plans.
        4. Pass complex commands to the injected planning components.

    Actual execution remains outside this class.
    """

    SIMPLE_COMMAND_PATTERNS = [
        (
            r"^(?:open|start|launch|run)\s+(?:the\s+)?(.+?)(?:\s+app(?:lication)?)?$",
            "open_app",
            "app",
        ),
        (
            r"^(?:close|exit|quit)\s+(?:the\s+)?(.+?)(?:\s+app(?:lication)?)?$",
            "close_app",
            "app",
        ),
        (
            r"^(?:type|write)\s+(.+)$",
            "type_text",
            "text",
        ),
        (
            r"^(?:press|hit)\s+(.+)$",
            "press_key",
            "key",
        ),
        (
            r"^(?:click|tap)\s+(.+)$",
            "click_ui",
            "text",
        ),
        (
            r"^scroll\s+(up|down)$",
            "scroll_page",
            "direction",
        ),
    ]

    def __init__(
        self,
        intent_classifier: Optional[Any] = None,
        target_resolver: Optional[Any] = None,
        task_planner: Optional[Any] = None,
    ) -> None:

        self.intent_classifier = intent_classifier
        self.target_resolver = target_resolver
        self.task_planner = task_planner

        logger.debug(
            "CommandProcessor initialized. "
            f"intent_classifier="
            f"{type(intent_classifier).__name__ if intent_classifier else None}, "
            f"target_resolver="
            f"{type(target_resolver).__name__ if target_resolver else None}, "
            f"task_planner="
            f"{type(task_planner).__name__ if task_planner else None}"
        )

    # ============================================================
    # DEPENDENCY INJECTION
    # ============================================================

    def set_intent_classifier(
        self,
        intent_classifier: Any,
    ) -> None:

        self.intent_classifier = intent_classifier

    def set_target_resolver(
        self,
        target_resolver: Any,
    ) -> None:

        self.target_resolver = target_resolver

    def set_task_planner(
        self,
        task_planner: Any,
    ) -> None:

        self.task_planner = task_planner

    # ============================================================
    # BASIC COMMAND PROCESSING
    # ============================================================

    def process(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:

        text = str(text or "").strip()

        if not text:
            return None

        cleaned = self._clean_command(text)

        if not cleaned:
            return None

        if cleaned in (
            "exit",
            "quit",
            "shutdown",
        ):

            return {
                "type": "system",
                "command": "shutdown",
            }

        return {
            "type": "user_input",
            "command": cleaned,
            "context": context or {},
        }

    # ============================================================
    # SIMPLE COMMAND DETECTION
    # ============================================================

    def create_simple_plan(
        self,
        text: str,
    ) -> List[Dict[str, Any]]:

        action = self._match_simple_command(text)

        if not action:
            return []

        logger.info(f"Using simple command plan: {action}")

        return [action]

    def is_simple_automation(
        self,
        text: str,
    ) -> bool:

        return self._match_simple_command(text) is not None

    # Alias useful for VoiceManager.
    looks_like_automation = is_simple_automation

    # ============================================================
    # FULL PLAN CREATION
    # ============================================================

    def create_plan(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:

        text = str(text or "").strip()

        if not text:
            return []

        # --------------------------------------------------------
        # 1. Fast deterministic plan.
        # --------------------------------------------------------

        simple_plan = self.create_simple_plan(text)

        if simple_plan:
            return simple_plan

        # --------------------------------------------------------
        # 2. Complex command -> shared TaskPlanner.
        # --------------------------------------------------------

        planner = self.task_planner

        if planner is None:

            return []

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

                try:

                    result = method(
                        text,
                        context=context,
                    )

                except TypeError:

                    result = method(text)

                if result is not None:
                    return result

            except Exception as error:

                logger.debug(f"TaskPlanner.{method_name} failed: " f"{error}")

        return []

    # ============================================================
    # COMMAND ANALYSIS
    # ============================================================

    def analyze(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        processed = self.process(
            text,
            context,
        )

        if processed is None:

            return {
                "success": False,
                "error": "Empty command.",
            }

        command = processed.get(
            "command",
            "",
        )

        simple_action = self._match_simple_command(command)

        intent = self._classify_intent(
            command,
            context or {},
        )

        return {
            "success": True,
            "command": command,
            "intent": intent,
            "simple": (simple_action is not None),
            "action": simple_action,
        }

    def _classify_intent(
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

                try:

                    result = method(
                        command,
                        context=context,
                    )

                except TypeError:

                    result = method(command)

                if result is not None:
                    return result

            except Exception as error:

                logger.debug(f"IntentClassifier.{method_name} " f"failed: {error}")

        return None

    # ============================================================
    # TARGET RESOLUTION
    # ============================================================

    def resolve_target(
        self,
        target: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:

        resolver = self.target_resolver

        if resolver is None:
            return None

        for method_name in (
            "resolve",
            "resolve_target",
            "find",
        ):

            method = getattr(
                resolver,
                method_name,
                None,
            )

            if not callable(method):
                continue

            try:

                try:

                    result = method(
                        target,
                        context=context or {},
                    )

                except TypeError:

                    result = method(target)

                if result is not None:
                    return result

            except Exception as error:

                logger.debug(f"TargetResolver.{method_name} " f"failed: {error}")

        return None

    # ============================================================
    # INTERNAL MATCHING
    # ============================================================

    def _match_simple_command(
        self,
        text: str,
    ) -> Optional[Dict[str, Any]]:

        text = self._clean_command(text)

        if not text:
            return None

        for (
            pattern,
            skill,
            param_name,
        ) in self.SIMPLE_COMMAND_PATTERNS:

            match = re.match(
                pattern,
                text,
            )

            if not match:
                continue

            value = self._clean_parameter(match.group(1))

            if not value:
                return None

            return {
                "skill": skill,
                "parameters": {param_name: value},
            }

        return None

    @staticmethod
    def _clean_command(
        text: str,
    ) -> str:

        text = str(text or "").lower().strip()

        text = re.sub(
            r"\b(?:hey\s+)?omnix\b",
            "",
            text,
        )

        text = re.sub(
            r"^(?:please|can you|could you|would you)\s+",
            "",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip(" .,!?:;")

    @staticmethod
    def _clean_parameter(
        value: str,
    ) -> str:

        value = str(value or "").strip(" .,!?:;")

        for prefix in (
            "please ",
            "the ",
        ):

            if value.startswith(prefix):

                value = value[len(prefix) :].strip()

        return value

    # ============================================================
    # STATUS
    # ============================================================

    def status(
        self,
    ) -> Dict[str, Any]:

        return {
            "available": True,
            "intent_classifier": (
                type(self.intent_classifier).__name__
                if self.intent_classifier is not None
                else None
            ),
            "target_resolver": (
                type(self.target_resolver).__name__
                if self.target_resolver is not None
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

        return True
