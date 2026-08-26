"""
Omnix V5 - Step Verifier

Verifies whether an individual workflow step actually succeeded.

The StepVerifier combines multiple sources of information:

    - Executor result
    - ObservationLoop observations
    - Custom verification providers
    - Step-specific verification rules
    - Legacy verification components

This module does not execute workflow steps. It only evaluates the
evidence available after execution and returns a normalized verification
result.
"""

from __future__ import annotations

import inspect

from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple

# ============================================================================
# VERIFICATION STATUS
# ============================================================================


class VerificationStatus(str, Enum):
    """
    Possible verification outcomes.
    """

    VERIFIED = "verified"
    FAILED = "failed"
    UNCERTAIN = "uncertain"
    SKIPPED = "skipped"


# ============================================================================
# VERIFICATION RESULT
# ============================================================================


@dataclass
class StepVerificationResult:
    """
    Normalized result of a workflow step verification.
    """

    status: VerificationStatus

    success: bool

    step_id: Optional[str] = None

    reason: Optional[str] = None

    confidence: Optional[float] = None

    evidence: List[Any] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(
        self,
    ) -> None:

        if not isinstance(
            self.status,
            VerificationStatus,
        ):

            try:

                self.status = VerificationStatus(str(self.status).strip().lower())

            except (
                TypeError,
                ValueError,
            ):

                self.status = VerificationStatus.UNCERTAIN

        self.success = bool(self.success)

        if self.step_id is not None:

            self.step_id = str(self.step_id).strip() or None

        if self.reason is not None:

            self.reason = str(self.reason).strip() or None

        if self.confidence is not None:

            try:

                self.confidence = float(self.confidence)

            except (
                TypeError,
                ValueError,
            ):

                self.confidence = None

            if self.confidence is not None:

                self.confidence = max(
                    0.0,
                    min(
                        1.0,
                        self.confidence,
                    ),
                )

        self.evidence = list(self.evidence or [])

        if not isinstance(
            self.metadata,
            dict,
        ):

            self.metadata = {"value": self.metadata}

        self.metadata = dict(self.metadata)

    @property
    def verified(
        self,
    ) -> bool:
        """
        Return True only when the step is verified.
        """

        return self.status == VerificationStatus.VERIFIED

    @property
    def failed(
        self,
    ) -> bool:
        """
        Return True when verification failed.
        """

        return self.status == VerificationStatus.FAILED

    @property
    def uncertain(
        self,
    ) -> bool:
        """
        Return True when the available evidence is insufficient.
        """

        return self.status == VerificationStatus.UNCERTAIN

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return {
            "status": self.status.value,
            "success": self.success,
            "step_id": self.step_id,
            "reason": self.reason,
            "confidence": self.confidence,
            "evidence": list(self.evidence),
            "metadata": dict(self.metadata),
        }


# ============================================================================
# STEP VERIFIER
# ============================================================================


