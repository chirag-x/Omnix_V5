"""
Omnix V5 - Session State

Thread-safe state management for the current Omnix session.

A session represents one logical period of Omnix usage, typically from
engine startup until shutdown or an explicit session reset.

This module intentionally stores only session-level state. It does not
own conversation history, runtime execution flags, or persistent memory.

Responsibilities:
    - Session identity
    - Session lifecycle
    - Command/activity counters
    - Success/failure tracking
    - Session metadata
    - Activity timestamps
    - Safe snapshots

Designed to work with both legacy Omnix components and the new V5
architecture without creating dependencies on higher-level subsystems.
"""

from __future__ import annotations

import threading
import time
import uuid

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

# ============================================================================
# SESSION STATUS
# ============================================================================


class SessionStatus(str, Enum):
    """
    Lifecycle status of an Omnix session.
    """

    NEW = "new"

    ACTIVE = "active"

    PAUSED = "paused"

    ENDED = "ended"


# ============================================================================
# SESSION SNAPSHOT
# ============================================================================


@dataclass
class SessionSnapshot:
    """
    Safe snapshot of the current session state.
    """

    session_id: str

    status: SessionStatus

    started_at: Optional[float]

    ended_at: Optional[float]

    last_activity_at: Optional[float]

    command_count: int

    successful_operations: int

    failed_operations: int

    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """
        Return True when the session is active.
        """

        return self.status == SessionStatus.ACTIVE

    @property
    def duration_seconds(self) -> float:
        """
        Return the total session duration.
        """

        if self.started_at is None:

            return 0.0

        end_time = self.ended_at if self.ended_at is not None else time.time()

        return max(0.0, end_time - self.started_at)

    @property
    def total_operations(self) -> int:
        """
        Return total completed operations.
        """

        return self.successful_operations + self.failed_operations

    @property
    def success_rate(self) -> float:
        """
        Return operation success rate.

        Returns a value between 0.0 and 1.0.
        """

        total = self.total_operations

        if total == 0:

            return 0.0

        return self.successful_operations / total

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Return a serializable session snapshot.
        """

        return {
            "session_id": self.session_id,
            "status": self.status.value,
            "is_active": self.is_active,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "last_activity_at": (self.last_activity_at),
            "duration_seconds": (self.duration_seconds),
            "command_count": (self.command_count),
            "successful_operations": (self.successful_operations),
            "failed_operations": (self.failed_operations),
            "total_operations": (self.total_operations),
            "success_rate": (self.success_rate),
            "metadata": dict(self.metadata),
        }


# ============================================================================
# SESSION STATE
# ============================================================================


class SessionState:
    """
    Thread-safe manager for the current Omnix session.

    Example:

        session = SessionState()

        session.start()

        session.record_command()

        try:
            execute_operation()
            session.record_success()

        except Exception:
            session.record_failure()
            raise

        snapshot = session.snapshot()

        session.end()

    A new session can be started after ending the previous one:

        session.start(new_session=True)
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
    ) -> None:

        self._session_id = (
            self._normalize_session_id(session_id)
            if session_id
            else self._generate_session_id()
        )

        self._status = SessionStatus.NEW

        self._started_at: Optional[float] = None

        self._ended_at: Optional[float] = None

        self._last_activity_at: Optional[float] = None

        self._command_count = 0

        self._successful_operations = 0

        self._failed_operations = 0

        self._metadata: Dict[str, Any] = {}

        self._lock = threading.RLock()

    # ========================================================================
    # LIFECYCLE
    # ========================================================================

    def start(
        self,
        *,
        new_session: bool = False,
    ) -> str:
        """
        Start or resume the session.

        Args:
            new_session:
                If True, create a completely new session ID and reset
                all counters and timestamps.

        Returns:
            The active session ID.
        """

        with self._lock:

            if new_session:

                self._create_new_session()

            if self._status == SessionStatus.ENDED:

                self._create_new_session()

            if self._status == SessionStatus.NEW:

                now = time.time()

                self._started_at = now

                self._last_activity_at = now

            self._ended_at = None

            self._status = SessionStatus.ACTIVE

            self._touch()

            return self._session_id

    def pause(
        self,
    ) -> None:
        """
        Pause the current session.
        """

        with self._lock:

            if self._status != SessionStatus.ACTIVE:

                return

            self._status = SessionStatus.PAUSED

            self._touch()

    def resume(
        self,
    ) -> None:
        """
        Resume a paused session.
        """

        with self._lock:

            if self._status != SessionStatus.PAUSED:

                return

            self._status = SessionStatus.ACTIVE

            self._touch()

    def end(
        self,
    ) -> None:
        """
        End the current session.

        The session data remains available until a new session is
        explicitly started.
        """

        with self._lock:

            if self._status == SessionStatus.ENDED:

                return

            now = time.time()

            self._ended_at = now

            if self._started_at is None:

                self._started_at = now

            self._last_activity_at = now

            self._status = SessionStatus.ENDED

    def reset(
        self,
        *,
        new_session_id: bool = True,
        clear_metadata: bool = False,
    ) -> None:
        """
        Reset session state.

        Args:
            new_session_id:
                Generate a new session ID.

            clear_metadata:
                Remove session metadata.
        """

        with self._lock:

            if new_session_id:

                self._session_id = self._generate_session_id()

            self._status = SessionStatus.NEW

            self._started_at = None

            self._ended_at = None

            self._last_activity_at = None

            self._command_count = 0

            self._successful_operations = 0

            self._failed_operations = 0

            if clear_metadata:

                self._metadata.clear()

    # ========================================================================
    # ACTIVITY
    # ========================================================================

    def record_command(
        self,
        amount: int = 1,
    ) -> int:
        """
        Record one or more processed commands.

        Returns the updated command count.
        """

        amount = self._validate_amount(amount)

        with self._lock:

            self._ensure_active()

            self._command_count += amount

            self._touch()

            return self._command_count

    def record_success(
        self,
        amount: int = 1,
    ) -> int:
        """
        Record successful operation(s).

        Returns the updated success count.
        """

        amount = self._validate_amount(amount)

        with self._lock:

            self._ensure_active()

            self._successful_operations += amount

            self._touch()

            return self._successful_operations

    def record_failure(
        self,
        amount: int = 1,
    ) -> int:
        """
        Record failed operation(s).

        Returns the updated failure count.
        """

        amount = self._validate_amount(amount)

        with self._lock:

            self._ensure_active()

            self._failed_operations += amount

            self._touch()

            return self._failed_operations

    def touch(
        self,
    ) -> None:
        """
        Update the last activity timestamp.
        """

        with self._lock:

            self._touch()

    # ========================================================================
    # METADATA
    # ========================================================================

    def set_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Store session metadata.
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
        Get a metadata value.
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
        Remove metadata.

        Returns True when a value was removed.
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
        Remove all session metadata.
        """

        with self._lock:

            self._metadata.clear()

            self._touch()

    # ========================================================================
    # SNAPSHOT
    # ========================================================================

    def snapshot(
        self,
    ) -> SessionSnapshot:
        """
        Return a safe snapshot of the session.
        """

        with self._lock:

            return SessionSnapshot(
                session_id=(self._session_id),
                status=self._status,
                started_at=(self._started_at),
                ended_at=(self._ended_at),
                last_activity_at=(self._last_activity_at),
                command_count=(self._command_count),
                successful_operations=(self._successful_operations),
                failed_operations=(self._failed_operations),
                metadata=dict(self._metadata),
            )

    def to_dict(
        self,
    ) -> Dict[str, Any]:
        """
        Return the session state as a dictionary.
        """

        return self.snapshot().to_dict()

    # ========================================================================
    # PROPERTIES
    # ========================================================================

    @property
    def session_id(
        self,
    ) -> str:

        with self._lock:

            return self._session_id

    @property
    def status(
        self,
    ) -> SessionStatus:

        with self._lock:

            return self._status

    @property
    def is_active(
        self,
    ) -> bool:

        with self._lock:

            return self._status == SessionStatus.ACTIVE

    @property
    def started_at(
        self,
    ) -> Optional[float]:

        with self._lock:

            return self._started_at

    @property
    def ended_at(
        self,
    ) -> Optional[float]:

        with self._lock:

            return self._ended_at

    @property
    def last_activity_at(
        self,
    ) -> Optional[float]:

        with self._lock:

            return self._last_activity_at

    @property
    def command_count(
        self,
    ) -> int:

        with self._lock:

            return self._command_count

    @property
    def successful_operations(
        self,
    ) -> int:

        with self._lock:

            return self._successful_operations

    @property
    def failed_operations(
        self,
    ) -> int:

        with self._lock:

            return self._failed_operations

    @property
    def total_operations(
        self,
    ) -> int:

        with self._lock:

            return self._successful_operations + self._failed_operations

    @property
    def success_rate(
        self,
    ) -> float:

        with self._lock:

            total = self._successful_operations + self._failed_operations

            if total == 0:

                return 0.0

            return self._successful_operations / total

    @property
    def duration_seconds(
        self,
    ) -> float:

        with self._lock:

            if self._started_at is None:

                return 0.0

            end_time = self._ended_at if self._ended_at is not None else time.time()

            return max(0.0, end_time - self._started_at)

    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================

    def _ensure_active(
        self,
    ) -> None:
        """
        Ensure the session is active.

        For compatibility with legacy Omnix flows, activity can
        automatically start a new session when necessary.
        """

        if self._status == SessionStatus.NEW:

            self.start()

        elif self._status == SessionStatus.PAUSED:

            self._status = SessionStatus.ACTIVE

        elif self._status == SessionStatus.ENDED:

            self.start(new_session=True)

    def _create_new_session(
        self,
    ) -> None:
        """
        Create a new empty session.
        """

        self._session_id = self._generate_session_id()

        self._status = SessionStatus.NEW

        self._started_at = None

        self._ended_at = None

        self._last_activity_at = None

        self._command_count = 0

        self._successful_operations = 0

        self._failed_operations = 0

    def _touch(
        self,
    ) -> None:
        """
        Update the last activity timestamp.
        """

        self._last_activity_at = time.time()

    @staticmethod
    def _generate_session_id() -> str:
        """
        Generate a unique session identifier.
        """

        return f"session_{uuid.uuid4().hex}"

    @staticmethod
    def _normalize_session_id(
        session_id: Any,
    ) -> str:
        """
        Validate a session ID.
        """

        value = str(session_id).strip()

        if not value:

            raise ValueError("Session ID cannot be empty.")

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

            raise ValueError("Metadata key cannot be empty.")

        return value

    @staticmethod
    def _validate_amount(
        amount: Any,
    ) -> int:
        """
        Validate counter increments.
        """

        if isinstance(
            amount,
            bool,
        ):

            raise TypeError("amount must be an integer.")

        try:

            value = int(amount)

        except (
            TypeError,
            ValueError,
        ) as error:

            raise TypeError("amount must be an integer.") from error

        if value < 1:

            raise ValueError("amount must be at least 1.")

        return value


# ============================================================================
# GLOBAL SESSION STATE
# ============================================================================


_default_session_state = SessionState()


def get_session_state() -> SessionState:
    """
    Return the shared Omnix session state.
    """

    return _default_session_state


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "SessionStatus",
    "SessionSnapshot",
    "SessionState",
    "get_session_state",
]
