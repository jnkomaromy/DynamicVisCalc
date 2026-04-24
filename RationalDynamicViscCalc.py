import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox,
    QLineEdit, QPushButton, QVBoxLayout,
    QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

from visc_engine import viscP, visc_kcl, FLUIDS

BLUE = {
    "bg":        "#0d1b2a",
    "panel":     "#1b2d45",
    "border":    "#1e3a5f",
    "accent":    "#1a6fbd",
    "accent_h":  "#2389e8",
    "text":      "#e0eeff",
    "muted":     "#7099c2",
    "result_bg": "#0f2340",
    "green":     "#3dd68c",
}

STYLESHEET = f"""
    QWidget {{
        background-color: {BLUE['bg']};
        color: {BLUE['text']};
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }}
    QLabel#title {{
        color: {BLUE['text']};
        font-size: 15px;
        font-weight: bold;
        letter-spacing: 1px;
    }}
    QLabel#subtitle {{
        color: {BLUE['muted']};
        font-size: 10px;
    }}
    QLabel#field_label {{
        color: {BLUE['muted']};
        font-size: 11px;
    }}
    QComboBox, QLineEdit {{
        background-color: {BLUE['panel']};
        border: 1px solid {BLUE['border']};
        border-radius: 6px;
        padding: 6px 10px;
        color: {BLUE['text']};
        font-size: 12px;
        selection-background-color: {BLUE['accent']};
    }}
    QComboBox:hover, QLineEdit:hover {{ border: 1px solid {BLUE['accent']}; }}
    QComboBox:focus, QLineEdit:focus {{ border: 1px solid {BLUE['accent_h']}; }}
    QComboBox QAbstractItemView {{
        background-color: {BLUE['panel']};
        border: 1px solid {BLUE['border']};
        selection-background-color: {BLUE['accent']};
        color: {BLUE['text']};
        padding: 4px;
    }}
    QComboBox::drop-down {{ border: none; padding-right: 8px; }}
    QPushButton {{
        background-color: {BLUE['accent']};
        color: {BLUE['text']};
        border: none;
        border-radius: 8px;
        padding: 10px 0;
        font-size: 13px;
        font-weight: bold;
        letter-spacing: 0.5px;
    }}
    QPushButton:hover {{ background-color: {BLUE['accent_h']}; }}
    QPushButton:pressed {{ background-color: {BLUE['accent']}; }}
    QFrame#card {{
        background-color: {BLUE['panel']};
        border: 1px solid {BLUE['border']};
        border-radius: 12px;
    }}
    QFrame#result_box {{
        background-color: {BLUE['result_bg']};
        border: 1px solid {BLUE['accent']};
        border-radius: 10px;
    }}
    QLabel#result_value {{
        color: {BLUE['green']};
        font-size: 22px;
        font-weight: bold;
    }}
    QLabel#result_detail {{
        color: {BLUE['muted']};
        font-size: 11px;
    }}
    QLabel#warning {{
        color: #e8a838;
        font-size: 10px;
    }}
"""


class ViscCalcApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rational Dynamic Viscosity Calculator")
        self.setMinimumWidth(420)
        self.setStyleSheet(STYLESHEET)
        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(16)

        title = QLabel("RATIONAL DYNAMIC VISC CALC")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Dynamic Viscosity  ·  cP  ·  powered by visc_engine")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)

        card_layout.addWidget(self._field_label("Fluid Type"))
        self.combo_fluid = QComboBox()
        self.combo_fluid.addItems(FLUIDS)
        self.combo_fluid.currentTextChanged.connect(self._on_fluid_changed)
        card_layout.addWidget(self.combo_fluid)

        # KCl concentration field — visible only when KCl is selected
        self.kcl_label = self._field_label("KCl Concentration (mol/kg H₂O)")
        self.entry_molality = QLineEdit()
        self.entry_molality.setPlaceholderText("e.g.  1.012  (default = 7 wt%)")
        card_layout.addWidget(self.kcl_label)
        card_layout.addWidget(self.entry_molality)
        self.kcl_label.setVisible(False)
        self.entry_molality.setVisible(False)

        card_layout.addWidget(self._field_label("Temperature (°F)"))
        self.entry_temp = QLineEdit()
        self.entry_temp.setPlaceholderText("e.g.  72")
        card_layout.addWidget(self.entry_temp)

        card_layout.addWidget(self._field_label("Test Pressure (psi)"))
        self.entry_pressure = QLineEdit()
        self.entry_pressure.setPlaceholderText("e.g.  500  (0 = no correction)")
        card_layout.addWidget(self.entry_pressure)

        warn = QLabel("Pressure correction coefficients (alpha) are placeholders — see visc_engine.py TODOs.")
        warn.setObjectName("warning")
        warn.setWordWrap(True)
        card_layout.addWidget(warn)

        root_layout.addWidget(card)

        btn = QPushButton("Calculate Viscosity")
        btn.clicked.connect(self._calculate)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setColor(QColor(26, 111, 189, 160))
        shadow.setOffset(0, 4)
        btn.setGraphicsEffect(shadow)
        root_layout.addWidget(btn)

        self.result_box = QFrame()
        self.result_box.setObjectName("result_box")
        result_layout = QVBoxLayout(self.result_box)
        result_layout.setContentsMargins(16, 14, 16, 14)
        result_layout.setSpacing(4)

        self.result_value = QLabel("—")
        self.result_value.setObjectName("result_value")
        self.result_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_detail = QLabel("")
        self.result_detail.setObjectName("result_detail")
        self.result_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)

        result_layout.addWidget(self.result_value)
        result_layout.addWidget(self.result_detail)
        root_layout.addWidget(self.result_box)

    def _field_label(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("field_label")
        return lbl

    def _on_fluid_changed(self, fluid_name):
        is_kcl = fluid_name == "KCl"
        self.kcl_label.setVisible(is_kcl)
        self.entry_molality.setVisible(is_kcl)

    def _calculate(self):
        try:
            fluid = self.combo_fluid.currentText()
            temp  = float(self.entry_temp.text())
            pres  = float(self.entry_pressure.text()) if self.entry_pressure.text().strip() else 0.0

            if fluid == "KCl":
                mol_text = self.entry_molality.text().strip()
                molality = float(mol_text) if mol_text else 1.012
                visc = visc_kcl(temp, pres, molality)
                fluid_label = f"KCl  {molality} mol/kg"
            else:
                visc = viscP(fluid, temp, pres)
                fluid_label = fluid

            self.result_value.setText(f"{visc} cP")
            self.result_detail.setText(f"{fluid_label}   ·   {temp}°F   ·   {pres} psi")
        except ValueError:
            self.result_value.setText("Invalid input")
            self.result_detail.setText("Check temperature and pressure fields.")
        except Exception as e:
            self.result_value.setText("Error")
            self.result_detail.setText(str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ViscCalcApp()
    window.show()
    sys.exit(app.exec())
