"""
Omnix V5
Application Model

Represents a desktop application known to the Omnix System.

This model is used throughout the entire System layer:
- Application Registry
- Application Scanner
- Application Cache
- Launch Strategy
- Application Monitor
- Planner
- Automation
- Memory

Author: Omnix V5
"""

from __future__ import annotations
from system.models.base_model import BaseModel
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(
    slots=True,
    kw_only=True,
)
class Application(BaseModel):
    """
    Represents a desktop application.

    Example:
        Application(
            name="Google Chrome",
            executable="chrome.exe",
            install_path="C:/Program Files/Google/Chrome/Application/chrome.exe",
            aliases=["chrome", "browser"],
            category="browser"
        )
    """

    # ------------------------------------------------------------------
    # Basic Information
    # ------------------------------------------------------------------

    name: str
    executable: str

    # ------------------------------------------------------------------
    # Optional Information
    # ------------------------------------------------------------------

    display_name: str | None = None
    install_path: str | None = None
    publisher: str | None = None
    version: str | None = None
    description: str | None = None
    category: str | None = None
    icon_path: str | None = None

    # ------------------------------------------------------------------
    # Runtime Information
    # ------------------------------------------------------------------

    process_name: str | None = None
    process_id: int | None = None

    running: bool = False

    # ------------------------------------------------------------------
    # Launch Information
    # ------------------------------------------------------------------

    launch_command: str | None = None
    launch_uri: str | None = None
    working_directory: str | None = None

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    aliases: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    # metadata: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:

        self.name = self.name.strip()
        self.executable = self.executable.strip()

        if self.display_name is None:
            self.display_name = self.name

        if self.process_name is None:
            self.process_name = self.executable

        self.aliases = sorted(
            {
                alias.strip().lower()
                for alias in self.aliases
                if alias and alias.strip()
            }
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def install_directory(self) -> Path | None:
        """
        Returns the installation directory if available.
        """

        if not self.install_path:
            return None

        return Path(self.install_path).parent

    @property
    def exists(self) -> bool:
        """
        Returns True if the executable exists.
        """

        if not self.install_path:
            return False

        return Path(self.install_path).exists()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def has_alias(self, name: str) -> bool:
        """
        Checks whether the supplied name matches this application.
        """

        value = name.strip().lower()

        return (
            value == self.name.lower()
            or value == self.display_name.lower()
            or value == self.executable.lower()
            or value in self.aliases
        )

    def add_alias(self, alias: str) -> None:
        """
        Adds a new alias if it doesn't already exist.
        """

        alias = alias.strip().lower()

        if alias and alias not in self.aliases:
            self.aliases.append(alias)
            self.aliases.sort()



    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __str__(self) -> str:

        status = "Running" if self.running else "Stopped"

        return f"{self.display_name} ({status})"

    def __repr__(self) -> str:

        return (
            f"Application("
            f"name={self.name!r}, "
            f"executable={self.executable!r}, "
            f"running={self.running}"
            f")"
        )