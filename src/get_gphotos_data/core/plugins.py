"""Plugin system using Python entry points.

This module provides a plugin management system that loads plugins
registered via setuptools entry points. Plugins can:
- Register commands for the command palette
- Implement hook methods that are called by the application
- Extend application functionality without modifying core code

Plugins are discovered from the 'get_gphotos_data.plugins' entry point group.
Each plugin can implement hook methods and command registration.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points  # type: ignore[no-redef]


class PluginManager:
    """Manages plugins loaded via entry points."""

    def __init__(self, entry_point_group: str = "get_gphotos_data.plugins") -> None:
        self.log = logging.getLogger(__name__)
        self.entry_point_group = entry_point_group
        self.plugins: dict[str, Any] = {}
        self._load_plugins()

    def _load_plugins(self) -> None:
        """Load all plugins registered via entry points."""
        try:
            eps = entry_points(group=self.entry_point_group)
            for ep in eps:
                try:
                    plugin = ep.load()
                    self.plugins[ep.name] = plugin
                    self.log.info("Loaded plugin: %s", ep.name)
                except Exception as e:
                    self.log.error("Failed to load plugin %s: %s", ep.name, e)
        except Exception as e:
            self.log.debug("No plugins found or error loading plugins: %s", e)

    def get_plugin(self, name: str) -> Any | None:
        """Get a plugin by name."""
        return self.plugins.get(name)

    def get_all_plugins(self) -> dict[str, Any]:
        """Get all loaded plugins."""
        return self.plugins.copy()

    def call_hook(self, hook_name: str, *args: Any, **kwargs: Any) -> list[Any]:
        """
        Call a hook on all plugins that support it.

        Args:
            hook_name: Name of the hook method to call
            *args: Positional arguments to pass to the hook
            **kwargs: Keyword arguments to pass to the hook

        Returns:
            List of return values from plugin hooks (None values are filtered out)
        """
        results = []
        for name, plugin in self.plugins.items():
            hook = getattr(plugin, hook_name, None)
            if hook and callable(hook):
                try:
                    result = hook(*args, **kwargs)
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    self.log.error("Error calling hook %s on plugin %s: %s", hook_name, name, e)
        return results

    def register_commands(
        self, command_registry: Callable[[str, str, str, Callable], None]
    ) -> None:
        """
        Register commands from plugins.

        Args:
            command_registry: Function to register a command (name, description, shortcut, action)
        """
        for name, plugin in self.plugins.items():
            if hasattr(plugin, "register_commands"):
                try:
                    plugin.register_commands(command_registry)
                    self.log.debug("Registered commands from plugin: %s", name)
                except Exception as e:
                    self.log.error("Error registering commands from plugin %s: %s", name, e)
