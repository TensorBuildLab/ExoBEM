# ExoBEM — Extraterrestrial Building Energy Modeling

ExoBEM is an open-source building energy simulation engine for habitats on the **Moon** and
**Mars**. Its zone heat-balance core re-implements the method documented in the EnergyPlus™
Engineering Reference: surface heat balances, transient conduction, TARP convection, Perez sky,
ScriptF interior radiation, zone air balance and ideal loads. It replaces every Earth-specific
assumption with planetary physics:

| Earth assumption in EnergyPlus | ExoBEM replacement |
|---|---|
| 24-h day, 365-day year, Earth solar position | Arbitrary time base; Mars24 ephemeris (88 775 s sol, Ls seasons); selenographic Sun (29.5-day lunar day) |
| Outdoor air is the convective and long-wave medium | Vacuum (Moon: no convection, 3 K sky); 600–900 Pa CO2 (Mars) with gas- and gravity-aware Nusselt correlations |
| Clear/cloudy sky models, EPW weather | Mars: delta-Eddington transfer through seasonal dust (τ), seasonal surface pressure, downwelling IR; Moon: direct sunlight only |
| Ground temperature from monthly inputs | 1-D regolith thermophysical model (Hayne et al. 2017 for the Moon; thermal-inertia column for Mars) |
| Interior convection correlations fitted at 1 g, 101 kPa | Scaled with gravity, cabin pressure and O2 fraction; mixed with forced cabin ventilation |
| Heat rejection to outdoor air | Radiator sink temperature and heat-pump lift; PV + storage sizing across the lunar night |

> ExoBEM is **not** EnergyPlus and is not endorsed by the U.S. DOE or the EnergyPlus developers.
> See [NOTICE](NOTICE) and [docs/LICENSE_ANALYSIS.md](docs/LICENSE_ANALYSIS.md).

## Verification against EnergyPlus 23.2 (Earth mode, Golden CO TMY3)

| Case (opaque ASHRAE 140 envelopes) | Heating, EnergyPlus / ExoBEM (kWh) | Cooling, EnergyPlus / ExoBEM (kWh) | Hourly load R² | Free-float T RMSE |
|---|---|---|---|---|
| 600 (lightweight) | 4504 / 4507 | 392 / 394 | 0.999 | 0.31 K |
| 900 (heavyweight) | 4147 / 4144 | 124 / 125 | 0.999 | 0.47 K |

Reproduce with `python verification/energyplus/make_idf.py`, run EnergyPlus (see below), then
`python verification/compare_energyplus.py`.

## Key case-study results (4-crew habitat, 6 m × 10 m cylinder, 1 m regolith cover)

| Site | Cooling load | Thermal-control electricity | Notes |
|---|---|---|---|
| Moon, equator | 67 kWh/day | 18 kWh/day | Vertical radiators see 390 K regolith at noon; heat pump runs 37% of the lunation |
| Moon, south-polar ridge (89.5°S) | 66 kWh/day | 3.6 kWh/day | Passive rejection; storage is set by eclipses |
| Mars, Jezero | 38 kWh/day | 3.6 kWh/day | Envelope loses ~1.2 kW; a global dust storm multiplies storage by ~4 |

A metre of lunar regolith (k ≈ 3–5 mW/m·K) makes the envelope nearly adiabatic. The design problem
becomes rejecting internal heat and storing energy through darkness. Reproduce with
`python studies/run_case_studies.py && python studies/make_figures.py && python paper/ExoBEM/build_paper.py`.

## Quick start

```bash
python -m venv .venv
.venv/Scripts/pip install numpy scipy matplotlib python-docx pytest   # Windows; use .venv/bin on Linux/macOS
.venv/Scripts/python -m exobem run examples/moon_south_pole.json -o out_moon
.venv/Scripts/python -m exobem run examples/mars_jezero.json -o out_mars
.venv/Scripts/python -m pytest tests
```

Python API:

```python
import datetime as dt
from exobem import simulate
from exobem.cases import lunar_habitat
from exobem.environment.sites import moon_site

env = moon_site(0.674, 23.473, dt.datetime(2030, 1, 1), duration_days=29.53, dt=1800)
res = simulate(lunar_habitat(), env)
print(res.summary())
```

## Repository layout

```
exobem/                 the engine
  ephemeris/            Mars24, Moon, Earth solar coordinates
  environment/          site environments, regolith model, two-stream dust radiative transfer
  conduction.py         implicit finite-volume conduction (CondFD-style)
  convection.py         TARP and physical (gas/gravity-aware) convection
  simulation.py         surface + zone air heat balance, ideal loads
  thermal_control.py    radiators and heat pumps
  power.py              PV and storage sizing
  io.py                 JSON input and CLI
examples/               JSON inputs (lunar south pole, Jezero)
tests/                  analytical, reference-data and EnergyPlus-parity tests
verification/           EnergyPlus 23.2 comparison (IDF generator + comparison script)
studies/                case studies and figures for the paper
paper/                  manuscripts: ExoBEM/ (this tool), ExoBEM-Core/ (C++ engine), archive/
docs/                   license analysis, roadmap, research dossier
```

## Running the EnergyPlus comparison

```bash
python verification/energyplus/make_idf.py
for f in verification/energyplus/idf/*.idf; do n=$(basename $f .idf); \
  energyplus -w USA_CO_Golden-NREL.724666_TMY3.epw -d verification/energyplus/runs/$n -r $f; done
python verification/compare_energyplus.py
```

## Status and roadmap

v0.1: single-zone engine, verified on Earth, demonstrated on the Moon and Mars. See
[docs/ROADMAP.md](docs/ROADMAP.md) for multi-zone, moisture, terrain shading, the Mars boundary layer and
ECLSS components.

**C++ companion:** [ExoBEM-Core](https://github.com/TensorBuildLab/ExoBEM-Core) is a fork of the full
EnergyPlus v26.2 engine with the same planetary physics (Moon and Mars). It reproduces EnergyPlus exactly on
Earth and agrees with this Python model within 1 % on the lunar and Martian habitat cases.

## Citation

If you use ExoBEM, please cite the accompanying paper (`paper/ExoBEM/ExoBEM_manuscript.docx`, in preparation) and
the repository, https://github.com/TensorBuildLab/ExoBEM.

## License

BSD 3-Clause (see [LICENSE](LICENSE)). EnergyPlus attribution in [NOTICE](NOTICE).
