"""
Omnix V5
Folder Operations

High-level directory manipulation.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from .path_resolver import PathResolver

logger = logging.getLogger(__name__)


class FolderOperations:
    """
    Directory manipulation utilities.
    """

    def __init__(self) -> None:

        self._resolver = PathResolver()

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------

    def create(
        self,
        path: str | Path,
        *,
        parents: bool = True,
        exist_ok: bool = True,
    ) -> Path:

        directory = self._resolver.resolve(path)

        directory.mkdir(
            parents=parents,
            exist_ok=exist_ok,
        )

        logger.info(
            "Created directory: %s",
            directory,
        )

        return directory

    # ---------------------------------------------------------
    # Copy
    # ---------------------------------------------------------

    def copy(
        self,
        source: str | Path,
        destination: str | Path,
        *,
        overwrite: bool = False,
    ) -> Path:

        source = self._resolver.resolve(source)
        destination = self._resolver.resolve(destination)

        if not source.is_dir():

            raise NotADirectoryError(source)

        if destination.exists():

            if not overwrite:

                raise FileExistsError(destination)

            shutil.rmtree(destination)

        shutil.copytree(
            source,
            destination,
        )

        logger.info(
            "Copied directory %s -> %s",
            source,
            destination,
        )

        return destination

    # ---------------------------------------------------------
    # Move
    # ---------------------------------------------------------

    def move(
        self,
        source: str | Path,
        destination: str | Path,
    ) -> Path:

        source = self._resolver.resolve(source)
        destination = self._resolver.resolve(destination)

        if not source.exists():

            raise FileNotFoundError(source)

        shutil.move(
            str(source),
            str(destination),
        )

        logger.info(
            "Moved directory %s -> %s",
            source,
            destination,
        )

        return destination

    # ---------------------------------------------------------
    # Rename
    # ---------------------------------------------------------

    def rename(
        self,
        path: str | Path,
        new_name: str,
    ) -> Path:

        path = self._resolver.resolve(path)

        if not path.exists():

            raise FileNotFoundError(path)

        destination = path.with_name(
            new_name,
        )

        path.rename(
            destination,
        )

        logger.info(
            "Renamed directory %s -> %s",
            path.name,
            destination.name,
        )

        return destination

    # ---------------------------------------------------------
    # Delete
    # ---------------------------------------------------------

    def delete(
        self,
        path: str | Path,
    ) -> bool:

        directory = self._resolver.resolve(path)

        if not directory.exists():

            return False

        shutil.rmtree(
            directory,
        )

        logger.info(
            "Deleted directory %s",
            directory,
        )

        return True

    # ---------------------------------------------------------
    # Empty
    # ---------------------------------------------------------

    def empty(
        self,
        path: str | Path,
    ) -> bool:
        """
        Remove all contents of a directory
        without deleting the directory itself.
        """

        directory = self._resolver.resolve(path)

        if not directory.is_dir():

            return False

        for item in directory.iterdir():

            try:

                if item.is_dir():

                    shutil.rmtree(item)

                else:

                    item.unlink()

            except Exception as e:

                logger.warning(
                    "Failed to remove %s: %s",
                    item,
                    e,
                )

        logger.info(
            "Emptied directory: %s",
            directory,
        )

        return True

    # ---------------------------------------------------------
    # Listing
    # ---------------------------------------------------------

    def list(
        self,
        path: str | Path,
    ) -> list[Path]:

        directory = self._resolver.resolve(path)

        if not directory.is_dir():

            return []

        return list(directory.iterdir())

    def files(
        self,
        path: str | Path,
    ) -> list[Path]:

        return [item for item in self.list(path) if item.is_file()]

    def folders(
        self,
        path: str | Path,
    ) -> list[Path]:

        return [item for item in self.list(path) if item.is_dir()]

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    def exists(
        self,
        path: str | Path,
    ) -> bool:

        return self._resolver.is_directory(
            path,
        )

    def count_files(
        self,
        path: str | Path,
        *,
        recursive: bool = True,
    ) -> int:

        directory = self._resolver.resolve(path)

        if not directory.exists():

            return 0

        if recursive:

            return sum(1 for item in directory.rglob("*") if item.is_file())

        return len(self.files(directory))

    def count_folders(
        self,
        path: str | Path,
        *,
        recursive: bool = True,
    ) -> int:

        directory = self._resolver.resolve(path)

        if not directory.exists():

            return 0

        if recursive:

            return sum(1 for item in directory.rglob("*") if item.is_dir())

        return len(self.folders(directory))

    def size(
        self,
        path: str | Path,
    ) -> int:

        directory = self._resolver.resolve(path)

        if not directory.exists():

            return 0

        total = 0

        for file in directory.rglob("*"):

            if file.is_file():

                try:

                    total += file.stat().st_size

                except OSError:

                    pass

        return total

    def statistics(
        self,
        path: str | Path,
    ) -> dict:

        directory = self._resolver.resolve(path)

        if not directory.exists():

            return {}

        return {
            "path": str(directory),
            "files": self.count_files(directory),
            "folders": self.count_folders(directory),
            "size": self.size(directory),
        }

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def ensure(
        self,
        path: str | Path,
    ) -> Path:

        return self.create(
            path,
            exist_ok=True,
        )

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return "FolderOperations()"
