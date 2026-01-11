"""Preferences dialog for application settings.

This dialog allows users to modify application preferences:
- Last open directory path
- Theme selection (light/dark)
- Splash screen configuration (enable/disable, duration)
- Maximum number of recent files to remember
- Clear recent files list
- Reset all settings to defaults

Settings are validated before saving, and the dialog emits a signal
when the theme changes so the application can update immediately.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..core.settings import Settings
from ..core.ui_loader import load_ui


class PreferencesDialog(QDialog):
    """Dialog for editing user preferences with validation and theme switching."""

    theme_changed = Signal(str)  # Emitted when theme changes

    def __init__(self, settings: Settings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self._settings = settings
        self._ui: QWidget
        self.button_box: QDialogButtonBox
        self.theme_combo: QComboBox
        self.last_dir: QLineEdit
        self.splash_enabled_check: QCheckBox
        self.splash_seconds_spin: QSpinBox
        self.max_recent_files_spin: QSpinBox
        self.clear_recent_files_btn: QPushButton

        self._ui = load_ui("preferences_dialog.ui", self)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self._ui)

        # Find all widgets from the UI file
        last_dir = self._ui.findChild(QLineEdit, "lastDirLineEdit")
        if last_dir is None:
            raise RuntimeError("lastDirLineEdit not found in preferences_dialog.ui")
        self.last_dir = last_dir
        self.last_dir.setText(self._settings.get_str(self._settings.keys.last_open_dir, ""))

        theme_combo = self._ui.findChild(QComboBox, "themeComboBox")
        if theme_combo is None:
            raise RuntimeError("themeComboBox not found in preferences_dialog.ui")
        self.theme_combo = theme_combo
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setCurrentText(self._settings.get_theme())

        splash_enabled_check = self._ui.findChild(QCheckBox, "splashEnabledCheckBox")
        if splash_enabled_check is None:
            raise RuntimeError("splashEnabledCheckBox not found in preferences_dialog.ui")
        self.splash_enabled_check = splash_enabled_check
        splash_seconds = self._settings.get_splash_screen_seconds()
        self.splash_enabled_check.setChecked(splash_seconds is not None)

        splash_seconds_spin = self._ui.findChild(QSpinBox, "splashSecondsSpinBox")
        if splash_seconds_spin is None:
            raise RuntimeError("splashSecondsSpinBox not found in preferences_dialog.ui")
        self.splash_seconds_spin = splash_seconds_spin
        # Set value: if None or 0, set to 0 (until OK), otherwise use the value
        splash_value = splash_seconds if splash_seconds is not None and splash_seconds > 0 else 0
        self.splash_seconds_spin.setValue(splash_value)

        splash_seconds_label = self._ui.findChild(QLabel, "splashSecondsLabel")
        if splash_seconds_label is None:
            raise RuntimeError("splashSecondsLabel not found in preferences_dialog.ui")

        # Enable/disable spinbox and label based on checkbox
        self.splash_seconds_spin.setEnabled(self.splash_enabled_check.isChecked())
        splash_seconds_label.setEnabled(self.splash_enabled_check.isChecked())
        self.splash_enabled_check.toggled.connect(self.splash_seconds_spin.setEnabled)
        self.splash_enabled_check.toggled.connect(splash_seconds_label.setEnabled)

        max_recent_files_spin = self._ui.findChild(QSpinBox, "maxRecentFilesSpinBox")
        if max_recent_files_spin is None:
            raise RuntimeError("maxRecentFilesSpinBox not found in preferences_dialog.ui")
        self.max_recent_files_spin = max_recent_files_spin
        self.max_recent_files_spin.setValue(self._settings.get_max_recent_files())

        clear_recent_files_btn = self._ui.findChild(QPushButton, "clearRecentFilesButton")
        if clear_recent_files_btn is None:
            raise RuntimeError("clearRecentFilesButton not found in preferences_dialog.ui")
        self.clear_recent_files_btn = clear_recent_files_btn
        self.clear_recent_files_btn.clicked.connect(self._on_clear_recent_files)

        reset_button = self._ui.findChild(QPushButton, "resetToDefaultsButton")
        if reset_button is None:
            raise RuntimeError("resetToDefaultsButton not found in preferences_dialog.ui")
        reset_button.clicked.connect(self._on_reset_defaults)

        button_box = self._ui.findChild(QDialogButtonBox, "buttonBox")
        if button_box is None:
            raise RuntimeError("buttonBox not found in preferences_dialog.ui")
        self.button_box = button_box
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def _on_reset_defaults(self) -> None:
        """Handle reset to defaults button click."""
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "This will reset all preferences to their default values.\n\n"
            "This action cannot be undone. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._settings.reset_to_defaults()
            # Reload current values
            self.last_dir.setText(self._settings.get_str(self._settings.keys.last_open_dir, ""))
            self.theme_combo.setCurrentText(self._settings.get_theme())
            # Reset splash screen preference
            splash_seconds = self._settings.get_splash_screen_seconds()
            self.splash_enabled_check.setChecked(splash_seconds is not None)
            if splash_seconds is not None and splash_seconds > 0:
                splash_value = splash_seconds
            else:
                splash_value = 0
            self.splash_seconds_spin.setValue(splash_value)
            # Reset max recent files
            self.max_recent_files_spin.setValue(self._settings.get_max_recent_files())

    def accept(self) -> None:
        """Validate and save preferences."""
        from PySide6.QtWidgets import QMessageBox

        # Validate last open dir
        last_dir_text = self.last_dir.text().strip()
        if not self._settings.validate_last_open_dir(last_dir_text):
            QMessageBox.warning(
                self,
                "Invalid Directory",
                f"The directory path is invalid:\n{last_dir_text}\n\n"
                "Please enter a valid directory path or leave it empty to use the home directory.",
            )
            return

        # Validate theme
        new_theme = self.theme_combo.currentText()
        if not self._settings.validate_theme(new_theme):
            QMessageBox.warning(
                self,
                "Invalid Theme",
                f"Invalid theme selected: {new_theme}",
            )
            return

        # Save preferences
        old_theme = self._settings.get_theme()
        self._settings.set_str(self._settings.keys.last_open_dir, last_dir_text)
        self._settings.set_theme(new_theme)

        # Save splash screen preference
        if self.splash_enabled_check.isChecked():
            splash_value = self.splash_seconds_spin.value()
            # 0 means "until OK clicked", so store as 0
            self._settings.set_splash_screen_seconds(splash_value)
        else:
            # Not enabled, remove setting (defaults to None = don't show)
            self._settings.set_splash_screen_seconds(None)

        # Save max recent files
        self._settings.set_max_recent_files(self.max_recent_files_spin.value())

        if old_theme != new_theme:
            self.theme_changed.emit(new_theme)

        super().accept()

    def _on_clear_recent_files(self) -> None:
        """Handle clear recent files button click."""
        from PySide6.QtWidgets import QMessageBox

        recent_count = len(self._settings.get_recent_files())
        if recent_count == 0:
            QMessageBox.information(
                self,
                "Clear Recent Files",
                "There are no recent files to clear.",
            )
            return

        reply = QMessageBox.question(
            self,
            "Clear Recent Files",
            f"This will remove {recent_count} file(s) from the recent files list.\n\n"
            "This action cannot be undone. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._settings.set_recent_files([])
            QMessageBox.information(
                self,
                "Recent Files Cleared",
                f"Cleared {recent_count} file(s) from the recent files list.",
            )
