"""
Omnix V5 Built-in System Skills

Exports all system related skills.
"""

from .restart_skill import RestartSkill
from .shutdown_skill import ShutdownSkill
from .system_info_skill import SystemInfoSkill

from .lock_skill import LockSkill
from .sleep_skill import SleepSkill

__all__ = [
    "RestartSkill",
    "ShutdownSkill",
    "SystemInfoSkill",
    "LockSkill",
    "SleepSkill",
]
