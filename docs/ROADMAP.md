# ExoBEM project plan and roadmap

Goal: a research-grade building energy modeling (BEM) tool for habitats on the Moon and Mars,
built on the EnergyPlus heat-balance method, with a verification trail and a journal paper.

## Why a re-implementation first (and not a direct fork)

EnergyPlus hard-codes Earth assumptions in many places: 24-hour days and 8760-hour years in the
weather manager and schedules; Earth solar position; outdoor air as the convective and long-wave
medium; psychrometrics of moist air; ground temperature models; and HVAC components that exchange
with outdoor air. A fork would have to change these across about 700,000 lines of C++ before a
single lunar run works. It would also need a full C++ toolchain, which this machine lacks.

Phase 1 therefore re-implements the parts of the EnergyPlus algorithms that habitats need, in a
compact Python engine whose time base, ephemeris and boundary conditions are planet-agnostic. It is
verified against EnergyPlus 23.2 on Earth, so the planetary extensions start from a trusted core.
Phase 3 ports the validated planetary physics back into EnergyPlus's C++ code base.

## Phase 1 — ExoBEM core (v0.1, this release) ✅

| Module | Content | Status |
|---|---|---|
| `ephemeris` | Mars24 (Allison & McEwen 2000), selenographic Sun (Meeus + Cassini laws), NOAA Earth | ✅ tested vs. Mars24 worked example |
| `environment` | EPW reader (Earth); lunar vacuum/regolith environment; Mars dust/pressure/air/sky environment | ✅ |
| `environment.regolith` | Hayne et al. (2017) lunar regolith thermophysics; Mars thermal-inertia column | ✅ vs. Diviner |
| `environment.twostream` | Delta-Eddington surface irradiance through Martian dust | ✅ |
| `conduction` | CondFD-style implicit finite volumes, stretched grids, T-dependent properties | ✅ analytic tests |
| `convection` | EnergyPlus TARP + gas/gravity-aware Nusselt correlations | ✅ |
| `simulation` | Surface + zone air heat balance, ScriptF, ideal loads, exact air/surface coupling, steady warm-up | ✅ vs. EnergyPlus 23.2 |
| `thermal_control` | Radiator sink, heat-pump lift, electric power | ✅ |
| `power` | PV and storage sizing | ✅ |
| `io` | JSON input, CLI | ✅ |

## Phase 2 — Science extensions (v0.2–v0.5)

1. **Multi-zone** habitats (inter-zone surfaces, airlocks, inter-module ventilation).
2. **Moisture balance** of the cabin air (crew water vapour, condensing heat exchanger), CO2/O2 tracking.
3. **Terrain and shading**: DEM horizon masks (LOLA for lunar poles, HiRISE/CTX for Mars), shading between modules, and exterior surface-to-surface radiation for non-convex bases.
4. **Mars boundary layer**: replace the empirical air-temperature surrogate with a 1-D surface-layer model (Monin–Obukhov); Mars Climate Database (MCD) and MEDA/REMS data readers.
5. **Windows/viewports** (multi-pane, angle-dependent optics, UV/radiation filters).
6. **Component HVAC/ECLSS**: pumped single-phase loops, heat exchangers, loop heat pipes, deployable radiators, waste-heat recovery.
7. **Calibration and validation** against thermal-vacuum chamber tests and analog habitats (HI-SEAS, MDRS, Mars-500).
8. **Uncertainty quantification**: Monte-Carlo over regolith properties, dust optical depth and crew schedules.

## Phase 3 — Back-port into EnergyPlus C++ (v1.0)

* Fork NREL/EnergyPlus into a renamed project (license clause 4: no "EnergyPlus" in the product name).
* Add a `Site:Planet` object (gravity, day length, atmosphere gas, solar constant and ephemeris).
* Generalize the WeatherManager time base to arbitrary day lengths and add an extraterrestrial weather format.
* Add a vacuum/CO2 outdoor-medium option to the convection and psychrometric modules.
* Add a regolith ground model and radiator plant components.
* Regression-test the fork against ExoBEM v0.x.

## Phase 4 — Dissemination

* Journal paper 1 (this release): method, verification, lunar/Mars case studies.
* Paper 2: design-space exploration and optimization of regolith-shielded habitats.
* Paper 3: coupled habitat–power–ECLSS operations for a lunar south-pole base.
* PyPI package, documentation site, tutorial notebooks.
