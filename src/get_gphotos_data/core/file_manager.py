"""File management functionality.

This module provides file operations including:
- Recent files list management
- File validation and cleanup
- Recent files persistence via Settings

Separated from MainWindow to improve modularity and testability.
"""

from __future__ import annotations

from pathlib import Path

from .settings import Settings


class FileManager:
    """Manages file operations and recent files list."""

    def __init__(self, settings: Settings, max_recent_files: int | None = None) -> None:
        """Initialize file manager.

        Args:
            settings: Settings instance for persisting recent files
            max_recent_files: Maximum number of recent files to remember.
                            If None, uses value from settings (default: 10).
        """
        self.settings = settings
        self._max_recent_files = max_recent_files

    @property
    def max_recent_files(self) -> int:
        """Get maximum number of recent files from settings or cached value."""
        if self._max_recent_files is None:
            return self.settings.get_max_recent_files()
        return self._max_recent_files

    def get_recent_files(self) -> list[Path]:
        """Load and validate recent files from settings.

        Removes duplicates, filters out non-existent files, and updates
        settings if the list was cleaned.

        Returns:
            List of valid recent file paths
        """
        recent: list[Path] = []
        seen: set[str] = set()
        raw = self.settings.get_recent_files()
        # Process each item, removing duplicates and invalid files
        for item in raw:
            path = Path(item).expanduser()
            if not path.is_file():
                continue
            key = str(path)
            if key in seen:
                continue
            recent.append(path)
            seen.add(key)
        # Update settings if we removed any invalid entries
        stored = [str(path) for path in recent]
        if stored != raw:
            self.settings.set_recent_files(stored)
        return recent

    def add_recent_file(self, path: Path) -> None:
        """Add a file to the recent files list, moving it to the top.

        Args:
            path: Path to the file to remember
        """
        path_str = str(path)
        # Put current file at the top
        recent = [path_str]
        # Add existing recent files, excluding the current one
        for item in self.settings.get_recent_files():
            if item != path_str:
                recent.append(item)
        # Limit to max and save (always use current setting value)
        max_files = self.settings.get_max_recent_files()
        self.settings.set_recent_files(recent[:max_files])

    def clear_recent_files(self) -> None:
        """Clear all recent files from the list."""
        self.settings.set_recent_files([])
