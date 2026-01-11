"""Table view demonstration with data model.

Shows QTableView with QStandardItemModel for displaying tabular data.
"""

from __future__ import annotations

from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QTableView, QVBoxLayout, QWidget

from ..core.ui_loader import load_ui


class TableViewDemo(QWidget):
    """Demonstration of QTableView with data model."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # Load UI from .ui file
        ui_widget = load_ui("table_view_demo.ui", self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(ui_widget)

        # Find table view widget
        table_view = ui_widget.findChild(QTableView, "table_view")
        if table_view is None:
            raise RuntimeError("table_view not found in table_view_demo.ui")
        self.table_view = table_view

        # Create and populate model
        self.model = QStandardItemModel(0, 4, self)
        self.model.setHorizontalHeaderLabels(["Name", "Type", "Size", "Modified"])

        # Add sample data
        sample_data = [
            ("document.pdf", "PDF", "2.4 MB", "2024-01-15"),
            ("image.png", "Image", "1.8 MB", "2024-01-14"),
            ("spreadsheet.xlsx", "Excel", "456 KB", "2024-01-13"),
            ("presentation.pptx", "PowerPoint", "5.2 MB", "2024-01-12"),
            ("archive.zip", "Archive", "12.3 MB", "2024-01-11"),
        ]

        for row_data in sample_data:
            row = []
            for item_data in row_data:
                item = QStandardItem(item_data)
                item.setEditable(False)
                row.append(item)
            self.model.appendRow(row)

        # Set column widths
        self.table_view.setModel(self.model)
        self.table_view.setColumnWidth(0, 200)
        self.table_view.setColumnWidth(1, 100)
        self.table_view.setColumnWidth(2, 100)
        self.table_view.setColumnWidth(3, 150)
