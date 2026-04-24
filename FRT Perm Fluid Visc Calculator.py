import sys
import math
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox,
    QLineEdit, QPushButton, QVBoxLayout,
    QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

# ============================================================
# FRT Permeability Fluid Dynamic Viscosity Calculator
# ============================================================
# Calculates dynamic viscosity (cP) as a function of
# TEMPERATURE (°F) and PRESSURE (psi).
#
# Temperature model: rational function fit to measured data
#   visc(T) = a/(T-x0)^2 + b/(T-x0) + c
#
# Pressure correction: Barus equation applied on top of visc(T)
#   visc(T,P) = visc(T) * exp(alpha * P)
#   where alpha [1/psi] is the pressure-viscosity coefficient.
#
# NOTE ON alpha VALUES:
#   The alpha placeholders below are currently set to 0.0,
#   meaning NO pressure correction is applied until you supply
#   measured or literature values for each fluid. Typical
#   order of magnitude: brines ~1e-6 to 1e-5 psi^-1 (small),
#   light hydrocarbons ~1e-5 to 1e-4 psi^-1 (more significant
#   at high confining pressures). Replace the 0.0 values once
#   you have them — the math is already wired in.
# ============================================================

BLUE = {
    "bg":        "#0d1b2a",   # deep navy background
    "panel":     "#1b2d45",   # card / panel surface
    "border":    "#1e3a5f",   # subtle border
    "accent":    "#1a6fbd",   # primary blue accent
    "accent_h":  "#2389e8",   # hover / highlight
    "text":      "#e0eeff",   # primary text
    "muted":     "#7099c2",   # secondary / label text
    "result_bg": "#0f2340",   # result display background
    "green":     "#3dd68c",   # success result value
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

    QComboBox:hover, QLineEdit:hover {{
        border: 1px solid {BLUE['accent']};
    }}

    QComboBox:focus, QLineEdit:focus {{
        border: 1px solid {BLUE['accent_h']};
    }}

    QComboBox QAbstractItemView {{
        background-color: {BLUE['panel']};
        border: 1px solid {BLUE['border']};
        selection-background-color: {BLUE['accent']};
        color: {BLUE['text']};
        padding: 4px;
    }}

    QComboBox::drop-down {{
        border: none;
        padding-right: 8px;
    }}

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

    QPushButton:hover {{
        background-color: {BLUE['accent_h']};
    }}

    QPushButton:pressed {{
        background-color: {BLUE['accent']};
    }}

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


def visc_rational(a, b, c, x_0, temp):
    # Rational function temperature model.
    return a * ((temp - x_0) ** -2) + b * ((temp - x_0) ** -1) + c


def barus_correction(visc_T, alpha, pressure_psi):
    # Barus pressure correction: mu(T,P) = mu(T) * exp(alpha * P)
    return visc_T * math.exp(alpha * pressure_psi)


def viscP(fluid_type, temp, pressure_psi=0.0):
    # Returns dynamic viscosity in cP at temperature (°F) and pressure (psi).

    if fluid_type == "7% KCl":
        a, b, c, x_0 = 14118.60487982875, 28.197267, 0.01992939, -68.2154
        alpha = 0.0  # TODO: replace with measured alpha for 7% KCl
        visc_T = visc_rational(a, b, c, x_0, temp)

    elif fluid_type == "Soltrol 130":
        a, b, c, x_0 = -2330, 172, -0.0177, 0
        alpha = 0.0  # TODO: replace with measured alpha for Soltrol 130
        density_correction = 0.7815 - (temp * 0.0003961)
        visc_T = visc_rational(a, b, c, x_0, temp) * density_correction

    elif fluid_type == "Sea Water":
        a, b, c, x_0 = 14811.8, 29.2862, 0.01149865, -64.6513
        alpha = 0.0  # TODO: replace with measured alpha for sea water
        visc_T = visc_rational(a, b, c, x_0, temp)

    elif fluid_type == "13.0 lbm/gal CaBr2":
        a, b, c, x_0 = 60000, 150, 0, -85
        alpha = 0.0  # TODO: replace with measured alpha for 13.0 lb/gal CaBr2
        visc_T = visc_rational(a, b, c, x_0, temp)

    elif fluid_type == "Fresh Water":
        a, b, c, x_0 = 16504.9, 10.8518, 0.032894, -68.2154
        alpha = 0.0  # TODO: replace with measured alpha for fresh water
        visc_T = visc_rational(a, b, c, x_0, temp)

    else:
        return 1.0

    return round(barus_correction(visc_T, alpha, pressure_psi), 4)


class ViscCalcApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FRT Fluid Viscosity Calculator")
        self.setMinimumWidth(420)
        self.setStyleSheet(STYLESHEET)
        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(16)

        # --- Title ---
        title = QLabel("FRT FLUID VISCOSITY")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Dynamic Viscosity Calculator  ·  cP")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)

        # --- Input card ---
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)

        # Fluid selector
        card_layout.addWidget(self._field_label("Fluid Type"))
        self.combo_fluid = QComboBox()
        self.combo_fluid.addItems([
            "7% KCl", "Soltrol 130", "Sea Water",
            "13.0 lbm/gal CaBr2", "Fresh Water"
        ])
        card_layout.addWidget(self.combo_fluid)

        # Temperature
        card_layout.addWidget(self._field_label("Temperature (°F)"))
        self.entry_temp = QLineEdit()
        self.entry_temp.setPlaceholderText("e.g.  72")
        card_layout.addWidget(self.entry_temp)

        # Pressure
        card_layout.addWidget(self._field_label("Pressure (psi)"))
        self.entry_pressure = QLineEdit()
        self.entry_pressure.setPlaceholderText("e.g.  500  (0 = no correction)")
        card_layout.addWidget(self.entry_pressure)

        # Pressure warning
        warn = QLabel("Pressure correction coefficients (alpha) are placeholders — see code TODOs.")
        warn.setObjectName("warning")
        warn.setWordWrap(True)
        card_layout.addWidget(warn)

        root_layout.addWidget(card)

        # --- Calculate button ---
        btn = QPushButton("Calculate Viscosity")
        btn.clicked.connect(self._calculate)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setColor(QColor(26, 111, 189, 160))
        shadow.setOffset(0, 4)
        btn.setGraphicsEffect(shadow)
        root_layout.addWidget(btn)

        # --- Result box ---
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

    def _calculate(self):
        try:
            fluid = self.combo_fluid.currentText()
            temp  = float(self.entry_temp.text())
            pres_text = self.entry_pressure.text().strip()
            pres  = float(pres_text) if pres_text else 0.0

            visc = viscP(fluid, temp, pres)

            self.result_value.setText(f"{visc} cP")
            self.result_detail.setText(
                f"{fluid}   ·   {temp}°F   ·   {pres} psi"
            )
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
