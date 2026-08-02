"""
Omnix V5
Path Resolver

Resolves, validates, and normalizes filesystem paths.
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class PathResolver:
    """
    Resolves filesystem paths into absolute Path objects.

    Supports:

    - Relative paths
    - Absolute paths
    - Environment variables
    - Home directory (~)
    - Windows special folders
    """

    _SPECIAL_FOLDERS = {
        "desktop": Path.home() / "Desktop",
        "downloads": Path.home() / "Downloads",
        "documents": Path.home() / "Documents",
        "pictures": Path.home() / "Pictures",
        "videos": Path.home() / "Videos",
        "music": Path.home() / "Music",
        "home": Path.home(),
        "temp": Path(tempfile.gettempdir()),
        "current": Path.cwd(),
    }

    def __init__(self) -> None:

        logger.debug("PathResolver initialized.")

    # ---------------------------------------------------------
    # Resolve
    # ---------------------------------------------------------

    def resolve(
        self,
        path: str | Path,
        *,
        strict: bool = False,
    ) -> Path:
        """
        Resolve any path into an absolute Path.
        """

        if isinstance(path, Path):
            value = path

        else:

            value = Path(self.expand(path))

        return value.resolve(
            strict=strict,
        )

    # ---------------------------------------------------------
    # Expand
    # ---------------------------------------------------------

    def expand(
        self,
        path: str,
    ) -> str:
        """
        Expand variables and aliases.
        """

        path = path.strip()

        key = path.lower()

        if key in self._SPECIAL_FOLDERS:

            return str(self._SPECIAL_FOLDERS[key])

        path = os.path.expandvars(path)

        path = os.path.expanduser(path)

        return path

    # ---------------------------------------------------------
    # Normalize
    # ---------------------------------------------------------

    def normalize(
        self,
        path: str | Path,
    ) -> Path:
        """
        Normalize separators and remove '..'.
        """

        return Path(os.path.normpath(str(path)))

    # ---------------------------------------------------------
    # Absolute / Relative
    # ---------------------------------------------------------

    def absolute(
        self,
        path: str | Path,
    ) -> Path:

        return self.resolve(path)

    def relative(
        self,
        path: str | Path,
        start: str | Path | None = None,
    ) -> Path:

        if start is None:

            start = Path.cwd()

        return Path(
            os.path.relpath(
                self.resolve(path),
                start=self.resolve(start),
            )
        )

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def exists(
        self,
        path: str | Path,
    ) -> bool:

        return self.resolve(path).exists()

    def is_file(
        self,
        path: str | Path,
    ) -> bool:

        return self.resolve(path).is_file()

    def is_directory(
        self,
        path: str | Path,
    ) -> bool:

        return self.resolve(path).is_dir()

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    def parent(
        self,
        path: str | Path,
    ) -> Path:

        return self.resolve(path).parent

    def filename(
        self,
        path: str | Path,
    ) -> str:

        return self.resolve(path).name

    def stem(
        self,
        path: str | Path,
    ) -> str:

        return self.resolve(path).stem

    def extension(
        self,
        path: str | Path,
    ) -> str:

        return self.resolve(path).suffix.lower()

    def size(
        self,
        path: str | Path,
    ) -> int:

        resolved = self.resolve(path)

        if not resolved.exists():

            return 0

        if resolved.is_file():

            return resolved.stat().st_size

        total = 0

        for file in resolved.rglob("*"):

            if file.is_file():

                try:

                    total += file.stat().st_size

                except OSError:

                    pass

        return total

    # ---------------------------------------------------------
    # Common Locations
    # ---------------------------------------------------------

    def home(self) -> Path:

        return self._SPECIAL_FOLDERS["home"]

    def desktop(self) -> Path:

        return self._SPECIAL_FOLDERS["desktop"]

    def downloads(self) -> Path:

        return self._SPECIAL_FOLDERS["downloads"]

    def documents(self) -> Path:

        return self._SPECIAL_FOLDERS["documents"]

    def pictures(self) -> Path:

        return self._SPECIAL_FOLDERS["pictures"]

    def videos(self) -> Path:

        return self._SPECIAL_FOLDERS["videos"]

    def music(self) -> Path:

        return self._SPECIAL_FOLDERS["music"]

    def temp(self) -> Path:

        return self._SPECIAL_FOLDERS["temp"]

    def current(self) -> Path:

        return Path.cwd()

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def same_path(
        self,
        first: str | Path,
        second: str | Path,
    ) -> bool:

        return self.resolve(first) == self.resolve(second)

    def ensure_directory(
        self,
        path: str | Path,
    ) -> Path:
        """
        Create directory if it doesn't exist.
        """

        directory = self.resolve(path)

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directory

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __call__(
        self,
        path: str | Path,
    ) -> Path:

        return self.resolve(path)

    def __repr__(
        self,
    ) -> str:

        return "PathResolver()"
