"""
Omnix V5
File Controller

Low-level filesystem operations.
"""

from __future__ import annotations

import logging
import shutil

from pathlib import Path

logger = logging.getLogger(__name__)


class FileController:
    """
    Direct operating system file operations.
    """

    def __init__(
        self,
    ) -> None:

        self._enabled = True

    # ---------------------------------------------------------
    # State
    # ---------------------------------------------------------

    @property
    def enabled(
        self,
    ) -> bool:

        return self._enabled

    def enable(
        self,
    ) -> None:

        self._enabled = True

    def disable(
        self,
    ) -> None:

        self._enabled = False

    # ---------------------------------------------------------
    # File Operations
    # ---------------------------------------------------------

    def create_file(
        self,
        path: str | Path,
    ) -> bool:

        try:

            Path(path).touch()

            return True

        except Exception as exc:

            logger.error(
                "Create file failed: %s",
                exc,
            )

            return False

    def create_folder(
        self,
        path: str | Path,
    ) -> bool:

        try:

            Path(path).mkdir(
                parents=True,
                exist_ok=True,
            )

            return True

        except Exception:

            return False

    def copy(
        self,
        source: str | Path,
        destination: str | Path,
    ) -> bool:

        try:

            shutil.copy2(
                source,
                destination,
            )

            return True

        except Exception:

            return False

    def move(
        self,
        source: str | Path,
        destination: str | Path,
    ) -> bool:

        try:

            shutil.move(
                source,
                destination,
            )

            return True

        except Exception:

            return False

    def delete(
        self,
        path: str | Path,
    ) -> bool:

        try:

            target = Path(path)

            if target.is_file():

                target.unlink()

            elif target.is_dir():

                shutil.rmtree(
                    target,
                )

            return True

        except Exception:

            return False

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    def exists(
        self,
        path: str | Path,
    ) -> bool:

        return Path(path).exists()

    def size(
        self,
        path: str | Path,
    ) -> int | None:

        try:

            return Path(path).stat().st_size

        except Exception:

            return None

    def metadata(
        self,
        path: str | Path,
    ) -> dict | None:

        try:

            info = Path(path).stat()

            return {
                "size": info.st_size,
                "created": info.st_ctime,
                "modified": info.st_mtime,
            }

        except Exception:

            return None

    # ---------------------------------------------------------
    # Diagnostics
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "enabled": self._enabled,
        }

    def __repr__(
        self,
    ) -> str:

        return "FileController(" f"enabled={self._enabled})"
