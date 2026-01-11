"""Calendar widget demonstration.

Shows QCalendarWidget for date selection.
"""

from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QCalendarWidget, QLabel, QVBoxLayout, QWidget

from ..core.ui_loader import load_ui


class CalendarDemo(QWidget):
    """Demonstration of QCalendarWidget."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # Load UI from .ui file
        ui_widget = load_ui("calendar_demo.ui", self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(ui_widget)

        # Find widgets
        calendar = ui_widget.findChild(QCalendarWidget, "calendar")
        date_label = ui_widget.findChild(QLabel, "date_label")

        if calendar is None or date_label is None:
            raise RuntimeError("Required widgets not found in calendar_demo.ui")

        self.calendar = calendar
        self.date_label = date_label

        # Configure calendar
        self.calendar.setSelectedDate(QDate.currentDate())
        self.calendar.selectionChanged.connect(self._on_date_selected)

        # Show initial date
        self._on_date_selected()

    def _on_date_selected(self) -> None:
        """Handle date selection."""
        selected_date = self.calendar.selectedDate()
        self.date_label.setText(f"Selected date: {selected_date.toString('yyyy-MM-dd (dddd)')}")
