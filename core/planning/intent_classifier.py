from __future__ import annotations

import inspect
import re
from typing import Any, Dict, Optional

from loguru import logger


class IntentClassifier:
    """
    Omnix V5 Intent Classifier.

    Responsibilities:
        - Classify the user's request.
        - Detect common deterministic intents.
        - Use the injected AIService for complex requests.

    This class does NOT create or own:
        - BrainManager
        - AI providers
        - SkillManager
        - VisionManager
        - VoiceManager
        - AutomationManager

    AI functionality is always accessed through the shared AIService.
    """

    # ============================================================
    # SIMPLE INTENT PATTERNS
    # ============================================================

    INTENT_PATTERNS = {
        "open": (r"^(?:open|launch|start|run)\b",),
        "close": (r"^(?:close|exit|quit)\b",),
        "search": (r"^(?:search|google|look up|find information)\b",),
        "file": (r"\b(?:file|folder|directory|document)\b",),
        "automation": (r"\b(?:click|type|write|press|scroll|download|upload)\b",),
        "vision": (r"\b(?:look at|see|find on screen|screen|button|icon)\b",),
        "conversation": (r"^(?:what|who|why|how|when|where|tell me|explain)\b",),
    }

    def __init__(
        self,
        ai_service: Optional[Any] = None,
        context_service: Optional[Any] = None,
    ) -> None:

        self.ai_service = ai_service
        self.context_service = context_service

        logger.debug(
            "IntentClassifier initialized. "
            f"ai_service="
            f"{type(ai_service).__name__ if ai_service else None}"
        )

    # ============================================================
    # DEPENDENCY INJECTION
    # ============================================================

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

    # ============================================================
    # MAIN CLASSIFICATION
    # ============================================================

    def classify(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        text = str(text or "").strip()

        if not text:
            return {
                "success": False,
                "intent": "unknown",
                "confidence": 0.0,
                "error": "Empty input.",
            }

        context = context or {}

        cleaned = self._clean_text(text)

        # --------------------------------------------------------
        # 1. Fast deterministic classification.
        # --------------------------------------------------------

        result = self._classify_simple(cleaned)

        if result is not None:
            return {
                "success": True,
                "intent": result,
                "confidence": 0.9,
                "source": "rule",
                "text": text,
            }

        # --------------------------------------------------------
        # 2. Complex request -> shared AIService.
        # --------------------------------------------------------

        ai_result = self._classify_with_ai(
            text,
            context,
        )

        if ai_result is not None:
            return self._normalize_ai_result(
                ai_result,
                text,
            )

        # --------------------------------------------------------
        # 3. Safe fallback.
        # --------------------------------------------------------

        return {
            "success": True,
            "intent": "conversation",
            "confidence": 0.3,
            "source": "fallback",
            "text": text,
        }

    # Compatibility aliases.
    analyze = classify
    predict = classify

    # ============================================================
    # SIMPLE CLASSIFICATION
    # ============================================================

    def _classify_simple(
        self,
        text: str,
    ) -> Optional[str]:

        for intent, patterns in self.INTENT_PATTERNS.items():

            for pattern in patterns:

                if re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                ):
                    return intent

        return None

    # ============================================================
    # AI CLASSIFICATION
    # ============================================================

    def _classify_with_ai(
        self,
        text: str,
        context: Dict[str, Any],
    ) -> Any:

        service = self.ai_service

        if service is None:
            return None

        prompt = self._build_prompt(
            text,
            context,
        )

        for method_name in (
            "classify_intent",
            "classify",
            "analyze",
            "process",
            "ask",
            "generate",
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
                    text,
                    prompt,
                    context,
                )

                if result is not None:
                    return result

            except Exception as error:

                logger.debug(
                    f"AIService.{method_name} " f"intent classification failed: {error}"
                )

        return None

    # ============================================================
    # AI CALLING
    # ============================================================

    @staticmethod
    def _call_ai_method(
        method: Any,
        text: str,
        prompt: str,
        context: Dict[str, Any],
    ) -> Any:

        attempts = (
            lambda: method(
                text,
                context=context,
            ),
            lambda: method(
                prompt,
                context=context,
            ),
            lambda: method(text),
            lambda: method(prompt),
        )

        last_error = None

        for attempt in attempts:

            try:

                result = attempt()

                if inspect.isawaitable(result):
                    raise RuntimeError(
                        "IntentClassifier received an async "
                        "AI result. Use the async execution path."
                    )

                return result

            except TypeError as error:

                last_error = error

        if last_error is not None:
            raise last_error

        return None

    # ============================================================
    # RESULT NORMALIZATION
    # ============================================================

    @staticmethod
    def _normalize_ai_result(
        result: Any,
        text: str,
    ) -> Dict[str, Any]:

        if isinstance(result, dict):

            intent = (
                result.get("intent")
                or result.get("type")
                or result.get("category")
                or "conversation"
            )

            confidence = result.get(
                "confidence",
                0.7,
            )

            normalized = dict(result)

            normalized.update(
                {
                    "success": True,
                    "intent": str(intent),
                    "confidence": confidence,
                    "source": "ai",
                    "text": text,
                }
            )

            return normalized

        if isinstance(result, str):

            return {
                "success": True,
                "intent": result.strip() or "conversation",
                "confidence": 0.7,
                "source": "ai",
                "text": text,
            }

        return {
            "success": True,
            "intent": "conversation",
            "confidence": 0.4,
            "source": "ai_fallback",
            "text": text,
            "raw_result": result,
        }

    # ============================================================
    # PROMPT
    # ============================================================

    @staticmethod
    def _build_prompt(
        text: str,
        context: Dict[str, Any],
    ) -> str:

        return (
            "Classify the user's request into the most appropriate "
            "Omnix intent. Consider categories such as: "
            "open, close, search, file, automation, vision, "
            "conversation, or another clear intent.\n\n"
            f"User request: {text}\n\n"
            f"Context: {context}"
        )

    # ============================================================
    # TEXT CLEANING
    # ============================================================

    @staticmethod
    def _clean_text(
        text: str,
    ) -> str:

        text = text.lower().strip()

        text = re.sub(
            r"\b(?:hey\s+)?omnix\b",
            "",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # ============================================================
    # STATUS
    # ============================================================

    def status(self) -> Dict[str, Any]:

        return {
            "available": True,
            "ai_service": (
                type(self.ai_service).__name__ if self.ai_service is not None else None
            ),
            "context_service": (
                type(self.context_service).__name__
                if self.context_service is not None
                else None
            ),
        }

    def health_check(self) -> bool:
        return True
