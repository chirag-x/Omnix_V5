"""
Omnix V5
Automation Interface

Defines automation system contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class AutomationInterface(ABC):
    """
    Interface for automation operations.
    """

    # ---------------------------------------------------------
    # Execute Task
    # ---------------------------------------------------------

    @abstractmethod
    def execute(
        self,
        task: str,
    ) -> bool:
        """
        Execute automation task.
        """

        pass

    # ---------------------------------------------------------
    # Create Plan
    # ---------------------------------------------------------

    @abstractmethod
    def create_plan(
        self,
        goal: str,
    ) -> dict:
        """
        Create execution plan.
        """

        pass

    # ---------------------------------------------------------
    # Run Workflow
    # ---------------------------------------------------------

    @abstractmethod
    def run_workflow(
        self,
        workflow: dict,
    ) -> bool:
        """
        Execute workflow steps.
        """

        pass

    # ---------------------------------------------------------
    # Status
    # ---------------------------------------------------------

    @abstractmethod
    def status(
        self,
    ) -> dict:
        """
        Return automation status.
        """

        pass

    # ---------------------------------------------------------
    # Cancel
    # ---------------------------------------------------------

    @abstractmethod
    def cancel(
        self,
        task_id: str,
    ) -> bool:
        """
        Cancel running automation.
        """

        pass
