"""Dialog demonstrations.

Shows various dialog types: QColorDialog, QFontDialog, QInputDialog, etc.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QColorDialog,
    QFontDialog,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core.ui_loader import load_ui


class DialogsDemo(QWidget):
    """Demonstration of various dialogs."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # Load UI from .ui file
        ui_widget = load_ui("dialogs_demo.ui", self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(ui_widget)

        # Find widgets
        self.color_button = ui_widget.findChild(QPushButton, "color_button")
        self.color_label = ui_widget.findChild(QLabel, "color_label")
        self.font_button = ui_widget.findChild(QPushButton, "font_button")
        self.font_label = ui_widget.findChild(QLabel, "font_label")
        self.text_input_btn = ui_widget.findChild(QPushButton, "text_input_btn")
        self.int_input_btn = ui_widget.findChild(QPushButton, "int_input_btn")
        self.double_input_btn = ui_widget.findChild(QPushButton, "double_input_btn")
        self.item_input_btn = ui_widget.findChild(QPushButton, "item_input_btn")
        self.info_btn = ui_widget.findChild(QPushButton, "info_btn")
        self.warning_btn = ui_widget.findChild(QPushButton, "warning_btn")
        self.question_btn = ui_widget.findChild(QPushButton, "question_btn")

        # Check each widget individually to help type checker
        if (
            self.color_button is None
            or self.color_label is None
            or self.font_button is None
            or self.font_label is None
            or self.text_input_btn is None
            or self.int_input_btn is None
            or self.double_input_btn is None
            or self.item_input_btn is None
            or self.info_btn is None
            or self.warning_btn is None
            or self.question_btn is None
        ):
            raise RuntimeError("Required widgets not found in dialogs_demo.ui")

        # Set initial stylesheet for color label
        self.color_label.setStyleSheet("background-color: #ffffff; padding: 10px;")

        # Connect signals
        self.color_button.clicked.connect(self._show_color_dialog)
        self.font_button.clicked.connect(self._show_font_dialog)
        self.text_input_btn.clicked.connect(self._show_text_input)
        self.int_input_btn.clicked.connect(self._show_int_input)
        self.double_input_btn.clicked.connect(self._show_double_input)
        self.item_input_btn.clicked.connect(self._show_item_input)
        self.info_btn.clicked.connect(self._show_info_message)
        self.warning_btn.clicked.connect(self._show_warning_message)
        self.question_btn.clicked.connect(self._show_question_message)

    def _show_color_dialog(self) -> None:
        """Show color dialog and update label."""
        if self.color_label is None:
            return
        color = QColorDialog.getColor(QColor(255, 255, 255), self, "Choose Color")
        if color.isValid():
            self.color_label.setStyleSheet(
                f"background-color: {color.name()}; padding: 10px; color: "
                f"{'white' if color.lightness() < 128 else 'black'};"
            )
            self.color_label.setText(f"Color: {color.name()}")

    def _show_font_dialog(self) -> None:
        """Show font dialog and update label."""
        if self.font_label is None:
            return
        font_result = QFontDialog.getFont(QFont("Arial", 12), self, "Choose Font")
        if isinstance(font_result, tuple) and len(font_result) == 2:
            font, ok = font_result
            if ok and isinstance(font, QFont):
                self.font_label.setFont(font)
                self.font_label.setText(f"Sample text ({font.family()}, {font.pointSize()}pt)")

    def _show_text_input(self) -> None:
        """Show text input dialog."""
        text, ok = QInputDialog.getText(self, "Text Input", "Enter text:")
        if ok and text:
            QMessageBox.information(self, "Result", f"You entered: {text}")

    def _show_int_input(self) -> None:
        """Show integer input dialog."""
        value, ok = QInputDialog.getInt(self, "Integer Input", "Enter number:", 0, 0, 100)
        if ok:
            QMessageBox.information(self, "Result", f"You entered: {value}")

    def _show_double_input(self) -> None:
        """Show double input dialog."""
        value, ok = QInputDialog.getDouble(
            self, "Double Input", "Enter number:", 0.0, 0.0, 100.0, 2
        )
        if ok:
            QMessageBox.information(self, "Result", f"You entered: {value:.2f}")

    def _show_item_input(self) -> None:
        """Show item selection dialog."""
        items = ["Apple", "Banana", "Cherry", "Date", "Elderberry"]
        item, ok = QInputDialog.getItem(self, "Item Selection", "Choose item:", items, 0, False)
        if ok:
            QMessageBox.information(self, "Result", f"You selected: {item}")

    def _show_info_message(self) -> None:
        """Show info message box."""
        QMessageBox.information(self, "Information", "This is an informational message.")

    def _show_warning_message(self) -> None:
        """Show warning message box."""
        QMessageBox.warning(self, "Warning", "This is a warning message!")

    def _show_question_message(self) -> None:
        """Show question message box."""
        reply = QMessageBox.question(
            self,
            "Question",
            "Do you want to proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Result", "You clicked Yes!")
        else:
            QMessageBox.information(self, "Result", "You clicked No.")
