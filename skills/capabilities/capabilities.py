from enum import Enum


class SkillCapability(str, Enum):

    # =====================================
    # Applications
    # =====================================

    OPEN_APPLICATION = "open_application"

    CLOSE_APPLICATION = "close_application"

    SWITCH_APPLICATION = "switch_application"

    # =====================================
    # Browser
    # =====================================

    OPEN_BROWSER = "open_browser"

    SEARCH_WEB = "search_web"

    NAVIGATE = "navigate"

    CLICK_LINK = "click_link"

    # =====================================
    # Files
    # =====================================

    OPEN_FILE = "open_file"

    CREATE_FILE = "create_file"

    DELETE_FILE = "delete_file"

    SEARCH_FILE = "search_file"

    # =====================================
    # Input
    # =====================================

    CLICK = "click"

    DOUBLE_CLICK = "double_click"

    TYPE = "type"

    HOTKEY = "hotkey"

    DRAG = "drag"

    # =====================================
    # Vision
    # =====================================

    FIND_UI = "find_ui"

    OCR = "ocr"

    DETECT_OBJECT = "detect_object"

    WAIT_FOR_UI = "wait_for_ui"

    # =====================================
    # System
    # =====================================

    SHUTDOWN = "shutdown"

    RESTART = "restart"

    SYSTEM_INFO = "system_info"