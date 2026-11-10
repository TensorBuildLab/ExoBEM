# ExoBEM compared with EnergyPlus

How ExoBEM relates to EnergyPlus, element by element. **same**: the same equations or algorithm (verified against
EnergyPlus 23.2 on Earth); **adapted**: the same structure, generalized for planetary conditions; **different**:
a different method or scope. Source: `paper/common/eplus_compare.py`.

| Element | EnergyPlus | ExoBEM | Relation |
|---|---|---|---|
| Input | IDF / epJSON text files; ~800 object types | JSON file (epJSON-inspired sections) or Python objects; ~15 object types | adapted |
| Program structure | Managers called from SimulationManager in nested environment / day / hour / time-step loops | Pre-processing, one time-step loop (simulate), post-processing (thermal control, power); see the flow figure of the paper | adapted |
| Weather | EPW file: 8,760 hourly records, read day by day, interpolated to the time step | PWF file or generated environment for the whole run at the time step; no Earth range checks | different |
| Time base | 24-hour days, 1-60 time steps per hour | Any time step; day length free (lunation, sol) | different |
| Solar position | Earth Fourier fits for declination and equation of time; 15°/h | NOAA (Earth), Mars24 (Mars), selenographic subsolar point (Moon) | different |
| Sky diffuse model | Perez anisotropic | Perez on Earth; isotropic + dust two-stream off-Earth | same on Earth |
| Outside-face heat balance | Absorbed solar + long-wave (sky, air, ground) + convection = conduction | Same terms; long-wave linearized about the current iterate; sky, ground and air terms set by the planet | same on Earth |
| Exterior convection | TARP, DOE-2, MoWiTT, adaptive | TARP (Earth); physical correlation for any gas, pressure, gravity; none in vacuum | same on Earth |
| Conduction | Conduction transfer functions (default) or CondFD | Implicit finite volumes (CondFD formulation), stretched grids, k(T) and cp(T), optional curved shells | adapted |
| Inside-face heat balance | Conduction + convection + ScriptF long-wave + radiant gains | Same | same |
| Interior convection | TARP and others (air at 1 atm, 1 g) | TARP (Earth); physical mixed convection for the cabin gas at cabin pressure and body gravity | same on Earth |
| Interior long-wave | ScriptF from approximate view factors | Same (Hottel ScriptF, area-weighted view factors with reciprocity) | same |
| Zone air balance | Predictor-corrector, 3rd-order backward difference; surfaces and air iterated | Implicit Euler; surfaces, interior radiation and air solved simultaneously by superposition | different |
| Loads | Ideal loads air system or full HVAC | Ideal loads (sensible) + condensing-heat-exchanger latent load + cold plates | adapted |
| Outdoor air | Infiltration, ventilation, outdoor-air systems | Earth only; forbidden off-Earth (sealed cabin); leakage and airlock losses instead | different |
| Moisture | Zone humidity balance; EMPD, HAMT for materials | Cabin vapour balance with condensing heat exchanger and dew-point check | adapted |
| Warm-up | Repeat the first day until zone temperatures converge | Steady pseudo-transient solve + one repetition of the first solar day; regolith columns equilibrated | different |
| Heat rejection and HVAC | Coils, chillers, towers, plant loops | Radiator sink temperature, heat-pump lift, pump power (post-processing) | different |
| Electric power | ElectricLoadCenter: PV, batteries, generators | PV with vacuum cell temperature and dust, Li-ion, regenerative fuel cell, fission; dispatch | adapted |
| Output | ESO / SQLite / tabular reports, report variables | CSV time series + JSON summary; Python result objects | adapted |
| Implementation | C++, ~720,000 lines | Python (NumPy, SciPy), ~3,500 lines | different |

## How a run is coordinated

1. **Model input**: JSON file or Python objects (materials, constructions, geometry, zone, gains, thermal control, power).
2. **Site environment**: a PWF weather file, or generated for the whole run (ephemeris, sky and dust radiation, regolith column, ambient gas, wind).
3. **Pre-processing**: model checks (sealed cabin, oxygen limits, Earth-only options refused); one stacked finite-volume grid for all constructions; view factors and ScriptF; incident solar on every surface for every step; schedules; cabin-gas properties.
4. **Initialization**: steady pseudo-transient solve with period-mean boundary conditions, then one repetition of the first solar day.
5. **Time-step loop**: outside faces (convection for the planet's gas or none, long-wave to sky and regolith) → banded conduction solve for n+2 right-hand sides → dense system for inside faces + zone air → ideal loads → iterate to 0.005 K → cabin vapour balance and condensing heat exchanger.
6. **Thermal control**: heat from cabin air, cold plates and condensing heat exchanger → radiator sink and temperature → passive rejection or heat-pump lift.
7. **Power system**: electric load (equipment, life support, lighting, thermal control) → PV, fission, battery, regenerative fuel cell dispatch → unmet and curtailed energy.
