"""
Omnix V5 - State Package

Central exports for Omnix state management.

This package provides:
    - Runtime state
    - Session state
    - System/component state
    - Conversation state
"""

from .runtime_state import (
    RuntimeState,
    RuntimeSnapshot,
    RuntimeStatus,
    get_runtime_state,
)

from .session_state import (
    SessionState,
    SessionSnapshot,
    SessionStatus,
    get_session_state,
)

from .system_state import (
    SystemState,
    SystemSnapshot,
    ComponentState,
    ComponentStatus,
    get_system_state,
)

from .conversation_manager import (
    ConversationManager,
    ConversationSnapshot,
    ConversationMessage,
    MessageRole,
    get_conversation_manager,
)

__all__ = [
    # Runtime
    "RuntimeState",
    "RuntimeSnapshot",
    "RuntimeStatus",
    "get_runtime_state",
    # Session
    "SessionState",
    "SessionSnapshot",
    "SessionStatus",
    "get_session_state",
    # System
    "SystemState",
    "SystemSnapshot",
    "ComponentState",
    "ComponentStatus",
    "get_system_state",
    # Conversation
    "ConversationManager",
    "ConversationSnapshot",
    "ConversationMessage",
    "MessageRole",
    "get_conversation_manager",
]
