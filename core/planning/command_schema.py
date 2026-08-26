"""
Omnix V5 - Command Schema

Standard command models used throughout the Omnix V5 planning system.

This module provides a stable representation of a command as it moves
through the Omnix pipeline:

    Raw Input
        ↓
    Command
        ↓
    Intent Classification
        ↓
    Target Resolution
        ↓
    Planning
        ↓
    Execution

The schema is intentionally independent from AI, Skills, Vision, and
Agent implementations so that both V5 and legacy components can use it.
"""

from __future__ import annotations

import time
import uuid

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# ============================================================================
# COMMAND STATUS
# ============================================================================


class CommandStatus(str, Enum):
    """
    Current processing status of an Omnix command.
    """

    RECEIVED = "received"

    PROCESSING = "processing"

    CLASSIFIED = "classified"

    RESOLVED = "resolved"

    PLANNED = "planned"

    EXECUTING = "executing"

    COMPLETED = "completed"

    FAILED = "failed"

    CANCELLED = "cancelled"


# ============================================================================
# COMMAND TYPE
# ============================================================================


class CommandType(str, Enum):
    """
    High-level type of command handled by the Omnix planning system.

    This represents the broad processing category, while ``intent``
    on the Command object can hold a more specific intent.
    """

    USER = "user"

    AUTOMATION = "automation"

    CHAT = "chat"

    SYSTEM = "system"

    AGENT = "agent"

    UNKNOWN = "unknown"


# ============================================================================
# COMMAND SOURCE
# ============================================================================


class CommandSource(str, Enum):
    """
    Source from which a command entered Omnix.
    """

    USER = "user"

    VOICE = "voice"

    UI = "ui"

    API = "api"

    SYSTEM = "system"

    AGENT = "agent"

    AUTOMATION = "automation"

    LEGACY = "legacy"


# ============================================================================
# COMMAND PRIORITY
# ============================================================================


class CommandPriority(str, Enum):
    """
    Execution importance of a command.
    """

    LOW = "low"

    NORMAL = "normal"

    HIGH = "high"

    CRITICAL = "critical"


# ============================================================================
# COMMAND
# ============================================================================


