"""
Omnix V5
File Operations

High-level file manipulation.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from .path_resolver import PathResolver

logger = logging.getLogger(__name__)


class FileOperations:
    """
    File manipulation utilities.
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
        overwrite: bool = False,
    ) -> Path:

        file = self._resolver.resolve(path)

        if file.exists() and not overwrite:

            raise FileExistsError(file)

        file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        file.touch(
            exist_ok=overwrite,
        )

        logger.info(
            "Created file: %s",
            file,
        )

        return file

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

        if not source.is_file():

            raise FileNotFoundError(source)

        if destination.exists() and not overwrite:

            raise FileExistsError(destination)

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source,
            destination,
        )

        logger.info(
            "Copied %s -> %s",
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
        *,
        overwrite: bool = False,
    ) -> Path:

        source = self._resolver.resolve(source)
        destination = self._resolver.resolve(destination)

        if not source.exists():

            raise FileNotFoundError(source)

        if destination.exists() and not overwrite:

            raise FileExistsError(destination)

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.move(
            str(source),
            str(destination),
        )

        logger.info(
            "Moved %s -> %s",
            source,
            destination,
        )

        return destination

    # ---------------------------------------------------------
    # Rename
    # ---------------------------------------------------------

    def rename(
        self,
        source: str | Path,
        new_name: str,
    ) -> Path:

        source = self._resolver.resolve(source)

        if not source.exists():

            raise FileNotFoundError(source)

        destination = source.with_name(
            new_name,
        )

        source.rename(
            destination,
        )

        logger.info(
            "Renamed %s -> %s",
            source.name,
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

        path = self._resolver.resolve(path)

        if not path.exists():

            return False

        path.unlink()

        logger.info(
            "Deleted file: %s",
            path,
        )

        return True

    # ---------------------------------------------------------
    # Read
    # ---------------------------------------------------------

    def read_text(
        self,
        path: str | Path,
        *,
        encoding: str = "utf-8",
    ) -> str:

        path = self._resolver.resolve(path)

        return path.read_text(
            encoding=encoding,
        )

    def read_bytes(
        self,
        path: str | Path,
    ) -> bytes:

        path = self._resolver.resolve(path)

        return path.read_bytes()

    # ---------------------------------------------------------
    # Write
    # ---------------------------------------------------------

    def write_text(
        self,
        path: str | Path,
        text: str,
        *,
        encoding: str = "utf-8",
    ) -> Path:

        path = self._resolver.resolve(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            text,
            encoding=encoding,
        )

        logger.info(
            "Wrote text to %s",
            path,
        )

        return path

    def append_text(
        self,
        path: str | Path,
        text: str,
        *,
        encoding: str = "utf-8",
    ) -> Path:

        path = self._resolver.resolve(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "a",
            encoding=encoding,
        ) as file:

            file.write(text)

        logger.info(
            "Appended text to %s",
            path,
        )

        return path

    def write_bytes(
        self,
        path: str | Path,
        data: bytes,
    ) -> Path:

        path = self._resolver.resolve(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_bytes(data)

        logger.info(
            "Wrote bytes to %s",
            path,
        )

        return path

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    def exists(
        self,
        path: str | Path,
    ) -> bool:

        return self._resolver.exists(path)

    def size(
        self,
        path: str | Path,
    ) -> int:

        path = self._resolver.resolve(path)

        return path.stat().st_size if path.exists() else 0

    def touch(
        self,
        path: str | Path,
    ) -> Path:

        path = self._resolver.resolve(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.touch(
            exist_ok=True,
        )

        return path

    # ---------------------------------------------------------
    # Hash
    # ---------------------------------------------------------

    def checksum(
        self,
        path: str | Path,
        algorithm: str = "sha256",
    ) -> str:

        import hashlib

        path = self._resolver.resolve(path)

        hasher = hashlib.new(
            algorithm,
        )

        with path.open(
            "rb",
        ) as file:

            while True:

                chunk = file.read(
                    8192,
                )

                if not chunk:

                    break

                hasher.update(
                    chunk,
                )

        return hasher.hexdigest()

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def statistics(
        self,
        path: str | Path,
    ) -> dict:

        path = self._resolver.resolve(path)

        if not path.exists():

            return {}

        stat = path.stat()

        return {
            "name": path.name,
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "accessed": stat.st_atime,
            "extension": path.suffix,
            "absolute_path": str(path),
        }

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return "FileOperations()"
