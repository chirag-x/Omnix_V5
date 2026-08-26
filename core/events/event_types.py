"""
Omnix V5 - Event Types

Standard event definitions used across the Omnix V5 Core.

This module provides:
    - Event categories
    - Event priorities
    - Event data structure
    - Common Omnix event names
    - Safe serialization

The event system is intentionally independent from the EventBus so that
all V5 subsystems and legacy components can create and consume events
without circular dependencies.
"""

from __future__ import annotations

import time
import uuid

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

# ============================================================================
# EVENT CATEGORY
# ============================================================================


class EventCategory(str, Enum):
    """
    High-level categories for Omnix events.
    """

    SYSTEM = "system"

    ENGINE = "engine"

    SERVICE = "service"

    STATE = "state"

    COMMAND = "command"

    PLANNING = "planning"

    TASK = "task"

    AGENT = "agent"

    SKILL = "skill"

    VISION = "vision"

    MEMORY = "memory"

    AI = "ai"

    VOICE = "voice"

    UI = "ui"

    AUTOMATION = "automation"

    ERROR = "error"

    HEALTH = "health"

    CUSTOM = "custom"


# ============================================================================
# EVENT PRIORITY
# ============================================================================


class EventPriority(str, Enum):
    """
    Processing importance of an event.
    """

    LOW = "low"

    NORMAL = "normal"

    HIGH = "high"

    CRITICAL = "critical"


# ============================================================================
# COMMON EVENT TYPES
# ============================================================================


class EventType(str, Enum):
    """
    Standard Omnix V5 event names.

    New subsystems can use these shared event names where appropriate.
    Custom events can still be emitted using plain strings.
    """

    # ------------------------------------------------------------------------
    # SYSTEM
    # ------------------------------------------------------------------------

    SYSTEM_STARTING = "system.starting"

    SYSTEM_STARTED = "system.started"

    SYSTEM_STOPPING = "system.stopping"

    SYSTEM_STOPPED = "system.stopped"

    SYSTEM_ERROR = "system.error"

    # ------------------------------------------------------------------------
    # ENGINE
    # ------------------------------------------------------------------------

    ENGINE_STARTING = "engine.starting"

    ENGINE_STARTED = "engine.started"

    ENGINE_STOPPING = "engine.stopping"

    ENGINE_STOPPED = "engine.stopped"

    ENGINE_ERROR = "engine.error"

    # ------------------------------------------------------------------------
    # SERVICE
    # ------------------------------------------------------------------------

    SERVICE_REGISTERED = "service.registered"

    SERVICE_STARTING = "service.starting"

    SERVICE_READY = "service.ready"

    SERVICE_DEGRADED = "service.degraded"

    SERVICE_STOPPING = "service.stopping"

    SERVICE_STOPPED = "service.stopped"

    SERVICE_ERROR = "service.error"

    # ------------------------------------------------------------------------
    # COMMAND
    # ------------------------------------------------------------------------

    COMMAND_RECEIVED = "command.received"

    COMMAND_PROCESSING = "command.processing"

    COMMAND_COMPLETED = "command.completed"

    COMMAND_FAILED = "command.failed"

    # ------------------------------------------------------------------------
    # PLANNING
    # ------------------------------------------------------------------------

    PLAN_CREATED = "plan.created"

    PLAN_STARTED = "plan.started"

    PLAN_UPDATED = "plan.updated"

    PLAN_COMPLETED = "plan.completed"

    PLAN_FAILED = "plan.failed"

    # ------------------------------------------------------------------------
    # TASK
    # ------------------------------------------------------------------------

    TASK_CREATED = "task.created"

    TASK_STARTED = "task.started"

    TASK_PROGRESS = "task.progress"

    TASK_COMPLETED = "task.completed"

    TASK_FAILED = "task.failed"

    TASK_CANCELLED = "task.cancelled"

    # ------------------------------------------------------------------------
    # AGENT
    # ------------------------------------------------------------------------

    AGENT_STARTED = "agent.started"

    AGENT_OBSERVATION = "agent.observation"

    AGENT_STEP_STARTED = "agent.step.started"

    AGENT_STEP_COMPLETED = "agent.step.completed"

    AGENT_RECOVERY = "agent.recovery"

    AGENT_COMPLETED = "agent.completed"

    AGENT_FAILED = "agent.failed"

    # ------------------------------------------------------------------------
    # SKILLS
    # ------------------------------------------------------------------------

    SKILL_REQUESTED = "skill.requested"

    SKILL_STARTED = "skill.started"

    SKILL_COMPLETED = "skill.completed"

    SKILL_FAILED = "skill.failed"

    # ------------------------------------------------------------------------
    # VISION
    # ------------------------------------------------------------------------

    VISION_STARTED = "vision.started"

    VISION_ANALYSIS_STARTED = "vision.analysis.started"

    VISION_ANALYSIS_COMPLETED = "vision.analysis.completed"

    VISION_TARGET_FOUND = "vision.target.found"

    VISION_ERROR = "vision.error"

    # ------------------------------------------------------------------------
    # MEMORY
    # ------------------------------------------------------------------------

    MEMORY_RETRIEVED = "memory.retrieved"

    MEMORY_STORED = "memory.stored"

    MEMORY_ERROR = "memory.error"

    # ------------------------------------------------------------------------
    # AI
    # ------------------------------------------------------------------------

    AI_REQUESTED = "ai.requested"

    AI_RESPONSE = "ai.response"

    AI_ERROR = "ai.error"

    # ------------------------------------------------------------------------
    # VOICE
    # ------------------------------------------------------------------------

    VOICE_INPUT = "voice.input"

    VOICE_OUTPUT = "voice.output"

    VOICE_ERROR = "voice.error"

    # ------------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------------

    UI_ACTION = "ui.action"

    UI_UPDATED = "ui.updated"

    UI_ERROR = "ui.error"

    # ------------------------------------------------------------------------
    # AUTOMATION
    # ------------------------------------------------------------------------

    AUTOMATION_STARTED = "automation.started"

    AUTOMATION_COMPLETED = "automation.completed"

    AUTOMATION_FAILED = "automation.failed"

    # ------------------------------------------------------------------------
    # HEALTH
    # ------------------------------------------------------------------------

    HEALTH_CHECK = "health.check"

    HEALTH_CHANGED = "health.changed"

    COMPONENT_DEGRADED = "component.degraded"

    COMPONENT_RECOVERED = "component.recovered"

    # ------------------------------------------------------------------------
    # ERROR
    # ------------------------------------------------------------------------

    ERROR_OCCURRED = "error.occurred"


