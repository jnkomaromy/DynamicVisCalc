# DynamicVisCalc — Claude Context

This file exists so that after a rate-limit restart, Claude can pick up exactly
where we left off without re-explaining the project.

---

## What this project is

A dynamic viscosity calculator for FRT (Formation Response Testing) permeability
fluids. Returns viscosity in **centipoise (cP)** as a function of temperature (°F)
and pressure (psi). Lives at: https://github.com/jnkomaromy/DynamicVisCalc

**Not** a permeability calculator — that is out of scope for this repo and belongs
in a separate project (FRT_Processor, which imports from visc_engine.py).

---

## Repo layout

```
src/
  visc_engine.py           ← pure calculation engine, the single source of truth
  RationalDynamicViscCalc.py  ← PyQt6 GUI, imports viscP() and FLUIDS from visc_engine
  README.md
  CLAUDE.md                ← this file
  LICENSE                  ← GPL v3 (required by iapws + PyQt6 dependencies)
```

---

## Architecture

`visc_engine.py` exposes two things:
- `FLUIDS` — list of supported fluid name strings
- `viscP(fluid_type, temp, pressure_psi=0.0)` — returns cP

The GUI (`RationalDynamicViscCalc.py`) imports only from `visc_engine`. No other
file in this repo should duplicate viscosity logic.

The pressure argument defaults to 0.0 so existing callers (e.g. FRT_Processor)
need no changes.

---

## Fluid model status

| Fluid                | Model                              | P-dependent? |
|---------------------|------------------------------------|--------------|
| Fresh Water          | IAPWS 2008 (via iapws.IAPWS97)     | ✅ Yes       |
| Sea Water            | Sharqawy et al. 2010 + IAPWS ratio | ✅ Yes       |
| 7% KCl               | Rational function + Barus (α=0)    | ⬜ TODO      |
| 13.0 lbm/gal CaBr₂  | Rational function + Barus (α=0)    | ⬜ TODO      |
| Soltrol 130          | Rational function + Barus (α=0)    | ⬜ TODO      |

**Next up: 7% KCl.**
Target model: Laliberté (2007) or Abdulagatov & Azizov (2005) for T+molality,
plus IAPWS pressure ratio correction (same pattern as Sea Water).
7% KCl ≈ 1.01 mol/kg (MW KCl = 74.551 g/mol; 7 g / 74.551 / 0.093 kg H₂O).

After KCl: 13.0 lbm/gal CaBr₂ (sparse literature — may need interpolation from
NIST or SPE data). Soltrol 130 is a proprietary isoparaffin; only experimental
data or Chevron Phillips TDS can provide a real pressure correction.

---

## Key design patterns established

### 1. Phase-safe IAPWS calls
Always use `_visc_fw_liquid_cP(T_K, P_MPa)` — never call `IAPWS97` directly in
fluid branches. This helper applies a saturation-pressure floor so we stay in the
liquid phase (critical at 100°C / 212°F near atmospheric).

```python
def _visc_fw_liquid_cP(T_K, P_MPa):
    sat_P = IAPWS97(T=T_K, x=0).P
    P_eff = max(P_MPa, sat_P * 1.01)
    return IAPWS97(T=T_K, P=P_eff).mu * 1000  # Pa·s → cP
```

### 2. IAPWS pressure ratio correction
For fluids without native T+P formulations, scale the atmospheric model by the
IAPWS fresh water pressure ratio:

```python
mu(T, S, P) = mu(T, S, atm) × [mu_fw(T, P) / mu_fw(T, atm)]
```

This is physically justified — pressure effects on aqueous viscosity are dominated
by water structural changes and are largely independent of solute at FRT pressures.
Used for Sea Water; will be used for KCl, CaBr₂.

### 3. Unit conversions (module-level constants)
```python
_ATM_MPA    = 0.101325
_PSI_TO_MPA = 0.00689476
_F_TO_K     = lambda f: (f - 32) * 5/9 + 273.15
_F_TO_C     = lambda f: (f - 32) * 5/9
```

---

## Licensing — important

| Package  | License | Why it matters |
|----------|---------|----------------|
| iapws    | GPL v3  | Repo must stay GPL v3 |
| PyQt6    | GPL v3  | Same |
| scipy    | BSD 3   | No constraint |
| numpy    | BSD 3   | No constraint |

Repo is already GPL v3. Source on GitHub = distribution obligation met.
All dependencies credited in README.md and inline in visc_engine.py.

---

## Citation style
Every published model gets:
- Inline comment in visc_engine.py with author, year, journal, DOI
- Entry in README.md Acknowledgements section with full reference

---

## Run / test
```bash
python RationalDynamicViscCalc.py          # launch GUI
python -c "from visc_engine import viscP; print(viscP('Fresh Water', 72, 0))"
```

---

## Related project
`g:/FRT_Processor/` — the FRT data processing pipeline. Its `perm_md.py`
originally contained the same rational viscosity functions. Going forward,
FRT_Processor should import viscP from this repo (visc_engine.py), not maintain
its own copy.
