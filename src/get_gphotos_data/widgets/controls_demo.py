"""Various input controls demonstration.

Shows QSpinBox, QDoubleSpinBox, QSlider, QCheckBox, QRadioButton, QComboBox, etc.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QLabel,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..core.ui_loader import load_ui


class ControlsDemo(QWidget):
    """Demonstration of various input controls."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # Load UI from .ui file
        ui_widget = load_ui("controls_demo.ui", self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(ui_widget)

        # Find widgets
        spin_box = ui_widget.findChild(QSpinBox, "spin_box")
        double_spin = ui_widget.findChild(QDoubleSpinBox, "double_spin")
        slider = ui_widget.findChild(QSlider, "slider")
        combo_box = ui_widget.findChild(QComboBox, "combo_box")
        value_label = ui_widget.findChild(QLabel, "value_label")

        if (
            spin_box is None
            or double_spin is None
            or slider is None
            or combo_box is None
            or value_label is None
        ):
            raise RuntimeError("Required widgets not found in controls_demo.ui")

        self.spin_box = spin_box
        self.double_spin = double_spin
        self.slider = slider
        self.combo_box = combo_box
        self.value_label = value_label

        # Connect signals
        self.spin_box.valueChanged.connect(self._on_spin_changed)
        self.double_spin.valueChanged.connect(self._on_double_spin_changed)
        self.slider.valueChanged.connect(self._on_slider_changed)

        # Populate combo box
        self.combo_box.addItems(["Option 1", "Option 2", "Option 3", "Option 4"])

    def _on_spin_changed(self, value: int) -> None:
        """Handle spin box value change."""
        self.value_label.setText(f"SpinBox value: {value}")

    def _on_double_spin_changed(self, value: float) -> None:
        """Handle double spin box value change."""
        self.value_label.setText(f"DoubleSpinBox value: {value:.2f}")

    def _on_slider_changed(self, value: int) -> None:
        """Handle slider value change."""
        self.value_label.setText(f"Slider value: {value}")
