"""System tray integration.

This module provides system tray (notification area) functionality:
- Tray icon with application icon
- Context menu with quick actions (show/hide/quit)
- Notification messages
- Click/double-click handling to restore window

The system tray is only available on platforms that support it.
The module gracefully handles cases where the system tray is not available.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from .paths import app_icon_bytes


class SystemTray(QObject):
    """System tray integration with notifications and quick actions."""

    activated = Signal(QSystemTrayIcon.ActivationReason)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.log = logging.getLogger(__name__)
        self.tray_icon: QSystemTrayIcon | None = None
        self._setup_tray()

    def _setup_tray(self) -> None:
        """Initialize system tray icon."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.log.warning("System tray is not available on this system")
            return

        self.tray_icon = QSystemTrayIcon(self)

        # Set icon
        try:
            icon_bytes = app_icon_bytes()
            pixmap = QPixmap()
            if pixmap.loadFromData(icon_bytes):
                self.tray_icon.setIcon(QIcon(pixmap))
        except Exception as e:
            self.log.warning("Failed to load tray icon: %s", e)

        # Set tooltip
        from .paths import APP_NAME

        self.tray_icon.setToolTip(APP_NAME)

        # Connect activation signal
        self.tray_icon.activated.connect(self.activated.emit)

    def set_visible(self, visible: bool) -> None:
        """Show or hide the system tray icon."""
        if self.tray_icon:
            self.tray_icon.setVisible(visible)

    def show_message(
        self,
        title: str,
        message: str,
        icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
        duration: int = 5000,
    ) -> None:
        """Show a notification message in the system tray."""
        if self.tray_icon:
            self.tray_icon.showMessage(title, message, icon, duration)

    def set_context_menu(self, menu: QMenu) -> None:
        """Set the context menu for the system tray icon."""
        if self.tray_icon:
            self.tray_icon.setContextMenu(menu)

    def create_default_menu(
        self,
        show_action: Callable[[], None],
        hide_action: Callable[[], None],
        quit_action: Callable[[], None],
    ) -> QMenu:
        """Create a default context menu with common actions."""
        menu = QMenu()

        show_item = QAction("Show", menu)
        show_item.triggered.connect(show_action)
        menu.addAction(show_item)

        hide_item = QAction("Hide", menu)
        hide_item.triggered.connect(hide_action)
        menu.addAction(hide_item)

        menu.addSeparator()

        quit_item = QAction("Quit", menu)
        quit_item.triggered.connect(quit_action)
        menu.addAction(quit_item)

        return menu

    def is_available(self) -> bool:
        """Check if system tray is available."""
        return QSystemTrayIcon.isSystemTrayAvailable() and self.tray_icon is not None
