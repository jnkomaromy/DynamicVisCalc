# DynamicVisCalc — Claude Context

This file exists so that after a rate-limit restart, Claude can pick up exactly
where we left off without re-explaining the project.

---

## What this project is

A dynamic viscosity calculator for FRT (Formation Response Testing) permeability
fluids. Returns viscosity in **centipoise (cP)** as a function of temperature (°F)
and pressure (psi). Lives at: https://github.com/jnkomaromy/DynamicVisCalc

**Not** a permeability calculator — that is out of scope for this repo and belongs
in a separate project (`g:/FRT_Processor/`, which should import from visc_engine.py).

---

## Repo layout

```
src/
  visc_engine.py              ← pure calculation engine, single source of truth
  RationalDynamicViscCalc.py  ← PyQt6 GUI, imports from visc_engine only
  README.md                   ← user-facing docs + full attribution
  CLAUDE.md                   ← this file
  LICENSE                     ← GPL v3 (required by iapws + PyQt6)
```

---

## Public API of visc_engine.py

```python
from visc_engine import viscP, visc_kcl, FLUIDS

# General interface — all fluids except KCl at arbitrary concentration
cP = viscP(fluid_type, temp_F, pressure_psi=0.0)

# KCl at arbitrary molality
cP = visc_kcl(temp_F, pressure_psi=0.0, molality=1.012)  # mol/kg H2O

# Fluid name strings
FLUIDS = ["KCl", "Soltrol 130", "Sea Water", "13.0 lbm/gal CaBr2", "Fresh Water"]
```

The pressure argument defaults to 0.0 so existing callers (e.g. FRT_Processor)
need no changes.

---

## Fluid model status

| Fluid               | Model                               | P-dependent? |
|---------------------|-------------------------------------|--------------|
| Fresh Water         | IAPWS 2008 (via iapws.IAPWS97)      | YES — native |
| Sea Water           | Sharqawy et al. 2010 + IAPWS ratio  | YES          |
| KCl                 | Laliberte 2009 + IAPWS ratio        | YES          |
| 13.0 lbm/gal CaBr2  | Rational function + Barus (a=0)     | TODO         |
| Soltrol 130         | Rational function + Barus (a=0)     | TODO         |

**Next up: 13.0 lbm/gal CaBr2.**
Strategy: check if Laliberte (2009) has CaBr2 coefficients in the dataset
(search CalebBell/chemicals Laliberte2009.tsv for CaBr2 or CAS 7789-41-5).
If not found, fall back to interpolation from NIST or SPE experimental data,
or fit a Jones-Dole extended equation to published data points.

After CaBr2: Soltrol 130. It is a proprietary Chevron Phillips isoparaffinic
solvent (C11-C14 blend). No public NIST data. Options: Chevron Phillips TDS,
or experimental lab measurement. Real pressure correction requires lab data —
Barus alpha for light isoparaffins is in the ~1e-5 to 1e-4 psi^-1 range.

---

## Key design patterns — follow these exactly

### 1. Phase-safe IAPWS calls
NEVER call IAPWS97(T, P) directly inside fluid branches. Always use the helper
`_visc_fw_liquid_cP(T_K, P_MPa)` which floors pressure at the saturation curve
(P_sat * 1.01) to guarantee liquid phase. This is critical at 100 C / 212 F
near atmospheric where IAPWS97 otherwise returns steam viscosity (~0.012 cP).

```python
def _visc_fw_liquid_cP(T_K, P_MPa):
    sat_P = IAPWS97(T=T_K, x=0).P   # saturation pressure at T
    P_eff = max(P_MPa, sat_P * 1.01)
    return IAPWS97(T=T_K, P=P_eff).mu * 1000  # Pa.s -> cP
```

### 2. IAPWS pressure ratio correction (pattern for all aqueous fluids)
For fluids with no native T+P formulation, compute viscosity at atmospheric
pressure using the fluid's own correlation, then scale by the IAPWS water
pressure ratio:

```python
mu(T, conc, P) = mu(T, conc, atm) * [mu_fw(T, P) / mu_fw(T, atm)]
```

Physically justified: pressure effects on aqueous viscosity are dominated by
water structural changes and are largely solute-independent at FRT pressures.
Used for Sea Water and KCl. Will be used for CaBr2.

