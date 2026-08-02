"""
Omnix V5
Interfaces Package

Abstract contracts for
Omnix subsystems.
"""

from .app_interface import (
    AppInterface,
)

from .automation_interface import (
    AutomationInterface,
)

from .file_interface import (
    FileInterface,
)

from .input_interface import (
    InputInterface,
)

from .process_interface import (
    ProcessInterface,
)

from .ui_interface import (
    UIInterface,
)

from .window_interface import (
    WindowInterface,
)

__all__ = [
    "AppInterface",
    "AutomationInterface",
    "FileInterface",
    "InputInterface",
    "ProcessInterface",
    "UIInterface",
    "WindowInterface",
]
