"""
Omnix V5
System Events

Common event models for the event subsystem.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class SystemEvent:
    """
    Base event for the Omnix event system.
    """

    name: str

    source: str

    data: dict[str, Any] = field(
        default_factory=dict,
    )

    timestamp: datetime = field(
        default_factory=datetime.utcnow,
    )


@dataclass(slots=True)
class WorkflowStartedEvent(SystemEvent):

    workflow_id: str = ""


@dataclass(slots=True)
class WorkflowCompletedEvent(SystemEvent):

    workflow_id: str = ""

    successful: bool = True


@dataclass(slots=True)
class ActionExecutedEvent(SystemEvent):

    action_type: str = ""


@dataclass(slots=True)
class ErrorEvent(SystemEvent):

    message: str = ""
