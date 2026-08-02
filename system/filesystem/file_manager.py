"""
Omnix V5
File Manager

Public API for the filesystem subsystem.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .archive_manager import ArchiveManager
from .file_monitor import FileMonitor
from .file_operations import FileOperations
from .file_search import FileSearch
from .folder_operations import FolderOperations
from .path_resolver import PathResolver
from .recycle_bin import RecycleBin

logger = logging.getLogger(__name__)


class FileManager:
    """
    Public API for filesystem operations.

    Coordinates:

        • Path resolution
        • File searching
        • File operations
        • Folder operations
        • Archive management
        • Recycle bin
        • File monitoring
    """

    def __init__(
        self,
        resolver=None,
        search=None,
        files=None,
        folders=None,
        archives=None,
        recycle=None,
        monitor=None,
    ):

        self._resolver = resolver or PathResolver()

        self._search = search or FileSearch()

        self._files = files or FileOperations()

        self._folders = folders or FolderOperations()

        self._archives = archives or ArchiveManager()

        self._recycle = recycle or RecycleBin()

        self._monitor = monitor or FileMonitor()

        self._initialized = False

    # ---------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------

    @property
    def initialized(self) -> bool:

        return self._initialized

    def initialize(self) -> None:

        if self._initialized:

            return

        logger.info("Initializing FileManager...")

        self._initialized = True

        logger.info("FileManager initialized.")

    def shutdown(self) -> None:

        logger.info("Shutting down FileManager...")

        self._monitor.stop()

        self._initialized = False

    # ---------------------------------------------------------
    # Services
    # ---------------------------------------------------------

    @property
    def resolver(self) -> PathResolver:

        return self._resolver

    @property
    def search_engine(self) -> FileSearch:

        return self._search

    @property
    def files(self) -> FileOperations:

        return self._files

    @property
    def folders(self) -> FolderOperations:

        return self._folders

    @property
    def archives(self) -> ArchiveManager:

        return self._archives

    @property
    def recycle_bin(self) -> RecycleBin:

        return self._recycle

    @property
    def monitor(self) -> FileMonitor:

        return self._monitor

    # ---------------------------------------------------------
    # Path
    # ---------------------------------------------------------

    def resolve(
        self,
        path: str | Path,
    ) -> Path:

        return self._resolver.resolve(path)

    def exists(
        self,
        path: str | Path,
    ) -> bool:

        return self._resolver.exists(path)

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    def search(
        self,
        root: str | Path,
        **kwargs,
    ):

        return self._search.search(
            root,
            **kwargs,
        )

    def by_name(
        self,
        root: str | Path,
        name: str,
    ):

        return self._search.by_name(
            root,
            name,
        )

    def by_extension(
        self,
        root: str | Path,
        extension: str,
    ):

        return self._search.by_extension(
            root,
            extension,
        )

    def contains_text(
        self,
        root: str | Path,
        text: str,
    ):

        return self._search.contains_text(
            root,
            text,
        )

    # ---------------------------------------------------------
    # File Operations
    # ---------------------------------------------------------

    def create_file(
        self,
        path: str | Path,
        **kwargs,
    ) -> Path:

        return self._files.create(
            path,
            **kwargs,
        )

    def copy_file(
        self,
        source: str | Path,
        destination: str | Path,
        **kwargs,
    ) -> Path:

        return self._files.copy(
            source,
            destination,
            **kwargs,
        )

    def move_file(
        self,
        source: str | Path,
        destination: str | Path,
        **kwargs,
    ) -> Path:

        return self._files.move(
            source,
            destination,
            **kwargs,
        )

    def rename_file(
        self,
        path: str | Path,
        new_name: str,
    ) -> Path:

        return self._files.rename(
            path,
            new_name,
        )

    def delete_file(
        self,
        path: str | Path,
    ) -> bool:

        return self._files.delete(
            path,
        )

    # ---------------------------------------------------------
    # Folder Operations
    # ---------------------------------------------------------

    def create_folder(
        self,
        path: str | Path,
        **kwargs,
    ) -> Path:

        return self._folders.create(
            path,
            **kwargs,
        )

    def copy_folder(
        self,
        source: str | Path,
        destination: str | Path,
        **kwargs,
    ) -> Path:

        return self._folders.copy(
            source,
            destination,
            **kwargs,
        )

    def move_folder(
        self,
        source: str | Path,
        destination: str | Path,
    ) -> Path:

        return self._folders.move(
            source,
            destination,
        )

    def rename_folder(
        self,
        path: str | Path,
        new_name: str,
    ) -> Path:

        return self._folders.rename(
            path,
            new_name,
        )

    def delete_folder(
        self,
        path: str | Path,
    ) -> bool:

        return self._folders.delete(
            path,
        )

    # ---------------------------------------------------------
    # Archive
    # ---------------------------------------------------------

    def create_archive(
        self,
        source: str | Path,
        archive: str | Path,
        **kwargs,
    ) -> Path:

        return self._archives.create(
            source,
            archive,
            **kwargs,
        )

    def extract_archive(
        self,
        archive: str | Path,
        destination: str | Path,
    ) -> Path:

        return self._archives.extract(
            archive,
            destination,
        )

    # ---------------------------------------------------------
    # Recycle Bin
    # ---------------------------------------------------------

    def recycle(
        self,
        path: str | Path,
    ) -> bool:

        return self._recycle.send(
            path,
        )

    def permanent_delete(
        self,
        path: str | Path,
    ) -> bool:

        return self._recycle.permanent_delete(
            path,
        )

    # ---------------------------------------------------------
    # Monitor
    # ---------------------------------------------------------

    def watch(
        self,
        path: str | Path,
        *,
        recursive: bool = True,
    ) -> None:

        self._monitor.watch(
            path,
            recursive=recursive,
        )

    def start_monitoring(
        self,
    ) -> None:

        self._monitor.start()

    def stop_monitoring(
        self,
    ) -> None:

        self._monitor.stop()

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "initialized": self._initialized,
            "monitor_running": self._monitor.running,
            "resolver": repr(self._resolver),
            "search": repr(self._search),
            "files": repr(self._files),
            "folders": repr(self._folders),
            "archives": repr(self._archives),
            "recycle_bin": repr(self._recycle),
        }

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return "FileManager(" f"initialized={self._initialized})"
