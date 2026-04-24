import tkinter as tk
from tkinter import messagebox

"""
As it turns out, the rational function works REALLY WELL for 
approximating centipoise curves for every perm fluid!
"""

def visc_rational(a,b,c,x_0,temp):
    return round(a*((temp-x_0)**-2) + b*((temp-x_0)**-1) + c, 4)


"""
temp curves to calculate Dynamic Viscosity in cP for given fluids. 
Other perm fluids can be made available if need be.

You'll need to fit the rational function above to known datapoints

Obviously get many datapoints. Several near ambient, a few in the middle
and several at reasonable test temperature ranges. 
"""
def viscP(fluid_type, temp):

    if fluid_type == "7% KCl":

        a = 14118.60487982875
        b = 28.197267
        c = 0.01992939
        x_0 = -68.2154

        return visc_rational(a,b,c,x_0,temp) 
    
    elif fluid_type == "Soltrol 130":

        a = -2330
        b = 172
        c = -0.0177
        x_0 = 0

        return visc_rational(a,b,c,x_0,temp) * (0.7815-(temp*0.0003961))
    
    elif fluid_type == "Sea Water":

        a = 14811.8
        b = 29.2862
        c = 0.01149865
        x_0 = -64.6513

        return visc_rational(a,b,c,x_0,temp)

    elif fluid_type == "13.0 lbm/gal CaBr2":

        a = 60000
        b = 150
        c = 0
        x_0 = -85

        return visc_rational(a,b,c,x_0,temp)
    
    elif fluid_type == "Fresh Water":

        a = 16504.9
        b = 10.8518
        c = 0.032894
        x_0 = -68.2154

        return visc_rational(a,b,c,x_0,temp)

    else:
        return 1.0   

def calculate_viscosity():
    fluid_type = fluid_type_var.get()
    temperature_fahrenheit = float(entry_temp.get())

    try:
        viscosity = viscP(fluid_type, temperature_fahrenheit)
        result_label.config(text=f"The viscosity of {fluid_type} at {temperature_fahrenheit}°F is {viscosity} cP.")
    except:
        messagebox.showerror("Error", "Invalid input or calculation error.")

# Create the main application window
root = tk.Tk()
root.title("Fluid Viscosity Calculator")

# Create the widgets
fluid_type_var = tk.StringVar(root)
fluid_type_var.set("7% KCl")
label_fluid_type = tk.Label(root, text="Select Fluid Type:")
dropdown_fluid_type = tk.OptionMenu(root, fluid_type_var, "7% KCl", "Soltrol 130", "Sea Water", "13.0 lbm/gal CaBr2", "Fresh Water")
label_temp = tk.Label(root, text="Enter Temperature (°F):")
entry_temp = tk.Entry(root)
calculate_button = tk.Button(root, text="Calculate", command=calculate_viscosity)
result_label = tk.Label(root, text="")

# Place the widgets on the grid
label_fluid_type.grid(row=0, column=0, sticky="w")
dropdown_fluid_type.grid(row=0, column=1, sticky="ew")
label_temp.grid(row=1, column=0, sticky="w")
entry_temp.grid(row=1, column=1, sticky="ew")
calculate_button.grid(row=2, columnspan=2, pady=10)
result_label.grid(row=3, columnspan=2)

# Run the application
root.mainloop()