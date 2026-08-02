"""
Omnix V5
File Monitor

Real-time filesystem monitoring.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .path_resolver import PathResolver

logger = logging.getLogger(__name__)


class _MonitorHandler(FileSystemEventHandler):
    """
    Internal watchdog handler.
    """

    def __init__(self) -> None:

        self.created_callbacks: list[Callable] = []
        self.deleted_callbacks: list[Callable] = []
        self.modified_callbacks: list[Callable] = []
        self.moved_callbacks: list[Callable] = []

    def on_created(self, event):

        for callback in self.created_callbacks:

            callback(event)

    def on_deleted(self, event):

        for callback in self.deleted_callbacks:

            callback(event)

    def on_modified(self, event):

        for callback in self.modified_callbacks:

            callback(event)

    def on_moved(self, event):

        for callback in self.moved_callbacks:

            callback(event)


class FileMonitor:
    """
    Watches directories for filesystem changes.
    """

    def __init__(self) -> None:

        self._resolver = PathResolver()

        self._observer = Observer()

        self._handler = _MonitorHandler()

        self._running = False

    # ---------------------------------------------------------
    # Start / Stop
    # ---------------------------------------------------------

    def watch(
        self,
        path: str | Path,
        *,
        recursive: bool = True,
    ) -> None:

        path = self._resolver.resolve(path)

        if not path.is_dir():

            raise NotADirectoryError(path)

        self._observer.schedule(
            self._handler,
            str(path),
            recursive=recursive,
        )

        logger.info(
            "Watching %s",
            path,
        )

    def start(self) -> None:

        if self._running:

            return

        self._observer.start()

        self._running = True

        logger.info("File monitor started.")

    def stop(self) -> None:

        if not self._running:

            return

        self._observer.stop()

        self._observer.join()

        self._running = False

        logger.info("File monitor stopped.")

    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------

    def on_created(
        self,
        callback: Callable,
    ) -> None:

        self._handler.created_callbacks.append(
            callback,
        )

    def on_deleted(
        self,
        callback: Callable,
    ) -> None:

        self._handler.deleted_callbacks.append(
            callback,
        )

    def on_modified(
        self,
        callback: Callable,
    ) -> None:

        self._handler.modified_callbacks.append(
            callback,
        )

    def on_moved(
        self,
        callback: Callable,
    ) -> None:

        self._handler.moved_callbacks.append(
            callback,
        )

    # ---------------------------------------------------------
    # Management
    # ---------------------------------------------------------

    def unwatch(self) -> None:
        """
        Stop monitoring all watched directories.
        """

        self.stop()

        self._observer = Observer()

        self._running = False

        logger.info("All watched directories removed.")

    def clear_callbacks(self) -> None:

        self._handler.created_callbacks.clear()

        self._handler.deleted_callbacks.clear()

        self._handler.modified_callbacks.clear()

        self._handler.moved_callbacks.clear()

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    @property
    def running(self) -> bool:

        return self._running

    def statistics(self) -> dict:

        return {
            "running": self._running,
            "created_callbacks": len(self._handler.created_callbacks),
            "deleted_callbacks": len(self._handler.deleted_callbacks),
            "modified_callbacks": len(self._handler.modified_callbacks),
            "moved_callbacks": len(self._handler.moved_callbacks),
        }

    # ---------------------------------------------------------
    # Context Manager
    # ---------------------------------------------------------

    def __enter__(self):

        self.start()

        return self

    def __exit__(
        self,
        exc_type,
        exc_val,
        exc_tb,
    ):

        self.stop()

    # ---------------------------------------------------------
    # Dunder
    # ---------------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return f"FileMonitor(" f"running={self._running})"
