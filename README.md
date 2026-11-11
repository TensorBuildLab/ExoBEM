<p align="center"><img src="docs/logo/exobem_logo.png" alt="ExoBEM" width="520"></p>

# ExoBEM: building energy simulation for the Moon and Mars

ExoBEM is an open-source Python tool for simulating the energy use of **sealed, pressurized habitats on the Moon
and Mars**. Its heat-balance core re-implements the method documented in the EnergyPlus™ Engineering Reference:
surface heat balances, finite-volume conduction, TARP convection, ScriptF interior radiation, zone air balance
and ideal loads. It is verified against EnergyPlus on Earth. Around that core it models what is different on
other worlds, factor by factor ([docs/planetary_factors.md](docs/planetary_factors.md)):

| On Earth (EnergyPlus) | On the Moon and Mars (ExoBEM) |
|---|---|
| 24-h day, Earth Sun, EPW weather | Lunar day of 29.5 d and Mars sol; Mars24 and lunar ephemerides; [planetary weather files (PWF)](docs/weather_format.md) |
| Outdoor air for convection, ventilation and humidity | Vacuum or 0.7 kPa CO₂; **no outdoor air at all**: leakage and airlock venting, a cabin vapour balance with a condensing heat exchanger, dew-point checks |
| Sky and ground models fitted to Earth | 2.7 K sky; dusty-CO₂ sky by delta-Eddington two-stream; regolith columns in periodic equilibrium |
| Correlations for air at 1 atm and 1 g | Convection for any gas, pressure and gravity; cabins at 56.5–101 kPa |
| Planar walls | Curved regolith shields (exact cylindrical and spherical shell conduction) |
| Heat rejection to outdoor air; grid power | Radiators with heat-pump lift; PV with cell temperature in vacuum, Li-ion, regenerative fuel cells, fission |

> ExoBEM is **not** EnergyPlus and is not endorsed by the U.S. DOE or the EnergyPlus developers.
> See [NOTICE](NOTICE) and [docs/LICENSE_ANALYSIS.md](docs/LICENSE_ANALYSIS.md).

## Install

```bash
python -m pip install "exobem[plot] @ git+https://github.com/TensorBuildLab/ExoBEM"
exobem --version
```

More options (working copy, tests): [docs/INSTALL.md](docs/INSTALL.md).

## Ten-minute tutorial

[docs/tutorial](docs/tutorial/README.md) simulates a four-crew habitat at the lunar south pole for 30 days: its
cooling and humidity, and whether a solar array and battery can carry it through a 12-day eclipse. The short
version:

```bash
exobem examples my_study && cd my_study
exobem weather --body moon --lat -89.5 --lon 0 --horizon -1.65 --start 2030-02-20T00:00:00 \
               --days 30 --timestep 3600 -o south_pole_30d.pwf
exobem geometry lunar_surface_habitat.json -o habitat.png
exobem run lunar_surface_habitat.json -o out        # -> out/summary.json, timeseries.csv, power.csv
```

```python
import json, exobem
from exobem.io import build_model
from exobem.weather import read_pwf

res = exobem.simulate(build_model(json.load(open("lunar_surface_habitat.json"))), read_pwf("south_pole_30d.pwf"))
print(res.summary())
```

## Verification

| Check | Result |
|---|---|
| Opaque ASHRAE 140 Cases 600/900 vs EnergyPlus 23.2 (Earth mode, Golden CO) | Annual loads within 0.7 %; hourly load R² 0.999; free-float RMSE 0.31–0.47 K |
| Mars24 worked example; Diviner lunar temperatures; Appelbaum–Flood Mars insolation; MEDA at Jezero | Reproduced (see the paper) |
| NASA Artemis surface habitat, night heat leak 1550 W / daylight net loss 850 W | Calibrated / 1053 W (+24 %) |
| Analytic: curved-shell conduction, PV cell in vacuum, cabin vapour balance, erfc conduction, ScriptF | Exact to < 10⁻⁶–10⁻³ |
| Thermonaut (independent EnergyPlus fork) on the same weather files | Cooling energy within 0.2 % (Moon) and 1.4 % (Mars) |

Run the test suite with `python -m pytest -q`. To reproduce the EnergyPlus comparison, see
[Running the EnergyPlus comparison](#running-the-energyplus-comparison).

## Case-study results (NASA-class habitats for the first crews)

| | Lunar habitat, south pole | Lunar habitat, equator | Mars habitat, Jezero |
|---|---|---|---|
| Crew, volume | 4, 174 m³ | 4, 174 m³ | 6, 224 m³ |
| Heat to the radiators (mean) | 12.7 kW | 12.9 kW | 8.6 kW |
| Thermal-control electricity | 3.6 kWh/day (passive) | 98 kWh/day (heat pump 41 % of the time) | 15 kWh/day |
| Condensation risk on inner surfaces | none | none | 4,839 h/year with aerogel only at 25 °C / 60 % RH; none at ≤ 50 % RH or with a 1 m regolith cover |
| Storage, PV at 2× energy-balance area (Li-ion) | 4.2 MWh (uniform-horizon eclipse of 12 d) | 6.6 MWh (354-h night) | 0.25 MWh (27 MWh in a global dust storm) |

Reproduce with `python studies/calibrate_lunar_mli.py && python studies/run_case_studies.py && python
studies/make_figures.py && python paper/ExoBEM/build_paper.py`.

## Repository layout

```
exobem/                 the package
  ephemeris/            Mars24, Moon, Earth solar coordinates
  environment/          site environments, regolith model (with equilibrium), dust two-stream radiative transfer
  weather.py            planetary weather files (PWF): read, write, validate, generate
  checks.py             sealed-habitat input checks
  conduction.py         implicit finite-volume conduction, curved shells
  convection.py         TARP and physical (gas/pressure/gravity-aware) convection
  simulation.py         surface + zone air heat balance, ideal loads, cabin humidity
  thermal_control.py    radiators and heat pumps
  power.py              PV, batteries, regenerative fuel cells, fission, dispatch
  cases.py              reference habitats (NASA-class lunar and Mars habitats)
  plot.py, io.py        geometry plots; JSON input and the exobem command
examples/               example models, weather files, tutorial script
docs/                   install guide, tutorial, weather format, factor analysis, EnergyPlus comparison, research dossiers
tests/                  analytical, reference-data and EnergyPlus-parity tests
verification/           EnergyPlus 23.2 comparison (IDF generator + comparison script)
studies/                case studies and figures for the paper
paper/                  manuscripts: ExoBEM/ (this tool), Thermonaut/ (C++ engine), archive/
```

## Running the EnergyPlus comparison

```bash
python verification/energyplus/make_idf.py
for f in verification/energyplus/idf/*.idf; do n=$(basename $f .idf); \
  energyplus -w USA_CO_Golden-NREL.724666_TMY3.epw -d verification/energyplus/runs/$n -r $f; done
python verification/compare_energyplus.py
```

## Related engine: Thermonaut

[Thermonaut](https://github.com/TensorBuildLab/Thermonaut) is a separate project: a fork of the full EnergyPlus
v26.2 engine with a planetary mode. Neither tool needs the other. Both read PWF weather files, so a design can be
run in both on the same environment; on the lunar and Martian verification habitats they agree within about 1.5 %.

## Citation

If you use ExoBEM, please cite the accompanying paper (`paper/ExoBEM/ExoBEM_manuscript.docx`, submitted to Applied Energy) and
the repository, https://github.com/TensorBuildLab/ExoBEM.

## License

BSD 3-Clause (see [LICENSE](LICENSE)). EnergyPlus attribution in [NOTICE](NOTICE).
