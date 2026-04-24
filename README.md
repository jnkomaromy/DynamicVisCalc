# DynamicVisCalc

Dynamic viscosity calculator for FRT (Formation Response Testing) permeability fluids.  
Returns viscosity in **centipoise (cP)** as a function of **temperature (°F)** and **pressure (psi)**.

## Fluids supported

| Fluid | Model |
|-------|-------|
| Fresh Water | IAPWS 2008 — full T + P formulation |
| Sea Water | Sharqawy et al. (2010) T + S model, IAPWS pressure ratio |
| 7% KCl | Rational function + Barus correction (alpha TBD) |
| 13.0 lbm/gal CaBr₂ | Rational function + Barus correction (alpha TBD) |
| Soltrol 130 | Rational function + Barus correction (alpha TBD) |

Fresh Water uses the IAPWS 2008 viscosity standard, which correctly captures the anomalous pressure–viscosity behaviour of water (viscosity decreases with pressure below ~30 °C, increases above it).

Sea Water uses the Sharqawy, Lienhard & Zubair (2010) correlation for temperature and salinity (fixed at standard ocean salinity 35 g/kg), with the IAPWS fresh water pressure ratio applied for the pressure dimension.

Remaining fluids use empirical rational function fits; pressure correction coefficients (alpha) are placeholder zeros awaiting measured or literature values.

## Files

- `visc_engine.py` — pure calculation engine, no GUI dependencies. Import `viscP()` from here.
- `RationalDynamicViscCalc.py` — PyQt6 desktop GUI.

## Usage

```python
from visc_engine import viscP, FLUIDS

# Fresh Water at 120 °F, 2000 psi — uses IAPWS 2008
cP = viscP("Fresh Water", temp=120.0, pressure_psi=2000.0)

# Any other fluid (pressure correction inactive until alpha is set)
cP = viscP("7% KCl", temp=100.0, pressure_psi=1500.0)
```

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).

## Acknowledgements

### IAPWS — International Association for the Properties of Water and Steam

The Fresh Water viscosity model implements the **IAPWS Formulation 2008 for the Viscosity of Ordinary Water Substance**, which itself rests on the **IAPWS-IF97 Industrial Formulation** for thermodynamic properties. Both are published standards freely available at [iapws.org](http://www.iapws.org).

- Wagner, W. & Kruse, A. — *Properties of Water and Steam* (Springer, 1998)
- IAPWS, 2008 — *Release on the IAPWS Formulation 2008 for the Viscosity of Ordinary Water Substance*
- IAPWS, 2012 — *Revised Release on the IAPWS Industrial Formulation 1997 for the Thermodynamic Properties of Water and Steam*

### Sharqawy, Lienhard & Zubair (2010)

The Sea Water model uses the viscosity correlation from:

> Sharqawy, M.H., Lienhard, J.H. & Zubair, S.M. (2010). *Thermophysical properties of seawater: A review of existing correlations and data.* Desalination and Water Treatment, 16(1-3), 354–380. DOI: 10.5004/dwt.2010.1079

### iapws Python package

The IAPWS standards are accessed in this project through the [`iapws`](https://github.com/jjgomera/iapws) Python package by **Juan José Gómez Romera (jjgomera)**, licensed under GPL v3. Without this implementation the Fresh Water model would require hundreds of lines of coefficient tables to implement from scratch.

### PyQt6

The desktop GUI is built with [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) by **Riverbank Computing Limited**, licensed under GPL v3.

### scipy / numpy

Numerical support provided by [SciPy](https://scipy.org) and [NumPy](https://numpy.org), both BSD 3-Clause licensed.
