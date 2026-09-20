"""
CONTINUO — Storage Abstraction & Local Storage Provider
Provides secure, project-scoped storage with path traversal protection.
Designed to support future cloud/S3/Supabase backends while currently providing
a hardened local filesystem implementation.
"""

from abc import ABC, abstractmethod
import os
from pathlib import Path
import shutil
from typing import BinaryIO, Optional

from backend.config import settings


class StorageProvider(ABC):
    """Abstract interface for project-scoped asset storage providers."""

    @abstractmethod
    def save(self, project_id: str, file_id: str, safe_extension: str, stream: BinaryIO) -> str:
        """
        Save a file stream for a given project under a generated UUID name.
        Returns the persistent storage_key.
        """
        pass

    @abstractmethod
    def get_path(self, storage_key: str) -> Path:
        """
        Return the resolved Path on the local filesystem.
        Must enforce strict containment within the storage root.
        """
        pass

    @abstractmethod
    def delete(self, storage_key: str) -> bool:
        """
        Safely delete the file identified by storage_key.
        Returns True if deleted, False if not found.
        """
        pass

    @abstractmethod
    def exists(self, storage_key: str) -> bool:
        """Check whether the file identified by storage_key exists."""
        pass

    @abstractmethod
    def open(self, storage_key: str) -> BinaryIO:
        """Open a readable binary stream for the file."""
        pass

    @abstractmethod
    def delete_project_storage(self, project_id: str) -> bool:
        """Delete all stored assets for a project upon project purge."""
        pass


class LocalStorageProvider(StorageProvider):
    """
    Secure local filesystem storage provider.
    Enforces project scoping and path containment, rejecting path traversal attacks.
    """

    def __init__(self, root_dir: Optional[str] = None):
        base_dir = root_dir or settings.STORAGE_LOCAL_DIR
        self.root_dir = Path(base_dir).resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _validate_and_resolve(self, storage_key: str) -> Path:
        """
        Validate that the storage key is safe and contained within root_dir.
        Rejects traversal patterns like '..', absolute paths, and symlink escapes.
        """
        if not storage_key or not isinstance(storage_key, str):
            raise ValueError("Invalid storage key: key must be a non-empty string.")

        # Normalize slashes and reject traversal sequences
        normalized_key = storage_key.replace("\\", "/").strip()
        if ".." in normalized_key.split("/"):
            raise ValueError(f"Path traversal detected in storage key: '{storage_key}'")

        if normalized_key.startswith("/") or ":" in normalized_key:
            raise ValueError(f"Absolute paths or drive letters forbidden: '{storage_key}'")

        target_path = (self.root_dir / normalized_key).resolve()

        # Enforce strict containment
        try:
            target_path.relative_to(self.root_dir)
        except ValueError:
            raise ValueError(f"Path escapes storage root: '{storage_key}'")

        return target_path

    def save(self, project_id: str, file_id: str, safe_extension: str, stream: BinaryIO) -> str:
        """Save stream into <root>/projects/{project_id}/assets/{file_id}.{safe_extension}."""
        # Sanitize extension (strip leading dot, enforce alphanumeric)
        ext = safe_extension.lstrip(".").lower()
        if not ext.isalnum():
            raise ValueError(f"Invalid file extension: '{safe_extension}'")

        storage_key = f"projects/{project_id}/assets/{file_id}.{ext}"
        target_path = self._validate_and_resolve(storage_key)

        target_path.parent.mkdir(parents=True, exist_ok=True)

        stream.seek(0)
        with open(target_path, "wb") as f_out:
            shutil.copyfileobj(stream, f_out)

        return storage_key

    def get_path(self, storage_key: str) -> Path:
        """Validate and return safe path."""
        return self._validate_and_resolve(storage_key)

    def exists(self, storage_key: str) -> bool:
        """Check if file exists on disk."""
        try:
            path = self._validate_and_resolve(storage_key)
            return path.is_file()
        except ValueError:
            return False

    def open(self, storage_key: str) -> BinaryIO:
        """Open binary read stream."""
        path = self._validate_and_resolve(storage_key)
        if not path.is_file():
            raise FileNotFoundError(f"Storage file not found: '{storage_key}'")
        return open(path, "rb")

    def delete(self, storage_key: str) -> bool:
        """Safely delete file from disk."""
        try:
            path = self._validate_and_resolve(storage_key)
            if path.is_file():
                path.unlink()
                return True
            return False
        except ValueError:
            return False

    def delete_project_storage(self, project_id: str) -> bool:
        """Safely remove the entire project asset directory."""
        project_assets_dir = (self.root_dir / "projects" / project_id).resolve()
        try:
            project_assets_dir.relative_to(self.root_dir)
            if project_assets_dir.is_dir():
                shutil.rmtree(project_assets_dir, ignore_errors=True)
                return True
            return False
        except ValueError:
            return False


_default_storage_provider: Optional[StorageProvider] = None


def get_storage_provider() -> StorageProvider:
    """Dependency injection factory for the configured StorageProvider."""
    global _default_storage_provider
    if _default_storage_provider is None:
        _default_storage_provider = LocalStorageProvider()
    return _default_storage_provider
