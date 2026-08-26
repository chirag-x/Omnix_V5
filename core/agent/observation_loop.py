"""
Omnix V5 - Observation Loop

Provides the observation layer for the Omnix V5 agent system.

The ObservationLoop collects information after or during agent execution
so Omnix can determine what actually happened instead of assuming that
an action succeeded.

Possible observation sources include:

    - Action execution results
    - Omnix V5 Vision subsystem
    - System state
    - UI state
    - Skills
    - Custom observers
    - Legacy observation providers

The loop itself does not execute actions. It gathers and normalizes
observations for verification and recovery components.
"""

from __future__ import annotations

import inspect

from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple

# ============================================================================
# OBSERVATION RESULT
# ============================================================================


@dataclass
class Observation:
    """
    Normalized observation produced by an observer.

    An observation may represent:

        - Visual state
        - Application state
        - System state
        - Execution result
        - UI state
        - Custom agent feedback
    """

    success: bool

    value: Any = None

    source: Optional[str] = None

    error: Optional[str] = None

    confidence: Optional[float] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(
        self,
    ) -> None:

        if self.source is not None:

            self.source = str(self.source).strip() or None

        if self.error is not None:

            self.error = str(self.error).strip() or None

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

        if not isinstance(
            self.metadata,
            dict,
        ):

            self.metadata = {"value": self.metadata}

        self.metadata = dict(self.metadata)

    @property
    def failed(
        self,
    ) -> bool:
        """
        Return True when observation failed.
        """

        return not self.success

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Convert observation to dictionary.
        """

        return {
            "success": self.success,
            "value": self.value,
            "source": self.source,
            "error": self.error,
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
        }


@dataclass
class ObservationBatch:
    """
    Collection of observations produced during one observation cycle.
    """

    observations: List[Observation] = field(default_factory=list)

    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(
        self,
    ) -> None:

        self.observations = list(self.observations)

        if not isinstance(
            self.context,
            dict,
        ):

            self.context = {"value": self.context}

        self.context = dict(self.context)

    @property
    def successful(
        self,
    ) -> List[Observation]:
        """
        Return successful observations.
        """

        return [observation for observation in self.observations if observation.success]

    @property
    def failed(
        self,
    ) -> List[Observation]:
        """
        Return failed observations.
        """

        return [observation for observation in self.observations if observation.failed]

    def get(
        self,
        source: str,
    ) -> Optional[Observation]:
        """
        Return the first observation from a source.
        """

        normalized_source = str(source).strip().lower()

        for observation in self.observations:

            if observation.source and observation.source.lower() == normalized_source:

                return observation

        return None

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Convert batch to dictionary.
        """

        return {
            "observations": [
                observation.to_dict() for observation in self.observations
            ],
            "context": dict(self.context),
        }


# ============================================================================
# OBSERVATION LOOP
# ============================================================================


