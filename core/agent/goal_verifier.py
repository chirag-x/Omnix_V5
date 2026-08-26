"""
Omnix V5 - Goal Verifier

Verifies whether an overall user goal has actually been achieved.

This operates above StepVerifier.

StepVerifier:
    Did an individual workflow step succeed?

GoalVerifier:
    Did the complete workflow achieve the user's actual goal?

The verifier supports:

    - Workflow objects
    - Legacy task/plan objects
    - Step verification results
    - Observation results
    - Custom goal verifiers
    - Explicit goal success conditions
    - Dictionary-based and object-based components
"""

from __future__ import annotations

import inspect

from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple

# ============================================================================
# GOAL VERIFICATION STATUS
# ============================================================================


class GoalVerificationStatus(str, Enum):
    """
    Possible overall goal verification states.
    """

    ACHIEVED = "achieved"
    FAILED = "failed"
    UNCERTAIN = "uncertain"
    PARTIAL = "partial"
    SKIPPED = "skipped"


# ============================================================================
# GOAL VERIFICATION RESULT
# ============================================================================


@dataclass
class GoalVerificationResult:
    """
    Normalized result of overall goal verification.
    """

    status: GoalVerificationStatus

    success: bool

    goal_id: Optional[str] = None

    reason: Optional[str] = None

    confidence: Optional[float] = None

    completed_steps: List[str] = field(default_factory=list)

    failed_steps: List[str] = field(default_factory=list)

    evidence: List[Any] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(
        self,
    ) -> None:

        if not isinstance(
            self.status,
            GoalVerificationStatus,
        ):

            try:

                self.status = GoalVerificationStatus(str(self.status).strip().lower())

            except (
                TypeError,
                ValueError,
            ):

                self.status = GoalVerificationStatus.UNCERTAIN

        self.success = bool(self.success)

        if self.goal_id is not None:

            self.goal_id = str(self.goal_id).strip() or None

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

        self.completed_steps = [
            str(step_id) for step_id in self.completed_steps if step_id is not None
        ]

        self.failed_steps = [
            str(step_id) for step_id in self.failed_steps if step_id is not None
        ]

        self.evidence = list(self.evidence or [])

        if not isinstance(
            self.metadata,
            dict,
        ):

            self.metadata = {"value": self.metadata}

        self.metadata = dict(self.metadata)

    @property
    def achieved(
        self,
    ) -> bool:

        return self.status == GoalVerificationStatus.ACHIEVED

    @property
    def failed(
        self,
    ) -> bool:

        return self.status == GoalVerificationStatus.FAILED

    @property
    def uncertain(
        self,
    ) -> bool:

        return self.status == GoalVerificationStatus.UNCERTAIN

    @property
    def partial(
        self,
    ) -> bool:

        return self.status == GoalVerificationStatus.PARTIAL

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return {
            "status": self.status.value,
            "success": self.success,
            "goal_id": self.goal_id,
            "reason": self.reason,
            "confidence": self.confidence,
            "completed_steps": list(self.completed_steps),
            "failed_steps": list(self.failed_steps),
            "evidence": list(self.evidence),
            "metadata": dict(self.metadata),
        }


# ============================================================================
# GOAL VERIFIER
# ============================================================================


