"""
Omnix V5
Recycle Bin

Safe deletion using the operating system recycle bin.
"""

from __future__ import annotations

import logging
from pathlib import Path

from send2trash import send2trash

from .path_resolver import PathResolver

logger = logging.getLogger(__name__)


class RecycleBin:
    """
    Safe delete operations.
    """

    def __init__(self) -> None:

        self._resolver = PathResolver()

    # ---------------------------------------------------------
    # Delete
    # ---------------------------------------------------------

    def send(
        self,
        path: str | Path,
    ) -> bool:
        """
        Move a file or folder to the recycle bin.
        """

        path = self._resolver.resolve(path)

        if not path.exists():

            return False

        send2trash(path)

        logger.info(
            "Moved to recycle bin: %s",
            path,
        )

        return True

    # ---------------------------------------------------------
    # Multiple
    # ---------------------------------------------------------

    def send_many(
        self,
        paths: list[str | Path],
    ) -> int:
        """
        Move multiple items to the recycle bin.

        Returns the number of successfully
        deleted items.
        """

        deleted = 0

        for item in paths:

            if self.send(item):

                deleted += 1

        return deleted

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def exists(
        self,
        path: str | Path,
    ) -> bool:

        return self._resolver.exists(path)

    # ---------------------------------------------------------
    # Permanent Delete
    # ---------------------------------------------------------

    def permanent_delete(
        self,
        path: str | Path,
    ) -> bool:
        """
        Permanently delete a file or folder.

        Use with caution.
        """

        path = self._resolver.resolve(path)

        if not path.exists():

            return False

        if path.is_file():

            path.unlink()

        else:

            import shutil

            shutil.rmtree(path)

        logger.warning(
            "Permanently deleted: %s",
            path,
        )

        return True

    # ---------------------------------------------------------
    # Safe Delete
    # ---------------------------------------------------------

    def delete_if_exists(
        self,
        path: str | Path,
    ) -> bool:
        """
        Send to recycle bin only if the path exists.
        """

        if not self.exists(path):

            return False

        return self.send(path)

    # ---------------------------------------------------------
    # Batch Delete
    # ---------------------------------------------------------

    def delete_directory_contents(
        self,
        directory: str | Path,
    ) -> int:
        """
        Move every item inside a directory
        to the recycle bin.

        Returns the number of deleted items.
        """

        directory = self._resolver.resolve(directory)

        if not directory.is_dir():

            return 0

        deleted = 0

        for item in directory.iterdir():

            if self.send(item):

                deleted += 1

        logger.info(
            "Moved %d item(s) from %s to recycle bin.",
            deleted,
            directory,
        )

        return deleted

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:
        """
        Basic recycle bin capabilities.
        """

        return {
            "supports_restore": False,
            "supports_listing": False,
            "supports_safe_delete": True,
            "supports_permanent_delete": True,
        }

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def empty(
        self,
        directory: str | Path,
    ) -> int:
        """
        Alias for delete_directory_contents().
        """

        return self.delete_directory_contents(
            directory,
        )

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return "RecycleBin()"
