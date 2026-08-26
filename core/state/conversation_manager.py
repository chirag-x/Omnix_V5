"""
Omnix V5 - Conversation Manager

Thread-safe management of the active Omnix conversation.

This module manages short-term conversation state only.

It does NOT replace:
    - Long-term memory
    - Persistent memory storage
    - AI model history management
    - Context retrieval systems

The ConversationManager provides a stable, lightweight API that can be
used by both legacy Omnix components and new V5 subsystems.

Typical flow:

    conversation = ConversationManager()

    conversation.start()

    conversation.add_user_message(
        "Open Chrome"
    )

    conversation.add_assistant_message(
        "Opening Chrome."
    )

    recent = conversation.get_messages()

The engine or context subsystem can later transform these messages into
the format required by an LLM or another subsystem.
"""

from __future__ import annotations

import threading
import time
import uuid

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

# ============================================================================
# MESSAGE ROLE
# ============================================================================


class MessageRole(str, Enum):
    """
    Supported conversation message roles.
    """

    SYSTEM = "system"

    USER = "user"

    ASSISTANT = "assistant"

    TOOL = "tool"


# ============================================================================
# CONVERSATION MESSAGE
# ============================================================================


@dataclass
class ConversationMessage:
    """
    Represents a single conversation message.
    """

    message_id: str

    role: MessageRole

    content: str

    created_at: float = field(default_factory=time.time)

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Return a serializable message.
        """

        return {
            "message_id": self.message_id,
            "role": self.role.value,
            "content": self.content,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


# ============================================================================
# CONVERSATION SNAPSHOT
# ============================================================================


@dataclass
class ConversationSnapshot:
    """
    Safe snapshot of the active conversation.
    """

    conversation_id: str

    created_at: float

    updated_at: float

    messages: List[ConversationMessage] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def message_count(
        self,
    ) -> int:
        """
        Return total number of messages.
        """

        return len(self.messages)

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Return a serializable conversation snapshot.
        """

        return {
            "conversation_id": (self.conversation_id),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message_count": (self.message_count),
            "messages": [message.to_dict() for message in self.messages],
            "metadata": dict(self.metadata),
        }


# ============================================================================
# CONVERSATION MANAGER
# ============================================================================


