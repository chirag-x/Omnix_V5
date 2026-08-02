"""
Omnix V5
Logger Utility

Central logging system.
"""

from __future__ import annotations

import logging

from pathlib import Path


from .constants import (
    LOG_FOLDER,
    DEFAULT_LOG_LEVEL,
)

# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

LOG_PATH = Path(LOG_FOLDER)

LOG_FILE = LOG_PATH / "omnix.log"


# ---------------------------------------------------------
# Logger Setup
# ---------------------------------------------------------


def setup_logger(
    name: str = "Omnix",
    level: str = DEFAULT_LOG_LEVEL,
) -> logging.Logger:
    """
    Create and configure logger.
    """

    logger = logging.getLogger(
        name,
    )

    if logger.handlers:

        return logger

    logger.setLevel(
        getattr(
            logging,
            level.upper(),
            logging.INFO,
        )
    )

    # Create folder

    LOG_PATH.mkdir(
        exist_ok=True,
    )

    # -----------------------------------------------------
    # Formatter
    # -----------------------------------------------------

    formatter = logging.Formatter(
        "%(asctime)s | " "%(levelname)s | " "%(name)s | " "%(message)s"
    )

    # -----------------------------------------------------
    # Console Handler
    # -----------------------------------------------------

    console = logging.StreamHandler()

    console.setFormatter(
        formatter,
    )

    logger.addHandler(
        console,
    )

    # -----------------------------------------------------
    # File Handler
    # -----------------------------------------------------

    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8",
    )

    file_handler.setFormatter(
        formatter,
    )

    logger.addHandler(
        file_handler,
    )

    return logger


# ---------------------------------------------------------
# Default Logger
# ---------------------------------------------------------

logger = setup_logger()


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------


def get_logger(
    name: str,
) -> logging.Logger:
    """
    Get subsystem logger.
    """

    return setup_logger(
        name,
    )
