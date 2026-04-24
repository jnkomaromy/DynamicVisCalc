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
#     Full T + P formulation.
#     Ref: IAPWS, 2008 — "Release on the IAPWS Formulation 2008
#     for the Viscosity of Ordinary Water Substance", iapws.org
#
#   Sea Water — Sharqawy, Lienhard & Zubair (2010) for T + S,
#     with IAPWS pressure ratio correction for P.
#     Ref: Sharqawy et al., Desalination and Water Treatment
#     16(1-3):354-380, 2010. DOI:10.5004/dwt.2010.1079
#     Assumes standard ocean salinity (35 g/kg).
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

_ATM_MPA    = 0.101325      # atmospheric pressure in MPa
_PSI_TO_MPA = 0.00689476    # psi → MPa
_F_TO_K     = lambda f: (f - 32) * 5 / 9 + 273.15
_F_TO_C     = lambda f: (f - 32) * 5 / 9

_SEAWATER_SALINITY_G_KG = 35.0  # standard ocean salinity


def _visc_fw_liquid_cP(T_K: float, P_MPa: float) -> float:
    """IAPWS97 fresh water viscosity in cP, guaranteed liquid phase.

    Uses saturation pressure as a floor to avoid returning steam
    viscosity when conditions are at or below the boiling point.
    """
    sat_P = IAPWS97(T=T_K, x=0).P          # saturation pressure at T
    P_eff = max(P_MPa, sat_P * 1.01)        # 1% above saturation = safely liquid
    state = IAPWS97(T=T_K, P=P_eff)
    if state.mu is None:
        raise ValueError(f"IAPWS97 out of range: T={T_K:.2f} K, P={P_eff:.4f} MPa")
    return state.mu * 1000                  # Pa·s → cP


def _visc_seawater_sharqawy(T_C: float, P_MPa: float,
                             S_gkg: float = _SEAWATER_SALINITY_G_KG) -> float:
    """Seawater dynamic viscosity in cP via Sharqawy et al. (2010) with
    IAPWS pressure ratio correction.

    Sharqawy correlation (T + S, atmospheric):
        mu_sw = mu_fw * (1 + A*S_A + B*S_A^2)
        A = 1.541 + 1.998e-2*T - 9.52e-5*T^2
        B = 7.974 - 7.561e-2*T + 4.724e-4*T^2
        S_A = absolute salinity in kg/kg, T in °C
        Valid: 0–180 °C, 0–150 g/kg

    Pressure correction:
        mu_sw(T,S,P) = mu_sw(T,S,atm) * [mu_fw(T,P) / mu_fw(T,atm)]
    The pressure effect on aqueous solution viscosity is dominated by
    water structure, so the IAPWS fresh water pressure ratio is a sound
    engineering correction across FRT pressure ranges.
    """
    S_A = S_gkg / 1000.0
    A   = 1.541 + 1.998e-2 * T_C - 9.52e-5 * T_C**2
    B   = 7.974 - 7.561e-2 * T_C + 4.724e-4 * T_C**2

    T_K        = T_C + 273.15
    P_eff      = max(P_MPa, _ATM_MPA)
    mu_fw_atm  = _visc_fw_liquid_cP(T_K, _ATM_MPA)
    mu_fw_P    = _visc_fw_liquid_cP(T_K, P_eff)
    mu_sw_atm  = mu_fw_atm * (1.0 + A * S_A + B * S_A**2)

    return mu_sw_atm * (mu_fw_P / mu_fw_atm)

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
        # Sharqawy et al. (2010) T+S model with IAPWS pressure ratio correction.
        # Ref: Desalination and Water Treatment 16(1-3):354-380
        # DOI: 10.5004/dwt.2010.1079
        T_C   = _F_TO_C(temp)
        P_MPa = max(pressure_psi * _PSI_TO_MPA, _ATM_MPA)
        return round(_visc_seawater_sharqawy(T_C, P_MPa), 4)

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
        return round(_visc_fw_liquid_cP(T_K, P_MPa), 4)

    else:
        return 1.0  # unknown fluid — water-like fallback

    return round(barus_correction(visc_T, alpha, pressure_psi), 4)
