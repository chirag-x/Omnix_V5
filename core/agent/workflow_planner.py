"""
Omnix V5 - Workflow Planner

Transforms planning output into a normalized executable workflow.

This module sits between the Planning layer and the Agent execution
layer. It does not replace core.planning.task_planner.

Responsibilities:
    - Normalize plans, tasks and steps from V5 or legacy components
    - Create executable workflow steps
    - Resolve step dependencies
    - Preserve execution order
    - Detect dependency problems
    - Provide ready-step selection for the executor
    - Support both dictionary-based and object-based legacy plans
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Set

# ============================================================================
# ENUMS
# ============================================================================


class WorkflowStatus(str, Enum):
    """
    Overall workflow status.
    """

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStepStatus(str, Enum):
    """
    Status of an individual workflow step.
    """

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class WorkflowStep:
    """
    A normalized executable step.

    The payload field preserves the original planning information so
    that V5 and legacy executors can access their own data.
    """

    id: str

    action: str

    description: str = ""

    target: Any = None

    parameters: Dict[str, Any] = field(default_factory=dict)

    dependencies: List[str] = field(default_factory=list)

    status: WorkflowStepStatus = WorkflowStepStatus.PENDING

    result: Any = None

    error: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    payload: Any = None

    def __post_init__(
        self,
    ) -> None:

        self.id = str(self.id).strip()

        if not self.id:

            raise ValueError("Workflow step id cannot be empty.")

        self.action = str(self.action).strip()

        if not self.action:

            raise ValueError("Workflow step action cannot be empty.")

        self.description = str(self.description or "").strip()

        self.dependencies = self._normalize_dependencies(self.dependencies)

        if not isinstance(
            self.parameters,
            dict,
        ):

            self.parameters = {"value": self.parameters}

        if not isinstance(
            self.metadata,
            dict,
        ):

            self.metadata = {"value": self.metadata}

        self.parameters = dict(self.parameters)

        self.metadata = dict(self.metadata)

        self.status = self._normalize_status(self.status)

    @staticmethod
    def _normalize_dependencies(
        dependencies: Any,
    ) -> List[str]:

        if dependencies is None:

            return []

        if isinstance(
            dependencies,
            str,
        ):

            dependencies = [dependencies]

        if not isinstance(
            dependencies,
            Iterable,
        ):

            return []

        normalized: List[str] = []
        seen: Set[str] = set()

        for dependency in dependencies:

            value = str(dependency).strip()

            if value and value not in seen:

                seen.add(value)

                normalized.append(value)

        return normalized

    @staticmethod
    def _normalize_status(
        status: Any,
    ) -> WorkflowStepStatus:

        if isinstance(
            status,
            WorkflowStepStatus,
        ):

            return status

        try:

            return WorkflowStepStatus(str(status).strip().lower())

        except (
            ValueError,
            TypeError,
        ):

            return WorkflowStepStatus.PENDING

    @property
    def is_terminal(
        self,
    ) -> bool:

        return self.status in (
            WorkflowStepStatus.COMPLETED,
            WorkflowStepStatus.FAILED,
            WorkflowStepStatus.SKIPPED,
            WorkflowStepStatus.CANCELLED,
        )

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return {
            "id": self.id,
            "action": self.action,
            "description": self.description,
            "target": self.target,
            "parameters": dict(self.parameters),
            "dependencies": list(self.dependencies),
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "metadata": dict(self.metadata),
        }


@dataclass
class Workflow:
    """
    Normalized executable workflow.
    """

    id: str

    steps: List[WorkflowStep] = field(default_factory=list)

    status: WorkflowStatus = WorkflowStatus.PENDING

    source_plan: Any = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(
        self,
    ) -> None:

        self.id = str(self.id).strip()

        if not self.id:

            raise ValueError("Workflow id cannot be empty.")

        self.status = self._normalize_status(self.status)

        if not isinstance(
            self.metadata,
            dict,
        ):

            self.metadata = {"value": self.metadata}

        self.metadata = dict(self.metadata)

        self.steps = list(self.steps)

    @staticmethod
    def _normalize_status(
        status: Any,
    ) -> WorkflowStatus:

        if isinstance(
            status,
            WorkflowStatus,
        ):

            return status

        try:

            return WorkflowStatus(str(status).strip().lower())

        except (
            ValueError,
            TypeError,
        ):

            return WorkflowStatus.PENDING

    def get_step(
        self,
        step_id: str,
    ) -> Optional[WorkflowStep]:

        step_id = str(step_id).strip()

        for step in self.steps:

            if step.id == step_id:

                return step

        return None

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return {
            "id": self.id,
            "status": self.status.value,
            "steps": [step.to_dict() for step in self.steps],
            "metadata": dict(self.metadata),
        }


# ============================================================================
# WORKFLOW PLANNER
# ============================================================================


class WorkflowPlanner:
    """
    Converts planning output into an executable Workflow.

    Compatible input examples:

        dict plans
        TaskPlan-like objects
        lists of steps
        legacy task objects

    Common supported fields:

        id / task_id / plan_id
        steps / tasks / actions
        action / name / type
        dependencies / depends_on
        parameters / args / kwargs
        target
        metadata
    """

    def __init__(
        self,
    ) -> None:

        self._workflow_counter = 0

    # ====================================================================
    # PUBLIC API
    # ====================================================================

    def create_workflow(
        self,
        plan: Any,
        *,
        workflow_id: Optional[str] = None,
    ) -> Workflow:
        """
        Convert a plan into a normalized Workflow.
        """

        if isinstance(
            plan,
            Workflow,
        ):

            return plan

        data = self._extract_plan_data(plan)

        resolved_id = (
            workflow_id
            or data.get("id")
            or data.get("workflow_id")
            or data.get("plan_id")
            or data.get("task_id")
            or self._generate_workflow_id()
        )

        raw_steps = self._extract_steps(
            plan,
            data,
        )

        steps = self._normalize_steps(raw_steps)

        workflow = Workflow(
            id=resolved_id,
            steps=steps,
            status=WorkflowStatus.READY,
            source_plan=plan,
            metadata=self._extract_metadata(data),
        )

        self.validate_workflow(workflow)

        return workflow

    build_workflow = create_workflow
    plan_workflow = create_workflow

    def validate_workflow(
        self,
        workflow: Workflow,
    ) -> None:
        """
        Validate workflow structure and dependencies.

        Raises:
            ValueError:
                For duplicate IDs, missing dependencies,
                self dependencies or circular dependencies.
        """

        step_ids = [step.id for step in workflow.steps]

        if len(step_ids) != len(set(step_ids)):

            raise ValueError("Workflow contains duplicate step IDs.")

        known_ids = set(step_ids)

        for step in workflow.steps:

            if step.id in step.dependencies:

                raise ValueError(f"Step '{step.id}' cannot depend " "on itself.")

            missing = [
                dependency
                for dependency in step.dependencies
                if dependency not in known_ids
            ]

            if missing:

                raise ValueError(
                    f"Step '{step.id}' has missing " f"dependencies: {missing}"
                )

        self._validate_no_cycles(workflow)

    def get_ready_steps(
        self,
        workflow: Workflow,
    ) -> List[WorkflowStep]:
        """
        Return steps whose dependencies have completed.

        This does not execute anything.
        """

        ready_steps: List[WorkflowStep] = []

        for step in workflow.steps:

            if step.status not in (
                WorkflowStepStatus.PENDING,
                WorkflowStepStatus.READY,
            ):

                continue

            if self._dependencies_completed(
                workflow,
                step,
            ):

                step.status = WorkflowStepStatus.READY

                ready_steps.append(step)

            elif self._dependencies_failed(
                workflow,
                step,
            ):

                step.status = WorkflowStepStatus.BLOCKED

        return ready_steps

    def get_execution_order(
        self,
        workflow: Workflow,
    ) -> List[WorkflowStep]:
        """
        Return steps in dependency-safe execution order.
        """

        self.validate_workflow(workflow)

        remaining = {step.id: step for step in workflow.steps}

        completed: Set[str] = set()

        ordered: List[WorkflowStep] = []

        while remaining:

            progress = False

            for step_id, step in list(remaining.items()):

                if all(dependency in completed for dependency in step.dependencies):

                    ordered.append(step)

                    completed.add(step_id)

                    del remaining[step_id]

                    progress = True

            if not progress:

                raise ValueError("Unable to resolve workflow " "execution order.")

        return ordered

    def mark_step_running(
        self,
        workflow: Workflow,
        step_id: str,
    ) -> WorkflowStep:

        step = self._require_step(
            workflow,
            step_id,
        )

        step.status = WorkflowStepStatus.RUNNING

        workflow.status = WorkflowStatus.RUNNING

        return step

    def mark_step_completed(
        self,
        workflow: Workflow,
        step_id: str,
        result: Any = None,
    ) -> WorkflowStep:

        step = self._require_step(
            workflow,
            step_id,
        )

        step.status = WorkflowStepStatus.COMPLETED

        step.result = result
        step.error = None

        self._refresh_workflow_status(workflow)

        return step

    def mark_step_failed(
        self,
        workflow: Workflow,
        step_id: str,
        error: Any = None,
    ) -> WorkflowStep:

        step = self._require_step(
            workflow,
            step_id,
        )

        step.status = WorkflowStepStatus.FAILED

        step.error = str(error) if error is not None else None

        self._refresh_workflow_status(workflow)

        return step

    def reset_step(
        self,
        workflow: Workflow,
        step_id: str,
    ) -> WorkflowStep:
        """
        Reset a step for retry.
        """

        step = self._require_step(
            workflow,
            step_id,
        )

        step.status = WorkflowStepStatus.PENDING

        step.error = None
        step.result = None

        self._refresh_workflow_status(workflow)

        return step

    # ====================================================================
    # PLAN EXTRACTION
    # ====================================================================

    @staticmethod
    def _extract_plan_data(
        plan: Any,
    ) -> Dict[str, Any]:

        if isinstance(
            plan,
            dict,
        ):

            return dict(plan)

        if plan is None:

            return {}

        data: Dict[str, Any] = {}

        for attribute in (
            "id",
            "workflow_id",
            "plan_id",
            "task_id",
            "steps",
            "tasks",
            "actions",
            "metadata",
            "description",
        ):

            if hasattr(
                plan,
                attribute,
            ):

                try:

                    data[attribute] = getattr(
                        plan,
                        attribute,
                    )

                except Exception:

                    continue

        return data

    @staticmethod
    def _extract_steps(
        plan: Any,
        data: Dict[str, Any],
    ) -> List[Any]:

        if isinstance(
            plan,
            (list, tuple),
        ):

            return list(plan)

        for key in (
            "steps",
            "tasks",
            "actions",
            "workflow",
        ):

            value = data.get(key)

            if isinstance(
                value,
                (list, tuple),
            ):

                return list(value)

        return []

    def _normalize_steps(
        self,
        raw_steps: List[Any],
    ) -> List[WorkflowStep]:

        steps: List[WorkflowStep] = []

        for index, raw_step in enumerate(
            raw_steps,
            start=1,
        ):

            steps.append(
                self._normalize_step(
                    raw_step,
                    index,
                )
            )

        return steps

    def _normalize_step(
        self,
        raw_step: Any,
        index: int,
    ) -> WorkflowStep:

        if isinstance(
            raw_step,
            WorkflowStep,
        ):

            return raw_step

        data = self._object_to_dict(raw_step)

        step_id = (
            data.get("id")
            or data.get("step_id")
            or data.get("task_id")
            or f"step_{index}"
        )

        action = (
            data.get("action")
            or data.get("name")
            or data.get("type")
            or data.get("command")
            or "execute"
        )

        description = data.get("description") or data.get("title") or ""

        target = data.get("target")

        parameters = data.get("parameters") or data.get("params") or {}

        if not parameters:

            parameters = {}

            if "args" in data:

                parameters["args"] = data["args"]

            if "kwargs" in data:

                parameters["kwargs"] = data["kwargs"]

        dependencies = (
            data.get("dependencies")
            or data.get("depends_on")
            or data.get("requires")
            or []
        )

        metadata = data.get("metadata") or {}

        return WorkflowStep(
            id=step_id,
            action=action,
            description=description,
            target=target,
            parameters=parameters,
            dependencies=dependencies,
            metadata=metadata,
            payload=raw_step,
        )

    @staticmethod
    def _object_to_dict(
        value: Any,
    ) -> Dict[str, Any]:

        if isinstance(
            value,
            dict,
        ):

            return dict(value)

        if value is None:

            return {}

        data: Dict[str, Any] = {}

        for attribute in (
            "id",
            "step_id",
            "task_id",
            "action",
            "name",
            "type",
            "command",
            "description",
            "title",
            "target",
            "parameters",
            "params",
            "args",
            "kwargs",
            "dependencies",
            "depends_on",
            "requires",
            "metadata",
        ):

            if hasattr(
                value,
                attribute,
            ):

                try:

                    data[attribute] = getattr(
                        value,
                        attribute,
                    )

                except Exception:

                    continue

        return data

    @staticmethod
    def _extract_metadata(
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        metadata = data.get("metadata", {})

        if isinstance(
            metadata,
            dict,
        ):

            return dict(metadata)

        return {}

    # ====================================================================
    # DEPENDENCY VALIDATION
    # ====================================================================

    @staticmethod
    def _validate_no_cycles(
        workflow: Workflow,
    ) -> None:

        graph = {step.id: list(step.dependencies) for step in workflow.steps}

        visiting: Set[str] = set()
        visited: Set[str] = set()

        def visit(
            step_id: str,
        ) -> None:

            if step_id in visited:

                return

            if step_id in visiting:

                raise ValueError(
                    "Circular workflow dependency " f"detected involving '{step_id}'."
                )

            visiting.add(step_id)

            for dependency in graph.get(
                step_id,
                [],
            ):

                visit(dependency)

            visiting.remove(step_id)

            visited.add(step_id)

        for step_id in graph:

            visit(step_id)

    @staticmethod
    def _dependencies_completed(
        workflow: Workflow,
        step: WorkflowStep,
    ) -> bool:

        for dependency_id in step.dependencies:

            dependency = workflow.get_step(dependency_id)

            if dependency is None:

                return False

            if dependency.status != (WorkflowStepStatus.COMPLETED):

                return False

        return True

    @staticmethod
    def _dependencies_failed(
        workflow: Workflow,
        step: WorkflowStep,
    ) -> bool:

        for dependency_id in step.dependencies:

            dependency = workflow.get_step(dependency_id)

            if dependency is None:

                return True

            if dependency.status in (
                WorkflowStepStatus.FAILED,
                WorkflowStepStatus.BLOCKED,
                WorkflowStepStatus.CANCELLED,
            ):

                return True

        return False

    # ====================================================================
    # STATUS MANAGEMENT
    # ====================================================================

    @staticmethod
    def _refresh_workflow_status(
        workflow: Workflow,
    ) -> None:

        statuses = [step.status for step in workflow.steps]

        if not statuses:

            workflow.status = WorkflowStatus.COMPLETED

            return

        if any(status == WorkflowStepStatus.FAILED for status in statuses):

            workflow.status = WorkflowStatus.FAILED

            return

        if all(
            status
            in (
                WorkflowStepStatus.COMPLETED,
                WorkflowStepStatus.SKIPPED,
            )
            for status in statuses
        ):

            workflow.status = WorkflowStatus.COMPLETED

            return

        if any(status == WorkflowStepStatus.RUNNING for status in statuses):

            workflow.status = WorkflowStatus.RUNNING

            return

        workflow.status = WorkflowStatus.READY

    @staticmethod
    def _require_step(
        workflow: Workflow,
        step_id: str,
    ) -> WorkflowStep:

        step = workflow.get_step(step_id)

        if step is None:

            raise KeyError(f"Workflow step not found: " f"{step_id}")

        return step

    def _generate_workflow_id(
        self,
    ) -> str:

        self._workflow_counter += 1

        return f"workflow_" f"{self._workflow_counter}"


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "WorkflowStatus",
    "WorkflowStepStatus",
    "WorkflowStep",
    "Workflow",
    "WorkflowPlanner",
]
