"""
Omnix V5
File Interface

Defines filesystem operation contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class FileInterface(ABC):
    """
    Interface for file operations.
    """

    # ---------------------------------------------------------
    # Read
    # ---------------------------------------------------------

    @abstractmethod
    def read(
        self,
        path: str,
    ) -> str:
        """
        Read file content.
        """

        pass

    # ---------------------------------------------------------
    # Write
    # ---------------------------------------------------------

    @abstractmethod
    def write(
        self,
        path: str,
        content: str,
    ) -> bool:
        """
        Write content to file.
        """

        pass

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------

    @abstractmethod
    def create(
        self,
        path: str,
    ) -> bool:
        """
        Create file or directory.
        """

        pass

    # ---------------------------------------------------------
    # Delete
    # ---------------------------------------------------------

    @abstractmethod
    def delete(
        self,
        path: str,
    ) -> bool:
        """
        Delete file or directory.
        """

        pass

    # ---------------------------------------------------------
    # Exists
    # ---------------------------------------------------------

    @abstractmethod
    def exists(
        self,
        path: str,
    ) -> bool:
        """
        Check path existence.
        """

        pass

    # ---------------------------------------------------------
    # Move
    # ---------------------------------------------------------

    @abstractmethod
    def move(
        self,
        source: str,
        destination: str,
    ) -> bool:
        """
        Move file or directory.
        """

        pass

    # ---------------------------------------------------------
    # Copy
    # ---------------------------------------------------------

    @abstractmethod
    def copy(
        self,
        source: str,
        destination: str,
    ) -> bool:
        """
        Copy file or directory.
        """

        pass