### 3. Laliberte (2009) mixing rule for electrolytes
```python
# Solute viscosity contribution (cP):
mu_s = exp((v1*(1-w_w)^v2 + v3) / (v4*t + 1)) / (v5*(1-w_w)^v6 + 1)
# Logarithmic mixing rule:
mu_mix = exp(w_w * ln(mu_w) + w_s * ln(mu_s))
```
where w_w = water mass fraction, t = temperature in degC.
mu_w is taken from IAPWS (not Laliberte's own water formula) for consistency.

### 4. Unit conversions — module-level constants, always use these
```python
_ATM_MPA    = 0.101325       # atmospheric pressure in MPa
_PSI_TO_MPA = 0.00689476     # psi -> MPa
_F_TO_K     = lambda f: (f - 32) * 5/9 + 273.15
_F_TO_C     = lambda f: (f - 32) * 5/9
```

### 5. KCl concentration conversion
```python
_MW_KCL = 74.551  # g/mol

def _kcl_molality_to_wt(molality):
    # mol/kg H2O -> mass fraction (kg KCl / kg solution)
    g_kcl = molality * _MW_KCL
    return g_kcl / (1000.0 + g_kcl)
```
Quick reference: 0.5 mol/kg = 3.6 wt%, 1.012 = 7%, 2.0 = 13%, 3.0 = 18%, 4.0 = 23%

---

## Laliberte (2009) KCl coefficients — verified, do not change

Source: Laliberte, M. (2009). J. Chem. Eng. Data, 54(6), 1725-1760.
DOI: 10.1021/je8008123. Transcribed from CalebBell/chemicals Laliberte2009.tsv.
Valid: 5-150 degC, w_KCl up to 0.306 (4.1 mol/kg).

```python
_KCL_V1 =  6.48805967116487
_KCL_V2 =  1.31753131265255
_KCL_V3 = -0.777820552977139
_KCL_V4 =  0.0927156022360008   # units: 1/degC
_KCL_V5 = -1.30020256174307
_KCL_V6 =  2.08120731758225
```

Interesting physics: KCl is a structure-breaking electrolyte (Jones-Dole B
slightly negative at low T). Viscosity at 1 mol/kg is LOWER than fresh water
below ~40 degC (~100 F), and HIGHER above it. The old rational function missed
this crossover entirely. At 3 mol/kg and above, KCl always runs higher than water.

---

## Sharqawy (2010) Sea Water coefficients — verified, do not change

Source: Sharqawy, Lienhard & Zubair. Desalination and Water Treatment
16(1-3):354-380, 2010. DOI: 10.5004/dwt.2010.1079
Fixed at standard ocean salinity: S = 35.0 g/kg.

```python
S_A = S_gkg / 1000.0   # absolute salinity, kg/kg
A = 1.541 + 1.998e-2*T_C - 9.52e-5*T_C**2
B = 7.974 - 7.561e-2*T_C + 4.724e-4*T_C**2
mu_sw_atm = mu_fw_atm * (1 + A*S_A + B*S_A**2)
```

---

## GUI (RationalDynamicViscCalc.py)

PyQt6, deep navy blue theme. Single window, no tabs.
Imports: viscP, visc_kcl, FLUIDS from visc_engine.
When "KCl" is selected in the dropdown, a molality input field appears
(default placeholder: 1.012 mol/kg = 7 wt%). Other fluids use viscP() directly.
The result box shows fluid, temperature, pressure, and viscosity.

---

## Licensing

| Package  | License | Constraint |
|----------|---------|------------|
| iapws    | GPL v3  | Repo must stay GPL v3 |
| PyQt6    | GPL v3  | Same |
| scipy    | BSD 3   | No constraint |
| numpy    | BSD 3   | No constraint |

Repo is GPL v3. Source on GitHub = distribution obligation met.
Every model gets: inline DOI comment in visc_engine.py + full ref in README.md.

---

## Related project

`g:/FRT_Processor/` — the FRT data processing pipeline.
- `perm_md.py` there originally had its own copy of viscP(). It should be
  updated to import from this repo instead.
- `process_perm.py` calls `perm_md.viscP(fluid, temp)` — the default
  pressure_psi=0.0 means it will work without changes once pointing here.

---

## Run / test

```bash
python RationalDynamicViscCalc.py

python -c "from visc_engine import viscP; print(viscP('Fresh Water', 72, 0))"
python -c "from visc_engine import visc_kcl; print(visc_kcl(120, 1500, 2.0))"
```
