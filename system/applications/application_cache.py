"""
Omnix V5
Application Cache

Provides an in-memory cache for discovered applications.
"""

from __future__ import annotations

import logging
from datetime import datetime

from system.models.application import Application

logger = logging.getLogger(__name__)


class ApplicationCache:
    """
    Stores discovered applications in memory.

    Responsibilities
    ----------------
    • Fast lookup
    • Cache management
    • Simple searching
    """

    def __init__(self) -> None:

        self._cache: dict[str, Application] = {}

        self._last_updated: datetime | None = None

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------

    @property
    def last_updated(self) -> datetime | None:
        return self._last_updated

    @property
    def count(self) -> int:
        return len(self._cache)

    # ---------------------------------------------------------
    # Cache Management
    # ---------------------------------------------------------

    def clear(self) -> None:

        self._cache.clear()

        self._last_updated = None

        logger.info("Application cache cleared.")

    def update(
        self,
        applications: list[Application],
    ) -> None:

        self._cache.clear()

        for app in applications:

            self._cache[app.name.lower()] = app

        self._last_updated = datetime.now()

        logger.info(
            "Cached %d applications.",
            len(self._cache),
        )

    # ---------------------------------------------------------
    # Lookup
    # ---------------------------------------------------------

    def get(
        self,
        name: str,
    ) -> Application | None:

        return self._cache.get(name.lower())

    def exists(
        self,
        name: str,
    ) -> bool:

        return name.lower() in self._cache

    def all(self) -> list[Application]:

        return sorted(
            self._cache.values(),
            key=lambda app: app.display_name.lower(),
        )

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    def search(
        self,
        query: str,
    ) -> list[Application]:

        query = query.lower().strip()

        if not query:
            return self.all()

        results = []

        for app in self._cache.values():

            if (
                query in app.name.lower()
                or query in app.display_name.lower()
            ):
                results.append(app)

        return sorted(
            results,
            key=lambda app: app.display_name.lower(),
        )

    # ---------------------------------------------------------
    # Modification
    # ---------------------------------------------------------

    def add(
        self,
        application: Application,
    ) -> None:

        self._cache[application.name.lower()] = application

    def remove(
        self,
        name: str,
    ) -> bool:

        name = name.lower()

        if name not in self._cache:
            return False

        del self._cache[name]

        return True