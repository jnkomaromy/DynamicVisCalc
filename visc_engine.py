# ============================================================
# visc_engine.py — Rational Dynamic Viscosity Engine
# ============================================================
# Pure calculation module — no GUI dependencies.
# Import and call viscP() from any script, notebook, or tool.
#
# Usage:
#   from visc_engine import viscP, FLUIDS
#   cP = viscP("7% KCl", temp=72.0, pressure_psi=500.0)
#
# Viscosity models by fluid:
#
#   Fresh Water — IAPWS 2008 (via iapws.IAPWS97)
#     Full T + P formulation. Requires the `iapws` package.
#     Converts °F → K and psi → MPa internally.
#
#   All other fluids — rational function fit to measured data
#     visc(T) = a/(T-x0)^2 + b/(T-x0) + c
#     Pressure correction: Barus equation  visc(T,P) = visc(T)*exp(alpha*P)
#     alpha values are currently 0.0 placeholders — no pressure
#     correction applied until measured/literature values supplied.
#     Typical order of magnitude:
#       brines:       ~1e-6 to 1e-5 psi^-1
#       hydrocarbons: ~1e-5 to 1e-4 psi^-1
# ============================================================

import math
from iapws import IAPWS97

_ATM_MPA   = 0.101325       # atmospheric pressure in MPa (floor for IAPWS calls)
_PSI_TO_MPA = 0.00689476    # unit conversion
_F_TO_K = lambda f: (f - 32) * 5 / 9 + 273.15

# Fluid names available to external callers
FLUIDS = [
    "7% KCl",
    "Soltrol 130",
    "Sea Water",
    "13.0 lbm/gal CaBr2",
    "Fresh Water",
]


def visc_rational(a, b, c, x_0, temp):
    # Rational function: a/(T-x0)^2 + b/(T-x0) + c
    # x_0 is a pole-offset keeping the denominator nonzero
    # across the valid temperature domain.
    return a * ((temp - x_0) ** -2) + b * ((temp - x_0) ** -1) + c


def barus_correction(visc_T, alpha, pressure_psi):
    # Barus pressure correction: mu(T,P) = mu(T) * exp(alpha * P)
    # alpha = 0 → pass-through (no pressure effect).
    return visc_T * math.exp(alpha * pressure_psi)


def viscP(fluid_type: str, temp: float, pressure_psi: float = 0.0) -> float:
    """Return dynamic viscosity in cP at temperature (°F) and pressure (psi).

    Args:
        fluid_type:   One of the strings in FLUIDS.
        temp:         Temperature in degrees Fahrenheit.
        pressure_psi: Gauge pressure in psi (default 0 = no correction).

    Returns:
        Viscosity in centipoise, rounded to 4 decimal places.
        Returns 1.0 cP for unrecognised fluid types.
    """
    if fluid_type == "7% KCl":
        # 7% potassium chloride brine — common non-damaging perm fluid
        a, b, c, x_0 = 14118.60487982875, 28.197267, 0.01992939, -68.2154
        alpha = 0.0  # TODO: replace with measured alpha for 7% KCl
        visc_T = visc_rational(a, b, c, x_0, temp)

    elif fluid_type == "Soltrol 130":
        # Soltrol 130 isoparaffinic oil.
        # Hydrocarbon viscosity is more pressure-sensitive than brines;
        # alpha matters more here once you have the coefficient.
        # Density correction applied for temperature-dependent density.
        a, b, c, x_0 = -2330, 172, -0.0177, 0
        alpha = 0.0  # TODO: replace with measured alpha for Soltrol 130
        density_correction = 0.7815 - (temp * 0.0003961)
        visc_T = visc_rational(a, b, c, x_0, temp) * density_correction

    elif fluid_type == "Sea Water":
        # Standard sea water (~3.5% NaCl equivalent salinity)
        a, b, c, x_0 = 14811.8, 29.2862, 0.01149865, -64.6513
        alpha = 0.0  # TODO: replace with measured alpha for sea water
        visc_T = visc_rational(a, b, c, x_0, temp)

    elif fluid_type == "13.0 lbm/gal CaBr2":
        # Calcium bromide brine at 13.0 lb/gal — high-density perm fluid
        a, b, c, x_0 = 60000, 150, 0, -85
        alpha = 0.0  # TODO: replace with measured alpha for 13.0 lb/gal CaBr2
        visc_T = visc_rational(a, b, c, x_0, temp)

    elif fluid_type == "Fresh Water":
        # IAPWS 2008 full T+P formulation — replaces rational function + Barus.
        # Standard: "Release on the IAPWS Formulation 2008 for the Viscosity of
        # Ordinary Water Substance", iapws.org
        # Implemented via the iapws package by jjgomera (GPL v3):
        # https://github.com/jjgomera/iapws
        # Pressure floor at atmospheric so IAPWS97 always gets a valid liquid state.
        T_K   = _F_TO_K(temp)
        P_MPa = max(pressure_psi * _PSI_TO_MPA, _ATM_MPA)
        state = IAPWS97(T=T_K, P=P_MPa)
        if state.mu is None:
            raise ValueError(f"IAPWS97: conditions out of range (T={temp}°F, P={pressure_psi} psi)")
        return round(state.mu * 1000, 4)  # Pa·s → cP

    else:
        return 1.0  # unknown fluid — water-like fallback

    return round(barus_correction(visc_T, alpha, pressure_psi), 4)