class ConversationManager:
    """
    Thread-safe manager for Omnix short-term conversation history.

    The manager intentionally has no dependency on the AI, Memory,
    Vision, Skill, Agent, or Context subsystems.

    This prevents circular dependencies and allows OmnixEngine to decide
    how conversation history should be shared between subsystems.

    Args:
        conversation_id:
            Optional ID for the initial conversation.

        max_messages:
            Maximum number of messages retained in memory.

    Example:

        manager = ConversationManager(
            max_messages=100
        )

        manager.add_user_message(
            "Open Chrome"
        )

        manager.add_assistant_message(
            "Opening Chrome."
        )
    """

    def __init__(
        self,
        conversation_id: Optional[str] = None,
        *,
        max_messages: int = 200,
    ) -> None:

        if max_messages < 1:

            raise ValueError("max_messages must be " "at least 1.")

        self._conversation_id = (
            self._normalize_conversation_id(conversation_id)
            if conversation_id
            else self._generate_conversation_id()
        )

        self._max_messages = int(max_messages)

        now = time.time()

        self._created_at = now

        self._updated_at = now

        self._messages: List[ConversationMessage] = []

        self._metadata: Dict[str, Any] = {}

        self._lock = threading.RLock()

    # ========================================================================
    # CONVERSATION LIFECYCLE
    # ========================================================================

    def start_new_conversation(
        self,
        *,
        conversation_id: Optional[str] = None,
        clear_metadata: bool = False,
    ) -> str:
        """
        Start a completely new conversation.

        The previous conversation history is cleared.

        Returns:
            The new conversation ID.
        """

        with self._lock:

            self._conversation_id = (
                self._normalize_conversation_id(conversation_id)
                if conversation_id
                else (self._generate_conversation_id())
            )

            now = time.time()

            self._created_at = now

            self._updated_at = now

            self._messages.clear()

            if clear_metadata:

                self._metadata.clear()

            return self._conversation_id

    def clear(
        self,
        *,
        keep_metadata: bool = True,
    ) -> None:
        """
        Clear conversation messages.

        The conversation ID remains unchanged.
        """

        with self._lock:

            self._messages.clear()

            if not keep_metadata:

                self._metadata.clear()

            self._touch()

    def reset(
        self,
    ) -> str:
        """
        Reset the manager with a new conversation.
        """

        return self.start_new_conversation(clear_metadata=True)

    # ========================================================================
    # ADD MESSAGES
    # ========================================================================

    def add_message(
        self,
        role: MessageRole | str,
        content: Any,
        *,
        metadata: Optional[Dict[str, Any]] = None,
        message_id: Optional[str] = None,
    ) -> ConversationMessage:
        """
        Add a message to the active conversation.

        Returns a safe copy of the stored message.
        """

        normalized_role = self._normalize_role(role)

        normalized_content = self._normalize_content(content)

        normalized_id = (
            self._normalize_message_id(message_id)
            if message_id
            else self._generate_message_id()
        )

        message = ConversationMessage(
            message_id=normalized_id,
            role=normalized_role,
            content=normalized_content,
            metadata=dict(metadata or {}),
        )

        with self._lock:

            self._messages.append(message)

            self._trim_messages()

            self._touch()

            return self._copy_message(message)

    def add_user_message(
        self,
        content: Any,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationMessage:
        """
        Add a user message.
        """

        return self.add_message(
            MessageRole.USER,
            content,
            metadata=metadata,
        )

    def add_assistant_message(
        self,
        content: Any,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationMessage:
        """
        Add an assistant message.
        """

        return self.add_message(
            MessageRole.ASSISTANT,
            content,
            metadata=metadata,
        )

    def add_system_message(
        self,
        content: Any,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationMessage:
        """
        Add a system message.
        """

        return self.add_message(
            MessageRole.SYSTEM,
            content,
            metadata=metadata,
        )

    def add_tool_message(
        self,
        content: Any,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationMessage:
        """
        Add a tool or skill message.
        """

        return self.add_message(
            MessageRole.TOOL,
            content,
            metadata=metadata,
        )

    # ========================================================================
    # MESSAGE LOOKUP
    # ========================================================================

    def get_messages(
        self,
        *,
        limit: Optional[int] = None,
        roles: Optional[Sequence[MessageRole | str]] = None,
    ) -> List[ConversationMessage]:
        """
        Return conversation messages.

        Args:
            limit:
                Optional maximum number of most recent messages.

            roles:
                Optional roles to include.
        """

        with self._lock:

            messages = list(self._messages)

        if roles is not None:

            normalized_roles = {self._normalize_role(role) for role in roles}

            messages = [
                message for message in messages if message.role in normalized_roles
            ]

        if limit is not None:

            if limit < 1:

                return []

            messages = messages[-int(limit) :]

        return [self._copy_message(message) for message in messages]

    def get_last_message(
        self,
        role: Optional[MessageRole | str] = None,
    ) -> Optional[ConversationMessage]:
        """
        Return the most recent message.

        Optionally filter by role.
        """

        normalized_role = self._normalize_role(role) if role is not None else None

        with self._lock:

            for message in reversed(self._messages):

                if normalized_role is None or message.role == normalized_role:

                    return self._copy_message(message)

        return None

    def get_message(
        self,
        message_id: str,
    ) -> Optional[ConversationMessage]:
        """
        Return a message by ID.
        """

        message_id = self._normalize_message_id(message_id)

        with self._lock:

            for message in self._messages:

                if message.message_id == message_id:

                    return self._copy_message(message)

        return None

    def remove_message(
        self,
        message_id: str,
    ) -> bool:
        """
        Remove a message by ID.

        Returns True when a message was removed.
        """

        message_id = self._normalize_message_id(message_id)

        with self._lock:

            for index, message in enumerate(self._messages):

                if message.message_id == message_id:

                    del self._messages[index]

                    self._touch()

                    return True

        return False

    # ========================================================================
    # LEGACY / LLM COMPATIBILITY
    # ========================================================================

    def as_messages(
        self,
        *,
        limit: Optional[int] = None,
        include_metadata: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Return messages in a simple LLM-friendly format.

        Example:

            [
                {
                    "role": "user",
                    "content": "Open Chrome"
                },
                {
                    "role": "assistant",
                    "content": "Opening Chrome."
                }
            ]

        This format is intentionally simple so the Brain or Context
        subsystem can adapt it to any model provider.
        """

        messages = self.get_messages(limit=limit)

        result: List[Dict[str, Any]] = []

        for message in messages:

            item: Dict[str, Any] = {
                "role": (message.role.value),
                "content": (message.content),
            }

            if include_metadata:

                item["message_id"] = message.message_id

                item["created_at"] = message.created_at

                item["metadata"] = dict(message.metadata)

            result.append(item)

        return result

    def history(
        self,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Legacy-friendly alias for as_messages().
        """

        return self.as_messages(limit=limit)

    # ========================================================================
    # METADATA
    # ========================================================================

    def set_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Store conversation metadata.
        """

        key = self._normalize_key(key)

        with self._lock:

            self._metadata[key] = value

            self._touch()

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

        with self._lock:

            for key, value in values.items():

                normalized_key = self._normalize_key(key)

                self._metadata[normalized_key] = value

            self._touch()

    def get_metadata(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Get conversation metadata.
        """

        key = self._normalize_key(key)

        with self._lock:

            return self._metadata.get(
                key,
                default,
            )

    def remove_metadata(
        self,
        key: str,
    ) -> bool:
        """
        Remove conversation metadata.
        """

        key = self._normalize_key(key)

        with self._lock:

            if key not in self._metadata:

                return False

            del self._metadata[key]

            self._touch()

            return True

    def clear_metadata(
        self,
    ) -> None:
        """
        Remove all conversation metadata.
        """

        with self._lock:

            self._metadata.clear()

            self._touch()

    # ========================================================================
    # SNAPSHOT
    # ========================================================================

    def snapshot(
        self,
    ) -> ConversationSnapshot:
        """
        Return a safe snapshot of the conversation.
        """

        with self._lock:

            return ConversationSnapshot(
                conversation_id=(self._conversation_id),
                created_at=(self._created_at),
                updated_at=(self._updated_at),
                messages=[self._copy_message(message) for message in self._messages],
                metadata=dict(self._metadata),
            )

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Return the complete conversation as a dictionary.
        """

        return self.snapshot().to_dict()

    # ========================================================================
    # PROPERTIES
    # ========================================================================

    @property
    def conversation_id(
        self,
    ) -> str:

        with self._lock:

            return self._conversation_id

    @property
    def created_at(
        self,
    ) -> float:

        with self._lock:

            return self._created_at

    @property
    def updated_at(
        self,
    ) -> float:

        with self._lock:

            return self._updated_at

    @property
    def message_count(
        self,
    ) -> int:

        with self._lock:

            return len(self._messages)

    @property
    def max_messages(
        self,
    ) -> int:

        return self._max_messages

    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================

    def _trim_messages(
        self,
    ) -> None:
        """
        Keep only the configured maximum number of messages.
        """

        overflow = len(self._messages) - self._max_messages

        if overflow > 0:

            del self._messages[:overflow]

    def _touch(
        self,
    ) -> None:
        """
        Update conversation modification time.
        """

        self._updated_at = time.time()

    @staticmethod
    def _copy_message(
        message: ConversationMessage,
    ) -> ConversationMessage:
        """
        Return a safe copy of a message.
        """

        return ConversationMessage(
            message_id=(message.message_id),
            role=message.role,
            content=message.content,
            created_at=(message.created_at),
            metadata=dict(message.metadata),
        )

    @staticmethod
    def _generate_conversation_id() -> str:
        """
        Generate a unique conversation ID.
        """

        return f"conversation_" f"{uuid.uuid4().hex}"

    @staticmethod
    def _generate_message_id() -> str:
        """
        Generate a unique message ID.
        """

        return f"message_" f"{uuid.uuid4().hex}"

    @staticmethod
    def _normalize_role(
        role: MessageRole | str,
    ) -> MessageRole:
        """
        Convert a role into MessageRole.
        """

        if isinstance(
            role,
            MessageRole,
        ):

            return role

        try:

            return MessageRole(str(role).strip().lower())

        except ValueError as error:

            valid_roles = ", ".join(item.value for item in MessageRole)

            raise ValueError(
                f"Invalid message role: "
                f"{role!r}. "
                f"Valid roles: "
                f"{valid_roles}"
            ) from error

    @staticmethod
    def _normalize_content(
        content: Any,
    ) -> str:
        """
        Normalize message content.
        """

        value = str(content).strip()

        if not value:

            raise ValueError("Message content " "cannot be empty.")

        return value

    @staticmethod
    def _normalize_conversation_id(
        conversation_id: Any,
    ) -> str:
        """
        Validate a conversation ID.
        """

        value = str(conversation_id).strip()

        if not value:

            raise ValueError("Conversation ID " "cannot be empty.")

        return value

    @staticmethod
    def _normalize_message_id(
        message_id: Any,
    ) -> str:
        """
        Validate a message ID.
        """

        value = str(message_id).strip()

        if not value:

            raise ValueError("Message ID cannot be empty.")

        return value

    @staticmethod
    def _normalize_key(
        key: Any,
    ) -> str:
        """
        Validate metadata keys.
        """

        value = str(key).strip()

        if not value:

            raise ValueError("Metadata key " "cannot be empty.")

        return value


# ============================================================================
# GLOBAL CONVERSATION MANAGER
# ============================================================================


_default_conversation_manager = ConversationManager()


def get_conversation_manager() -> ConversationManager:
    """
    Return the shared Omnix conversation manager.
    """

    return _default_conversation_manager


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "MessageRole",
    "ConversationMessage",
    "ConversationSnapshot",
    "ConversationManager",
    "get_conversation_manager",
]
