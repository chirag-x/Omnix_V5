"""
Omnix V5 Skill Context

Shared execution context passed to every skill.

Author: Chirag Sharma
Project: Omnix V5
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SkillContext:
    """
    Shared execution context.

    Every skill receives a SkillContext instance
    containing user request information, extracted
    entities, runtime state and access to Omnix
    services.
    """

    # ==================================================
    # User Request
    # ==================================================

    command: str

    parsed_goal: str = ""

    intent: str = ""

    confidence: float = 1.0

    language: str = "en"

    # ==================================================
    # NLP
    # ==================================================

    entities: dict[str, Any] = field(default_factory=dict)

    parameters: dict[str, Any] = field(default_factory=dict)

    variables: dict[str, Any] = field(default_factory=dict)

    # ==================================================
    # Session
    # ==================================================

    conversation_id: str = ""

    session_id: str = ""

    user_id: str = ""

    # ==================================================
    # Services
    # ==================================================

    planner: Any = None

    automation: Any = None

    browser: Any = None

    vision: Any = None

    input: Any = None

    memory: Any = None

    ai: Any = None

    system: Any = None

    skills: Any = None

    ui: Any = None

    logger: Any = None

    config: Any = None

    events: Any = None

    clipboard: Any = None

    files: Any = None

    network: Any = None

    notifications: Any = None

    # ==================================================
    # Runtime
    # ==================================================

    shared: dict[str, Any] = field(default_factory=dict)

    state: dict[str, Any] = field(default_factory=dict)

    metadata: dict[str, Any] = field(default_factory=dict)
    # ==================================================
    # Shared Data Helpers
    # ==================================================

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Get a shared runtime value.
        """
        return self.shared.get(
            key,
            default,
        )

    def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Store a shared runtime value.
        """
        self.shared[key] = value

    def has(
        self,
        key: str,
    ) -> bool:
        """
        Check if shared data exists.
        """
        return key in self.shared

    def remove(
        self,
        key: str,
    ) -> None:
        """
        Remove shared value.
        """
        self.shared.pop(
            key,
            None,
        )

    def clear_shared(
        self,
    ) -> None:
        """
        Clear shared runtime values.
        """
        self.shared.clear()

    def has_service(
        self,
        name: str,
    ) -> bool:

        return getattr(self, name, None) is not None

    # ==================================================
    # State Helpers
    # ==================================================

    def get_state(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self.state.get(
            key,
            default,
        )

    def set_state(
        self,
        key: str,
        value: Any,
    ) -> None:
        self.state[key] = value

    def has_state(
        self,
        key: str,
    ) -> bool:
        return key in self.state

    def clear_state(
        self,
    ) -> None:
        self.state.clear()

    # ==================================================
    # Metadata Helpers
    # ==================================================

    def get_metadata(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self.metadata.get(
            key,
            default,
        )

    def set_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:
        self.metadata[key] = value

    # ==================================================
    # Entity Helpers
    # ==================================================

    def entity(
        self,
        name: str,
        default=None,
    ):
        """
        Returns an extracted entity.

        Falls back to parameters and common aliases.
        """

        if name in self.entities:
            return self.entities[name]

        if name in self.parameters:
            return self.parameters[name]

        aliases = {
            "application": ["app"],
            "app": ["application"],
            "text": ["message", "content"],
            "query": ["search"],
            "key": ["keys"],
        }

        for alias in aliases.get(name, []):
            if alias in self.entities:
                return self.entities[alias]

            if alias in self.parameters:
                return self.parameters[alias]

        return default

    def require_entity(
        self,
        name: str,
    ) -> Any:
        value = self.entities.get(name)

        if value is None:
            raise ValueError(f"Missing required entity '{name}'.")

        return value

    # ==================================================
    # Parameter Helpers
    # ==================================================

    def parameter(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        return self.parameters.get(
            name,
            default,
        )

    def require_parameter(
        self,
        name: str,
    ) -> Any:
        value = self.parameters.get(name)

        if value is None:
            raise ValueError(f"Missing required parameter '{name}'.")

        return value

    # ==================================================
    # Logging
    # ==================================================

    def log_debug(
        self,
        message: str,
    ) -> None:
        if self.logger:
            self.logger.debug(message)

    def log_info(
        self,
        message: str,
    ) -> None:
        if self.logger:
            self.logger.info(message)

    def log_warning(
        self,
        message: str,
    ) -> None:
        if self.logger:
            self.logger.warning(message)

    def log_error(
        self,
        message: str,
    ) -> None:
        if self.logger:
            self.logger.error(message)

    def log_exception(
        self,
        exception: Exception,
    ) -> None:
        if self.logger:
            self.logger.exception(exception)

    # ==================================================
    # Utility
    # ==================================================

    def reset_runtime(self):

        self.shared.clear()

        self.state.clear()

        self.metadata.clear()

        self.entities.clear()

        self.parameters.clear()

        self.variables.clear()
