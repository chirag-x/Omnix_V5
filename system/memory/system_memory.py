"""
Omnix V5
System Memory

Central persistent memory manager.
"""

from __future__ import annotations

import json
import logging

from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class SystemMemory:
    """
    Handles persistent Omnix memory.
    """

    def __init__(
        self,
        memory_path: str | Path | None = None,
    ) -> None:

        self._base_path = Path(memory_path or Path(__file__).parent)

        self._files = {
            "aliases": "learned_aliases.json",
            "recent_apps": "recent_apps.json",
            "failures": "failures.json",
            "statistics": "launch_statistics.json",
        }

        self._memory = {}

        self.load()

    # ---------------------------------------------------------
    # Loading
    # ---------------------------------------------------------

    def load(
        self,
    ) -> None:

        for key, filename in self._files.items():

            path = self._base_path / filename

            try:

                if path.exists():

                    with open(
                        path,
                        "r",
                        encoding="utf-8",
                    ) as file:

                        self._memory[key] = json.load(file)

                else:

                    self._memory[key] = {}

            except Exception as exc:

                logger.error(
                    "Memory load failed %s: %s",
                    filename,
                    exc,
                )

                self._memory[key] = {}

    # ---------------------------------------------------------
    # Saving
    # ---------------------------------------------------------

    def save(
        self,
    ) -> None:

        for key, filename in self._files.items():

            path = self._base_path / filename

            try:

                with open(
                    path,
                    "w",
                    encoding="utf-8",
                ) as file:

                    json.dump(
                        self._memory.get(
                            key,
                            {},
                        ),
                        file,
                        indent=4,
                    )

            except Exception as exc:

                logger.error(
                    "Memory save failed %s: %s",
                    filename,
                    exc,
                )

    # ---------------------------------------------------------
    # Generic Access
    # ---------------------------------------------------------

    def get(
        self,
        category: str,
        key: str,
        default=None,
    ):

        return self._memory.get(category, {}).get(
            key,
            default,
        )

    def set(
        self,
        category: str,
        key: str,
        value,
    ) -> None:

        if category not in self._memory:

            self._memory[category] = {}

        self._memory[category][key] = value

        self.save()

    # ---------------------------------------------------------
    # Aliases
    # ---------------------------------------------------------

    def add_alias(
        self,
        name: str,
        command: str,
    ) -> None:

        aliases = self._memory["aliases"]

        aliases[name] = command

        self.save()

    def get_alias(
        self,
        name: str,
    ):

        return self._memory["aliases"].get(
            name,
        )

    # ---------------------------------------------------------
    # Recent Applications
    # ---------------------------------------------------------

    def add_recent_app(
        self,
        app_name: str,
    ) -> None:

        apps = self._memory["recent_apps"]

        apps[app_name] = {
            "last_used": datetime.utcnow().isoformat(),
        }

        self.save()

    # ---------------------------------------------------------
    # Failures
    # ---------------------------------------------------------

    def add_failure(
        self,
        error: str,
        context: str = "",
    ) -> None:

        failures = self._memory["failures"]

        timestamp = datetime.utcnow().isoformat()

        failures[timestamp] = {
            "error": error,
            "context": context,
        }

        self.save()

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def statistics(
        self,
    ) -> dict:

        return {
            "categories": list(self._memory.keys()),
        }

    def __repr__(
        self,
    ) -> str:

        return "SystemMemory(" f"categories={len(self._memory)})"
