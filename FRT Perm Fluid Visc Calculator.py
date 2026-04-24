import tkinter as tk
from tkinter import messagebox
import math

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


def visc_rational(a, b, c, x_0, temp):
    # Rational function temperature model.
    # x_0 is a pole-offset keeping the denominator nonzero
    # across the valid temperature domain.
    return round(a * ((temp - x_0) ** -2) + b * ((temp - x_0) ** -1) + c, 4)


def barus_correction(visc_T, alpha, pressure_psi):
    # Barus pressure correction: mu(T,P) = mu(T) * exp(alpha * P)
    # alpha = 0 means no correction (pass-through).
    return visc_T * math.exp(alpha * pressure_psi)


def viscP(fluid_type, temp, pressure_psi=0.0):
    # Returns dynamic viscosity in cP at temperature (°F) and
    # pressure (psi gauge). Pressure correction uses Barus equation.

    if fluid_type == "7% KCl":
        # 7% potassium chloride brine — common non-damaging perm fluid
        a, b, c, x_0 = 14118.60487982875, 28.197267, 0.01992939, -68.2154
        alpha = 0.0  # TODO: replace with measured alpha for 7% KCl
        visc_T = visc_rational(a, b, c, x_0, temp)

    elif fluid_type == "Soltrol 130":
        # Soltrol 130 isoparaffinic oil — hydrocarbon viscosity is more
        # pressure-sensitive than brines; alpha matters more here.
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
        # Deionized / distilled fresh water
        a, b, c, x_0 = 16504.9, 10.8518, 0.032894, -68.2154
        alpha = 0.0  # TODO: replace with measured alpha for fresh water
        visc_T = visc_rational(a, b, c, x_0, temp)

    else:
        # Unknown fluid — return 1.0 cP (water-like fallback), no correction
        return 1.0

    return round(barus_correction(visc_T, alpha, pressure_psi), 4)


def calculate_viscosity():
    fluid_type = fluid_type_var.get()

    try:
        temperature_fahrenheit = float(entry_temp.get())
        pressure_psi = float(entry_pressure.get()) if entry_pressure.get().strip() else 0.0

        viscosity = viscP(fluid_type, temperature_fahrenheit, pressure_psi)
        result_label.config(
            text=(
                f"Viscosity of {fluid_type}\n"
                f"at {temperature_fahrenheit}°F, {pressure_psi} psi  →  {viscosity} cP"
            )
        )
    except Exception:
        messagebox.showerror("Error", "Invalid input or calculation error.")


# --- GUI setup ---
root = tk.Tk()
root.title("FRT Fluid Viscosity Calculator")

fluid_type_var = tk.StringVar(root)
fluid_type_var.set("7% KCl")

tk.Label(root, text="Select Fluid Type:").grid(row=0, column=0, sticky="w", padx=6, pady=4)
tk.OptionMenu(
    root, fluid_type_var,
    "7% KCl", "Soltrol 130", "Sea Water", "13.0 lbm/gal CaBr2", "Fresh Water"
).grid(row=0, column=1, sticky="ew", padx=6)

tk.Label(root, text="Temperature (°F):").grid(row=1, column=0, sticky="w", padx=6, pady=4)
entry_temp = tk.Entry(root)
entry_temp.grid(row=1, column=1, sticky="ew", padx=6)

tk.Label(root, text="Pressure (psi):").grid(row=2, column=0, sticky="w", padx=6, pady=4)
entry_pressure = tk.Entry(root)
entry_pressure.insert(0, "0")
entry_pressure.grid(row=2, column=1, sticky="ew", padx=6)

tk.Button(root, text="Calculate", command=calculate_viscosity).grid(
    row=3, columnspan=2, pady=10
)

result_label = tk.Label(root, text="", justify="center")
result_label.grid(row=4, columnspan=2, pady=4)

root.mainloop()
