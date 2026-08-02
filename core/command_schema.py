"""
Omnix V5 Structured Command

Represents a parsed user command before planning.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class StructuredCommand:
    """
    Standard command representation used throughout Omnix.

    Flow:

    Voice/Text
            ↓
    IntentClassifier
            ↓
    CommandProcessor
            ↓
    StructuredCommand
            ↓
    Planner
    """

    # ==========================================================
    # Original Input
    # ==========================================================

    original_text: str = ""

    normalized_text: str = ""

    language: str = "en"

    # ==========================================================
    # Intent
    # ==========================================================

    intent: str = "automation"

    action: str | None = None

    confidence: float = 1.0

    # ==========================================================
    # Target
    # ==========================================================

    target: str | None = None

    target_type: str | None = None

    application: str | None = None

    platform: str | None = None

    recipient: str | None = None

    # ==========================================================
    # Content
    # ==========================================================

    query: str | None = None

    text: str | None = None

    # ==========================================================
    # Extracted Information
    # ==========================================================

    entities: dict[str, Any] = field(default_factory=dict)

    parameters: dict[str, Any] = field(default_factory=dict)

    arguments: dict[str, Any] = field(default_factory=dict)

    metadata: dict[str, Any] = field(default_factory=dict)

    # ==========================================================
    # Planner
    # ==========================================================

    goal_type: str | None = None

    priority: int = 0

    requires_confirmation: bool = False

    multi_step: bool = False

    # ==========================================================
    # Runtime
    # ==========================================================

    timestamp: datetime = field(default_factory=datetime.utcnow)
    # ==========================================================
    # Intent Helpers
    # ==========================================================

    @property
    def is_automation(self) -> bool:
        """
        Returns True if this command represents
        a desktop automation request.
        """
        return self.intent == "automation"

    @property
    def is_chat(self) -> bool:
        """
        Returns True if this command represents
        a conversational request.
        """
        return self.intent == "chat"

    # ==========================================================
    # Entity Helpers
    # ==========================================================

    def set_entity(
        self,
        name: str,
        value: Any,
    ) -> None:

        self.entities[name] = value

    def get_entity(
        self,
        name: str,
        default: Any = None,
    ) -> Any:

        return self.entities.get(
            name,
            default,
        )

    def has_entity(
        self,
        name: str,
    ) -> bool:

        return name in self.entities

    # ==========================================================
    # Parameter Helpers
    # ==========================================================

    def set_parameter(
        self,
        name: str,
        value: Any,
    ) -> None:

        self.parameters[name] = value

    def get_parameter(
        self,
        name: str,
        default: Any = None,
    ) -> Any:

        return self.parameters.get(
            name,
            default,
        )

    def has_parameter(
        self,
        name: str,
    ) -> bool:

        return name in self.parameters

    # ==========================================================
    # Metadata Helpers
    # ==========================================================

    def set_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:

        self.metadata[key] = value

    def get_metadata(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        return self.metadata.get(
            key,
            default,
        )

    # ==========================================================
    # Validation
    # ==========================================================

    def is_valid(self) -> bool:
        """
        Basic validation before sending the command
        to the Planner.
        """

        if not self.intent:
            return False

        if self.is_automation and not self.action:
            return False

        return True

    # ==========================================================
    # Serialization
    # ==========================================================

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the command into a serializable dictionary.
        """

        return {
            "original_text": self.original_text,
            "normalized_text": self.normalized_text,
            "language": self.language,
            "intent": self.intent,
            "action": self.action,
            "confidence": self.confidence,
            "target": self.target,
            "target_type": self.target_type,
            "application": self.application,
            "platform": self.platform,
            "recipient": self.recipient,
            "query": self.query,
            "text": self.text,
            "entities": self.entities,
            "parameters": self.parameters,
            "arguments": self.arguments,
            "metadata": self.metadata,
            "goal_type": self.goal_type,
            "priority": self.priority,
            "requires_confirmation": self.requires_confirmation,
            "multi_step": self.multi_step,
            "timestamp": self.timestamp.isoformat(),
        }

    # ==========================================================
    # Debug
    # ==========================================================

    def __str__(
        self,
    ) -> str:

        return (
            f"StructuredCommand("
            f"intent={self.intent}, "
            f"action={self.action}, "
            f"target={self.target}, "
            f"application={self.application}, "
            f"confidence={self.confidence:.2f})"
        )
