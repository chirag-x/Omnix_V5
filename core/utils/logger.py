"""
Omnix V5 - Core Logging Utility

Central logging utilities for the Omnix V5 Core.

This module provides:
    - Consistent logger creation
    - Console logging
    - Optional file logging
    - Duplicate handler prevention
    - Log level management
    - Exception logging
    - Backward-friendly helper functions

This module intentionally uses Python's built-in logging system so it
can work cleanly with both new V5 modules and older Omnix components.
"""

from __future__ import annotations

import logging
import sys
import threading

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Union

# ============================================================================
# CONSTANTS
# ============================================================================


DEFAULT_LOGGER_NAME = "omnix"

DEFAULT_LOG_LEVEL = logging.INFO

DEFAULT_FORMAT = "%(asctime)s | " "%(levelname)-8s | " "%(name)s | " "%(message)s"

DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass(frozen=True)
class LoggerConfig:
    """
    Configuration used to set up an Omnix logger.
    """

    name: str = DEFAULT_LOGGER_NAME

    level: int = DEFAULT_LOG_LEVEL

    console: bool = True

    file_path: Optional[Path] = None

    format_string: str = DEFAULT_FORMAT

    date_format: str = DEFAULT_DATE_FORMAT

    propagate: bool = False


# ============================================================================
# LOGGER MANAGER
# ============================================================================


class LoggerManager:
    """
    Central manager for Core logging.

    The manager keeps track of configured loggers so repeated calls do
    not accidentally add duplicate console or file handlers.
    """

    _lock = threading.RLock()

    _configured_loggers: Dict[
        str,
        logging.Logger,
    ] = {}

    @classmethod
    def configure(
        cls,
        name: str = DEFAULT_LOGGER_NAME,
        *,
        level: Union[int, str] = DEFAULT_LOG_LEVEL,
        console: bool = True,
        file_path: Optional[Union[str, Path]] = None,
        format_string: str = DEFAULT_FORMAT,
        date_format: str = DEFAULT_DATE_FORMAT,
        propagate: bool = False,
        force: bool = False,
    ) -> logging.Logger:
        """
        Configure and return a logger.

        Parameters
        ----------
        name:
            Logger name.

        level:
            Logging level as an integer or string such as:
            "DEBUG", "INFO", "WARNING", "ERROR".

        console:
            Enable console output.

        file_path:
            Optional path for file logging.

        force:
            If True, existing Omnix-managed handlers for this logger are
            removed before applying the new configuration.
        """

        normalized_name = cls._normalize_name(name)

        resolved_level = cls._resolve_level(level)

        resolved_file_path = Path(file_path) if file_path is not None else None

        with cls._lock:

            logger = logging.getLogger(normalized_name)

            logger.setLevel(resolved_level)

            logger.propagate = bool(propagate)

            if force:

                cls._remove_managed_handlers(logger)

            formatter = logging.Formatter(
                fmt=format_string,
                datefmt=date_format,
            )

            if console:

                cls._ensure_console_handler(
                    logger,
                    formatter,
                )

            if resolved_file_path is not None:

                cls._ensure_file_handler(
                    logger,
                    resolved_file_path,
                    formatter,
                )

            cls._configured_loggers[normalized_name] = logger

            return logger

    @classmethod
    def get(
        cls,
        name: str = DEFAULT_LOGGER_NAME,
        *,
        level: Optional[Union[int, str]] = None,
    ) -> logging.Logger:
        """
        Get an Omnix logger.

        If the logger has not been configured yet, it receives a safe
        default configuration with console logging enabled.
        """

        normalized_name = cls._normalize_name(name)

        with cls._lock:

            logger = cls._configured_loggers.get(normalized_name)

            if logger is None:

                logger = cls.configure(normalized_name)

            if level is not None:

                logger.setLevel(cls._resolve_level(level))

            return logger

    @classmethod
    def set_level(
        cls,
        level: Union[int, str],
        name: Optional[str] = None,
    ) -> None:
        """
        Set the level for one logger or all managed Omnix loggers.
        """

        resolved_level = cls._resolve_level(level)

        with cls._lock:

            if name is not None:

                logger = cls.get(name)

                logger.setLevel(resolved_level)

                return

            for logger in cls._configured_loggers.values():

                logger.setLevel(resolved_level)

    @classmethod
    def shutdown(
        cls,
        name: Optional[str] = None,
    ) -> None:
        """
        Close and remove Omnix-managed handlers.

        If no name is provided, all managed loggers are shut down.
        """

        with cls._lock:

            if name is not None:

                normalized_name = cls._normalize_name(name)

                logger = cls._configured_loggers.pop(
                    normalized_name,
                    None,
                )

                if logger is not None:

                    cls._remove_managed_handlers(logger)

                return

            logger_names = list(cls._configured_loggers.keys())

            for logger_name in logger_names:

                logger = cls._configured_loggers.pop(
                    logger_name,
                    None,
                )

                if logger is not None:

                    cls._remove_managed_handlers(logger)

    @classmethod
    def is_configured(
        cls,
        name: str = DEFAULT_LOGGER_NAME,
    ) -> bool:
        """
        Return True if the logger is managed by LoggerManager.
        """

        normalized_name = cls._normalize_name(name)

        with cls._lock:

            return normalized_name in cls._configured_loggers

    @classmethod
    def configured_names(
        cls,
    ) -> list[str]:
        """
        Return names of configured Omnix loggers.
        """

        with cls._lock:

            return sorted(cls._configured_loggers.keys())

    # ========================================================================
    # INTERNAL HANDLER MANAGEMENT
    # ========================================================================

    @staticmethod
    def _ensure_console_handler(
        logger: logging.Logger,
        formatter: logging.Formatter,
    ) -> None:
        """
        Add one managed console handler if needed.
        """

        for handler in logger.handlers:

            if getattr(
                handler,
                "_omnix_console_handler",
                False,
            ):

                handler.setFormatter(formatter)

                return

        handler = logging.StreamHandler(stream=sys.stdout)

        handler._omnix_console_handler = True

        handler.setFormatter(formatter)

        logger.addHandler(handler)

    @staticmethod
    def _ensure_file_handler(
        logger: logging.Logger,
        file_path: Path,
        formatter: logging.Formatter,
    ) -> None:
        """
        Add one managed file handler for the requested path.
        """

        file_path = file_path.expanduser()

        try:

            file_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        except Exception as exc:

            raise RuntimeError(
                f"Unable to create log directory " f"'{file_path.parent}': {exc}"
            ) from exc

        resolved_path = str(file_path.resolve())

        for handler in logger.handlers:

            if not getattr(
                handler,
                "_omnix_file_handler",
                False,
            ):

                continue

            existing_path = getattr(
                handler,
                "_omnix_file_path",
                None,
            )

            if existing_path == resolved_path:

                handler.setFormatter(formatter)

                return

        handler = logging.FileHandler(
            filename=file_path,
            encoding="utf-8",
        )

        handler._omnix_file_handler = True

        handler._omnix_file_path = resolved_path

        handler.setFormatter(formatter)

        logger.addHandler(handler)

    @staticmethod
    def _remove_managed_handlers(
        logger: logging.Logger,
    ) -> None:
        """
        Remove only handlers created by LoggerManager.

        Existing handlers created by other parts of Omnix or third-party
        libraries are left untouched.
        """

        handlers = list(logger.handlers)

        for handler in handlers:

            is_managed = getattr(
                handler,
                "_omnix_console_handler",
                False,
            ) or getattr(
                handler,
                "_omnix_file_handler",
                False,
            )

            if not is_managed:

                continue

            logger.removeHandler(handler)

            try:

                handler.close()

            except Exception:

                pass

    # ========================================================================
    # NORMALIZATION
    # ========================================================================

    @staticmethod
    def _normalize_name(
        name: str,
    ) -> str:
        """
        Normalize logger names.
        """

        if not isinstance(
            name,
            str,
        ):

            raise TypeError("Logger name must be a string.")

        name = name.strip()

        if not name:

            return DEFAULT_LOGGER_NAME

        return name

    @staticmethod
    def _resolve_level(
        level: Union[int, str],
    ) -> int:
        """
        Convert a numeric or textual logging level into its integer value.
        """

        if isinstance(
            level,
            int,
        ):

            return level

        if isinstance(
            level,
            str,
        ):

            normalized = level.strip().upper()

            value = logging.getLevelName(normalized)

            if isinstance(
                value,
                int,
            ):

                return value

        raise ValueError(f"Invalid logging level: {level!r}")


