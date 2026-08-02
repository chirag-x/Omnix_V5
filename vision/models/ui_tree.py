"""
Omnix V5 - UI Tree

Represents the hierarchical UI structure of the current screen.

The UI Tree is the canonical representation consumed by:
- Planner
- Memory
- Automation
- Semantic Summary
- Screen State
- Target Resolver
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from vision.models.ui_element import UIElement


@dataclass(slots=True)
class UITree:
    """
    Complete UI hierarchy for one screen.
    """

    # Flat list of all UI elements
    elements: list[UIElement] = field(default_factory=list)

    # Root elements (elements without parents)
    roots: list[UIElement] = field(default_factory=list)

    # Lookup tables
    by_id: dict[str, UIElement] = field(default_factory=dict)
    by_name: dict[str, UIElement] = field(default_factory=dict)

    # Metadata
    metadata: dict = field(default_factory=dict)

    # ----------------------------------------------------
    # Build
    # ----------------------------------------------------

    @classmethod
    def from_elements(
        cls,
        elements: list[UIElement],
    ) -> "UITree":

        tree = cls()

        tree.elements = elements

        # Build lookup tables
        for element in elements:

            tree.by_id[element.id] = element

            if element.name:
                tree.by_name[element.name.lower()] = element

        # Find root nodes
        for element in elements:

            if (
                element.parent_id is None
                or element.parent_id not in tree.by_id
            ):
                tree.roots.append(element)

        return tree

    # ----------------------------------------------------
    # Queries
    # ----------------------------------------------------

    def get(
        self,
        element_id: str,
    ) -> Optional[UIElement]:

        return self.by_id.get(element_id)

    def find(
        self,
        name: str,
    ) -> Optional[UIElement]:

        return self.by_name.get(name.lower())

    def find_type(
        self,
        element_type: str,
    ) -> list[UIElement]:

        return [
            e
            for e in self.elements
            if e.element_type.lower() == element_type.lower()
        ]

    def clickable(self) -> list[UIElement]:

        return [
            e
            for e in self.elements
            if e.clickable
        ]

    def editable(self) -> list[UIElement]:

        return [
            e
            for e in self.elements
            if e.editable
        ]

    def visible(self) -> list[UIElement]:

        return [
            e
            for e in self.elements
            if e.visible
        ]

    def focused(self) -> Optional[UIElement]:

        for element in self.elements:

            if element.focused:
                return element

        return None

    # ----------------------------------------------------
    # Statistics
    # ----------------------------------------------------

    @property
    def count(self) -> int:

        return len(self.elements)

    @property
    def root_count(self) -> int:

        return len(self.roots)

    # ----------------------------------------------------
    # Export
    # ----------------------------------------------------

    def to_dict(self) -> dict:

        return {

            "elements": [
                element.to_dict()
                for element in self.elements
            ],

            "roots": [
                root.id
                for root in self.roots
            ],

            "metadata": self.metadata,
        }

    # ----------------------------------------------------

    def __len__(self):

        return len(self.elements)

    def __iter__(self):

        return iter(self.elements)

    def __contains__(
        self,
        item,
    ):

        if isinstance(item, str):
            return item in self.by_id

        return item in self.elements

    def __repr__(self):

        return (
            f"UITree("
            f"elements={len(self.elements)}, "
            f"roots={len(self.roots)})"
        )