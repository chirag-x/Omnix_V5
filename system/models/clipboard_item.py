"""
Omnix V5
Clipboard Item Model

Represents a single clipboard entry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .base_model import BaseModel


class ClipboardType(str, Enum):
    """Supported clipboard content types."""

    TEXT = "text"
    HTML = "html"
    IMAGE = "image"
    FILE = "file"
    FILES = "files"
    AUDIO = "audio"
    VIDEO = "video"
    URL = "url"
    COLOR = "color"
    UNKNOWN = "unknown"


@dataclass(
    slots=True,
    kw_only=True,
)
class ClipboardItem(BaseModel):
    """
    Represents one clipboard entry.
    """

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    content_type: ClipboardType = ClipboardType.TEXT

    # ---------------------------------------------------------
    # Content
    # ---------------------------------------------------------

    content: Any = None

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    size: int = 0

    source_application: str | None = None

    source_window: str | None = None

    copied_by: str | None = None

    # ---------------------------------------------------------
    # State
    # ---------------------------------------------------------

    favorite: bool = False

    pinned: bool = False

    encrypted: bool = False

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    tags: list[str] = field(default_factory=list)

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @property
    def is_text(self) -> bool:
        return self.content_type == ClipboardType.TEXT

    @property
    def is_image(self) -> bool:
        return self.content_type == ClipboardType.IMAGE

    @property
    def is_file(self) -> bool:
        return self.content_type in (
            ClipboardType.FILE,
            ClipboardType.FILES,
        )

    @property
    def preview(self) -> str:
        """
        Returns a short preview of the clipboard item.
        """

        if self.content is None:
            return ""

        if self.is_text:
            text = str(self.content).replace("\n", " ")

            if len(text) > 100:
                return text[:97] + "..."

            return text

        if self.is_file:

            if isinstance(self.content, list):
                return f"{len(self.content)} files"

            return Path(str(self.content)).name

        if self.is_image:
            return "<Image>"

        return str(self.content)

    # ---------------------------------------------------------
    # Tag Helpers
    # ---------------------------------------------------------

    def add_tag(
        self,
        tag: str,
    ) -> None:

        tag = tag.strip().lower()

        if tag and tag not in self.tags:
            self.tags.append(tag)

            self.touch()

    def remove_tag(
        self,
        tag: str,
    ) -> None:

        tag = tag.strip().lower()

        if tag in self.tags:
            self.tags.remove(tag)

            self.touch()

    def has_tag(
        self,
        tag: str,
    ) -> bool:

        return tag.strip().lower() in self.tags

    # ---------------------------------------------------------
    # Pinning
    # ---------------------------------------------------------

    def pin(self) -> None:

        self.pinned = True
        self.touch()

    def unpin(self) -> None:

        self.pinned = False
        self.touch()

    # ---------------------------------------------------------
    # Favorites
    # ---------------------------------------------------------

    def favorite_item(self) -> None:

        self.favorite = True
        self.touch()

    def unfavorite(self) -> None:

        self.favorite = False
        self.touch()

    # ---------------------------------------------------------
    # Representation
    # ---------------------------------------------------------

    def __str__(self) -> str:

        return (
            f"{self.content_type.value}: "
            f"{self.preview}"
        )