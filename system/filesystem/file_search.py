"""
Omnix V5
File Search

High-performance filesystem searching.
"""

from __future__ import annotations

import fnmatch
import logging
from pathlib import Path
from typing import Iterable

from .path_resolver import PathResolver

logger = logging.getLogger(__name__)


class FileSearch:
    """
    Search for files using various filters.
    """

    def __init__(self) -> None:

        self._resolver = PathResolver()

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    def search(
        self,
        root: str | Path,
        *,
        pattern: str = "*",
        recursive: bool = True,
        include_hidden: bool = False,
    ) -> list[Path]:
        """
        Search files matching a pattern.
        """

        root = self._resolver.resolve(root)

        if not root.exists():

            return []

        if not root.is_dir():

            return []

        iterator: Iterable[Path]

        if recursive:

            iterator = root.rglob("*")

        else:

            iterator = root.iterdir()

        results: list[Path] = []

        for item in iterator:

            if not item.is_file():

                continue

            if not include_hidden and item.name.startswith("."):

                continue

            if fnmatch.fnmatch(
                item.name,
                pattern,
            ):

                results.append(item)

        logger.debug(
            "Search '%s' -> %d file(s)",
            pattern,
            len(results),
        )

        return results

    # ---------------------------------------------------------
    # Name Search
    # ---------------------------------------------------------

    def by_name(
        self,
        root: str | Path,
        name: str,
        *,
        recursive: bool = True,
    ) -> list[Path]:

        return self.search(
            root,
            pattern=name,
            recursive=recursive,
        )

    # ---------------------------------------------------------
    # Extension Search
    # ---------------------------------------------------------

    def by_extension(
        self,
        root: str | Path,
        extension: str,
        *,
        recursive: bool = True,
    ) -> list[Path]:

        extension = extension.lstrip(".")

        return self.search(
            root,
            pattern=f"*.{extension}",
            recursive=recursive,
        )

    # ---------------------------------------------------------
    # Wildcard
    # ---------------------------------------------------------

    def wildcard(
        self,
        root: str | Path,
        pattern: str,
        *,
        recursive: bool = True,
    ) -> list[Path]:

        return self.search(
            root,
            pattern=pattern,
            recursive=recursive,
        )

    # ---------------------------------------------------------
    # Exact Path
    # ---------------------------------------------------------

    def exact(
        self,
        path: str | Path,
    ) -> Path | None:
        """
        Return the file if it exists.
        """

        path = self._resolver.resolve(path)

        if path.exists() and path.is_file():

            return path

        return None

    # ---------------------------------------------------------
    # Text Search
    # ---------------------------------------------------------

    def contains_text(
        self,
        root: str | Path,
        text: str,
        *,
        recursive: bool = True,
        encoding: str = "utf-8",
    ) -> list[Path]:
        """
        Search text inside files.
        """

        results: list[Path] = []

        for file in self.search(
            root,
            recursive=recursive,
        ):

            try:

                content = file.read_text(
                    encoding=encoding,
                    errors="ignore",
                )

            except Exception:

                continue

            if text.lower() in content.lower():

                results.append(file)

        return results

    # ---------------------------------------------------------
    # Size Filters
    # ---------------------------------------------------------

    def larger_than(
        self,
        root: str | Path,
        size: int,
        *,
        recursive: bool = True,
    ) -> list[Path]:

        return [
            file
            for file in self.search(
                root,
                recursive=recursive,
            )
            if file.stat().st_size > size
        ]

    def smaller_than(
        self,
        root: str | Path,
        size: int,
        *,
        recursive: bool = True,
    ) -> list[Path]:

        return [
            file
            for file in self.search(
                root,
                recursive=recursive,
            )
            if file.stat().st_size < size
        ]

    # ---------------------------------------------------------
    # Date Filters
    # ---------------------------------------------------------

    def newest(
        self,
        root: str | Path,
        *,
        recursive: bool = True,
    ) -> Path | None:

        files = self.search(
            root,
            recursive=recursive,
        )

        if not files:

            return None

        return max(
            files,
            key=lambda f: f.stat().st_mtime,
        )

    def oldest(
        self,
        root: str | Path,
        *,
        recursive: bool = True,
    ) -> Path | None:

        files = self.search(
            root,
            recursive=recursive,
        )

        if not files:

            return None

        return min(
            files,
            key=lambda f: f.stat().st_mtime,
        )

    # ---------------------------------------------------------
    # Duplicate Names
    # ---------------------------------------------------------

    def duplicate_names(
        self,
        root: str | Path,
        *,
        recursive: bool = True,
    ) -> dict[str, list[Path]]:

        duplicates: dict[str, list[Path]] = {}

        for file in self.search(
            root,
            recursive=recursive,
        ):

            duplicates.setdefault(
                file.name,
                [],
            ).append(file)

        return {name: paths for name, paths in duplicates.items() if len(paths) > 1}

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def statistics(
        self,
        root: str | Path,
        *,
        recursive: bool = True,
    ) -> dict:

        files = self.search(
            root,
            recursive=recursive,
        )

        total_size = sum(file.stat().st_size for file in files)

        return {
            "files": len(files),
            "total_size": total_size,
        }

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def exists(
        self,
        path: str | Path,
    ) -> bool:

        return self.exact(path) is not None

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return "FileSearch()"
