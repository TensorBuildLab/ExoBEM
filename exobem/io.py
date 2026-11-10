"""JSON input files (an epJSON-inspired schema) and the ``exobem`` command-line tool.

A model file has these sections (all lengths in m, temperatures in C unless the key says K;
see docs/input_reference.md and examples/)::

    {
      "simulation": {"name": "artemis_base", "timestep_s": 1800},
      "site": {"weather_file": "moon_south_pole.pwf"}                  <- a PWF weather file, or
      "site": {"planet": "moon", "latitude": -89.45, "longitude": -137.3,  <- generate on the fly
               "start_utc": "2030-01-01T00:00:00", "duration_days": 59.06, "horizon_deg": -1.0},
      "materials": {"my_foam": {"thickness": 0.05, "conductivity": 0.03, "density": 30, "specific_heat": 1200}},
      "constructions": {"shell": ["lunar_regolith_cover_1m", "beta_cloth_outer_1mm", "mli_20layer_vacuum",
                                  "aluminum_2219_4mm", "interior_panel_10mm"]},
      "geometry": {"type": "horizontal_cylinder", "radius": 3, "length": 10,
                   "shell": "shell", "end": "shell", "floor": "floor"},
      "zone": {"cabin_pressure_kPa": 70.3, "o2_fraction": 0.265, "leakage_kg_per_day": 0.1,
               "airlock_cycles_per_day": 0.5, "airlock_loss_kg_per_cycle": 0.5,
               "heating_setpoint_C": 18, "cooling_setpoint_C": 27, "humidity_control": true,
               "internal_mass": [{"name": "racks", "construction": "rack", "area_m2": 60}]},
      "gains": [{"name": "crew", "power_W": 340, "latent_W": 215, "radiant_fraction": 0.5,
                 "schedule": [0.65, ..., 1.0], "category": "crew"},
                {"name": "eclss", "power_W": 2000, "electric": true, "category": "eclss"}],
      "thermal_control": {"radiator_area_m2": 40, "radiator_azimuth": 0},
      "power": {"pv": [{"area_m2": 120, "tracking": "vertical_single_axis"}],
                "battery": {"capacity_kWh": 400}, "rfc": {"capacity_kWh": 2000},
                "fission": {"rated_kWe": 40}, "external_load_W": 0}
    }
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import shutil
from pathlib import Path

import numpy as np

from . import geometry as geo
from .materials import Construction, Material, NoMassMaterial, library, hayne_conductivity, hayne_specific_heat
from .model import InternalGain, InternalMass, Model, ThermalControlSystem, Thermostat, Zone
from .simulation import simulate
from .environment import sites

EXAMPLES = Path(__file__).resolve().parent / "data" / "examples"


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


def build_environment(site: dict, dt: float, base_dir: Path | None = None):
    """Environment from a PWF weather file (``weather_file``) or generated from site parameters."""
    if "weather_file" in site:
        from .weather import read_pwf
        p = Path(site["weather_file"])
        if not p.is_absolute() and base_dir is not None:
            p = base_dir / p
        env = read_pwf(p)
        if abs(env.dt - dt) > 1e-6:
            raise ValueError(f"weather file time step {env.dt} s differs from simulation timestep_s {dt} s")
        return env
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
        env = sites.moon_site(site["latitude"], site["longitude"], start, site.get("duration_days", 29.53),
                              dt=dt, horizon=horizon)
    elif planet == "mars":
        kw = {k: site[k] for k in ("tau", "P_mean", "thermal_inertia", "albedo", "wind_mean") if k in site}
        if "dust_storm" in site:
            kw["tau_kwargs"] = dict(storm=tuple(site["dust_storm"]))
        env = sites.mars_site(site["latitude"], site["longitude"], start, site.get("duration_sols", 30),
                              dt=dt, horizon=horizon, **kw)
    else:
        raise ValueError(f"unknown planet {planet}")
    env.extra["start_utc"] = start
    env.extra["site_name"] = site.get("name", "")
    return env


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
                          d.get("schedule", 1.0), d.get("electric", False), d.get("category", ""),
                          d.get("heat_fraction", 1.0), d.get("coldplate_fraction", 0.0))
             for d in cfg.get("gains", [])]
    zone = Zone(cfg.get("simulation", {}).get("name", "zone"), geom, gains,
                Thermostat(z.get("heating_setpoint_C", 18.0), z.get("cooling_setpoint_C", 27.0)),
                cabin_pressure_Pa=1000.0 * z.get("cabin_pressure_kPa", 101.325),
                cabin_o2_fraction=z.get("o2_fraction", 0.21),
                infiltration_ach=z.get("infiltration_ach", 0.0),
                leakage_kg_per_day=z.get("leakage_kg_per_day", 0.0),
                airlock_cycles_per_day=z.get("airlock_cycles_per_day", 0.0),
                airlock_loss_kg_per_cycle=z.get("airlock_loss_kg_per_cycle", 0.0),
                makeup_gas_temperature_C=z.get("makeup_gas_temperature_C"),
                interior_convection=z.get("interior_convection", "physical"),
                cabin_air_velocity=z.get("cabin_air_velocity", 0.15),
                initial_temperature_C=z.get("initial_temperature_C", 21.0),
                internal_mass=[InternalMass(m["name"], m["construction"], m["area_m2"])
                               for m in z.get("internal_mass", [])],
                humidity_control=z.get("humidity_control", True),
                rh_max=z.get("rh_max", 0.60), rh_min=z.get("rh_min", 0.25), initial_rh=z.get("initial_rh", 0.45))
    tcs = ThermalControlSystem(**cfg["thermal_control"]) if "thermal_control" in cfg else None
    sim = cfg.get("simulation", {})
    return Model(sim.get("name", "model"), zone, cons, timestep_s=sim.get("timestep_s", 1800.0),
                 thermal_control=tcs)


def build_power(cfg: dict):
    from .power import Battery, FissionPower, PowerSystem, PVArray, RegenerativeFuelCell
    p = cfg.get("power")
    if not p:
        return None, 0.0
    sysm = PowerSystem(pv=[PVArray(**a) for a in p.get("pv", [])],
                       fission=FissionPower(**p["fission"]) if "fission" in p else None,
                       battery=Battery(**p["battery"]) if "battery" in p else None,
                       rfc=RegenerativeFuelCell(**p["rfc"]) if "rfc" in p else None)
    return sysm, float(p.get("external_load_W", 0.0))


def electric_load(res, external_W=0.0):
    """Total habitat electric demand [W]: electric internal gains + thermal control + external loads."""
    P = np.array(res.electric_internal_W, float)
    if res.electric_W is not None:
        P = P + res.electric_W
    return P + external_W


def run_file(path, out_dir=None, verbose=False):
    path = Path(path)
    cfg = json.loads(path.read_text())
    model = build_model(cfg)
    env = build_environment(cfg["site"], model.timestep_s, base_dir=path.parent)
    res = simulate(model, env, verbose=verbose)
    out = Path(out_dir or path.with_suffix(""))
    out.mkdir(parents=True, exist_ok=True)
    res.to_csv(out / "timeseries.csv")
    env.to_csv(out / "environment.csv")
    summary = res.summary()
    system, ext = build_power(cfg)
    if system is not None:
        from .power import simulate_power
        load = electric_load(res, ext)
        pr = simulate_power(system, env, load, repeat_cycles=2)
        summary["power"] = pr["summary"]
        import csv
        with open(out / "power.csv", "w", newline="") as f:
            w = csv.writer(f)
            keys = ["load_W", "generation_pv_W", "generation_fission_W", "battery_W", "rfc_W", "soc_battery_kWh",
                    "soc_rfc_kWh", "unmet_W", "curtailed_W"]
            w.writerow(["time_s"] + keys)
            for i in range(env.n):
                w.writerow([f"{env.time_s[i]:.6g}"] + [f"{pr[k][i]:.6g}" for k in keys])
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    res.summary_full = summary
    return res


def main(argv=None):
    from . import __version__
    p = argparse.ArgumentParser(prog="exobem", description="ExoBEM - building energy simulation for the Moon and Mars")
    p.add_argument("--version", action="version", version=f"exobem {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run a JSON model; writes timeseries.csv, environment.csv, power.csv, summary.json")
    r.add_argument("input")
    r.add_argument("-o", "--output", help="output folder (default: input file name without extension)")
    r.add_argument("-v", "--verbose", action="store_true")
    w = sub.add_parser("weather", help="generate a planetary weather (PWF) file")
    w.add_argument("--body", required=True, choices=["moon", "mars"])
    w.add_argument("--lat", type=float, required=True, help="latitude, deg (north positive)")
    w.add_argument("--lon", type=float, required=True, help="longitude, deg (east positive)")
    w.add_argument("--start", default="2030-01-01T00:00:00", help="start time, UTC (ISO 8601)")
    w.add_argument("--days", type=float, required=True, help="duration in Earth days")
    w.add_argument("--timestep", type=float, default=1800.0, help="time step, s")
    w.add_argument("--horizon", type=float, default=None, help="uniform horizon elevation, deg")
    w.add_argument("--site-name", default="")
    w.add_argument("--dust-storm", nargs=3, type=float, metavar=("LS_START", "LS_END", "TAU"),
                   help="Mars global dust storm")
    w.add_argument("-o", "--output", required=True)
    g = sub.add_parser("geometry", help="plot the geometry of a JSON model to an image")
    g.add_argument("input")
    g.add_argument("-o", "--output", required=True)
    e = sub.add_parser("examples", help="copy the example models into a folder")
    e.add_argument("folder", nargs="?", default="exobem_examples")
    i = sub.add_parser("info", help="print the header and a summary of a PWF weather file")
    i.add_argument("weather_file")
    a = p.parse_args(argv)
    if a.cmd == "run":
        res = run_file(a.input, a.output, a.verbose)
        print(json.dumps(res.summary_full, indent=2))
    elif a.cmd == "weather":
        from .weather import generate, write_pwf
        kw = {}
        if a.horizon is not None:
            kw["horizon"] = ([0.0, 360.0], [a.horizon, a.horizon])
        if a.dust_storm:
            if a.body != "mars":
                p.error("--dust-storm applies to Mars only")
            kw["tau_kwargs"] = dict(storm=tuple(a.dust_storm))
        env = generate(a.body, a.lat, a.lon, a.start, a.days, a.timestep, a.site_name, **kw)
        write_pwf(env, a.output, site_name=a.site_name, horizon=kw.get("horizon"),
                  generator=f"exobem {__version__} weather --body {a.body} --lat {a.lat} --lon {a.lon} "
                            f"--start {a.start} --days {a.days} --timestep {a.timestep}")
        print(f"wrote {a.output}: {env.n} records of {a.timestep:g} s")
    elif a.cmd == "geometry":
        from .plot import plot_geometry
        cfg = json.loads(Path(a.input).read_text())
        plot_geometry(build_model(cfg), a.output, title=cfg.get("simulation", {}).get("name"))
        print(f"wrote {a.output}")
    elif a.cmd == "examples":
        dst = Path(a.folder)
        dst.mkdir(parents=True, exist_ok=True)
        for f in sorted(EXAMPLES.glob("*")):
            shutil.copy(f, dst / f.name)
            print("copied", dst / f.name)
    elif a.cmd == "info":
        from .weather import read_pwf
        env = read_pwf(a.weather_file)
        for k, v in env.extra["pwf_header"].items():
            print(f"{k:>22}: {v}")
        print(f"{'records':>22}: {env.n} x {env.dt:g} s = {env.n * env.dt / 86400:.2f} Earth days")
        print(f"{'ground temperature':>22}: {env.T_ground.min():.1f} .. {env.T_ground.max():.1f} K")
        print(f"{'Sun visible':>22}: {100 * np.mean(env.sun_visible > 0):.0f} % of records (any part of the disk)")
        print(f"{'direct normal':>22}: mean {env.dni.mean():.1f}, max {env.dni.max():.1f} W/m2")
        print(f"{'global horizontal':>22}: mean {env.ghi.mean():.1f}, max {env.ghi.max():.1f} W/m2"
              + ("  (Sun below the astronomical horizon: flat ground is unlit)" if env.ghi.max() == 0 and env.dni.max() > 0 else ""))
        if env.gas is not None:
            print(f"{'ambient pressure':>22}: {env.pressure.min():.0f} .. {env.pressure.max():.0f} Pa")


if __name__ == "__main__":
    main()
