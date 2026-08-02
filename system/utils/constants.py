"""
Omnix V5
Constants

Global fixed values.
"""

from __future__ import annotations

# ---------------------------------------------------------
# Application
# ---------------------------------------------------------

OMNIX_NAME = "Omnix"

OMNIX_VERSION = "V5"


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

SYSTEM_FOLDER = "system"

CONFIG_FOLDER = "config"

LOG_FOLDER = "logs"

MEMORY_FOLDER = "memory"

ASSETS_FOLDER = "assets"


# ---------------------------------------------------------
# Default Timeouts
# ---------------------------------------------------------

DEFAULT_TIMEOUT = 5.0

UI_WAIT_TIMEOUT = 5.0

PROCESS_TIMEOUT = 10.0

NETWORK_TIMEOUT = 15.0


# ---------------------------------------------------------
# Limits
# ---------------------------------------------------------

MAX_MEMORY_ENTRIES = 1000

MAX_HISTORY_ENTRIES = 500

MAX_LOG_SIZE_MB = 50


# ---------------------------------------------------------
# Automation
# ---------------------------------------------------------

MAX_AUTOMATION_STEPS = 100

DEFAULT_RETRY_COUNT = 3


# ---------------------------------------------------------
# Vision
# ---------------------------------------------------------

DEFAULT_CONFIDENCE = 0.5

VISION_INTERVAL = 0.5


# ---------------------------------------------------------
# System States
# ---------------------------------------------------------

STATE_INITIALIZING = "initializing"

STATE_RUNNING = "running"

STATE_STOPPING = "stopping"

STATE_STOPPED = "stopped"

STATE_ERROR = "error"


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

DEFAULT_LOG_LEVEL = "INFO"


# ---------------------------------------------------------
# Supported Actions
# ---------------------------------------------------------

ACTION_CLICK = "click"

ACTION_TYPE = "type"

ACTION_OPEN = "open"

ACTION_CLOSE = "close"

ACTION_SEARCH = "search"
