"""
Omnix V5
Archive Manager

ZIP archive management.
"""

from __future__ import annotations

import logging
import zipfile
from pathlib import Path

from .path_resolver import PathResolver

logger = logging.getLogger(__name__)


class ArchiveManager:
    """
    ZIP archive operations.
    """

    def __init__(self) -> None:

        self._resolver = PathResolver()

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------

    def create(
        self,
        source: str | Path,
        archive: str | Path,
        *,
        overwrite: bool = False,
    ) -> Path:
        """
        Create a ZIP archive from a file or directory.
        """

        source = self._resolver.resolve(source)
        archive = self._resolver.resolve(archive)

        if not source.exists():

            raise FileNotFoundError(source)

        if archive.exists() and not overwrite:

            raise FileExistsError(archive)

        archive.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with zipfile.ZipFile(
            archive,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as zipf:

            if source.is_file():

                zipf.write(
                    source,
                    arcname=source.name,
                )

            else:

                for file in source.rglob("*"):

                    if file.is_file():

                        zipf.write(
                            file,
                            arcname=file.relative_to(source),
                        )

        logger.info(
            "Created archive %s",
            archive,
        )

        return archive

    # ---------------------------------------------------------
    # Extract
    # ---------------------------------------------------------

    def extract(
        self,
        archive: str | Path,
        destination: str | Path,
    ) -> Path:

        archive = self._resolver.resolve(archive)
        destination = self._resolver.resolve(destination)

        if not archive.exists():

            raise FileNotFoundError(archive)

        destination.mkdir(
            parents=True,
            exist_ok=True,
        )

        with zipfile.ZipFile(
            archive,
            "r",
        ) as zipf:

            zipf.extractall(
                destination,
            )

        logger.info(
            "Extracted %s",
            archive,
        )

        return destination

    # ---------------------------------------------------------
    # List
    # ---------------------------------------------------------

    def contents(
        self,
        archive: str | Path,
    ) -> list[str]:

        archive = self._resolver.resolve(archive)

        with zipfile.ZipFile(
            archive,
            "r",
        ) as zipf:

            return zipf.namelist()

    # ---------------------------------------------------------
    # Add File
    # ---------------------------------------------------------

    def add(
        self,
        archive: str | Path,
        file: str | Path,
    ) -> None:

        archive = self._resolver.resolve(archive)
        file = self._resolver.resolve(file)

        with zipfile.ZipFile(
            archive,
            "a",
            compression=zipfile.ZIP_DEFLATED,
        ) as zipf:

            zipf.write(
                file,
                arcname=file.name,
            )

        logger.info(
            "Added %s to %s",
            file,
            archive,
        )

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def exists(
        self,
        archive: str | Path,
    ) -> bool:

        archive = self._resolver.resolve(archive)

        return archive.exists()

    def is_archive(
        self,
        archive: str | Path,
    ) -> bool:

        archive = self._resolver.resolve(archive)

        return archive.is_file() and zipfile.is_zipfile(archive)

    def test(
        self,
        archive: str | Path,
    ) -> bool:
        """
        Test archive integrity.
        """

        archive = self._resolver.resolve(archive)

        if not self.is_archive(archive):

            return False

        with zipfile.ZipFile(
            archive,
            "r",
        ) as zipf:

            return zipf.testzip() is None

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    def size(
        self,
        archive: str | Path,
    ) -> int:

        archive = self._resolver.resolve(archive)

        if not archive.exists():

            return 0

        return archive.stat().st_size

    def statistics(
        self,
        archive: str | Path,
    ) -> dict:

        archive = self._resolver.resolve(archive)

        if not self.is_archive(archive):

            return {}

        with zipfile.ZipFile(
            archive,
            "r",
        ) as zipf:

            info = zipf.infolist()

            compressed = sum(item.compress_size for item in info)

            uncompressed = sum(item.file_size for item in info)

            return {
                "name": archive.name,
                "entries": len(info),
                "compressed_size": compressed,
                "uncompressed_size": uncompressed,
                "archive_size": archive.stat().st_size,
            }

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def open(
        self,
        archive: str | Path,
        mode: str = "r",
    ) -> zipfile.ZipFile:

        archive = self._resolver.resolve(archive)

        return zipfile.ZipFile(
            archive,
            mode,
            compression=zipfile.ZIP_DEFLATED,
        )

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return "ArchiveManager()"
