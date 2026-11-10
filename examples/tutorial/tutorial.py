"""ExoBEM tutorial, Python part (docs/tutorial/README.md walks through it step by step).

Run from a folder that contains south_pole_30d.pwf and lunar_surface_habitat.json (steps 1-2 of the tutorial):

    python tutorial.py

It runs the lunar habitat, prints the key results, compares three design options and writes
tutorial_results.png.
"""
import copy
import json
from pathlib import Path

import numpy as np

import exobem
from exobem.io import build_environment, build_model, build_power, electric_load
from exobem.power import FissionPower, PowerSystem, simulate_power
from exobem.weather import read_pwf

HERE = Path.cwd()

# ----------------------------------------------------------------------------- 1. load the model and weather
cfg = json.loads((HERE / "lunar_surface_habitat.json").read_text())
model = build_model(cfg)
env = read_pwf(HERE / cfg["site"]["weather_file"])
print(f"ExoBEM {exobem.__version__}: {model.name}, {model.zone.geometry.volume:.0f} m3, "
      f"{env.n} steps of {env.dt:.0f} s on the {env.planet}")

# ----------------------------------------------------------------------------- 2. simulate
res = exobem.simulate(model, env)
s = res.summary()
days = env.n * env.dt / 86400
print(f"cabin air cooling      {s['cooling_kWh'] / days:6.1f} kWh/day (peak {s['peak_cooling_W'] / 1000:.1f} kW)")
print(f"cold-plate heat        {s['coldplate_kWh'] / days:6.1f} kWh/day")
print(f"latent (condensate)    {s['latent_kWh'] / days:6.1f} kWh/day, {s['condensate_kg'] / days:.1f} kg water/day")
print(f"cabin RH               {s['rh_min']:.2f} - {s['rh_max']:.2f}; coldest surface "
      f"{s['min_surface_minus_dewpoint_K']:.1f} K above the dew point")
print(f"gas to make up         {s['cabin_gas_makeup_kg'] / days:.2f} kg/day (leakage + airlock)")
print(f"thermal control power  {s['thermal_control_electric_kWh'] / days:6.1f} kWh/day")

# ----------------------------------------------------------------------------- 3. power system
system, ext = build_power(cfg)
load = electric_load(res, ext)
pw = simulate_power(system, env, load, repeat_cycles=2)
print("PV + battery:", {k: round(v, 3) for k, v in pw["summary"].items() if isinstance(v, float)})
fis = simulate_power(PowerSystem(fission=FissionPower(40.0, 0.181)), env, load)
print("40 kWe fission: unmet", fis["summary"]["unmet_kWh"], "kWh; curtailed",
      round(fis["summary"]["curtailed_kWh"]), "kWh")

# ----------------------------------------------------------------------------- 4. a design change: 1 m regolith cover
cfg2 = copy.deepcopy(cfg)
cfg2["constructions"]["covered"] = ["lunar_regolith_cover_1m"] + cfg["constructions"]["shell"]
cfg2["geometry"].update(wall="covered", roof="covered")
res2 = exobem.simulate(build_model(cfg2), env)
print(f"with a 1 m regolith cover: cabin cooling {res2.summary()['cooling_kWh'] / days:.1f} kWh/day")

# ----------------------------------------------------------------------------- 5. plot
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    t = env.time_s / 86400
    fig, ax = plt.subplots(3, 1, figsize=(7, 6.5), sharex=True)
    ax[0].plot(t, env.T_ground - 273.15, label="regolith surface")
    ax[0].plot(t, res.T_outside_C[:, 0], label="outer face, wall facing north")
    ax[0].set_ylabel("°C")
    ax[0].legend(fontsize=7)
    ax[1].plot(t, res.Q_cooling_W / 1000, label="cabin air cooling")
    ax[1].plot(t, res.Q_coldplate_W / 1000, label="cold plates")
    ax[1].plot(t, load / 1000, label="electric load")
    ax[1].set_ylabel("kW")
    ax[1].legend(fontsize=7)
    ax[2].plot(t, pw["soc_battery_kWh"] / system.battery.capacity_kWh, label="battery state of charge")
    ax[2].plot(t, env.sun_visible, label="Sun visible (fraction of disk)", alpha=0.6)
    ax[2].set_xlabel("Elapsed time (Earth days)")
    ax[2].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(HERE / "tutorial_results.png", dpi=150)
    print("wrote tutorial_results.png")
except ImportError:
    print("matplotlib not installed: skipping the plot (pip install exobem[plot])")