class ObservationLoop:
    """
    Collects observations from registered observers.

    An observer can be:

        - An object with observe()
        - An object with inspect()
        - An object with get_state()
        - An object with capture()
        - A callable

    The observer may return:

        - Observation
        - dict
        - bool
        - Any custom value

    All results are normalized into Observation objects.
    """

    def __init__(
        self,
    ) -> None:

        self._observers: Dict[str, Any] = {}

        self._lock = RLock()

        self._observation_count = 0

    # ====================================================================
    # OBSERVER MANAGEMENT
    # ====================================================================

    def register_observer(
        self,
        name: str,
        observer: Any,
        *,
        replace: bool = False,
    ) -> None:
        """
        Register an observation provider.
        """

        normalized_name = self._normalize_name(name)

        if observer is None:

            raise ValueError("Observer cannot be None.")

        with self._lock:

            if normalized_name in self._observers and not replace:

                raise ValueError(f"Observer already exists: " f"{normalized_name}")

            self._observers[normalized_name] = observer

    def unregister_observer(
        self,
        name: str,
    ) -> bool:
        """
        Remove a registered observer.
        """

        normalized_name = self._normalize_name(name)

        with self._lock:

            if normalized_name not in self._observers:

                return False

            del self._observers[normalized_name]

            return True

    def get_observer(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Return a registered observer.
        """

        normalized_name = self._normalize_name(name)

        with self._lock:

            return self._observers.get(
                normalized_name,
                default,
            )

    def has_observer(
        self,
        name: str,
    ) -> bool:
        """
        Check whether an observer exists.
        """

        normalized_name = self._normalize_name(name)

        with self._lock:

            return normalized_name in self._observers

    def get_observer_names(
        self,
    ) -> List[str]:
        """
        Return all registered observer names.
        """

        with self._lock:

            return list(self._observers.keys())

    def clear_observers(
        self,
    ) -> None:
        """
        Remove all registered observers.
        """

        with self._lock:

            self._observers.clear()

    # ====================================================================
    # OBSERVATION
    # ====================================================================

    def observe(
        self,
        subject: Any = None,
        *,
        observer: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ObservationBatch:
        """
        Collect observations.

        If observer is provided, only that observer is used.

        Otherwise all registered observers are queried.

        Args:
            subject:
                Object, workflow step, execution result or state
                being observed.

            observer:
                Optional observer name.

            context:
                Additional information for observation.

            kwargs:
                Additional arguments forwarded to observers.
        """

        selected = self._select_observers(observer)

        observation_context = dict(context or {})

        observation_context.setdefault(
            "subject",
            subject,
        )

        observations: List[Observation] = []

        for name, provider in selected:

            try:

                result = self._call_observer(
                    provider,
                    subject,
                    observation_context,
                    **kwargs,
                )

                if inspect.isawaitable(result):

                    raise RuntimeError(
                        "Async observers are not "
                        "supported by the synchronous "
                        "ObservationLoop."
                    )

                normalized = self._normalize_observation(
                    result,
                    source=name,
                )

            except Exception as error:

                normalized = Observation(
                    success=False,
                    source=name,
                    error=str(error),
                )

            observations.append(normalized)

        with self._lock:

            self._observation_count += 1

        return ObservationBatch(
            observations=observations,
            context=observation_context,
        )

    def observe_one(
        self,
        observer: str,
        subject: Any = None,
        *,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Observation:
        """
        Observe using one specific observer.
        """

        batch = self.observe(
            subject,
            observer=observer,
            context=context,
            **kwargs,
        )

        if batch.observations:

            return batch.observations[0]

        return Observation(
            success=False,
            source=observer,
            error="Observer was not found.",
        )

    # ====================================================================
    # CONVENIENCE METHODS
    # ====================================================================

    def observe_execution(
        self,
        execution_result: Any,
        *,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ObservationBatch:
        """
        Observe the result of an executed action.
        """

        merged_context = dict(context or {})

        merged_context["observation_type"] = "execution"

        return self.observe(
            execution_result,
            context=merged_context,
            **kwargs,
        )

    def observe_step(
        self,
        step: Any,
        *,
        result: Any = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ObservationBatch:
        """
        Observe an executed workflow step.
        """

        merged_context = dict(context or {})

        merged_context["observation_type"] = "step"

        merged_context["step"] = step

        if result is not None:

            merged_context["result"] = result

        return self.observe(
            step,
            context=merged_context,
            **kwargs,
        )

    def observe_state(
        self,
        state: Any = None,
        *,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ObservationBatch:
        """
        Collect current system or application state.
        """

        merged_context = dict(context or {})

        merged_context["observation_type"] = "state"

        return self.observe(
            state,
            context=merged_context,
            **kwargs,
        )

    # ====================================================================
    # INTERNAL OBSERVER EXECUTION
    # ====================================================================

    @staticmethod
    def _call_observer(
        observer: Any,
        subject: Any,
        context: Dict[str, Any],
        **kwargs: Any,
    ) -> Any:
        """
        Call an observer using a compatible method.
        """

        for method_name in (
            "observe",
            "inspect",
            "get_state",
            "capture",
            "analyze",
        ):

            method = getattr(
                observer,
                method_name,
                None,
            )

            if not callable(method):

                continue

            return ObservationLoop._invoke(
                method,
                subject,
                context,
                **kwargs,
            )

        if callable(observer):

            return ObservationLoop._invoke(
                observer,
                subject,
                context,
                **kwargs,
            )

        raise AttributeError(
            "Observer does not expose a " "supported observation method."
        )

    @staticmethod
    def _invoke(
        function: Any,
        subject: Any,
        context: Dict[str, Any],
        **kwargs: Any,
    ) -> Any:
        """
        Call an observer while supporting common signatures.
        """

        try:

            signature = inspect.signature(function)

            parameters = signature.parameters

            call_kwargs = dict(kwargs)

            if "context" in parameters:

                call_kwargs["context"] = context

            if "subject" in parameters:

                call_kwargs["subject"] = subject

                return function(**call_kwargs)

            positional_parameters = [
                parameter
                for parameter in parameters.values()
                if parameter.kind
                in (
                    parameter.POSITIONAL_ONLY,
                    parameter.POSITIONAL_OR_KEYWORD,
                )
            ]

            if positional_parameters:

                return function(
                    subject,
                    **call_kwargs,
                )

            return function(**call_kwargs)

        except (
            TypeError,
            ValueError,
        ):

            return function(
                subject,
                context=context,
                **kwargs,
            )

    # ====================================================================
    # NORMALIZATION
    # ====================================================================

    @staticmethod
    def _normalize_observation(
        result: Any,
        *,
        source: str,
    ) -> Observation:
        """
        Convert observer output into Observation.
        """

        if isinstance(
            result,
            Observation,
        ):

            if result.source is None:

                result.source = source

            return result

        if isinstance(
            result,
            bool,
        ):

            return Observation(
                success=result,
                value=result,
                source=source,
            )

        if isinstance(
            result,
            dict,
        ):

            success = result.get(
                "success",
                result.get(
                    "ok",
                    True,
                ),
            )

            confidence = result.get("confidence")

            metadata = result.get(
                "metadata",
                {},
            )

            value = result.get(
                "value",
                result.get(
                    "result",
                    result.get(
                        "data",
                        result,
                    ),
                ),
            )

            return Observation(
                success=bool(success),
                value=value,
                source=result.get(
                    "source",
                    source,
                ),
                error=result.get("error"),
                confidence=confidence,
                metadata=(
                    metadata
                    if isinstance(
                        metadata,
                        dict,
                    )
                    else {}
                ),
            )

        return Observation(
            success=True,
            value=result,
            source=source,
        )

    # ====================================================================
    # OBSERVER SELECTION
    # ====================================================================

    def _select_observers(
        self,
        observer: Optional[str],
    ) -> List[Tuple[str, Any]]:
        """
        Select observers for an observation cycle.
        """

        with self._lock:

            if observer is not None:

                normalized_name = self._normalize_name(observer)

                provider = self._observers.get(normalized_name)

                if provider is None:

                    return []

                return [
                    (
                        normalized_name,
                        provider,
                    )
                ]

            return list(self._observers.items())

    # ====================================================================
    # STATUS
    # ====================================================================

    def status(
        self,
    ) -> Dict[str, Any]:
        """
        Return ObservationLoop status.
        """

        with self._lock:

            observer_names = list(self._observers.keys())

            observation_count = self._observation_count

        return {
            "observer_count": len(observer_names),
            "observers": observer_names,
            "observation_count": (observation_count),
        }

    # ====================================================================
    # UTILITIES
    # ====================================================================

    @staticmethod
    def _normalize_name(
        name: str,
    ) -> str:
        """
        Normalize observer names.
        """

        normalized = str(name).strip().lower()

        if not normalized:

            raise ValueError("Observer name cannot be empty.")

        return normalized


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "Observation",
    "ObservationBatch",
    "ObservationLoop",
]
