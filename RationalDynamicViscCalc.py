import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox,
    QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QGraphicsDropShadowEffect, QTabWidget,
    QRadioButton, QButtonGroup
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

import perm_md
from visc_engine import FLUIDS

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
    "warn":      "#e8a838",
}

STYLESHEET = f"""
    QWidget {{
        background-color: {BLUE['bg']};
        color: {BLUE['text']};
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }}
    QTabWidget::pane {{
        border: 1px solid {BLUE['border']};
        border-radius: 8px;
        background-color: {BLUE['bg']};
    }}
    QTabBar::tab {{
        background-color: {BLUE['panel']};
        color: {BLUE['muted']};
        border: 1px solid {BLUE['border']};
        border-bottom: none;
        border-radius: 6px 6px 0 0;
        padding: 7px 22px;
        font-size: 11px;
        font-weight: bold;
    }}
    QTabBar::tab:selected {{
        background-color: {BLUE['accent']};
        color: {BLUE['text']};
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {BLUE['border']};
        color: {BLUE['text']};
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
    QLabel#section_label {{
        color: {BLUE['accent_h']};
        font-size: 10px;
        font-weight: bold;
        letter-spacing: 1px;
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
        color: {BLUE['warn']};
        font-size: 10px;
    }}
    QRadioButton {{
        color: {BLUE['text']};
        font-size: 11px;
        spacing: 6px;
    }}
    QRadioButton::indicator {{
        width: 14px; height: 14px;
        border-radius: 7px;
        border: 2px solid {BLUE['border']};
        background-color: {BLUE['panel']};
    }}
    QRadioButton::indicator:checked {{
        background-color: {BLUE['accent']};
        border: 2px solid {BLUE['accent_h']};
    }}
"""


def _shadow():
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(18)
    s.setColor(QColor(26, 111, 189, 160))
    s.setOffset(0, 4)
    return s


def _field_label(text):
    lbl = QLabel(text)
    lbl.setObjectName("field_label")
    return lbl


def _section_label(text):
    lbl = QLabel(text)
    lbl.setObjectName("section_label")
    return lbl


def _result_box():
    box = QFrame()
    box.setObjectName("result_box")
    layout = QVBoxLayout(box)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(4)
    value = QLabel("—")
    value.setObjectName("result_value")
    value.setAlignment(Qt.AlignmentFlag.AlignCenter)
    detail = QLabel("")
    detail.setObjectName("result_detail")
    detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(value)
    layout.addWidget(detail)
    return box, value, detail


def _card(inner_layout):
    card = QFrame()
    card.setObjectName("card")
    card.setLayout(inner_layout)
    inner_layout.setContentsMargins(16, 16, 16, 16)
    inner_layout.setSpacing(10)
    return card


# ── Viscosity tab ────────────────────────────────────────────

class ViscTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        card_layout = QVBoxLayout()
        card_layout.addWidget(_field_label("Fluid Type"))
        self.combo_fluid = QComboBox()
        self.combo_fluid.addItems(FLUIDS)
        card_layout.addWidget(self.combo_fluid)

        card_layout.addWidget(_field_label("Temperature (°F)"))
        self.entry_temp = QLineEdit()
        self.entry_temp.setPlaceholderText("e.g.  72")
        card_layout.addWidget(self.entry_temp)

        card_layout.addWidget(_field_label("Test Pressure (psi)"))
        self.entry_pressure = QLineEdit()
        self.entry_pressure.setPlaceholderText("e.g.  500  (0 = no correction)")
        card_layout.addWidget(self.entry_pressure)

        warn = QLabel("Pressure correction coefficients (alpha) are placeholders — see perm_md.py TODOs.")
        warn.setObjectName("warning")
        warn.setWordWrap(True)
        card_layout.addWidget(warn)

        layout.addWidget(_card(card_layout))

        btn = QPushButton("Calculate Viscosity")
        btn.setGraphicsEffect(_shadow())
        btn.clicked.connect(self._calculate)
        layout.addWidget(btn)

        self.result_box, self.result_value, self.result_detail = _result_box()
        layout.addWidget(self.result_box)

    def _calculate(self):
        try:
            fluid = self.combo_fluid.currentText()
            temp  = float(self.entry_temp.text())
            pres  = float(self.entry_pressure.text()) if self.entry_pressure.text().strip() else 0.0
            visc  = perm_md.viscP(fluid, temp, pres)
            self.result_value.setText(f"{visc} cP")
            self.result_detail.setText(f"{fluid}   ·   {temp}°F   ·   {pres} psi")
        except ValueError:
            self.result_value.setText("Invalid input")
            self.result_detail.setText("Check temperature and pressure fields.")
        except Exception as e:
            self.result_value.setText("Error")
            self.result_detail.setText(str(e))


# ── Permeability tab ─────────────────────────────────────────

class PermTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # ── Fluid & conditions card ──
        cond_layout = QVBoxLayout()
        cond_layout.addWidget(_section_label("FLUID CONDITIONS"))

        cond_layout.addWidget(_field_label("Fluid Type"))
        self.combo_fluid = QComboBox()
        self.combo_fluid.addItems(FLUIDS)
        cond_layout.addWidget(self.combo_fluid)

        row1 = QHBoxLayout()
        row1.setSpacing(10)
        col_temp = QVBoxLayout()
        col_temp.addWidget(_field_label("Temperature (°F)"))
        self.entry_temp = QLineEdit()
        self.entry_temp.setPlaceholderText("e.g.  120")
        col_temp.addWidget(self.entry_temp)
        row1.addLayout(col_temp)

        col_pres = QVBoxLayout()
        col_pres.addWidget(_field_label("Confining Pressure (psi)"))
        self.entry_conf_pres = QLineEdit()
        self.entry_conf_pres.setPlaceholderText("e.g.  1500")
        col_pres.addWidget(self.entry_conf_pres)
        row1.addLayout(col_pres)
        cond_layout.addLayout(row1)

        layout.addWidget(_card(cond_layout))

        # ── Sample geometry card ──
        geom_layout = QVBoxLayout()
        geom_layout.addWidget(_section_label("SAMPLE GEOMETRY"))
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        col_d = QVBoxLayout()
        col_d.addWidget(_field_label("Diameter (in)"))
        self.entry_diam = QLineEdit()
        self.entry_diam.setPlaceholderText("e.g.  1.5")
        col_d.addWidget(self.entry_diam)
        row2.addLayout(col_d)
        col_l = QVBoxLayout()
        col_l.addWidget(_field_label("Length (in)"))
        self.entry_len = QLineEdit()
        self.entry_len.setPlaceholderText("e.g.  2.0")
        col_l.addWidget(self.entry_len)
        row2.addLayout(col_l)
        geom_layout.addLayout(row2)
        layout.addWidget(_card(geom_layout))

        # ── Method card ──
        method_layout = QVBoxLayout()
        method_layout.addWidget(_section_label("CALCULATION METHOD"))

        self.radio_direct = QRadioButton("Direct  (flow rate + ΔP)")
        self.radio_slope  = QRadioButton("Slope   (ΔP / Q regression)")
        self.radio_direct.setChecked(True)
        self._method_group = QButtonGroup(self)
        self._method_group.addButton(self.radio_direct)
        self._method_group.addButton(self.radio_slope)
        self.radio_direct.toggled.connect(self._toggle_method)

        method_layout.addWidget(self.radio_direct)
        method_layout.addWidget(self.radio_slope)

        # Direct inputs
        self.direct_widget = QWidget()
        direct_inner = QHBoxLayout(self.direct_widget)
        direct_inner.setContentsMargins(0, 4, 0, 0)
        direct_inner.setSpacing(10)
        col_q = QVBoxLayout()
        col_q.addWidget(_field_label("Flow Rate (ml/min)"))
        self.entry_flow = QLineEdit()
        self.entry_flow.setPlaceholderText("e.g.  2.0")
        col_q.addWidget(self.entry_flow)
        direct_inner.addLayout(col_q)
        col_dp = QVBoxLayout()
        col_dp.addWidget(_field_label("Differential Pressure ΔP (psi)"))
        self.entry_dp = QLineEdit()
        self.entry_dp.setPlaceholderText("e.g.  12.5")
        col_dp.addWidget(self.entry_dp)
        direct_inner.addLayout(col_dp)
        method_layout.addWidget(self.direct_widget)

        # Slope input
        self.slope_widget = QWidget()
        slope_inner = QVBoxLayout(self.slope_widget)
        slope_inner.setContentsMargins(0, 4, 0, 0)
        slope_inner.addWidget(_field_label("Slope  (psi·min / cm³)"))
        self.entry_slope = QLineEdit()
        self.entry_slope.setPlaceholderText("e.g.  4.75")
        slope_inner.addWidget(self.entry_slope)
        self.slope_widget.setVisible(False)
        method_layout.addWidget(self.slope_widget)

        layout.addWidget(_card(method_layout))

        btn = QPushButton("Calculate Permeability")
        btn.setGraphicsEffect(_shadow())
        btn.clicked.connect(self._calculate)
        layout.addWidget(btn)

        self.result_box, self.result_value, self.result_detail = _result_box()
        layout.addWidget(self.result_box)

    def _toggle_method(self, direct_checked):
        self.direct_widget.setVisible(direct_checked)
        self.slope_widget.setVisible(not direct_checked)

    def _calculate(self):
        try:
            fluid    = self.combo_fluid.currentText()
            temp     = float(self.entry_temp.text())
            conf_p   = float(self.entry_conf_pres.text()) if self.entry_conf_pres.text().strip() else 0.0
            diameter = float(self.entry_diam.text())
            length   = float(self.entry_len.text())

            # Viscosity at test temperature and confining pressure
            visc = perm_md.viscP(fluid, temp, conf_p)

            if self.radio_direct.isChecked():
                flow = float(self.entry_flow.text())
                dp   = float(self.entry_dp.text())
                k    = perm_md.perm_md(diameter, length, dp, flow, visc)
                method_str = f"Direct  ·  Q={flow} ml/min  ·  ΔP={dp} psi"
            else:
                slope = float(self.entry_slope.text())
                k     = perm_md.perm_slope(slope, visc, length, diameter)
                method_str = f"Slope  ·  {slope} psi·min/cm³"

            self.result_value.setText(f"{abs(k):.3f} mD")
            self.result_detail.setText(
                f"{fluid}   ·   {temp}°F   ·   {conf_p} psi   ·   μ={visc} cP\n{method_str}"
            )
        except ValueError:
            self.result_value.setText("Invalid input")
            self.result_detail.setText("Check all fields.")
        except Exception as e:
            self.result_value.setText("Error")
            self.result_detail.setText(str(e))


# ── Main window ──────────────────────────────────────────────

class ViscCalcApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rational Dynamic Viscosity Calculator")
        self.setMinimumWidth(460)
        self.setStyleSheet(STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("RATIONAL DYNAMIC VISC CALC")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("FRT Permeability Fluid Calculator  ·  powered by perm_md")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        tabs = QTabWidget()
        tabs.addTab(ViscTab(),  "Viscosity  (cP)")
        tabs.addTab(PermTab(),  "Permeability  (mD)")
        layout.addWidget(tabs)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ViscCalcApp()
    window.show()
    sys.exit(app.exec())
