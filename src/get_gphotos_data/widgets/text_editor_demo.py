"""Rich text editor demonstration.

Shows QTextEdit with rich text formatting capabilities.
"""

from __future__ import annotations

from PySide6.QtGui import QTextCharFormat
from PySide6.QtWidgets import QPushButton, QTextEdit, QVBoxLayout, QWidget

from ..core.ui_loader import load_ui


class TextEditorDemo(QWidget):
    """Demonstration of QTextEdit with rich text formatting."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # Load UI from .ui file
        ui_widget = load_ui("text_editor_demo.ui", self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(ui_widget)

        # Find widgets
        bold_btn = ui_widget.findChild(QPushButton, "bold_btn")
        italic_btn = ui_widget.findChild(QPushButton, "italic_btn")
        underline_btn = ui_widget.findChild(QPushButton, "underline_btn")
        text_edit = ui_widget.findChild(QTextEdit, "text_edit")

        if bold_btn is None or italic_btn is None or underline_btn is None or text_edit is None:
            raise RuntimeError("Required widgets not found in text_editor_demo.ui")

        self.bold_btn = bold_btn
        self.italic_btn = italic_btn
        self.underline_btn = underline_btn
        self.text_edit = text_edit

        # Connect signals
        self.bold_btn.clicked.connect(self._toggle_bold)
        self.italic_btn.clicked.connect(self._toggle_italic)
        self.underline_btn.clicked.connect(self._toggle_underline)
        self.text_edit.cursorPositionChanged.connect(self._update_format_buttons)

        # Set some sample formatted text
        self.text_edit.setHtml(
            "<h1>Rich Text Editor</h1>"
            "<p>This is a <b>bold</b> text editor with <i>formatting</i> capabilities.</p>"
            "<p>You can use <u>underlining</u> and other formatting options.</p>"
            "<ul><li>Item 1</li><li>Item 2</li><li>Item 3</li></ul>"
        )

    def _toggle_bold(self) -> None:
        """Toggle bold formatting."""
        if self.bold_btn.isChecked():
            self._set_format(700)  # Bold weight
        else:
            self._set_format(400)  # Normal weight

    def _toggle_italic(self) -> None:
        """Toggle italic formatting."""
        format_obj = QTextCharFormat()
        format_obj.setFontItalic(self.italic_btn.isChecked())
        self._apply_format(format_obj)

    def _toggle_underline(self) -> None:
        """Toggle underline formatting."""
        format_obj = QTextCharFormat()
        format_obj.setUnderlineStyle(
            QTextCharFormat.UnderlineStyle.SingleUnderline
            if self.underline_btn.isChecked()
            else QTextCharFormat.UnderlineStyle.NoUnderline
        )
        self._apply_format(format_obj)

    def _set_format(self, weight: int) -> None:
        """Set font weight."""
        format_obj = QTextCharFormat()
        format_obj.setFontWeight(weight)
        self._apply_format(format_obj)

    def _apply_format(self, format_obj: QTextCharFormat) -> None:
        """Apply format to current selection or at cursor."""
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            cursor.mergeCharFormat(format_obj)
        else:
            format_obj.merge(cursor.charFormat())
            cursor.setCharFormat(format_obj)
        self.text_edit.setFocus()

    def _update_format_buttons(self) -> None:
        """Update button states based on current formatting."""
        cursor = self.text_edit.textCursor()
        char_format = cursor.charFormat()

        # FontWeight returns an int, Bold is typically 700
        self.bold_btn.setChecked(char_format.fontWeight() >= 700)
        self.italic_btn.setChecked(char_format.fontItalic())
        is_underlined = char_format.underlineStyle() != QTextCharFormat.UnderlineStyle.NoUnderline
        self.underline_btn.setChecked(is_underlined)
