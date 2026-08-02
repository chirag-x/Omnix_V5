"""
Omnix V5
Base Model

Base class for all system models.
"""

from __future__ import annotations

import copy
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass(
    slots=True,
    kw_only=True,
)
class BaseModel:
    """
    Base class for every Omnix model.
    """

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    id: str = field(default_factory=lambda: str(uuid4()))

    # ---------------------------------------------------------
    # Timestamps
    # ---------------------------------------------------------

    created_at: datetime = field(default_factory=datetime.now)

    updated_at: datetime = field(default_factory=datetime.now)

    # ---------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------

    metadata: dict[str, Any] = field(default_factory=dict)

    # ---------------------------------------------------------
    # Timestamp Helpers
    # ---------------------------------------------------------

    def touch(self) -> None:
        """
        Updates the modification timestamp.
        """

        self.updated_at = datetime.now()

    # ---------------------------------------------------------
    # Metadata Helpers
    # ---------------------------------------------------------

    def set_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:

        self.metadata[key] = value
        self.touch()

    def get_metadata(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        return self.metadata.get(key, default)

    def remove_metadata(
        self,
        key: str,
    ) -> None:

        self.metadata.pop(key, None)
        self.touch()

    # ---------------------------------------------------------
    # Update Helpers
    # ---------------------------------------------------------

    def update(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Updates model fields.
        """

        for key, value in kwargs.items():

            if hasattr(self, key):
                setattr(self, key, value)

        self.touch()

    # ---------------------------------------------------------
    # Serialization
    # ---------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Converts model into dictionary.
        """

        data = asdict(self)

        for key, value in data.items():

            if isinstance(value, datetime):
                data[key] = value.isoformat()

        return data

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ):
        """
        Creates model from dictionary.
        """

        data = data.copy()

        for key in ("created_at", "updated_at"):

            if key in data and data[key]:

                data[key] = datetime.fromisoformat(data[key])

        return cls(**data)

    # ---------------------------------------------------------
    # JSON
    # ---------------------------------------------------------

    def to_json(
        self,
        indent: int = 4,
    ) -> str:

        return json.dumps(
            self.to_dict(),
            indent=indent,
            ensure_ascii=False,
        )

    @classmethod
    def from_json(
        cls,
        json_data: str,
    ):

        return cls.from_dict(json.loads(json_data))

    # ---------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------

    def copy(self):
        """
        Returns a deep copy.
        """

        return copy.deepcopy(self)

    def validate(self) -> bool:
        """
        Override in subclasses.
        """

        return True

    # ---------------------------------------------------------
    # Representation
    # ---------------------------------------------------------

    def __repr__(self) -> str:

        return f"{self.__class__.__name__}" f"(id='{self.id}')"