class StepVerifier:
    """
    Verifies individual workflow steps.

    Verification order:

        1. Explicit verification rules on the step
        2. Registered verification providers
        3. Execution result analysis
        4. Observation analysis
        5. Evidence aggregation

    Registered verifiers may expose:

        verify()
        evaluate()
        check()

    Or they may simply be callable.
    """

    def __init__(
        self,
        *,
        require_observation: bool = False,
        minimum_confidence: float = 0.5,
    ) -> None:

        self.require_observation = bool(require_observation)

        self.minimum_confidence = self._normalize_confidence(
            minimum_confidence,
            default=0.5,
        )

        self._verifiers: Dict[str, Any] = {}

        self._lock = RLock()

        self._verification_count = 0

    # ====================================================================
    # VERIFIER MANAGEMENT
    # ====================================================================

    def register_verifier(
        self,
        name: str,
        verifier: Any,
        *,
        replace: bool = False,
    ) -> None:
        """
        Register a custom step verification provider.
        """

        normalized_name = self._normalize_name(name)

        if verifier is None:

            raise ValueError("Verifier cannot be None.")

        with self._lock:

            if normalized_name in self._verifiers and not replace:

                raise ValueError(f"Verifier already exists: " f"{normalized_name}")

            self._verifiers[normalized_name] = verifier

    def unregister_verifier(
        self,
        name: str,
    ) -> bool:
        """
        Remove a verifier.
        """

        normalized_name = self._normalize_name(name)

        with self._lock:

            if normalized_name not in self._verifiers:

                return False

            del self._verifiers[normalized_name]

            return True

    def get_verifier(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Return a registered verifier.
        """

        normalized_name = self._normalize_name(name)

        with self._lock:

            return self._verifiers.get(
                normalized_name,
                default,
            )

    def get_verifier_names(
        self,
    ) -> List[str]:
        """
        Return all registered verifier names.
        """

        with self._lock:

            return list(self._verifiers.keys())

    def clear_verifiers(
        self,
    ) -> None:
        """
        Remove all registered verifiers.
        """

        with self._lock:

            self._verifiers.clear()

    # ====================================================================
    # MAIN VERIFICATION
    # ====================================================================

    def verify(
        self,
        step: Any,
        execution_result: Any = None,
        observations: Any = None,
        *,
        context: Optional[Dict[str, Any]] = None,
        verifier: Optional[str] = None,
        **kwargs: Any,
    ) -> StepVerificationResult:
        """
        Verify whether a workflow step succeeded.

        Args:
            step:
                Workflow step or compatible legacy step.

            execution_result:
                Result returned by the executor or skill.

            observations:
                ObservationBatch, list, dict or custom observation data.

            context:
                Additional execution context.

            verifier:
                Optional specific verifier name.
        """

        step_id = self._extract_step_id(step)

        verification_context = dict(context or {})

        evidence: List[Any] = []

        # --------------------------------------------------------------
        # 1. Explicit step verification rule
        # --------------------------------------------------------------

        explicit_rule = self._extract_verification_rule(step)

        if explicit_rule is not None:

            result = self._evaluate_rule(
                explicit_rule,
                step=step,
                execution_result=execution_result,
                observations=observations,
                context=verification_context,
            )

            if result is not None:

                normalized = self._normalize_result(
                    result,
                    step_id=step_id,
                    source="step_rule",
                )

                normalized.evidence.extend(evidence)

                self._increment_count()

                return normalized

        # --------------------------------------------------------------
        # 2. Custom verification providers
        # --------------------------------------------------------------

        provider_results = self._run_verifiers(
            step=step,
            execution_result=execution_result,
            observations=observations,
            context=verification_context,
            verifier=verifier,
            **kwargs,
        )

        if provider_results:

            aggregated = self._aggregate_results(
                provider_results,
                step_id=step_id,
            )

            self._increment_count()

            return aggregated

        # --------------------------------------------------------------
        # 3. Analyze execution result
        # --------------------------------------------------------------

        execution_state = self._analyze_execution_result(execution_result)

        if execution_state is not None:

            evidence.append(
                {
                    "source": "execution_result",
                    "state": execution_state,
                    "value": execution_result,
                }
            )

        # --------------------------------------------------------------
        # 4. Analyze observations
        # --------------------------------------------------------------

        observation_state = self._analyze_observations(observations)

        if observation_state is not None:

            evidence.append(
                {
                    "source": "observations",
                    "state": observation_state,
                }
            )

        # --------------------------------------------------------------
        # 5. Final decision
        # --------------------------------------------------------------

        result = self._build_default_result(
            step_id=step_id,
            execution_state=execution_state,
            observation_state=observation_state,
            evidence=evidence,
        )

        self._increment_count()

        return result

    # ====================================================================
    # STEP RULES
    # ====================================================================

    @staticmethod
    def _extract_verification_rule(
        step: Any,
    ) -> Any:

        if isinstance(
            step,
            dict,
        ):

            for key in (
                "verification",
                "verify",
                "success_condition",
            ):

                if key in step:

                    return step[key]

            metadata = step.get("metadata")

            if isinstance(
                metadata,
                dict,
            ):

                return metadata.get("verification")

            return None

        for attribute in (
            "verification",
            "verify",
            "success_condition",
        ):

            if hasattr(
                step,
                attribute,
            ):

                try:

                    value = getattr(
                        step,
                        attribute,
                    )

                    if value is not None:

                        return value

                except Exception:

                    continue

        metadata = getattr(
            step,
            "metadata",
            None,
        )

        if isinstance(
            metadata,
            dict,
        ):

            return metadata.get("verification")

        return None

    @staticmethod
    def _evaluate_rule(
        rule: Any,
        *,
        step: Any,
        execution_result: Any,
        observations: Any,
        context: Dict[str, Any],
    ) -> Any:

        if callable(rule):

            return StepVerifier._invoke_callable(
                rule,
                step=step,
                execution_result=execution_result,
                observations=observations,
                context=context,
            )

        if isinstance(
            rule,
            bool,
        ):

            return rule

        if isinstance(
            rule,
            dict,
        ):

            return rule

        return None

    # ====================================================================
    # CUSTOM VERIFIERS
    # ====================================================================

    def _run_verifiers(
        self,
        *,
        step: Any,
        execution_result: Any,
        observations: Any,
        context: Dict[str, Any],
        verifier: Optional[str],
        **kwargs: Any,
    ) -> List[StepVerificationResult]:

        selected = self._select_verifiers(verifier)

        results: List[StepVerificationResult] = []

        step_id = self._extract_step_id(step)

        for name, provider in selected:

            try:

                raw_result = self._call_verifier(
                    provider,
                    step=step,
                    execution_result=execution_result,
                    observations=observations,
                    context=context,
                    **kwargs,
                )

                if inspect.isawaitable(raw_result):

                    raise RuntimeError(
                        "Async verifiers are not "
                        "supported by the synchronous "
                        "StepVerifier."
                    )

                normalized = self._normalize_result(
                    raw_result,
                    step_id=step_id,
                    source=name,
                )

            except Exception as error:

                normalized = StepVerificationResult(
                    status=(VerificationStatus.UNCERTAIN),
                    success=False,
                    step_id=step_id,
                    reason=str(error),
                    metadata={
                        "source": name,
                        "verifier_error": True,
                    },
                )

            results.append(normalized)

        return results

    @staticmethod
    def _call_verifier(
        verifier: Any,
        *,
        step: Any,
        execution_result: Any,
        observations: Any,
        context: Dict[str, Any],
        **kwargs: Any,
    ) -> Any:

        for method_name in (
            "verify",
            "evaluate",
            "check",
        ):

            method = getattr(
                verifier,
                method_name,
                None,
            )

            if callable(method):

                return StepVerifier._invoke_callable(
                    method,
                    step=step,
                    execution_result=(execution_result),
                    observations=observations,
                    context=context,
                    **kwargs,
                )

        if callable(verifier):

            return StepVerifier._invoke_callable(
                verifier,
                step=step,
                execution_result=(execution_result),
                observations=observations,
                context=context,
                **kwargs,
            )

        raise AttributeError(
            "Verifier does not expose a " "supported verification method."
        )

    @staticmethod
    def _invoke_callable(
        function: Any,
        **available_kwargs: Any,
    ) -> Any:

        try:

            signature = inspect.signature(function)

            parameters = signature.parameters

            accepts_kwargs = any(
                parameter.kind == parameter.VAR_KEYWORD
                for parameter in parameters.values()
            )

            if accepts_kwargs:

                return function(**available_kwargs)

            filtered = {
                name: value
                for name, value in available_kwargs.items()
                if name in parameters
            }

            return function(**filtered)

        except (
            TypeError,
            ValueError,
        ):

            return function(**available_kwargs)

    # ====================================================================
    # RESULT ANALYSIS
    # ====================================================================

    @staticmethod
    def _analyze_execution_result(
        result: Any,
    ) -> Optional[bool]:

        if result is None:

            return None

        if isinstance(
            result,
            bool,
        ):

            return result

        if isinstance(
            result,
            dict,
        ):

            for key in (
                "success",
                "ok",
                "completed",
            ):

                if key in result:

                    return bool(result[key])

            status = result.get("status")

            if status is not None:

                normalized = str(status).strip().lower()

                if normalized in (
                    "success",
                    "completed",
                    "verified",
                    "done",
                ):

                    return True

                if normalized in (
                    "failed",
                    "error",
                    "cancelled",
                ):

                    return False

            return None

        for attribute in (
            "success",
            "ok",
            "completed",
        ):

            if hasattr(
                result,
                attribute,
            ):

                try:

                    value = getattr(
                        result,
                        attribute,
                    )

                    if value is not None:

                        return bool(value)

                except Exception:

                    continue

        return None

    @staticmethod
    def _analyze_observations(
        observations: Any,
    ) -> Optional[bool]:

        if observations is None:

            return None

        if isinstance(
            observations,
            bool,
        ):

            return observations

        if isinstance(
            observations,
            dict,
        ):

            if "success" in observations:

                return bool(observations["success"])

            return None

        observation_list = getattr(
            observations,
            "observations",
            observations,
        )

        if not isinstance(
            observation_list,
            (list, tuple),
        ):

            return None

        if not observation_list:

            return None

        states: List[bool] = []

        for observation in observation_list:

            if isinstance(
                observation,
                dict,
            ):

                if "success" in observation:

                    states.append(bool(observation["success"]))

            elif hasattr(
                observation,
                "success",
            ):

                try:

                    states.append(bool(observation.success))

                except Exception:

                    continue

            elif isinstance(
                observation,
                bool,
            ):

                states.append(observation)

        if not states:

            return None

        if any(state is False for state in states):

            return False

        if all(state is True for state in states):

            return True

        return None

    # ====================================================================
    # DEFAULT DECISION
    # ====================================================================

    def _build_default_result(
        self,
        *,
        step_id: Optional[str],
        execution_state: Optional[bool],
        observation_state: Optional[bool],
        evidence: List[Any],
    ) -> StepVerificationResult:

        if execution_state is False or observation_state is False:

            return StepVerificationResult(
                status=(VerificationStatus.FAILED),
                success=False,
                step_id=step_id,
                reason=("Execution or observation " "indicates failure."),
                confidence=1.0,
                evidence=evidence,
            )

        if execution_state is True and observation_state is True:

            return StepVerificationResult(
                status=(VerificationStatus.VERIFIED),
                success=True,
                step_id=step_id,
                reason=("Execution and observation " "both indicate success."),
                confidence=1.0,
                evidence=evidence,
            )

        if execution_state is True and observation_state is None:

            if self.require_observation:

                return StepVerificationResult(
                    status=(VerificationStatus.UNCERTAIN),
                    success=False,
                    step_id=step_id,
                    reason=("Execution succeeded but " "no observation was available."),
                    confidence=0.5,
                    evidence=evidence,
                )

            return StepVerificationResult(
                status=(VerificationStatus.VERIFIED),
                success=True,
                step_id=step_id,
                reason=("Execution result indicates " "success."),
                confidence=0.75,
                evidence=evidence,
            )

        if observation_state is True and execution_state is None:

            return StepVerificationResult(
                status=(VerificationStatus.VERIFIED),
                success=True,
                step_id=step_id,
                reason=("Observation indicates " "successful completion."),
                confidence=0.75,
                evidence=evidence,
            )

        return StepVerificationResult(
            status=(VerificationStatus.UNCERTAIN),
            success=False,
            step_id=step_id,
            reason=("Insufficient evidence to verify " "workflow step completion."),
            confidence=0.0,
            evidence=evidence,
        )

    # ====================================================================
    # PROVIDER RESULT NORMALIZATION
    # ====================================================================

    @staticmethod
    def _normalize_result(
        result: Any,
        *,
        step_id: Optional[str],
        source: str,
    ) -> StepVerificationResult:

        if isinstance(
            result,
            StepVerificationResult,
        ):

            if result.step_id is None:

                result.step_id = step_id

            result.metadata.setdefault(
                "source",
                source,
            )

            return result

        if isinstance(
            result,
            bool,
        ):

            return StepVerificationResult(
                status=(
                    VerificationStatus.VERIFIED if result else VerificationStatus.FAILED
                ),
                success=result,
                step_id=step_id,
                confidence=1.0,
                metadata={
                    "source": source,
                },
            )

        if isinstance(
            result,
            dict,
        ):

            status_value = result.get("status")

            success_value = result.get(
                "success",
                result.get("ok"),
            )

            if status_value is not None:

                try:

                    status = VerificationStatus(str(status_value).strip().lower())

                except ValueError:

                    status = VerificationStatus.UNCERTAIN

            elif success_value is True:

                status = VerificationStatus.VERIFIED

            elif success_value is False:

                status = VerificationStatus.FAILED

            else:

                status = VerificationStatus.UNCERTAIN

            success = status == VerificationStatus.VERIFIED

            metadata = result.get(
                "metadata",
                {},
            )

            if not isinstance(
                metadata,
                dict,
            ):

                metadata = {}

            metadata = dict(metadata)

            metadata.setdefault(
                "source",
                source,
            )

            return StepVerificationResult(
                status=status,
                success=success,
                step_id=result.get(
                    "step_id",
                    step_id,
                ),
                reason=result.get(
                    "reason",
                    result.get("error"),
                ),
                confidence=result.get("confidence"),
                evidence=list(
                    result.get(
                        "evidence",
                        [],
                    )
                    or []
                ),
                metadata=metadata,
            )

        return StepVerificationResult(
            status=(VerificationStatus.UNCERTAIN),
            success=False,
            step_id=step_id,
            reason=("Verifier returned an " "unsupported result."),
            metadata={
                "source": source,
                "raw_result": result,
            },
        )

    # ====================================================================
    # RESULT AGGREGATION
    # ====================================================================

    def _aggregate_results(
        self,
        results: List[StepVerificationResult],
        *,
        step_id: Optional[str],
    ) -> StepVerificationResult:

        verified = [result for result in results if result.verified]

        failed = [result for result in results if result.failed]

        uncertain = [result for result in results if result.uncertain]

        evidence: List[Any] = []

        for result in results:

            evidence.extend(result.evidence)

            evidence.append(
                {
                    "source": (result.metadata.get("source")),
                    "status": (result.status.value),
                    "reason": (result.reason),
                }
            )

        if failed:

            confidence = max(
                (result.confidence or 0.0 for result in failed),
                default=1.0,
            )

            return StepVerificationResult(
                status=(VerificationStatus.FAILED),
                success=False,
                step_id=step_id,
                reason=("At least one verifier " "reported failure."),
                confidence=confidence,
                evidence=evidence,
                metadata={
                    "verified_count": len(verified),
                    "failed_count": len(failed),
                    "uncertain_count": len(uncertain),
                },
            )

        if verified:

            confidence = max(
                (result.confidence or 0.0 for result in verified),
                default=0.75,
            )

            if confidence < self.minimum_confidence:

                return StepVerificationResult(
                    status=(VerificationStatus.UNCERTAIN),
                    success=False,
                    step_id=step_id,
                    reason=(
                        "Verification confidence " "is below the required " "threshold."
                    ),
                    confidence=confidence,
                    evidence=evidence,
                )

            return StepVerificationResult(
                status=(VerificationStatus.VERIFIED),
                success=True,
                step_id=step_id,
                reason=("Step verified successfully."),
                confidence=confidence,
                evidence=evidence,
                metadata={
                    "verified_count": len(verified),
                    "failed_count": 0,
                    "uncertain_count": len(uncertain),
                },
            )

        return StepVerificationResult(
            status=(VerificationStatus.UNCERTAIN),
            success=False,
            step_id=step_id,
            reason=("No verifier could confirm " "step completion."),
            confidence=0.0,
            evidence=evidence,
            metadata={
                "uncertain_count": len(uncertain),
            },
        )

    # ====================================================================
    # VERIFIER SELECTION
    # ====================================================================

    def _select_verifiers(
        self,
        verifier: Optional[str],
    ) -> List[Tuple[str, Any]]:

        with self._lock:

            if verifier is not None:

                normalized_name = self._normalize_name(verifier)

                provider = self._verifiers.get(normalized_name)

                if provider is None:

                    return []

                return [
                    (
                        normalized_name,
                        provider,
                    )
                ]

            return list(self._verifiers.items())

    # ====================================================================
    # UTILITIES
    # ====================================================================

    @staticmethod
    def _extract_step_id(
        step: Any,
    ) -> Optional[str]:

        if isinstance(
            step,
            dict,
        ):

            value = step.get("id") or step.get("step_id") or step.get("task_id")

        else:

            value = (
                getattr(
                    step,
                    "id",
                    None,
                )
                or getattr(
                    step,
                    "step_id",
                    None,
                )
                or getattr(
                    step,
                    "task_id",
                    None,
                )
            )

        if value is None:

            return None

        return str(value).strip() or None

    def _increment_count(
        self,
    ) -> None:

        with self._lock:

            self._verification_count += 1

    @staticmethod
    def _normalize_confidence(
        value: Any,
        *,
        default: float,
    ) -> float:

        try:

            confidence = float(value)

        except (
            TypeError,
            ValueError,
        ):

            confidence = default

        return max(
            0.0,
            min(
                1.0,
                confidence,
            ),
        )

    @staticmethod
    def _normalize_name(
        name: str,
    ) -> str:

        normalized = str(name).strip().lower()

        if not normalized:

            raise ValueError("Verifier name cannot be empty.")

        return normalized

    # ====================================================================
    # STATUS
    # ====================================================================

    def status(
        self,
    ) -> Dict[str, Any]:
        """
        Return StepVerifier status.
        """

        with self._lock:

            verifier_names = list(self._verifiers.keys())

            verification_count = self._verification_count

        return {
            "verifier_count": len(verifier_names),
            "verifiers": verifier_names,
            "verification_count": (verification_count),
            "require_observation": (self.require_observation),
            "minimum_confidence": (self.minimum_confidence),
        }


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "VerificationStatus",
    "StepVerificationResult",
    "StepVerifier",
]