@dataclass
class Command:
    """
    Standard Omnix command.

    This object represents a user or system request while it moves
    through the V5 planning and execution pipeline.

    Example:

        command = Command(
            text="Open Chrome and search AI agents",
            source=CommandSource.USER,
        )
    """

    text: str

    source: CommandSource | str = CommandSource.USER

    command_id: str = field(default_factory=lambda: (f"command_{uuid.uuid4().hex}"))

    status: CommandStatus | str = CommandStatus.RECEIVED

    priority: CommandPriority | str = CommandPriority.NORMAL

    intent: Optional[str] = None

    target: Optional[str] = None

    entities: Dict[str, Any] = field(default_factory=dict)

    parameters: Dict[str, Any] = field(default_factory=dict)

    metadata: Dict[str, Any] = field(default_factory=dict)

    created_at: float = field(default_factory=time.time)

    updated_at: float = field(default_factory=time.time)

    def __post_init__(
        self,
    ) -> None:
        """
        Normalize and validate command data.
        """

        self.text = self._normalize_text(self.text)

        self.source = self._normalize_source(self.source)

        self.status = self._normalize_status(self.status)

        self.priority = self._normalize_priority(self.priority)

        self.command_id = self._normalize_command_id(self.command_id)

        if not isinstance(
            self.entities,
            dict,
        ):

            raise TypeError("entities must be a dictionary.")

        if not isinstance(
            self.parameters,
            dict,
        ):

            raise TypeError("parameters must be a dictionary.")

        if not isinstance(
            self.metadata,
            dict,
        ):

            raise TypeError("metadata must be a dictionary.")

        self.entities = dict(self.entities)

        self.parameters = dict(self.parameters)

        self.metadata = dict(self.metadata)

    # ====================================================================
    # STATUS
    # ====================================================================

    def set_status(
        self,
        status: CommandStatus | str,
    ) -> None:
        """
        Update the command processing status.
        """

        self.status = self._normalize_status(status)

        self._touch()

    def mark_processing(
        self,
    ) -> None:

        self.set_status(CommandStatus.PROCESSING)

    def mark_classified(
        self,
    ) -> None:

        self.set_status(CommandStatus.CLASSIFIED)

    def mark_resolved(
        self,
    ) -> None:

        self.set_status(CommandStatus.RESOLVED)

    def mark_planned(
        self,
    ) -> None:

        self.set_status(CommandStatus.PLANNED)

    def mark_executing(
        self,
    ) -> None:

        self.set_status(CommandStatus.EXECUTING)

    def mark_completed(
        self,
    ) -> None:

        self.set_status(CommandStatus.COMPLETED)

    def mark_failed(
        self,
    ) -> None:

        self.set_status(CommandStatus.FAILED)

    def mark_cancelled(
        self,
    ) -> None:

        self.set_status(CommandStatus.CANCELLED)

    # ====================================================================
    # INTENT AND TARGET
    # ====================================================================

    def set_intent(
        self,
        intent: Optional[str],
    ) -> None:
        """
        Set the classified command intent.
        """

        self.intent = self._normalize_optional_string(intent)

        self._touch()

    def set_target(
        self,
        target: Optional[str],
    ) -> None:
        """
        Set the resolved command target.
        """

        self.target = self._normalize_optional_string(target)

        self._touch()

    # ====================================================================
    # ENTITIES
    # ====================================================================

    def set_entity(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Store an extracted command entity.
        """

        key = self._normalize_key(
            key,
            "Entity key",
        )

        self.entities[key] = value

        self._touch()

    def get_entity(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Retrieve an extracted entity.
        """

        return self.entities.get(
            key,
            default,
        )

    def remove_entity(
        self,
        key: str,
    ) -> bool:
        """
        Remove an entity.

        Returns True if removed.
        """

        if key not in self.entities:

            return False

        del self.entities[key]

        self._touch()

        return True

    # ====================================================================
    # PARAMETERS
    # ====================================================================

    def set_parameter(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Store a command parameter.
        """

        key = self._normalize_key(
            key,
            "Parameter key",
        )

        self.parameters[key] = value

        self._touch()

    def get_parameter(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Retrieve a command parameter.
        """

        return self.parameters.get(
            key,
            default,
        )

    def remove_parameter(
        self,
        key: str,
    ) -> bool:
        """
        Remove a parameter.

        Returns True if removed.
        """

        if key not in self.parameters:

            return False

        del self.parameters[key]

        self._touch()

        return True

    # ====================================================================
    # METADATA
    # ====================================================================

    def set_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Store command metadata.
        """

        key = self._normalize_key(
            key,
            "Metadata key",
        )

        self.metadata[key] = value

        self._touch()

    def get_metadata(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Retrieve command metadata.
        """

        return self.metadata.get(
            key,
            default,
        )

    def update_metadata(
        self,
        values: Dict[str, Any],
    ) -> None:
        """
        Update multiple metadata values.
        """

        if not isinstance(
            values,
            dict,
        ):

            raise TypeError("values must be a dictionary.")

        self.metadata.update(values)

        self._touch()

    # ====================================================================
    # SERIALIZATION
    # ====================================================================

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Convert the command into a serializable dictionary.
        """

        return {
            "command_id": (self.command_id),
            "text": self.text,
            "source": (self.source.value),
            "status": (self.status.value),
            "priority": (self.priority.value),
            "intent": self.intent,
            "target": self.target,
            "entities": dict(self.entities),
            "parameters": dict(self.parameters),
            "metadata": dict(self.metadata),
            "created_at": (self.created_at),
            "updated_at": (self.updated_at),
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ) -> "Command":
        """
        Create a Command from serialized data.
        """

        if not isinstance(
            data,
            dict,
        ):

            raise TypeError("data must be a dictionary.")

        return cls(
            text=data.get(
                "text",
                "",
            ),
            source=data.get(
                "source",
                CommandSource.USER,
            ),
            command_id=data.get(
                "command_id",
                (f"command_" f"{uuid.uuid4().hex}"),
            ),
            status=data.get(
                "status",
                CommandStatus.RECEIVED,
            ),
            priority=data.get(
                "priority",
                CommandPriority.NORMAL,
            ),
            intent=data.get("intent"),
            target=data.get("target"),
            entities=dict(
                data.get(
                    "entities",
                    {},
                )
            ),
            parameters=dict(
                data.get(
                    "parameters",
                    {},
                )
            ),
            metadata=dict(
                data.get(
                    "metadata",
                    {},
                )
            ),
            created_at=float(
                data.get(
                    "created_at",
                    time.time(),
                )
            ),
            updated_at=float(
                data.get(
                    "updated_at",
                    time.time(),
                )
            ),
        )

    # ====================================================================
    # CONVENIENCE
    # ====================================================================

    @property
    def is_finished(
        self,
    ) -> bool:
        """
        Return True when processing has ended.
        """

        return self.status in {
            CommandStatus.COMPLETED,
            CommandStatus.FAILED,
            CommandStatus.CANCELLED,
        }

    @property
    def is_successful(
        self,
    ) -> bool:
        """
        Return True when the command completed successfully.
        """

        return self.status == CommandStatus.COMPLETED

    @property
    def is_failed(
        self,
    ) -> bool:
        """
        Return True when the command failed.
        """

        return self.status == CommandStatus.FAILED

    def _touch(
        self,
    ) -> None:
        """
        Update the modification timestamp.
        """

        self.updated_at = time.time()

    # ====================================================================
    # NORMALIZATION
    # ====================================================================

    @staticmethod
    def _normalize_text(
        text: Any,
    ) -> str:
        """
        Validate command text.
        """

        value = str(text).strip()

        if not value:

            raise ValueError("Command text cannot be empty.")

        return value

    @staticmethod
    def _normalize_command_id(
        command_id: Any,
    ) -> str:
        """
        Validate command ID.
        """

        value = str(command_id).strip()

        if not value:

            raise ValueError("Command ID cannot be empty.")

        return value

    @staticmethod
    def _normalize_source(
        source: CommandSource | str,
    ) -> CommandSource:
        """
        Normalize command source.
        """

        if isinstance(
            source,
            CommandSource,
        ):

            return source

        try:

            return CommandSource(str(source).strip().lower())

        except ValueError as error:

            valid = ", ".join(item.value for item in CommandSource)

            raise ValueError(
                f"Invalid command source: " f"{source!r}. " f"Valid values: {valid}"
            ) from error

    @staticmethod
    def _normalize_status(
        status: CommandStatus | str,
    ) -> CommandStatus:
        """
        Normalize command status.
        """

        if isinstance(
            status,
            CommandStatus,
        ):

            return status

        try:

            return CommandStatus(str(status).strip().lower())

        except ValueError as error:

            valid = ", ".join(item.value for item in CommandStatus)

            raise ValueError(
                f"Invalid command status: " f"{status!r}. " f"Valid values: {valid}"
            ) from error

    @staticmethod
    def _normalize_priority(
        priority: CommandPriority | str,
    ) -> CommandPriority:
        """
        Normalize command priority.
        """

        if isinstance(
            priority,
            CommandPriority,
        ):

            return priority

        try:

            return CommandPriority(str(priority).strip().lower())

        except ValueError as error:

            valid = ", ".join(item.value for item in CommandPriority)

            raise ValueError(
                f"Invalid command priority: " f"{priority!r}. " f"Valid values: {valid}"
            ) from error

    @staticmethod
    def _normalize_optional_string(
        value: Optional[Any],
    ) -> Optional[str]:
        """
        Normalize an optional string.
        """

        if value is None:

            return None

        result = str(value).strip()

        return result or None

    @staticmethod
    def _normalize_key(
        key: Any,
        name: str,
    ) -> str:
        """
        Validate dictionary keys.
        """

        value = str(key).strip()

        if not value:

            raise ValueError(f"{name} cannot be empty.")

        return value


# ============================================================================
# CONVENIENCE FACTORY
# ============================================================================


def create_command(
    text: Any,
    *,
    source: CommandSource | str = (CommandSource.USER),
    priority: CommandPriority | str = (CommandPriority.NORMAL),
    metadata: Optional[Dict[str, Any]] = None,
) -> Command:
    """
    Create a new Omnix command.
    """

    return Command(
        text=text,
        source=source,
        priority=priority,
        metadata=dict(metadata or {}),
    )


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "Command",
    "CommandStatus",
    "CommandType",
    "CommandSource",
    "CommandPriority",
    "create_command",
]