class GoalVerifier:
    """
    Verifies whether a complete goal has been achieved.

    Verification priority:

        1. Explicit goal success condition
        2. Registered custom goal verifiers
        3. Workflow/step completion analysis
        4. Observation analysis
        5. Final evidence aggregation

    Registered providers may expose:

        verify_goal()
        verify()
        evaluate()
        check()

    Or they may simply be callable.
    """

    def __init__(
        self,
        *,
        minimum_confidence: float = 0.5,
        require_all_steps: bool = True,
        require_observation: bool = False,
    ) -> None:

        self.minimum_confidence = self._normalize_confidence(
            minimum_confidence,
            default=0.5,
        )

        self.require_all_steps = bool(require_all_steps)

        self.require_observation = bool(require_observation)

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

        normalized_name = self._normalize_name(name)

        with self._lock:

            return self._verifiers.get(
                normalized_name,
                default,
            )

    def get_verifier_names(
        self,
    ) -> List[str]:

        with self._lock:

            return list(self._verifiers.keys())

    def clear_verifiers(
        self,
    ) -> None:

        with self._lock:

            self._verifiers.clear()

    # ====================================================================
    # MAIN VERIFICATION
    # ====================================================================

    def verify(
        self,
        goal: Any,
        *,
        workflow: Any = None,
        step_results: Any = None,
        observations: Any = None,
        context: Optional[Dict[str, Any]] = None,
        verifier: Optional[str] = None,
        **kwargs: Any,
    ) -> GoalVerificationResult:
        """
        Verify whether a goal was achieved.

        Args:
            goal:
                Original goal, task, plan or goal object.

            workflow:
                Executed workflow.

            step_results:
                Results produced by individual step verification.

            observations:
                Final observations from ObservationLoop.

            context:
                Additional execution context.

            verifier:
                Optional specific custom verifier.
        """

        goal_id = self._extract_goal_id(
            goal,
            workflow,
        )

        verification_context = dict(context or {})

        verification_context.setdefault(
            "goal",
            goal,
        )

        verification_context.setdefault(
            "workflow",
            workflow,
        )

        evidence: List[Any] = []

        # --------------------------------------------------------------
        # 1. Explicit goal verification rule
        # --------------------------------------------------------------

        explicit_rule = self._extract_goal_rule(goal)

        if explicit_rule is not None:

            result = self._evaluate_rule(
                explicit_rule,
                goal=goal,
                workflow=workflow,
                step_results=step_results,
                observations=observations,
                context=verification_context,
            )

            if result is not None:

                normalized = self._normalize_result(
                    result,
                    goal_id=goal_id,
                    source="goal_rule",
                )

                self._increment_count()

                return normalized

        # --------------------------------------------------------------
        # 2. Custom goal verifiers
        # --------------------------------------------------------------

        provider_results = self._run_verifiers(
            goal=goal,
            workflow=workflow,
            step_results=step_results,
            observations=observations,
            context=verification_context,
            verifier=verifier,
            **kwargs,
        )

        if provider_results:

            result = self._aggregate_results(
                provider_results,
                goal_id=goal_id,
            )

            self._increment_count()

            return result

        # --------------------------------------------------------------
        # 3. Analyze workflow steps
        # --------------------------------------------------------------

        completed_steps, failed_steps, total_steps = self._analyze_steps(
            workflow,
            step_results,
        )

        if total_steps > 0:

            evidence.append(
                {
                    "source": "workflow",
                    "total_steps": total_steps,
                    "completed_steps": list(completed_steps),
                    "failed_steps": list(failed_steps),
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
        # 5. Build final result
        # --------------------------------------------------------------

        result = self._build_default_result(
            goal_id=goal_id,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            total_steps=total_steps,
            observation_state=observation_state,
            evidence=evidence,
        )

        self._increment_count()

        return result

    verify_goal = verify

    # ====================================================================
    # GOAL RULES
    # ====================================================================

    @staticmethod
    def _extract_goal_rule(
        goal: Any,
    ) -> Any:

        if isinstance(
            goal,
            dict,
        ):

            for key in (
                "goal_verification",
                "verification",
                "verify",
                "success_condition",
                "completion_condition",
            ):

                if key in goal:

                    return goal[key]

            metadata = goal.get("metadata")

            if isinstance(
                metadata,
                dict,
            ):

                for key in (
                    "goal_verification",
                    "verification",
                    "success_condition",
                ):

                    if key in metadata:

                        return metadata[key]

            return None

        for attribute in (
            "goal_verification",
            "verification",
            "verify",
            "success_condition",
            "completion_condition",
        ):

            if hasattr(
                goal,
                attribute,
            ):

                try:

                    value = getattr(
                        goal,
                        attribute,
                    )

                    if value is not None:

                        return value

                except Exception:

                    continue

        metadata = getattr(
            goal,
            "metadata",
            None,
        )

        if isinstance(
            metadata,
            dict,
        ):

            for key in (
                "goal_verification",
                "verification",
                "success_condition",
            ):

                if key in metadata:

                    return metadata[key]

        return None

    @staticmethod
    def _evaluate_rule(
        rule: Any,
        *,
        goal: Any,
        workflow: Any,
        step_results: Any,
        observations: Any,
        context: Dict[str, Any],
    ) -> Any:

        if callable(rule):

            return GoalVerifier._invoke_callable(
                rule,
                goal=goal,
                workflow=workflow,
                step_results=step_results,
                observations=observations,
                context=context,
            )

        if isinstance(
            rule,
            (bool, dict),
        ):

            return rule

        return None

    # ====================================================================
    # CUSTOM VERIFIERS
    # ====================================================================

    def _run_verifiers(
        self,
        *,
        goal: Any,
        workflow: Any,
        step_results: Any,
        observations: Any,
        context: Dict[str, Any],
        verifier: Optional[str],
        **kwargs: Any,
    ) -> List[GoalVerificationResult]:

        selected = self._select_verifiers(verifier)

        results: List[GoalVerificationResult] = []

        goal_id = self._extract_goal_id(
            goal,
            workflow,
        )

        for name, provider in selected:

            try:

                raw_result = self._call_verifier(
                    provider,
                    goal=goal,
                    workflow=workflow,
                    step_results=step_results,
                    observations=observations,
                    context=context,
                    **kwargs,
                )

                if inspect.isawaitable(raw_result):

                    raise RuntimeError(
                        "Async goal verifiers are "
                        "not supported by the "
                        "synchronous GoalVerifier."
                    )

                normalized = self._normalize_result(
                    raw_result,
                    goal_id=goal_id,
                    source=name,
                )

            except Exception as error:

                normalized = GoalVerificationResult(
                    status=(GoalVerificationStatus.UNCERTAIN),
                    success=False,
                    goal_id=goal_id,
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
        **available_kwargs: Any,
    ) -> Any:

        for method_name in (
            "verify_goal",
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

                return GoalVerifier._invoke_callable(
                    method,
                    **available_kwargs,
                )

        if callable(verifier):

            return GoalVerifier._invoke_callable(
                verifier,
                **available_kwargs,
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
    # STEP ANALYSIS
    # ====================================================================

    def _analyze_steps(
        self,
        workflow: Any,
        step_results: Any,
    ) -> Tuple[
        List[str],
        List[str],
        int,
    ]:

        completed: List[str] = []
        failed: List[str] = []

        # --------------------------------------------------------------
        # Explicit step verification results
        # --------------------------------------------------------------

        normalized_results = self._normalize_step_results(step_results)

        if normalized_results:

            for result in normalized_results:

                step_id = self._extract_step_result_id(result)

                state = self._extract_step_result_state(result)

                if step_id is None:

                    continue

                if state is True:

                    completed.append(step_id)

                elif state is False:

                    failed.append(step_id)

            total = len(normalized_results)

            return (
                completed,
                failed,
                total,
            )

        # --------------------------------------------------------------
        # Workflow step status
        # --------------------------------------------------------------

        steps = self._extract_workflow_steps(workflow)

        for step in steps:

            step_id = self._extract_step_id(step)

            if step_id is None:

                continue

            status = self._extract_status(step)

            if status in (
                "completed",
                "verified",
                "success",
                "done",
            ):

                completed.append(step_id)

            elif status in (
                "failed",
                "error",
                "blocked",
                "cancelled",
            ):

                failed.append(step_id)

        return (
            completed,
            failed,
            len(steps),
        )

    @staticmethod
    def _normalize_step_results(
        step_results: Any,
    ) -> List[Any]:

        if step_results is None:

            return []

        if isinstance(
            step_results,
            dict,
        ):

            if "results" in step_results:

                value = step_results["results"]

                if isinstance(
                    value,
                    (list, tuple),
                ):

                    return list(value)

            return [step_results]

        if isinstance(
            step_results,
            (list, tuple),
        ):

            return list(step_results)

        results = getattr(
            step_results,
            "results",
            None,
        )

        if isinstance(
            results,
            (list, tuple),
        ):

            return list(results)

        return []

    @staticmethod
    def _extract_workflow_steps(
        workflow: Any,
    ) -> List[Any]:

        if workflow is None:

            return []

        if isinstance(
            workflow,
            dict,
        ):

            for key in (
                "steps",
                "tasks",
                "actions",
            ):

                value = workflow.get(key)

                if isinstance(
                    value,
                    (list, tuple),
                ):

                    return list(value)

            return []

        for attribute in (
            "steps",
            "tasks",
            "actions",
        ):

            value = getattr(
                workflow,
                attribute,
                None,
            )

            if isinstance(
                value,
                (list, tuple),
            ):

                return list(value)

        return []

    # ====================================================================
    # OBSERVATION ANALYSIS
    # ====================================================================

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
                bool,
            ):

                states.append(observation)

            elif isinstance(
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

        if not states:

            return None

        if any(state is False for state in states):

            return False

        if all(state is True for state in states):

            return True

        return None

    # ====================================================================
    # DEFAULT RESULT
    # ====================================================================

    def _build_default_result(
        self,
        *,
        goal_id: Optional[str],
        completed_steps: List[str],
        failed_steps: List[str],
        total_steps: int,
        observation_state: Optional[bool],
        evidence: List[Any],
    ) -> GoalVerificationResult:

        # Explicit observation says goal failed
        if observation_state is False:

            return GoalVerificationResult(
                status=(GoalVerificationStatus.FAILED),
                success=False,
                goal_id=goal_id,
                reason=(
                    "Final observation indicates " "that the goal was not achieved."
                ),
                confidence=1.0,
                completed_steps=completed_steps,
                failed_steps=failed_steps,
                evidence=evidence,
            )

        # Failed steps exist
        if failed_steps:

            if completed_steps:

                return GoalVerificationResult(
                    status=(GoalVerificationStatus.PARTIAL),
                    success=False,
                    goal_id=goal_id,
                    reason=(
                        "Some workflow steps completed, "
                        "but one or more steps failed."
                    ),
                    confidence=0.9,
                    completed_steps=completed_steps,
                    failed_steps=failed_steps,
                    evidence=evidence,
                )

            return GoalVerificationResult(
                status=(GoalVerificationStatus.FAILED),
                success=False,
                goal_id=goal_id,
                reason=("Workflow execution contains " "failed steps."),
                confidence=1.0,
                completed_steps=completed_steps,
                failed_steps=failed_steps,
                evidence=evidence,
            )

        # All known steps completed
        if total_steps > 0 and len(completed_steps) == total_steps:

            if self.require_observation and observation_state is None:

                return GoalVerificationResult(
                    status=(GoalVerificationStatus.UNCERTAIN),
                    success=False,
                    goal_id=goal_id,
                    reason=(
                        "All workflow steps completed, "
                        "but no final observation was "
                        "available."
                    ),
                    confidence=0.5,
                    completed_steps=completed_steps,
                    failed_steps=failed_steps,
                    evidence=evidence,
                )

            confidence = 1.0 if observation_state is True else 0.85

            return GoalVerificationResult(
                status=(GoalVerificationStatus.ACHIEVED),
                success=True,
                goal_id=goal_id,
                reason=("All required workflow steps " "completed successfully."),
                confidence=confidence,
                completed_steps=completed_steps,
                failed_steps=failed_steps,
                evidence=evidence,
            )

        # Some completed, but workflow incomplete
        if completed_steps:

            return GoalVerificationResult(
                status=(GoalVerificationStatus.PARTIAL),
                success=False,
                goal_id=goal_id,
                reason=("The goal is only partially " "completed."),
                confidence=(
                    len(completed_steps)
                    / max(
                        total_steps,
                        1,
                    )
                ),
                completed_steps=completed_steps,
                failed_steps=failed_steps,
                evidence=evidence,
            )

        return GoalVerificationResult(
            status=(GoalVerificationStatus.UNCERTAIN),
            success=False,
            goal_id=goal_id,
            reason=(
                "Insufficient evidence to determine " "whether the goal was achieved."
            ),
            confidence=0.0,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            evidence=evidence,
        )

    # ====================================================================
    # RESULT NORMALIZATION
    # ====================================================================

    @staticmethod
    def _normalize_result(
        result: Any,
        *,
        goal_id: Optional[str],
        source: str,
    ) -> GoalVerificationResult:

        if isinstance(
            result,
            GoalVerificationResult,
        ):

            if result.goal_id is None:

                result.goal_id = goal_id

            result.metadata.setdefault(
                "source",
                source,
            )

            return result

        if isinstance(
            result,
            bool,
        ):

            return GoalVerificationResult(
                status=(
                    GoalVerificationStatus.ACHIEVED
                    if result
                    else GoalVerificationStatus.FAILED
                ),
                success=result,
                goal_id=goal_id,
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

                    status = GoalVerificationStatus(str(status_value).strip().lower())

                except ValueError:

                    status = GoalVerificationStatus.UNCERTAIN

            elif success_value is True:

                status = GoalVerificationStatus.ACHIEVED

            elif success_value is False:

                status = GoalVerificationStatus.FAILED

            else:

                status = GoalVerificationStatus.UNCERTAIN

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

            return GoalVerificationResult(
                status=status,
                success=(status == GoalVerificationStatus.ACHIEVED),
                goal_id=result.get(
                    "goal_id",
                    result.get(
                        "id",
                        goal_id,
                    ),
                ),
                reason=result.get(
                    "reason",
                    result.get("error"),
                ),
                confidence=result.get("confidence"),
                completed_steps=list(
                    result.get(
                        "completed_steps",
                        [],
                    )
                    or []
                ),
                failed_steps=list(
                    result.get(
                        "failed_steps",
                        [],
                    )
                    or []
                ),
                evidence=list(
                    result.get(
                        "evidence",
                        [],
                    )
                    or []
                ),
                metadata=metadata,
            )

        return GoalVerificationResult(
            status=(GoalVerificationStatus.UNCERTAIN),
            success=False,
            goal_id=goal_id,
            reason=("Verifier returned an unsupported " "result."),
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
        results: List[GoalVerificationResult],
        *,
        goal_id: Optional[str],
    ) -> GoalVerificationResult:

        achieved = [result for result in results if result.achieved]

        failed = [result for result in results if result.failed]

        partial = [result for result in results if result.partial]

        evidence: List[Any] = []

        completed_steps: List[str] = []

        failed_steps: List[str] = []

        for result in results:

            evidence.extend(result.evidence)

            completed_steps.extend(result.completed_steps)

            failed_steps.extend(result.failed_steps)

            evidence.append(
                {
                    "source": (result.metadata.get("source")),
                    "status": (result.status.value),
                    "reason": result.reason,
                }
            )

        completed_steps = list(dict.fromkeys(completed_steps))

        failed_steps = list(dict.fromkeys(failed_steps))

        if failed:

            confidence = max(
                (result.confidence or 0.0 for result in failed),
                default=1.0,
            )

            return GoalVerificationResult(
                status=(GoalVerificationStatus.FAILED),
                success=False,
                goal_id=goal_id,
                reason=("At least one goal verifier " "reported failure."),
                confidence=confidence,
                completed_steps=completed_steps,
                failed_steps=failed_steps,
                evidence=evidence,
            )

        if achieved:

            confidence = max(
                (result.confidence or 0.0 for result in achieved),
                default=0.75,
            )

            if confidence >= self.minimum_confidence:

                return GoalVerificationResult(
                    status=(GoalVerificationStatus.ACHIEVED),
                    success=True,
                    goal_id=goal_id,
                    reason=("Goal verified successfully."),
                    confidence=confidence,
                    completed_steps=completed_steps,
                    failed_steps=failed_steps,
                    evidence=evidence,
                )

        if partial:

            confidence = max(
                (result.confidence or 0.0 for result in partial),
                default=0.5,
            )

            return GoalVerificationResult(
                status=(GoalVerificationStatus.PARTIAL),
                success=False,
                goal_id=goal_id,
                reason=("Goal was partially completed."),
                confidence=confidence,
                completed_steps=completed_steps,
                failed_steps=failed_steps,
                evidence=evidence,
            )

        return GoalVerificationResult(
            status=(GoalVerificationStatus.UNCERTAIN),
            success=False,
            goal_id=goal_id,
            reason=("No verifier could confirm that " "the goal was achieved."),
            confidence=0.0,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            evidence=evidence,
        )

    # ====================================================================
    # EXTRACTION UTILITIES
    # ====================================================================

    @staticmethod
    def _extract_goal_id(
        goal: Any,
        workflow: Any,
    ) -> Optional[str]:

        for source in (
            goal,
            workflow,
        ):

            if source is None:

                continue

            if isinstance(
                source,
                dict,
            ):

                value = (
                    source.get("goal_id")
                    or source.get("workflow_id")
                    or source.get("plan_id")
                    or source.get("task_id")
                    or source.get("id")
                )

            else:

                value = None

                for attribute in (
                    "goal_id",
                    "workflow_id",
                    "plan_id",
                    "task_id",
                    "id",
                ):

                    try:

                        value = getattr(
                            source,
                            attribute,
                            None,
                        )

                    except Exception:

                        value = None

                    if value is not None:

                        break

            if value is not None:

                return str(value).strip() or None

        return None

    @staticmethod
    def _extract_step_id(
        step: Any,
    ) -> Optional[str]:

        if isinstance(
            step,
            dict,
        ):

            value = step.get("step_id") or step.get("task_id") or step.get("id")

        else:

            value = (
                getattr(
                    step,
                    "step_id",
                    None,
                )
                or getattr(
                    step,
                    "task_id",
                    None,
                )
                or getattr(
                    step,
                    "id",
                    None,
                )
            )

        if value is None:

            return None

        return str(value).strip() or None

    @staticmethod
    def _extract_status(
        value: Any,
    ) -> Optional[str]:

        if isinstance(
            value,
            dict,
        ):

            status = value.get("status")

        else:

            status = getattr(
                value,
                "status",
                None,
            )

        if status is None:

            return None

        if hasattr(
            status,
            "value",
        ):

            status = status.value

        return str(status).strip().lower()

    @staticmethod
    def _extract_step_result_id(
        result: Any,
    ) -> Optional[str]:

        if isinstance(
            result,
            dict,
        ):

            value = result.get("step_id") or result.get("task_id") or result.get("id")

        else:

            value = (
                getattr(
                    result,
                    "step_id",
                    None,
                )
                or getattr(
                    result,
                    "task_id",
                    None,
                )
                or getattr(
                    result,
                    "id",
                    None,
                )
            )

        if value is None:

            return None

        return str(value).strip() or None

    @staticmethod
    def _extract_step_result_state(
        result: Any,
    ) -> Optional[bool]:

        if isinstance(
            result,
            bool,
        ):

            return result

        if isinstance(
            result,
            dict,
        ):

            if "success" in result:

                return bool(result["success"])

            status = result.get("status")

        else:

            if hasattr(
                result,
                "success",
            ):

                try:

                    return bool(result.success)

                except Exception:

                    pass

            status = getattr(
                result,
                "status",
                None,
            )

        if status is None:

            return None

        if hasattr(
            status,
            "value",
        ):

            status = status.value

        normalized = str(status).strip().lower()

        if normalized in (
            "verified",
            "completed",
            "success",
            "done",
            "achieved",
        ):

            return True

        if normalized in (
            "failed",
            "error",
            "blocked",
            "cancelled",
        ):

            return False

        return None

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
    # STATUS
    # ====================================================================

    def status(
        self,
    ) -> Dict[str, Any]:

        with self._lock:

            verifier_names = list(self._verifiers.keys())

            verification_count = self._verification_count

        return {
            "verifier_count": len(verifier_names),
            "verifiers": verifier_names,
            "verification_count": (verification_count),
            "minimum_confidence": (self.minimum_confidence),
            "require_all_steps": (self.require_all_steps),
            "require_observation": (self.require_observation),
        }

    # ====================================================================
    # INTERNAL UTILITIES
    # ====================================================================

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


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "GoalVerificationStatus",
    "GoalVerificationResult",
    "GoalVerifier",
]