# ============================================================================
# OMNIX EVENT
# ============================================================================


@dataclass
class OmnixEvent:
    """
    Standard event object used throughout Omnix V5.

    Example:

        event = OmnixEvent(
            event_type=EventType.SKILL_STARTED,
            source="skills_service",
            data={
                "skill": "browser"
            },
        )
    """

    event_type: EventType | str

    source: str = "unknown"

    data: Dict[str, Any] = field(default_factory=dict)

    category: Optional[EventCategory | str] = None

    priority: EventPriority | str = EventPriority.NORMAL

    event_id: str = field(default_factory=lambda: (f"event_{uuid.uuid4().hex}"))

    timestamp: float = field(default_factory=time.time)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(
        self,
    ) -> None:
        """
        Normalize event fields after creation.
        """

        self.event_type = self._normalize_event_type(self.event_type)

        self.source = self._normalize_source(self.source)

        self.category = self._normalize_category(self.category)

        self.priority = self._normalize_priority(self.priority)

        if not isinstance(
            self.data,
            dict,
        ):

            raise TypeError("Event data must be a dictionary.")

        if not isinstance(
            self.metadata,
            dict,
        ):

            raise TypeError("Event metadata must be a dictionary.")

        self.data = dict(self.data)

        self.metadata = dict(self.metadata)

    # ========================================================================
    # SERIALIZATION
    # ========================================================================

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Return a serializable event dictionary.
        """

        return {
            "event_id": self.event_id,
            "event_type": (self.event_type),
            "source": self.source,
            "category": (
                self.category.value
                if isinstance(
                    self.category,
                    EventCategory,
                )
                else self.category
            ),
            "priority": (
                self.priority.value
                if isinstance(
                    self.priority,
                    EventPriority,
                )
                else self.priority
            ),
            "timestamp": self.timestamp,
            "data": dict(self.data),
            "metadata": dict(self.metadata),
        }

    # ========================================================================
    # HELPERS
    # ========================================================================

    @property
    def name(
        self,
    ) -> str:
        """
        Return the normalized event name.
        """

        return self.event_type

    @property
    def is_critical(
        self,
    ) -> bool:
        """
        Return True for critical events.
        """

        return self.priority == EventPriority.CRITICAL

    @property
    def is_high_priority(
        self,
    ) -> bool:
        """
        Return True for high or critical events.
        """

        return self.priority in {
            EventPriority.HIGH,
            EventPriority.CRITICAL,
        }

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Get a value from event data.
        """

        return self.data.get(
            key,
            default,
        )

    # ========================================================================
    # INTERNAL NORMALIZATION
    # ========================================================================

    @staticmethod
    def _normalize_event_type(
        event_type: EventType | str,
    ) -> str:
        """
        Convert an EventType or string into a normalized event name.
        """

        if isinstance(
            event_type,
            EventType,
        ):

            return event_type.value

        value = str(event_type).strip()

        if not value:

            raise ValueError("Event type cannot be empty.")

        return value

    @staticmethod
    def _normalize_source(
        source: Any,
    ) -> str:
        """
        Normalize event source.
        """

        value = str(source).strip()

        if not value:

            return "unknown"

        return value

    @staticmethod
    def _normalize_category(
        category: Optional[EventCategory | str],
    ) -> Optional[EventCategory]:
        """
        Normalize the event category.
        """

        if category is None:

            return None

        if isinstance(
            category,
            EventCategory,
        ):

            return category

        try:

            return EventCategory(str(category).strip().lower())

        except ValueError:

            return EventCategory.CUSTOM

    @staticmethod
    def _normalize_priority(
        priority: EventPriority | str,
    ) -> EventPriority:
        """
        Normalize event priority.
        """

        if isinstance(
            priority,
            EventPriority,
        ):

            return priority

        try:

            return EventPriority(str(priority).strip().lower())

        except ValueError as error:

            valid = ", ".join(item.value for item in EventPriority)

            raise ValueError(
                f"Invalid event priority: " f"{priority!r}. " f"Valid values: {valid}"
            ) from error


# ============================================================================
# CONVENIENCE FACTORY
# ============================================================================


def create_event(
    event_type: EventType | str,
    *,
    source: str = "unknown",
    data: Optional[Dict[str, Any]] = None,
    category: Optional[EventCategory | str] = None,
    priority: EventPriority | str = (EventPriority.NORMAL),
    metadata: Optional[Dict[str, Any]] = None,
) -> OmnixEvent:
    """
    Create a standard Omnix event.
    """

    return OmnixEvent(
        event_type=event_type,
        source=source,
        data=dict(data or {}),
        category=category,
        priority=priority,
        metadata=dict(metadata or {}),
    )


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "EventCategory",
    "EventPriority",
    "EventType",
    "OmnixEvent",
    "create_event",
]
