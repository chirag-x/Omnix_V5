from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from loguru import logger

# ==========================================================
# Verification Status
# ==========================================================


class VerificationStatus(str, Enum):

    SUCCESS = "success"

    FAILED = "failed"

    PARTIAL = "partial"

    UNKNOWN = "unknown"


# ==========================================================
# Verification Result
# ==========================================================


@dataclass(slots=True)
class VerificationResult:

    status: VerificationStatus

    confidence: float

    reason: str

    retry: bool = False

    expected: dict[str, Any] = field(default_factory=dict)

    evidence: dict[str, Any] = field(default_factory=dict)

    metadata: dict[str, Any] = field(default_factory=dict)


# ==========================================================
# Step Verifier
# ==========================================================


class StepVerifier:
    """
    Omnix V5 Step Verifier

    Responsible for verifying whether an individual
    execution step actually achieved its expected result.

    Verification sources:

    • SkillResult
    • Vision
    • UI Automation
    • OCR
    • ExecutionContext
    """

    def __init__(
        self,
        ui_controller=None,
        execution_context=None,
    ):

        self.ui_controller = ui_controller

        self.execution_context = execution_context

        # ---------------------------------------------
        # Skill-specific verifiers
        # ---------------------------------------------

        self.skill_handlers: dict[
            str,
            Callable,
        ] = {
            "open_app": self._verify_open_app,
            "close_app": self._verify_close_app,
            "click_ui": self._verify_click,
            "ui_control": self._verify_ui_control,
            "wait_for_ui": self._verify_wait,
            "type_text": self._verify_input,
            "press_key": self._verify_input,
            "hotkey": self._verify_input,
            "browser_action": self._verify_browser,
        }

    # ==========================================================
    # Public API
    # ==========================================================

    def verify(
        self,
        step: dict,
        result,
        before: dict | None = None,
        after: dict | None = None,
    ) -> VerificationResult:

        skill = step.get("skill", "")

        logger.info(f"[StepVerifier] Verifying {skill}")

        # ---------------------------------------------
        # Verify SkillResult first
        # ---------------------------------------------

        verification = self._verify_result(
            result,
        )

        if verification is not None:

            return verification

        expected = self._expected(step)

        if expected:

            verification = self._verify_expected(
                expected,
                after,
            )

            if verification.status is VerificationStatus.SUCCESS:

                return verification

        handler = self.skill_handlers.get(skill)

        if handler:

            return handler(
                step,
                before,
                after,
            )

        return VerificationResult(
            status=VerificationStatus.UNKNOWN,
            confidence=0.40,
            reason=f"No verifier registered for '{skill}'.",
        )

    # ==========================================================
    # Skill Result Verification
    # ==========================================================

    def _verify_result(
        self,
        result,
    ) -> VerificationResult | None:
        """
        Verify the returned SkillResult before performing
        vision/UI verification.
        """

        if result is None:

            return VerificationResult(
                status=VerificationStatus.FAILED,
                confidence=1.0,
                reason="Skill returned None.",
                retry=False,
            )

        # --------------------------------------------------
        # Legacy string results
        # --------------------------------------------------

        if isinstance(result, str):

            if result.lower() == "success":

                return VerificationResult(
                    status=VerificationStatus.SUCCESS,
                    confidence=0.75,
                    reason="Legacy success result.",
                )

            if result.lower() == "error":

                return VerificationResult(
                    status=VerificationStatus.FAILED,
                    confidence=1.0,
                    reason="Legacy error result.",
                    retry=True,
                )

            return None

        # --------------------------------------------------
        # V5 SkillResult
        # --------------------------------------------------

        success = getattr(result, "success", None)

        if success is True:

            return None

        if success is False:

            return VerificationResult(
                status=VerificationStatus.FAILED,
                confidence=1.0,
                reason=getattr(
                    result,
                    "message",
                    "Skill execution failed.",
                ),
                retry=True,
                metadata={
                    "execution_time": getattr(
                        result,
                        "execution_time",
                        None,
                    )
                },
            )

        return None

    # ==========================================================
    # Expected Outcome Verification
    # ==========================================================

    def _verify_expected(
        self,
        expected: dict,
        observation: dict | None,
    ) -> VerificationResult:

        expected_type = expected.get("type")
        target = expected.get("target")

        logger.debug(f"[StepVerifier] Expected={expected_type}")

        handlers = {
            "app_active": self._verify_expected_app,
            "text_visible": self._verify_expected_text,
            "element_visible": self._verify_expected_text,
            "ui_changed": self._verify_expected_ui,
            "toggle_state": self._verify_expected_toggle,
        }

        handler = handlers.get(expected_type)

        if handler is None:

            return VerificationResult(
                status=VerificationStatus.UNKNOWN,
                confidence=0.30,
                reason=f"Unknown expected type '{expected_type}'.",
                expected=expected,
            )

        return handler(
            target,
            expected,
            observation,
        )

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
    # Evidence
    # ==========================================================

    def _evidence(
        self,
        observation: dict | None,
    ) -> dict:

        if not observation:

            return {}

        return {
            "active_app": observation.get("active_app"),
            "active_window": observation.get("active_window"),
            "changed": observation.get("changed"),
            "screen_summary": observation.get("screen_summary"),
            "ocr_available": bool(observation.get("ocr_text")),
            "ui_count": len(
                observation.get(
                    "ui_elements",
                    [],
                )
            ),
        }

    # ==========================================================
    # Skill Handlers
    # ==========================================================

    def _verify_open_app(
        self,
        step: dict,
        before: dict | None,
        after: dict | None,
    ) -> VerificationResult:

        app = str(step.get("parameters", {}).get("app", "")).lower().replace(".exe", "")

        active_app = (
            str((after or {}).get("active_app", "")).lower().replace(".exe", "")
        )

        active_window = str((after or {}).get("active_window", "")).lower()

        matched = active_app == app or app in active_window

        return VerificationResult(
            status=(
                VerificationStatus.SUCCESS if matched else VerificationStatus.PARTIAL
            ),
            confidence=self._confidence(
                matched,
                2,
            ),
            reason=(
                "Application is active."
                if matched
                else "Application launch not confirmed."
            ),
            retry=not matched,
            evidence=self._evidence(after),
        )

    def _verify_close_app(
        self,
        step,
        before,
        after,
    ) -> VerificationResult:

        app = str(step.get("parameters", {}).get("app", "")).lower().replace(".exe", "")

        active_app = (
            str((after or {}).get("active_app", "")).lower().replace(".exe", "")
        )

        matched = active_app != app

        return VerificationResult(
            status=(
                VerificationStatus.SUCCESS if matched else VerificationStatus.PARTIAL
            ),
            confidence=self._confidence(
                matched,
                2,
            ),
            reason=(
                "Application closed."
                if matched
                else "Application still appears active."
            ),
            retry=not matched,
            evidence=self._evidence(after),
        )

    def _verify_click(
        self,
        step,
        before,
        after,
    ) -> VerificationResult:

        changed = bool((after or {}).get("changed"))

        return VerificationResult(
            status=(
                VerificationStatus.SUCCESS if changed else VerificationStatus.PARTIAL
            ),
            confidence=self._confidence(
                changed,
                1,
            ),
            reason=(
                "UI changed after click."
                if changed
                else "Click completed but no visible change detected."
            ),
            retry=not changed,
            evidence=self._evidence(after),
        )

    def _verify_ui_control(
        self,
        step,
        before,
        after,
    ) -> VerificationResult:

        changed = bool((after or {}).get("changed"))

        return VerificationResult(
            status=(
                VerificationStatus.SUCCESS if changed else VerificationStatus.PARTIAL
            ),
            confidence=self._confidence(
                changed,
                2,
            ),
            reason=(
                "UI control updated."
                if changed
                else "UI update could not be confirmed."
            ),
            retry=not changed,
            evidence=self._evidence(after),
        )

    def _verify_wait(
        self,
        step,
        before,
        after,
    ) -> VerificationResult:

        return VerificationResult(
            status=VerificationStatus.SUCCESS,
            confidence=1.0,
            reason="Wait completed.",
            retry=False,
            evidence=self._evidence(after),
        )

    def _verify_input(
        self,
        step,
        before,
        after,
    ) -> VerificationResult:

        changed = bool((after or {}).get("changed"))

        return VerificationResult(
            status=(
                VerificationStatus.SUCCESS if changed else VerificationStatus.PARTIAL
            ),
            confidence=self._confidence(
                changed,
                1,
            ),
            reason=(
                "Input affected the UI."
                if changed
                else "Input executed but no observable UI change."
            ),
            retry=not changed,
            evidence=self._evidence(after),
        )

    def _verify_browser(
        self,
        step,
        before,
        after,
    ) -> VerificationResult:

        changed = bool((after or {}).get("changed"))

        active_window = str((after or {}).get("active_window", "")).lower()

        browser_detected = any(
            browser in active_window
            for browser in (
                "chrome",
                "edge",
                "firefox",
                "brave",
                "opera",
            )
        )

        matched = changed or browser_detected

        return VerificationResult(
            status=(
                VerificationStatus.SUCCESS if matched else VerificationStatus.PARTIAL
            ),
            confidence=self._confidence(
                matched,
                2,
            ),
            reason=(
                "Browser action verified."
                if matched
                else "Browser action could not be confirmed."
            ),
            retry=not matched,
            evidence=self._evidence(after),
        )

    # ==========================================================
    # Expected Outcome Handlers
    # ==========================================================

    def _verify_expected_app(
        self,
        target,
        expected,
        observation,
    ) -> VerificationResult:

        app = str(expected.get("app") or target or "").lower().replace(".exe", "")

        active_app = (
            str(
                (observation or {}).get(
                    "active_app",
                    "",
                )
            )
            .lower()
            .replace(".exe", "")
        )

        matched = active_app == app

        return VerificationResult(
            status=(
                VerificationStatus.SUCCESS if matched else VerificationStatus.PARTIAL
            ),
            confidence=self._confidence(
                matched,
                2,
            ),
            reason=(
                "Expected application is active."
                if matched
                else "Expected application not active."
            ),
            retry=not matched,
            evidence=self._evidence(observation),
        )

    def _verify_expected_text(
        self,
        target,
        expected,
        observation,
    ) -> VerificationResult:

        visible = self._text_present(
            target,
            observation,
        )

        return VerificationResult(
            status=(
                VerificationStatus.SUCCESS if visible else VerificationStatus.PARTIAL
            ),
            confidence=self._confidence(
                visible,
                2,
            ),
            reason=(
                "Expected text is visible." if visible else "Expected text not visible."
            ),
            retry=not visible,
            evidence=self._evidence(observation),
        )

    def _verify_expected_ui(
        self,
        target,
        expected,
        observation,
    ) -> VerificationResult:

        changed = bool((observation or {}).get("changed"))

        return VerificationResult(
            status=(
                VerificationStatus.SUCCESS if changed else VerificationStatus.PARTIAL
            ),
            confidence=self._confidence(
                changed,
                2,
            ),
            reason=("UI updated." if changed else "UI change not detected."),
            retry=not changed,
            evidence=self._evidence(observation),
        )

    def _verify_expected_toggle(
        self,
        target,
        expected,
        observation,
    ) -> VerificationResult:

        if self.ui_controller is None:

            return VerificationResult(
                status=VerificationStatus.UNKNOWN,
                confidence=0.0,
                reason="UI controller unavailable.",
            )

        control = self.ui_controller.find_control(
            target=target,
        )

        if control is None:

            return VerificationResult(
                status=VerificationStatus.PARTIAL,
                confidence=0.30,
                reason="Toggle control not found.",
                retry=True,
            )

        current = self.ui_controller.get_toggle_state(
            control,
        )

        desired = self._normalize_bool(expected.get("state"))

        matched = current is desired

        return VerificationResult(
            status=(
                VerificationStatus.SUCCESS if matched else VerificationStatus.FAILED
            ),
            confidence=self._confidence(
                matched,
                3,
            ),
            reason=("Toggle state verified." if matched else "Toggle state mismatch."),
            retry=not matched,
            evidence={
                "current": current,
                "desired": desired,
            },
        )

    # ==========================================================
    # Utilities
    # ==========================================================

    def _expected(
        self,
        step: dict,
    ) -> dict:

        expected = step.get("expected")

        if isinstance(expected, dict):
            return expected

        params = (
            step.get(
                "parameters",
                {},
            )
            or {}
        )

        expected = params.get("expected")

        return expected if isinstance(expected, dict) else {}

    def _text_present(
        self,
        target,
        observation,
    ) -> bool:

        target = str(target or "").lower().strip()

        if not target:
            return False

        summary = str(
            (observation or {}).get(
                "screen_summary",
                "",
            )
        ).lower()

        if target in summary:
            return True

        ocr = str(
            (observation or {}).get(
                "ocr_text",
                "",
            )
        ).lower()

        if target in ocr:
            return True

        for element in (observation or {}).get(
            "ui_elements",
            [],
        ):

            text = str(element.get("text") or "").lower()

            if target in text:
                return True

        return False

    def _normalize_bool(
        self,
        value,
    ) -> bool:

        if isinstance(
            value,
            bool,
        ):
            return value

        return str(value).lower() in {
            "true",
            "1",
            "on",
            "checked",
            "enabled",
            "yes",
        }
