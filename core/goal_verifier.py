from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from loguru import logger

# ==========================================================
# Goal Verification Status
# ==========================================================


class GoalStatus(str, Enum):

    SUCCESS = "success"

    FAILED = "failed"

    PARTIAL = "partial"

    UNKNOWN = "unknown"


# ==========================================================
# Goal Verification Result
# ==========================================================


@dataclass(slots=True)
class GoalVerificationResult:

    status: GoalStatus

    confidence: float

    reason: str

    retry: bool = False

    evidence: dict[str, Any] = field(default_factory=dict)

    metadata: dict[str, Any] = field(default_factory=dict)


# ==========================================================
# Goal Verifier
# ==========================================================


class GoalVerifier:
    """
    Omnix V5 Goal Verifier

    Responsible for verifying whether the user's
    overall goal has been achieved.

    Unlike StepVerifier, this class evaluates
    the COMPLETE outcome of a workflow.
    """

    def __init__(
        self,
        ui_controller=None,
        execution_context=None,
    ):

        self.ui_controller = ui_controller

        self.execution_context = execution_context

        # --------------------------------------------------
        # Goal Handler Registry
        # --------------------------------------------------

        self.goal_handlers: dict[
            str,
            Callable,
        ] = {
            "application": self._verify_application_goal,
            "browser": self._verify_browser_goal,
            "system": self._verify_system_goal,
            "file": self._verify_file_goal,
            "ui": self._verify_ui_goal,
            "media": self._verify_media_goal,
            "text": self._verify_text_goal,
        }

    # ==========================================================
    # Public API
    # ==========================================================

    def verify(
        self,
        goal,
        observation=None,
    ) -> GoalVerificationResult:

        goal = str(goal or "").strip()

        if not goal:

            return GoalVerificationResult(
                status=GoalStatus.UNKNOWN,
                confidence=0.0,
                reason="Goal is empty.",
            )

        logger.info(f"[GoalVerifier] Verifying goal: {goal}")

        goal_type = self._classify_goal(goal)

        handler = self.goal_handlers.get(goal_type)

        if handler is None:

            return GoalVerificationResult(
                status=GoalStatus.UNKNOWN,
                confidence=0.30,
                reason=f"No verifier for goal type '{goal_type}'.",
            )

        return handler(
            goal,
            observation,
        )

    # ==========================================================
    # Goal Classification
    # ==========================================================

    def _classify_goal(
        self,
        goal: str,
    ) -> str:

        goal = goal.lower()

        application_keywords = {
            "open",
            "launch",
            "start",
            "close",
            "quit",
            "exit",
            "run",
        }

        browser_keywords = {
            "search",
            "browse",
            "google",
            "website",
            "url",
            "tab",
            "page",
        }

        system_keywords = {
            "shutdown",
            "restart",
            "sleep",
            "lock",
            "bluetooth",
            "wifi",
            "volume",
            "brightness",
        }

        file_keywords = {
            "file",
            "folder",
            "document",
            "copy",
            "move",
            "delete",
            "rename",
            "save",
        }

        ui_keywords = {
            "click",
            "button",
            "window",
            "menu",
            "dialog",
            "checkbox",
        }

        media_keywords = {
            "music",
            "video",
            "spotify",
            "pause",
            "play",
            "resume",
            "next",
        }

        words = set(goal.split())

        if words & application_keywords:
            return "application"

        if words & browser_keywords:
            return "browser"

        if words & system_keywords:
            return "system"

        if words & file_keywords:
            return "file"

        if words & ui_keywords:
            return "ui"

        if words & media_keywords:
            return "media"

        return "text"

    # ==========================================================
    # Confidence
    # ==========================================================

    def _confidence(
        self,
        matched: bool,
        evidence_count: int = 1,
    ) -> float:

        if not matched:

            return 0.30

        confidence = 0.70

        confidence += evidence_count * 0.05

        return min(
            confidence,
            1.0,
        )

    # ==========================================================
    # Evidence Collection
    # ==========================================================

    def _evidence(
        self,
        observation,
    ) -> dict:

        if not observation:
            return {}

        return {
            "active_app": observation.get("active_app"),
            "active_window": observation.get("active_window"),
            "changed": observation.get("changed"),
            "screen_summary": observation.get("screen_summary"),
            "ocr": bool(observation.get("ocr_text")),
            "ui_elements": len(
                observation.get(
                    "ui_elements",
                    [],
                )
            ),
        }

    # ==========================================================
    # Execution Context
    # ==========================================================

    def _context_data(
        self,
    ) -> dict:

        if self.execution_context is None:
            return {}

        return {
            "goal": getattr(
                self.execution_context,
                "current_goal",
                None,
            ),
            "step": getattr(
                self.execution_context,
                "current_step",
                None,
            ),
            "attempt": getattr(
                self.execution_context,
                "attempt",
                None,
            ),
        }

    # ==========================================================
    # Visible Text
    # ==========================================================

    def _visible_text(
        self,
        observation,
    ) -> str:

        if not observation:
            return ""

        parts = []

        summary = str(
            observation.get(
                "screen_summary",
                "",
            )
        )

        if summary:
            parts.append(summary)

        ocr = str(
            observation.get(
                "ocr_text",
                "",
            )
        )

        if ocr:
            parts.append(ocr)

        seen = set()

        for element in observation.get(
            "ui_elements",
            [],
        ):

            text = str(element.get("text") or "").strip()

            if text and text not in seen:

                seen.add(text)

                parts.append(text)

        return "\n".join(parts).lower()

    # ==========================================================
    # Goal Handlers
    # ==========================================================

    def _verify_application_goal(
        self,
        goal: str,
        observation,
    ) -> GoalVerificationResult:

        active_app = str(
            (observation or {}).get(
                "active_app",
                "",
            )
        ).lower()

        active_window = str(
            (observation or {}).get(
                "active_window",
                "",
            )
        ).lower()

        ctx_app = ""
        ctx_browser = ""

        if self.execution_context:

            ctx_app = (
                getattr(
                    self.execution_context,
                    "current_app",
                    "",
                )
                or ""
            ).lower()

            ctx_browser = (
                getattr(
                    self.execution_context,
                    "current_browser",
                    "",
                )
                or ""
            ).lower()

        matched = False

        for word in goal.lower().split():

            if len(word) < 3:
                continue

            if (
                word in active_app
                or word in active_window
                or word in ctx_app
                or word in ctx_browser
            ):
                matched = True
                break

        logger.info(
            f"[GoalVerifier] "
            f"active_app={active_app} | "
            f"active_window={active_window} | "
            f"context_app={ctx_app} | "
            f"context_browser={ctx_browser}"
        )

        return GoalVerificationResult(
            status=(GoalStatus.SUCCESS if matched else GoalStatus.PARTIAL),
            confidence=self._confidence(
                matched,
                2,
            ),
            reason=(
                "Application goal verified."
                if matched
                else "Application goal not confirmed."
            ),
            retry=not matched,
            evidence=self._evidence(
                observation,
            ),
            metadata=self._context_data(),
        )

    # ==========================================================

    def _verify_browser_goal(
        self,
        goal: str,
        observation,
    ) -> GoalVerificationResult:

        visible = self._visible_text(
            observation,
        )

        matched = False

        for word in goal.lower().split():

            if len(word) < 3:
                continue

            if word in visible:

                matched = True
                break

        return GoalVerificationResult(
            status=(GoalStatus.SUCCESS if matched else GoalStatus.PARTIAL),
            confidence=self._confidence(
                matched,
                2,
            ),
            reason=(
                "Browser goal verified." if matched else "Browser result not visible."
            ),
            retry=not matched,
            evidence=self._evidence(
                observation,
            ),
            metadata=self._context_data(),
        )

    # ==========================================================

    def _verify_system_goal(
        self,
        goal: str,
        observation,
    ) -> GoalVerificationResult:

        changed = bool((observation or {}).get("changed"))

        return GoalVerificationResult(
            status=(GoalStatus.SUCCESS if changed else GoalStatus.PARTIAL),
            confidence=self._confidence(
                changed,
                2,
            ),
            reason=(
                "System state updated." if changed else "System state not confirmed."
            ),
            retry=not changed,
            evidence=self._evidence(
                observation,
            ),
            metadata=self._context_data(),
        )

    # ==========================================================

    def _verify_file_goal(
        self,
        goal: str,
        observation,
    ) -> GoalVerificationResult:

        visible = self._visible_text(
            observation,
        )

        matched = any(word in visible for word in goal.lower().split() if len(word) > 2)

        return GoalVerificationResult(
            status=(GoalStatus.SUCCESS if matched else GoalStatus.PARTIAL),
            confidence=self._confidence(
                matched,
                1,
            ),
            reason=(
                "File goal verified." if matched else "File operation not confirmed."
            ),
            retry=not matched,
            evidence=self._evidence(
                observation,
            ),
            metadata=self._context_data(),
        )

    # ==========================================================

    def _verify_ui_goal(
        self,
        goal: str,
        observation,
    ) -> GoalVerificationResult:

        changed = bool((observation or {}).get("changed"))

        return GoalVerificationResult(
            status=(GoalStatus.SUCCESS if changed else GoalStatus.PARTIAL),
            confidence=self._confidence(
                changed,
                2,
            ),
            reason=(
                "UI goal verified." if changed else "UI interaction not confirmed."
            ),
            retry=not changed,
            evidence=self._evidence(
                observation,
            ),
            metadata=self._context_data(),
        )

    # ==========================================================

    def _verify_media_goal(
        self,
        goal: str,
        observation,
    ) -> GoalVerificationResult:

        active_window = str(
            (observation or {}).get(
                "active_window",
                "",
            )
        ).lower()

        visible = self._visible_text(
            observation,
        )

        matched = (
            "spotify" in active_window
            or "youtube" in active_window
            or "playing" in visible
            or "pause" in visible
            or "now playing" in visible
        )

        return GoalVerificationResult(
            status=(GoalStatus.SUCCESS if matched else GoalStatus.PARTIAL),
            confidence=self._confidence(
                matched,
                2,
            ),
            reason=(
                "Media goal verified." if matched else "Media playback not confirmed."
            ),
            retry=not matched,
            evidence=self._evidence(
                observation,
            ),
            metadata=self._context_data(),
        )

    # ==========================================================

    def _verify_text_goal(
        self,
        goal: str,
        observation,
    ) -> GoalVerificationResult:

        visible = self._visible_text(
            observation,
        )

        matched = any(word in visible for word in goal.lower().split() if len(word) > 3)

        return GoalVerificationResult(
            status=(GoalStatus.SUCCESS if matched else GoalStatus.UNKNOWN),
            confidence=self._confidence(
                matched,
                1,
            ),
            reason=(
                "Goal text detected." if matched else "Unable to verify text goal."
            ),
            retry=False,
            evidence=self._evidence(
                observation,
            ),
            metadata=self._context_data(),
        )

    # ==========================================================
    # Recovery Strategy
    # ==========================================================

    def recovery_strategy(
        self,
        result: GoalVerificationResult,
    ) -> dict:
        """
        Recommend what the GoalExecutor should do next.
        """

        if result.status is GoalStatus.SUCCESS:

            return {
                "action": "continue",
                "reason": "Goal completed successfully.",
            }

        if result.status is GoalStatus.PARTIAL:

            if result.retry:

                return {
                    "action": "retry",
                    "reason": result.reason,
                }

            return {
                "action": "replan",
                "reason": result.reason,
            }

        if result.status is GoalStatus.FAILED:

            return {
                "action": "replan",
                "reason": result.reason,
            }

        return {
            "action": "ask_user",
            "reason": result.reason,
        }

    # ==========================================================
    # Summary
    # ==========================================================

    def summarize(
        self,
        result: GoalVerificationResult,
    ) -> dict:
        """
        Produce a normalized verification summary.
        """

        return {
            "status": result.status.value,
            "confidence": result.confidence,
            "reason": result.reason,
            "retry": result.retry,
            "evidence": result.evidence,
            "metadata": result.metadata,
            "next_action": self.recovery_strategy(result),
        }

    # ==========================================================
    # Factory Helpers
    # ==========================================================

    def _success(
        self,
        reason,
        confidence=1.0,
        evidence=None,
    ):

        return GoalVerificationResult(
            status=GoalStatus.SUCCESS,
            confidence=confidence,
            reason=reason,
            retry=False,
            evidence=evidence or {},
            metadata=self._context_data(),
        )

    def _partial(
        self,
        reason,
        confidence=0.60,
        retry=True,
        evidence=None,
    ):

        return GoalVerificationResult(
            status=GoalStatus.PARTIAL,
            confidence=confidence,
            reason=reason,
            retry=retry,
            evidence=evidence or {},
            metadata=self._context_data(),
        )

    def _failed(
        self,
        reason,
        confidence=1.0,
        evidence=None,
    ):

        return GoalVerificationResult(
            status=GoalStatus.FAILED,
            confidence=confidence,
            reason=reason,
            retry=False,
            evidence=evidence or {},
            metadata=self._context_data(),
        )

    def _unknown(
        self,
        reason,
    ):

        return GoalVerificationResult(
            status=GoalStatus.UNKNOWN,
            confidence=0.0,
            reason=reason,
            retry=False,
            metadata=self._context_data(),
        )
