"""
Omnix V5
Power State Model
"""

from enum import Enum


class PowerAction(Enum):
    """
    Available system power actions.
    """

    SHUTDOWN = "shutdown"

    RESTART = "restart"

    SLEEP = "sleep"

    HIBERNATE = "hibernate"

    LOCK = "lock"

    LOGOFF = "logoff"


class PowerStatus(Enum):
    """
    Current power status.
    """

    AVAILABLE = "available"

    EXECUTING = "executing"

    FAILED = "failed"