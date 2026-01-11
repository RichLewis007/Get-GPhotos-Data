"""Tree view demonstration with hierarchical data model.

Shows QTreeView with QStandardItemModel for displaying hierarchical/tree data.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QTreeView, QVBoxLayout, QWidget

from ..core.ui_loader import load_ui


class TreeViewDemo(QWidget):
    """Demonstration of QTreeView with hierarchical data model."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # Load UI from .ui file
        ui_widget = load_ui("tree_view_demo.ui", self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(ui_widget)

        # Find tree view widget
        tree_view = ui_widget.findChild(QTreeView, "tree_view")
        if tree_view is None:
            raise RuntimeError("tree_view not found in tree_view_demo.ui")
        self.tree_view = tree_view

        # Create and populate model
        self.model = QStandardItemModel(0, 1, self)
        self.model.setHeaderData(0, Qt.Orientation.Horizontal, "Name")

        # Build hierarchical structure
        root_item = self.model.invisibleRootItem()

        # Create sample folder structure
        projects_item = QStandardItem("Projects")
        projects_item.setEditable(False)
        root_item.appendRow(projects_item)

        project1 = QStandardItem("Web App")
        project1.setEditable(False)
        projects_item.appendRow(project1)
        project1.appendRow(QStandardItem("src/main.py"))
        project1.appendRow(QStandardItem("src/utils.py"))
        project1.appendRow(QStandardItem("README.md"))

        project2 = QStandardItem("Desktop App")
        project2.setEditable(False)
        projects_item.appendRow(project2)
        project2.appendRow(QStandardItem("main_window.py"))
        project2.appendRow(QStandardItem("dialogs.py"))

        documents_item = QStandardItem("Documents")
        documents_item.setEditable(False)
        root_item.appendRow(documents_item)
        documents_item.appendRow(QStandardItem("Notes.txt"))
        documents_item.appendRow(QStandardItem("Todo.md"))

        # Expand first level
        self.tree_view.setModel(self.model)
        self.tree_view.expandAll()
