"""
Omnix V5
Services Package

Low-level OS service controllers.
"""

from .app_controller import AppController
from .process_controller import ProcessController
from .window_controller import WindowController
from .file_controller import FileController

from .keyboard_controller import KeyboardController
from .mouse_controller import MouseController
from .clipboard_controller import ClipboardController

from .display_controller import DisplayController
from .resource_controller import ResourceController
from .power_controller import PowerController
from .ui_controller import UIController

__all__ = [
    # Applications
    "AppController",
    # Processes
    "ProcessController",
    # Windows
    "WindowController",
    # Filesystem
    "FileController",
    # Input
    "KeyboardController",
    "MouseController",
    "ClipboardController",
    # System
    "DisplayController",
    "ResourceController",
    "PowerController",
    # UI
    "UIController",
]
