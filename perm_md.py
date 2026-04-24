# ============================================================
# perm_md.py — FRT Permeability Engine
# ============================================================
# Copied from FRT_Processor/perm_md.py.
# Viscosity is sourced from visc_engine.py — one universal
# calculation used by both this module and the GUI.
#
# Public API:
#   viscP(fluid_type, temp, pressure_psi=0.0) -> cP  (re-exported from visc_engine)
#   perm_md(diameter_inch, length_inch, delta_p_psi,
#           flow_rate_ml_min, viscosity_cP)           -> mD
#   perm_slope(slope, viscosity_cP,
#              length_inch, diameter_inch)             -> mD
# ============================================================

import math
from visc_engine import viscP, FLUIDS  # single source of truth for viscosity

__all__ = ["viscP", "FLUIDS", "perm_md", "perm_slope"]


def perm_md(diameter_inch, length_inch, delta_p_psi, flow_rate_ml_min, viscosity_cP):
    """Permeability in millidarcies via Darcy's law (direct method).

    If testing at elevated confining pressure, pass viscosity calculated
    at that pressure — viscP(..., pressure_psi=confining_psi) — so the
    Barus correction is applied before the Darcy calculation.

    Args:
        diameter_inch:    Sample diameter in inches.
        length_inch:      Sample length in inches.
        delta_p_psi:      Differential pressure across sample in psi.
        flow_rate_ml_min: Flow rate in ml/min.
        viscosity_cP:     Fluid viscosity in centipoise.

    Returns:
        Permeability in millidarcies.
    """
    delta_p   = delta_p_psi / 14.696                                 # psi → atm
    flow_rate = flow_rate_ml_min / 60                                 # ml/min → ml/s
    length    = float(length_inch) * 2.54                             # in → cm
    area      = math.pi * ((float(diameter_inch) * 2.54 / 2) ** 2)   # cm²

    permeability_Darcy = (flow_rate * viscosity_cP * length) / (area * delta_p)
    return permeability_Darcy * 1000  # Darcy → millidarcy


def perm_slope(slope, viscosity_cP, length_inch, diameter_inch):
    """Permeability in millidarcies via slope method (ΔP/Q regression).

    Args:
        slope:         Linear regression slope of ΔP vs Q (psi·min / cm³).
        viscosity_cP:  Fluid viscosity in centipoise.
        length_inch:   Sample length in inches.
        diameter_inch: Sample diameter in inches.

    Returns:
        Permeability in millidarcies.
    """
    return (122.8 * length_inch * viscosity_cP) / (slope * diameter_inch)
