import tkinter as tk
from tkinter import messagebox

# ============================================================
# FRT Permeability Fluid Dynamic Viscosity Calculator
# ============================================================
# Calculates dynamic viscosity (cP) for common FRT perm fluids
# as a function of TEMPERATURE ONLY.
#
# KNOWN LIMITATION — PRESSURE DEPENDENCE NOT MODELED:
#   Viscosity also increases with pressure (especially for oils
#   like Soltrol 130 at elevated test pressures). At moderate
#   lab pressures (<~500 psi) this effect is small for aqueous
#   fluids (<1-2%), but can be significant for hydrocarbons at
#   high confining pressures. A pressure correction term
#   (e.g. Barus equation: mu_p = mu_0 * exp(alpha * P)) would
#   be needed for high-pressure accuracy.
#
# Curve fitting: rational function  a/(T-x0)^2 + b/(T-x0) + c
#   Fit coefficients were determined from known viscosity-
#   temperature data points for each fluid. Gather several
#   points near ambient, a few mid-range, and several at the
#   upper test temperature limit before refitting.
# ============================================================


def visc_rational(a, b, c, x_0, temp):
    # Rational function: fits viscosity-temperature curves well
    # for most Newtonian perm fluids across typical test ranges.
    # x_0 is a pole-offset that keeps the denominator well away
    # from zero across the valid temperature domain.
    return round(a * ((temp - x_0) ** -2) + b * ((temp - x_0) ** -1) + c, 4)


def viscP(fluid_type, temp):
    # Returns dynamic viscosity in cP at the given temperature (°F).
    # Coefficients below are empirical fits — do not extrapolate
    # far outside the temperature range used during curve fitting.

    if fluid_type == "7% KCl":
        # 7% potassium chloride brine — common non-damaging perm fluid
        a = 14118.60487982875
        b = 28.197267
        c = 0.01992939
        x_0 = -68.2154
        return visc_rational(a, b, c, x_0, temp)

    elif fluid_type == "Soltrol 130":
        # Soltrol 130 isoparaffinic oil — NOTE: hydrocarbon viscosity
        # is more pressure-sensitive than brines; results at high
        # confining pressures will be underestimates.
        # An additional linear density correction is applied here
        # to account for the temperature-dependent density change.
        a = -2330
        b = 172
        c = -0.0177
        x_0 = 0
        density_correction = 0.7815 - (temp * 0.0003961)
        return visc_rational(a, b, c, x_0, temp) * density_correction

    elif fluid_type == "Sea Water":
        # Standard sea water (~3.5% NaCl equivalent salinity)
        a = 14811.8
        b = 29.2862
        c = 0.01149865
        x_0 = -64.6513
        return visc_rational(a, b, c, x_0, temp)

    elif fluid_type == "13.0 lbm/gal CaBr2":
        # Calcium bromide brine at 13.0 lb/gal — high-density perm fluid
        a = 60000
        b = 150
        c = 0
        x_0 = -85
        return visc_rational(a, b, c, x_0, temp)

    elif fluid_type == "Fresh Water":
        # Deionized / distilled fresh water
        a = 16504.9
        b = 10.8518
        c = 0.032894
        x_0 = -68.2154
        return visc_rational(a, b, c, x_0, temp)

    else:
        # Unknown fluid — return 1.0 cP (water-like fallback)
        return 1.0


def calculate_viscosity():
    fluid_type = fluid_type_var.get()
    temperature_fahrenheit = float(entry_temp.get())

    try:
        viscosity = viscP(fluid_type, temperature_fahrenheit)
        result_label.config(
            text=f"The viscosity of {fluid_type} at {temperature_fahrenheit}°F is {viscosity} cP."
        )
    except Exception:
        messagebox.showerror("Error", "Invalid input or calculation error.")


# --- GUI setup ---
root = tk.Tk()
root.title("Fluid Viscosity Calculator")

fluid_type_var = tk.StringVar(root)
fluid_type_var.set("7% KCl")

label_fluid_type = tk.Label(root, text="Select Fluid Type:")
dropdown_fluid_type = tk.OptionMenu(
    root, fluid_type_var,
    "7% KCl", "Soltrol 130", "Sea Water", "13.0 lbm/gal CaBr2", "Fresh Water"
)
label_temp = tk.Label(root, text="Enter Temperature (°F):")
entry_temp = tk.Entry(root)
calculate_button = tk.Button(root, text="Calculate", command=calculate_viscosity)
result_label = tk.Label(root, text="")

label_fluid_type.grid(row=0, column=0, sticky="w")
dropdown_fluid_type.grid(row=0, column=1, sticky="ew")
label_temp.grid(row=1, column=0, sticky="w")
entry_temp.grid(row=1, column=1, sticky="ew")
calculate_button.grid(row=2, columnspan=2, pady=10)
result_label.grid(row=3, columnspan=2)

root.mainloop()
