"""JSON input files (an epJSON-inspired schema) and the command-line runner.

Example (see ``examples/``)::

    {
      "simulation": {"name": "artemis_base", "timestep_s": 1800},
      "site": {"planet": "moon", "latitude": -89.45, "longitude": -137.3,
               "start_utc": "2030-01-01T00:00:00", "duration_days": 59.06,
               "horizon_deg": -1.0},
      "materials": { "my_foam": {"thickness": 0.05, "conductivity": 0.03,
                                  "density": 30, "specific_heat": 1200} },
      "constructions": { "shell": ["lunar_regolith_cover_1m", "beta_cloth_outer_1mm",
                                    "mli_20layer_vacuum", "aluminum_2219_4mm"] },
      "geometry": {"type": "horizontal_cylinder", "radius": 3, "length": 10,
                   "shell": "shell", "end": "shell", "floor": "floor"},
      "zone": {"cabin_pressure_kPa": 70.3, "o2_fraction": 0.265, "leakage_kg_per_day": 0.1,
               "heating_setpoint_C": 18.3, "cooling_setpoint_C": 26.7,
               "interior_convection": "physical"},
      "gains": [{"name": "crew", "power_W": 328, "radiant_fraction": 0.5, "latent_W": 252,
                 "schedule": [0.3,0.3,0.3,0.3,0.3,0.3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0.3,0.3]}],
      "thermal_control": {"radiator_area_m2": 40, "radiator_azimuth": 0}
    }
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path

from . import geometry as geo
from .materials import Construction, Material, NoMassMaterial, library, hayne_conductivity, hayne_specific_heat
from .model import InternalGain, Model, ThermalControlSystem, Thermostat, Zone
from .simulation import simulate
from .environment import sites


def _material(name, d):
    if "resistance" in d:
        return NoMassMaterial(name, d["resistance"], d.get("solar_absorptance", 0.7),
                              d.get("thermal_emissivity", 0.9), d.get("roughness", "MediumRough"))
    kw = {}
    if d.get("conductivity_model") == "hayne":
        kw["k_of_T"] = hayne_conductivity(d["conductivity"], d.get("chi", 2.7))
    if d.get("specific_heat_model") == "hayne":
        kw["cp_of_T"] = hayne_specific_heat
    return Material(name, d["thickness"], d["conductivity"], d["density"], d["specific_heat"],
                    d.get("solar_absorptance", 0.7), d.get("thermal_emissivity", 0.9),
                    d.get("roughness", "MediumRough"), **kw)


def build_environment(site: dict, dt: float):
    planet = site["planet"].lower()
    if planet == "earth":
        return sites.earth_from_epw(site["epw"], dt=dt, n_days=int(site.get("duration_days", 365)),
                                    ground_reflectance=site.get("ground_reflectance", 0.2),
                                    ground_temperature_C=site.get("ground_temperature_C", 10.0))
    start = _dt.datetime.fromisoformat(site.get("start_utc", "2030-01-01T00:00:00"))
    horizon = site.get("horizon_deg")
    if isinstance(horizon, dict):
        horizon = (horizon["azimuth"], horizon["elevation"])
    elif horizon is not None:
        h = float(horizon)
        horizon = ([0.0, 360.0], [h, h])
    if planet == "moon":
        return sites.moon_site(site["latitude"], site["longitude"], start, site.get("duration_days", 29.53),
                               dt=dt, horizon=horizon)
    if planet == "mars":
        kw = {k: site[k] for k in ("tau", "P_mean", "thermal_inertia", "albedo", "wind_mean") if k in site}
        if "dust_storm" in site:
            kw["tau_kwargs"] = dict(storm=tuple(site["dust_storm"]))
        return sites.mars_site(site["latitude"], site["longitude"], start, site.get("duration_sols", 30),
                               dt=dt, horizon=horizon, **kw)
    raise ValueError(f"unknown planet {planet}")


def build_model(cfg: dict) -> Model:
    lib = library()
    for name, d in cfg.get("materials", {}).items():
        lib[name] = _material(name, d)
    cons = {name: Construction(name, [lib[l] for l in layers]) for name, layers in cfg["constructions"].items()}
    g = dict(cfg["geometry"])
    kind = g.pop("type")
    builder = {"box": geo.box, "vertical_cylinder": geo.vertical_cylinder,
               "horizontal_cylinder": geo.horizontal_cylinder, "dome": geo.dome}[kind]
    geom = builder(**g)
    z = cfg.get("zone", {})
    gains = [InternalGain(d["name"], d["power_W"], d.get("radiant_fraction", 0.5), d.get("latent_W", 0.0),
                          d.get("schedule", 1.0)) for d in cfg.get("gains", [])]
    zone = Zone(cfg.get("simulation", {}).get("name", "zone"), geom, gains,
                Thermostat(z.get("heating_setpoint_C", 18.3), z.get("cooling_setpoint_C", 26.7)),
                cabin_pressure_Pa=1000.0 * z.get("cabin_pressure_kPa", 101.325),
                cabin_o2_fraction=z.get("o2_fraction", 0.21),
                infiltration_ach=z.get("infiltration_ach", 0.0),
                leakage_kg_per_day=z.get("leakage_kg_per_day", 0.0),
                makeup_gas_temperature_C=z.get("makeup_gas_temperature_C"),
                interior_convection=z.get("interior_convection", "physical"),
                cabin_air_velocity=z.get("cabin_air_velocity", 0.15),
                initial_temperature_C=z.get("initial_temperature_C", 21.0))
    tcs = ThermalControlSystem(**cfg["thermal_control"]) if "thermal_control" in cfg else None
    sim = cfg.get("simulation", {})
    return Model(sim.get("name", "model"), zone, cons, timestep_s=sim.get("timestep_s", 1800.0),
                 thermal_control=tcs)


def run_file(path, out_dir=None, verbose=False):
    cfg = json.loads(Path(path).read_text())
    model = build_model(cfg)
    env = build_environment(cfg["site"], model.timestep_s)
    res = simulate(model, env, verbose=verbose)
    out = Path(out_dir or Path(path).with_suffix(""))
    out.mkdir(parents=True, exist_ok=True)
    res.to_csv(out / "timeseries.csv")
    env.to_csv(out / "environment.csv")
    (out / "summary.json").write_text(json.dumps(res.summary(), indent=2))
    return res


def main(argv=None):
    p = argparse.ArgumentParser(prog="exobem", description="ExoBEM - building energy simulation for the Moon and Mars")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run a JSON model")
    r.add_argument("input")
    r.add_argument("-o", "--output")
    r.add_argument("-v", "--verbose", action="store_true")
    a = p.parse_args(argv)
    if a.cmd == "run":
        res = run_file(a.input, a.output, a.verbose)
        print(json.dumps(res.summary(), indent=2))


if __name__ == "__main__":
    main()
