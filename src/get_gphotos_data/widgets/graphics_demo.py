"""Graphics view demonstration.

Shows QGraphicsView with QGraphicsScene for custom graphics rendering.
"""

from __future__ import annotations

from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QVBoxLayout,
    QWidget,
)

from ..core.ui_loader import load_ui


class GraphicsDemo(QWidget):
    """Demonstration of QGraphicsView with custom graphics."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # Load UI from .ui file
        ui_widget = load_ui("graphics_demo.ui", self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(ui_widget)

        # Find graphics view widget
        graphics_view = ui_widget.findChild(QGraphicsView, "graphics_view")
        if graphics_view is None:
            raise RuntimeError("graphics_view not found in graphics_demo.ui")
        self.graphics_view = graphics_view

        # Create scene
        self.scene = QGraphicsScene(self)
        self.graphics_view.setScene(self.scene)
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Add some sample graphics items
        # Rectangle
        rect = QGraphicsRectItem(50, 50, 100, 80)
        rect.setBrush(QBrush(QColor(100, 150, 200)))
        rect.setPen(QPen(QColor(0, 0, 0), 2))
        self.scene.addItem(rect)

        # Circle
        ellipse = QGraphicsEllipseItem(200, 50, 100, 100)
        ellipse.setBrush(QBrush(QColor(200, 100, 100)))
        ellipse.setPen(QPen(QColor(0, 0, 0), 2))
        self.scene.addItem(ellipse)

        # Text
        text = QGraphicsTextItem("Graphics View Demo")
        text.setPos(50, 180)
        text.setDefaultTextColor(QColor(0, 0, 0))
        self.scene.addItem(text)

        # Another rectangle
        rect2 = QGraphicsRectItem(200, 200, 120, 60)
        rect2.setBrush(QBrush(QColor(100, 200, 100)))
        rect2.setPen(QPen(QColor(0, 0, 0), 2))
        self.scene.addItem(rect2)

        # Set scene rectangle to fit all items
        self.scene.setSceneRect(0, 0, 400, 300)
