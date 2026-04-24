# ============================================================
# perm_md.py — FRT Permeability & Viscosity Engine
# ============================================================
# Copied from FRT_Processor/perm_md.py.
# Original: viscosity (temperature only).
# Updated:  Barus pressure correction added to viscP().
#
# Public API:
#   viscP(fluid_type, temp, pressure_psi=0.0) -> cP
#   perm_md(diameter_inch, length_inch, delta_p_psi,
#           flow_rate_ml_min, viscosity_cP)      -> mD
#   perm_slope(slope, viscosity_cP,
#              length_inch, diameter_inch)        -> mD
# ============================================================

import math

# ── Viscosity ────────────────────────────────────────────────

def visc_rational(a, b, c, x_0, temp):
    # Rational function: a/(T-x0)^2 + b/(T-x0) + c
    # Fits viscosity-temperature curves well for Newtonian perm fluids.
    return a * ((temp - x_0) ** -2) + b * ((temp - x_0) ** -1) + c


def _barus(visc_T, alpha, pressure_psi):
    # Barus pressure correction: mu(T,P) = mu(T) * exp(alpha * P)
    # alpha = 0 → no correction (pass-through).
    return visc_T * math.exp(alpha * pressure_psi)


def viscP(fluid_type: str, temp: float, pressure_psi: float = 0.0) -> float:
    """Dynamic viscosity in cP at temperature (°F) and pressure (psi).

    pressure_psi defaults to 0 so existing callers need no changes.

    NOTE: alpha (Barus pressure-viscosity coefficient) is set to 0.0
    for all fluids — no pressure correction until you supply measured
    or literature values.  Typical order of magnitude:
        brines:       ~1e-6 to 1e-5 psi^-1  (small)
        hydrocarbons: ~1e-5 to 1e-4 psi^-1  (notable at high P)
    """
    if fluid_type == "7% KCl":
        a, b, c, x_0 = 14118.60487982875, 28.197267, 0.01992939, -68.2154
        alpha = 0.0  # TODO: measured alpha for 7% KCl
        visc_T = visc_rational(a, b, c, x_0, temp)

    elif fluid_type == "Soltrol 130":
        # Density correction for temperature-dependent density.
        # Hydrocarbon — alpha matters more here than for brines.
        a, b, c, x_0 = -2330, 172, -0.0177, 0
        alpha = 0.0  # TODO: measured alpha for Soltrol 130
        visc_T = visc_rational(a, b, c, x_0, temp) * (0.7815 - (temp * 0.0003961))

    elif fluid_type == "Sea Water":
        a, b, c, x_0 = 14811.8, 29.2862, 0.01149865, -64.6513
        alpha = 0.0  # TODO: measured alpha for sea water
        visc_T = visc_rational(a, b, c, x_0, temp)

    elif fluid_type == "13.0 lbm/gal CaBr2":
        a, b, c, x_0 = 60000, 150, 0, -85
        alpha = 0.0  # TODO: measured alpha for 13.0 lb/gal CaBr2
        visc_T = visc_rational(a, b, c, x_0, temp)

    elif fluid_type == "Fresh Water":
        a, b, c, x_0 = 16504.9, 10.8518, 0.032894, -68.2154
        alpha = 0.0  # TODO: measured alpha for fresh water
        visc_T = visc_rational(a, b, c, x_0, temp)

    else:
        return 1.0  # unknown fluid — water-like fallback

    return round(_barus(visc_T, alpha, pressure_psi), 4)


# ── Permeability ─────────────────────────────────────────────

def perm_md(diameter_inch, length_inch, delta_p_psi, flow_rate_ml_min, viscosity_cP):
    """Permeability in millidarcies via Darcy's law (direct method).

    NOTE ON PRESSURE: delta_p_psi is the differential pressure across
    the sample (already in the Darcy equation). If testing at elevated
    confining pressure, pass viscosity calculated at that pressure using
    viscP(..., pressure_psi=confining_psi) for consistency.

    Args:
        diameter_inch:    Sample diameter in inches.
        length_inch:      Sample length in inches.
        delta_p_psi:      Differential pressure across sample in psi.
        flow_rate_ml_min: Flow rate in ml/min.
        viscosity_cP:     Fluid viscosity in centipoise.

    Returns:
        Permeability in millidarcies.
    """
    delta_p   = delta_p_psi / 14.696                                      # psi → atm
    flow_rate = flow_rate_ml_min / 60                                      # ml/min → ml/s
    length    = float(length_inch) * 2.54                                  # in → cm
    area      = math.pi * ((float(diameter_inch) * 2.54 / 2) ** 2)        # cm²

    permeability_Darcy = (flow_rate * viscosity_cP * length) / (area * delta_p)
    return permeability_Darcy * 1000  # Darcy → millidarcy


def perm_slope(slope, viscosity_cP, length_inch, diameter_inch):
    """Permeability in millidarcies via slope method (ΔP/Q regression).

    Args:
        slope:         Linear regression slope of ΔP vs Q,
                       units: (psi · min) / cm³.
        viscosity_cP:  Fluid viscosity in centipoise.
        length_inch:   Sample length in inches.
        diameter_inch: Sample diameter in inches.

    Returns:
        Permeability in millidarcies.
    """
    return (122.8 * length_inch * viscosity_cP) / (slope * diameter_inch)