# ============================================================================
# PUBLIC HELPERS
# ============================================================================


def configure_logger(
    name: str = DEFAULT_LOGGER_NAME,
    **kwargs,
) -> logging.Logger:
    """
    Configure and return an Omnix logger.

    Example:

        logger = configure_logger(
            "omnix.vision",
            level="DEBUG",
        )
    """

    return LoggerManager.configure(
        name,
        **kwargs,
    )


def get_logger(
    name: str = DEFAULT_LOGGER_NAME,
    *,
    level: Optional[Union[int, str]] = None,
) -> logging.Logger:
    """
    Get a configured Omnix logger.

    This is the recommended function for most Core modules.
    """

    return LoggerManager.get(
        name,
        level=level,
    )


def set_log_level(
    level: Union[int, str],
    name: Optional[str] = None,
) -> None:
    """
    Change logging level.

    If name is None, all Omnix-managed loggers are updated.
    """

    LoggerManager.set_level(
        level,
        name,
    )


def shutdown_logging(
    name: Optional[str] = None,
) -> None:
    """
    Shut down one or all Omnix-managed loggers.
    """

    LoggerManager.shutdown(name)


# ============================================================================
# MODULE EXPORTS
# ============================================================================


__all__ = [
    "DEFAULT_DATE_FORMAT",
    "DEFAULT_FORMAT",
    "DEFAULT_LOGGER_NAME",
    "DEFAULT_LOG_LEVEL",
    "LoggerConfig",
    "LoggerManager",
    "configure_logger",
    "get_logger",
    "set_log_level",
    "shutdown_logging",
]
