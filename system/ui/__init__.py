"""
Omnix V5
UI Package

UI detection,
verification,
automation,
and interaction system.
"""

from .ui_manager import UIManager

from .ui_locator import (
    UILocator,
    UIElement,
)

from .ocr_locator import (
    OCRLocator,
)

from .ui_verifier import (
    UIVerifier,
)

from .ui_waiter import (
    UIWaiter,
)

from .ui_actions import (
    UIActions,
)

from .smart_click import (
    SmartClick,
)

from .ui_navigation import (
    UINavigation,
)

from .accessibility import (
    AccessibilityManager,
    AccessibleElement,
)

__all__ = [
    # Main
    "UIManager",
    # Locator
    "UILocator",
    "UIElement",
    # OCR
    "OCRLocator",
    # Validation
    "UIVerifier",
    # Waiting
    "UIWaiter",
    # Actions
    "UIActions",
    # Smart interaction
    "SmartClick",
    # Navigation
    "UINavigation",
    # Accessibility
    "AccessibilityManager",
    "AccessibleElement",
]
