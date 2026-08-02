"""
Omnix V5
Utils Package

Shared utility functions and helpers.
"""

from .constants import *


from .logger import (
    setup_logger,
    get_logger,
)


from .path_utils import (
    PathManager,
)


from .permissions import (
    PermissionManager,
)


from .powershell import (
    PowerShellManager,
)


from .registry import (
    RegistryManager,
)


from .retry import (
    retry,
    execute_with_retry,
)


from .string_matching import (
    StringMatcher,
)


from .timers import (
    Timer,
    current_time,
    sleep,
)


from .validators import (
    is_valid_string,
    is_not_empty,
    is_number,
    in_range,
    valid_path,
    exists,
    has_keys,
    valid_email,
)


from .win32_utils import (
    Win32Utils,
)

__all__ = [
    # Logger
    "setup_logger",
    "get_logger",
    # Paths
    "PathManager",
    # Permissions
    "PermissionManager",
    # Windows
    "PowerShellManager",
    "RegistryManager",
    "Win32Utils",
    # Retry
    "retry",
    "execute_with_retry",
    # Matching
    "StringMatcher",
    # Timers
    "Timer",
    "current_time",
    "sleep",
    # Validators
    "is_valid_string",
    "is_not_empty",
    "is_number",
    "in_range",
    "valid_path",
    "exists",
    "has_keys",
    "valid_email",
]
