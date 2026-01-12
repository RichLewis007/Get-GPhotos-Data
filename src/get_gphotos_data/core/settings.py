"""Settings management using QSettings.

This module provides a typed wrapper around Qt's QSettings for persistent
application settings. It centralizes setting keys and provides convenience
methods for common data types (strings, string lists, window state, etc.).

Settings are automatically persisted to platform-appropriate locations:
- macOS: ~/Library/Preferences/
- Windows: Registry
- Linux: ~/.config/
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QSettings


@dataclass(frozen=True)
class SettingsKeys:
    """Centralize QSettings keys used by the application."""

    last_open_dir: str = "paths/last_open_dir"
    theme: str = "ui/theme"
    recent_files: str = "files/recent"
    max_recent_files: str = "files/max_recent_files"
    window_geometry: str = "window/geometry"
    window_state: str = "window/state"
    splash_screen_seconds: str = "ui/splash_screen_seconds"
    debug_api: str = "debug/api_logging"


class Settings:
    """Wrapper around QSettings with convenience getters/setters."""

    def __init__(self) -> None:
        self._qs = QSettings()
        self.keys = SettingsKeys()

    def get_str(self, key: str, default: str = "") -> str:
        value = self._qs.value(key, defaultValue=default)
        return str(value) if value is not None else default

    def set_str(self, key: str, value: str) -> None:
        self._qs.setValue(key, value)

    def get_str_list(self, key: str, default: list[str] | None = None) -> list[str]:
        if default is None:
            default = []
        value = self._qs.value(key, defaultValue=default)
        if value is None:
            return list(default)
        if isinstance(value, (list, tuple)):
            return [str(item) for item in value]
        if isinstance(value, str):
            return [value] if value else []
        return [str(value)]

    def set_str_list(self, key: str, values: list[str]) -> None:
        self._qs.setValue(key, list(values))

    def get_recent_files(self) -> list[str]:
        return self.get_str_list(self.keys.recent_files, [])

    def set_recent_files(self, files: list[str]) -> None:
        self.set_str_list(self.keys.recent_files, files)

    def get_theme(self) -> str:
        return self.get_str(self.keys.theme, "light")

    def set_theme(self, theme: str) -> None:
        self.set_str(self.keys.theme, theme)

    def get_window_geometry(self) -> bytes | None:
        """Get saved window geometry as bytes, or None if not set."""
        value = self._qs.value(self.keys.window_geometry)
        if value is None:
            return None
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            try:
                return value.encode("latin1")
            except UnicodeEncodeError:
                return None
        return None

    def set_window_geometry(self, geometry: bytes) -> None:
        """Save window geometry as bytes."""
        self._qs.setValue(self.keys.window_geometry, geometry)

    def get_window_state(self) -> bytes | None:
        """Get saved window state as bytes, or None if not set."""
        value = self._qs.value(self.keys.window_state)
        if value is None:
            return None
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            try:
                return value.encode("latin1")
            except UnicodeEncodeError:
                return None
        return None

    def set_window_state(self, state: bytes) -> None:
        """Save window state (toolbars, docks, etc.) as bytes."""
        self._qs.setValue(self.keys.window_state, state)

    def reset_to_defaults(self) -> None:
        """Reset all settings to their default values."""
        self._qs.clear()

    def validate_last_open_dir(self, path_str: str) -> bool:
        """Validate that last_open_dir is a valid directory path."""
        if not path_str:
            return True  # Empty is valid (will use home directory)
        from pathlib import Path

        try:
            path = Path(path_str).expanduser()
            return path.is_dir()
        except (OSError, ValueError):
            return False

    def validate_theme(self, theme: str) -> bool:
        """Validate that theme is one of the supported themes."""
        return theme in ("light", "dark")

    def get_splash_screen_seconds(self) -> int | None:
        """Get splash screen display duration in seconds.

        Returns:
            Number of seconds to show splash screen (0 = show until user clicks OK),
            or None to not show it (default).
        """
        value = self._qs.value(self.keys.splash_screen_seconds)
        if value is None:
            return None
        try:
            return int(str(value))
        except (ValueError, TypeError):
            return None

    def set_splash_screen_seconds(self, seconds: int | None) -> None:
        """Set splash screen display duration in seconds.

        Args:
            seconds: Number of seconds to show splash screen (0 = show until user clicks OK),
                    or None to not show it (removes the setting).
        """
        if seconds is None:
            self._qs.remove(self.keys.splash_screen_seconds)
        else:
            self._qs.setValue(self.keys.splash_screen_seconds, seconds)

    def get_max_recent_files(self) -> int:
        """Get maximum number of recent files to remember.

        Returns:
            Maximum number of recent files (default: 10).
        """
        value = self._qs.value(self.keys.max_recent_files)
        if value is None:
            return 10  # Default value
        try:
            int_value = int(str(value))
            # Ensure reasonable bounds (1-100)
            return max(1, min(100, int_value))
        except (ValueError, TypeError):
            return 10

    def set_max_recent_files(self, max_files: int) -> None:
        """Set maximum number of recent files to remember.

        Args:
            max_files: Maximum number of recent files (1-100).
        """
        # Ensure reasonable bounds
        clamped = max(1, min(100, max_files))
        self._qs.setValue(self.keys.max_recent_files, clamped)

    def get_debug_api(self) -> bool:
        """Get API debug logging setting.

        Returns:
            True if API debug logging is enabled (default: True).
        """
        value = self._qs.value(self.keys.debug_api)
        if value is None:
            return True  # Default to enabled
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, str)):
            # Support both 1/0 and "true"/"false"
            return str(value).lower() in ("1", "true", "yes")
        return True

    def set_debug_api(self, enabled: bool) -> None:
        """Set API debug logging setting.

        Args:
            enabled: Whether to enable API debug logging.
        """
        self._qs.setValue(self.keys.debug_api, enabled)
