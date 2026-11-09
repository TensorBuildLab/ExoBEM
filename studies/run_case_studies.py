"""Case studies for the ExoBEM paper.  Writes studies/results/*.json and *.npz.

    python studies/run_case_studies.py
"""
from __future__ import annotations

import copy
import datetime as dt
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from exobem import simulate  # noqa: E402
from exobem.cases import lunar_habitat, mars_habitat  # noqa: E402
from exobem.environment.sites import moon_site, mars_site  # noqa: E402
from exobem.ephemeris import jd_from_datetime, mars as mars_eph  # noqa: E402
from exobem.model import ThermalControlSystem, evaluate_schedule  # noqa: E402
from exobem.thermal_control import evaluate_thermal_control  # noqa: E402
from exobem.power import size_pv_for_balance  # noqa: E402
from exobem.convection import natural_physical, forced_physical, mixed_physical  # noqa: E402
from exobem import gas as G  # noqa: E402

OUT = ROOT / "studies" / "results"
OUT.mkdir(parents=True, exist_ok=True)
SOL = mars_eph.MARS_SOL_SECONDS

MOON_EQ = dict(name="Moon - Mare Tranquillitatis (0.67N, 23.47E)", lat=0.674, lon=23.473)
MOON_SP = dict(name="Moon - south-polar ridge (89.5S)", lat=-89.5, lon=0.0, horizon=([0, 360], [-1.65, -1.65]))
MARS_JZ = dict(name="Mars - Jezero crater (18.44N, 77.45E)", lat=18.44, lon=77.45)


def mars_year_start(year_guess=2028):
    """UTC datetime when Ls crosses 0 near the given year."""
    t0 = jd_from_datetime(dt.datetime(year_guess, 1, 1))
    jd = t0 + np.arange(0, 800, 0.05)
    Ls = mars_eph.areocentric(jd)["Ls"]
    i = np.where(np.diff(Ls) < -300)[0][0] + 1
    return dt.datetime(2000, 1, 1, 12) + dt.timedelta(days=float(jd[i] - 2451545.0))


def electric_internal(model, env):
    p = np.zeros(env.n)
    for g in model.zone.gains:
        if g.name in ("equipment", "lighting"):
            p += g.power_W * evaluate_schedule(g.schedule, env.local_time_h, env.day_index)
    return p


def metrics(res, env, model):
    days = env.n * env.dt / 86400.0
    s = res.summary()
    A = np.array([x.area for x in model.zone.geometry.surfaces])
    q_env = (res.q_cond_inside_W_m2 * A[None, :]).sum(axis=1)
    s.update(duration_earth_days=days,
             heating_kWh_per_day=s["heating_kWh"] / days, cooling_kWh_per_day=s["cooling_kWh"] / days,
             thermal_control_kWh_per_day=s.get("thermal_control_electric_kWh", np.nan) / days,
             envelope_gain_mean_W=float(q_env.mean()), envelope_gain_min_W=float(q_env.min()),
             envelope_gain_max_W=float(q_env.max()),
             T_out_min_K=float(res.T_outside_C.min() + 273.15), T_out_max_K=float(res.T_outside_C.max() + 273.15),
             T_in_surface_min_C=float(res.T_inside_C.min()), T_in_surface_max_C=float(res.T_inside_C.max()),
             mean_iterations=float(res.iterations.mean()))
    if res.cop_cooling is not None:
        c = res.cop_cooling[np.isfinite(res.cop_cooling)]
        s["heat_pump_hours_frac"] = float(np.isfinite(res.cop_cooling).mean())
        s["cop_min"] = float(c.min()) if len(c) else None
        s["radiator_sink_min_K"] = float(res.radiator_sink_K.min())
        s["radiator_sink_max_K"] = float(res.radiator_sink_K.max())
    return s


def save_series(name, res, env, extra=None):
    d = dict(t_days=env.time_s / 86400.0, T_zone=res.T_zone_C, Qh=res.Q_heating_W, Qc=res.Q_cooling_W,
             Qlat=res.Q_latent_W, Tin=res.T_inside_C, Tout=res.T_outside_C, ghi=env.ghi, dni=env.dni,
             dhi=env.dhi, T_ground=env.T_ground, T_sky=env.T_sky, T_air=env.T_air, zenith=env.zenith,
             pressure=env.pressure, hco=res.h_conv_out, hci=res.h_conv_in, sun_visible=env.sun_visible,
             names=np.array(res.surface_names))
    if res.electric_W is not None:
        d.update(elec=res.electric_W, T_rad=res.radiator_T_K, T_sink=res.radiator_sink_K, cop=res.cop_cooling)
    for k in ("Ls", "tau", "L_down", "ltst_h", "lunar_local_time_h"):
        if k in env.extra:
            d[k] = env.extra[k]
    if extra:
        d.update(extra)
    np.savez_compressed(OUT / f"{name}.npz", **d)


def run(label, model, env, store=True):
    t = time.time()
    res = simulate(model, env)
    m = metrics(res, env, model)
    print(f"[{time.time() - t:6.1f}s] {label}: heat {m['heating_kWh_per_day']:.2f} kWh/d, "
          f"cool {m['cooling_kWh_per_day']:.2f} kWh/d, TCS {m['thermal_control_kWh_per_day']:.2f} kWh/d")
    if store:
        save_series(label, res, env)
    return res, m


def main():
    report = {}
    # ------------------------------------------------------------------ baseline sites
    start_moon = dt.datetime(2030, 1, 1)
    env_meq = moon_site(MOON_EQ["lat"], MOON_EQ["lon"], start_moon, 2 * 29.530589, dt=1800.0)
    env_msp = moon_site(MOON_SP["lat"], MOON_SP["lon"], start_moon, 12 * 29.530589, dt=3600.0,
                        horizon=MOON_SP["horizon"])
    my_start = mars_year_start(2028)
    dt_mars = SOL / 24.0
    env_mjz = mars_site(MARS_JZ["lat"], MARS_JZ["lon"], my_start, 668.6, dt=dt_mars)
    env_mjz_storm = mars_site(MARS_JZ["lat"], MARS_JZ["lon"], my_start, 668.6, dt=dt_mars,
                              tau_kwargs=dict(storm=(190.0, 270.0, 6.0)))
    report["sites"] = dict(moon_equator=MOON_EQ | dict(start=str(start_moon), days=2 * 29.53, dt=1800),
                           moon_pole=dict(name=MOON_SP["name"], lat=MOON_SP["lat"], horizon_deg=-1.65,
                                          start=str(start_moon), days=12 * 29.53, dt=3600,
                                          illuminated_fraction=float((env_msp.sun_visible > 0.5).mean())),
                           mars_jezero=MARS_JZ | dict(start=str(my_start), sols=668.6, dt=dt_mars))
    for key, e in (("moon_equator", env_meq), ("moon_pole", env_msp), ("mars_jezero", env_mjz),
                   ("mars_jezero_storm", env_mjz_storm)):
        report.setdefault("environment", {})[key] = dict(
            T_ground_min_K=float(e.T_ground.min()), T_ground_max_K=float(e.T_ground.max()),
            T_ground_mean_K=float(e.T_ground.mean()), T_deep_K=float(e.T_deep[0]),
            ghi_max=float(e.ghi.max()), ghi_mean=float(e.ghi.mean()),
            T_air_min_K=float(np.nanmin(e.T_air)) if not np.all(np.isnan(e.T_air)) else None,
            T_air_max_K=float(np.nanmax(e.T_air)) if not np.all(np.isnan(e.T_air)) else None,
            P_min=float(e.pressure.min()), P_max=float(e.pressure.max()),
            T_sky_min_K=float(e.T_sky.min()), T_sky_max_K=float(e.T_sky.max()),
            sunlit_fraction=float((e.sun_visible > 0.5).mean()),
            L_down_mean=float(np.mean(e.extra["L_down"])) if "L_down" in e.extra else None,
            L_down_min=float(np.min(e.extra["L_down"])) if "L_down" in e.extra else None,
            L_down_max=float(np.max(e.extra["L_down"])) if "L_down" in e.extra else None,
            tau_max=float(np.max(e.extra["tau"])) if "tau" in e.extra else None,
            longest_dark_days=_longest_dark(e))

    base = {}
    for key, mdl, env in (("moon_equator", lunar_habitat(dt=1800.0), env_meq),
                          ("moon_pole", lunar_habitat(dt=3600.0), env_msp),
                          ("mars_jezero", mars_habitat(dt=dt_mars), env_mjz),
                          ("mars_jezero_storm", mars_habitat(dt=dt_mars), env_mjz_storm)):
        res, m = run(key, mdl, env)
        base[key] = (res, env, mdl)
        report.setdefault("baseline", {})[key] = m

    # ------------------------------------------------------------------ envelope parametrics
    moon_env = {
        "MLI only": dict(shield=None),
        "MLI + 0.5 m regolith": dict(shield="lunar_regolith_cover_0.5m"),
        "MLI + 1 m regolith": dict(shield="lunar_regolith_cover_1m"),
        "MLI + 2 m regolith": dict(shield="lunar_regolith_cover_2m"),
        "1 m regolith, no MLI": dict(shield="lunar_regolith_cover_1m", insulation=None),
        "2 m regolith, no MLI": dict(shield="lunar_regolith_cover_2m", insulation=None),
    }
    for site, env, dtt in (("moon_equator", env_meq, 1800.0), ("moon_pole", env_msp, 3600.0)):
        for lab, kw in moon_env.items():
            mdl = _lunar_variant(dtt, **kw)
            _, m = run(f"{site}|{lab}", mdl, env, store=False)
            report.setdefault("envelope_" + site, {})[lab] = m
    mars_env = {
        "Aerogel 20 mm": dict(shield=None),
        "Aerogel + 1 m regolith": dict(shield="mars_regolith_cover_1m"),
        "MLI (in CO2) + 1 m regolith": dict(shield="mars_regolith_cover_1m", insulation="mli_20layer_mars"),
        "1 m regolith, no insulation": dict(shield="mars_regolith_cover_1m", insulation=None),
        "Polyimide foam 50 mm": dict(shield=None, insulation="polyimide_foam_50mm"),
    }
    for lab, kw in mars_env.items():
        mdl = _mars_variant(dt_mars, **kw)
        _, m = run(f"mars|{lab}", mdl, env_mjz, store=False)
        report.setdefault("envelope_mars_jezero", {})[lab] = m

    # ------------------------------------------------------------------ radiator orientation
    res, env, mdl = base["moon_equator"]
    for lab, tcs in (("Vertical, faces N/S (pole-facing)", ThermalControlSystem(radiator_azimuth=0.0)),
                     ("Vertical, faces E/W", ThermalControlSystem(radiator_azimuth=90.0)),
                     ("Horizontal, faces up", ThermalControlSystem(radiator_tilt=0.0, radiator_two_sided=False)),
                     ("Horizontal, dust-degraded (alpha = 0.35)",
                      ThermalControlSystem(radiator_tilt=0.0, radiator_two_sided=False, radiator_absorptance=0.35)),
                     ("Vertical N/S, 2x area", ThermalControlSystem(radiator_azimuth=0.0, radiator_area_m2=80.0))):
        r2 = copy.copy(res)
        evaluate_thermal_control(r2, tcs)
        days = env.n * env.dt / 86400
        report.setdefault("radiator_moon_equator", {})[lab] = dict(
            tcs_kWh_per_day=float(r2.electric_W.sum() * env.dt / 3.6e6 / days),
            peak_W=float(r2.electric_W.max()), sink_max_K=float(r2.radiator_sink_K.max()),
            sink_min_K=float(r2.radiator_sink_K.min()),
            heat_pump_frac=float(np.isfinite(r2.cop_cooling).mean()),
            longest_dark_days=None)
        if lab.startswith("Vertical, faces E/W") or lab.startswith("Horizontal"):
            np.savez_compressed(OUT / f"radiator_{'EW' if 'E/W' in lab else 'H'}.npz", T_sink=r2.radiator_sink_K,
                                elec=r2.electric_W, t_days=env.time_s / 86400)

    # ------------------------------------------------------------------ power system sizing
    for key, track, dust in (("moon_equator", "two_axis", 1.0), ("moon_pole", "vertical_single_axis", 1.0),
                             ("mars_jezero", "two_axis", 0.85), ("mars_jezero_storm", "two_axis", 0.85)):
        res, env, mdl = base[key]
        load = electric_internal(mdl, env) + res.electric_W
        r = size_pv_for_balance(env, load, efficiency=0.30, tracking=track, dust_factor=dust)
        r.update(mean_load_W=float(load.mean()), peak_load_W=float(load.max()),
                 thermal_control_share=float(res.electric_W.mean() / load.mean()), tracking=track)
        report.setdefault("power", {})[key] = r
        print("power", key, {k: (round(v, 1) if isinstance(v, float) else v) for k, v in r.items()})

    # ------------------------------------------------------------------ convection vs gravity/pressure
    gs = np.linspace(0.5, 10.0, 60)
    conv = {}
    for P_kPa, o2 in ((101.3, 0.21), (70.3, 0.265), (56.5, 0.34)):
        gas = G.cabin_gas(o2)
        conv[f"{P_kPa}"] = [float(natural_physical(gas, 297.15, 294.15, P_kPa * 1e3, g, 0.0, 2.5, 1.0)) for g in gs]
    conv["forced_0.15"] = float(forced_physical(G.cabin_gas(0.265), 297.15, 294.15, 70.3e3, 0.15, 2.5))
    # Mars exterior: natural + forced in 700 Pa CO2 at 3.71 m/s2 vs Earth air
    winds = np.linspace(0.5, 20, 40)
    conv["mars_ext_mixed"] = [float(mixed_physical(G.MARS_CO2, 240.0, 210.0, 700.0, 3.721, 0.0, v, 3.0, 1.5, 3.0))
                              for v in winds]
    conv["earth_ext_mixed"] = [float(mixed_physical(G.DRY_AIR, 300.0, 290.0, 101325.0, 9.81, 0.0, v, 3.0, 1.5, 3.0))
                               for v in winds]
    conv["g"] = gs.tolist()
    conv["wind"] = winds.tolist()
    report["convection"] = conv

    (OUT / "case_studies.json").write_text(json.dumps(report, indent=2, default=float))
    print("done")


def _longest_dark(e):
    dark = (e.sun_visible <= 0.5).astype(int)
    d = np.diff(np.concatenate([[0], dark, [0]]))
    st, en = np.where(d == 1)[0], np.where(d == -1)[0]
    return float((en - st).max() * e.dt / 86400.0) if len(st) else 0.0


def _lunar_variant(dtt, shield="lunar_regolith_cover_1m", insulation="mli_20layer_vacuum"):
    from exobem.materials import Construction, library
    m = lunar_habitat(dt=dtt)
    lib = library()
    layers = ([lib[shield]] if shield else []) + [lib["beta_cloth_outer_1mm"]] + \
             ([lib[insulation]] if insulation else []) + [lib["aluminum_2219_4mm"], lib["interior_panel_10mm"]]
    m.constructions["shell"] = Construction("shell", layers)
    m.constructions["end"] = Construction("end", layers)
    return m


def _mars_variant(dtt, shield="mars_regolith_cover_1m", insulation="aerogel_blanket_20mm"):
    from exobem.materials import Construction, library
    m = mars_habitat(dt=dtt)
    lib = library()
    layers = ([lib[shield]] if shield else []) + [lib["beta_cloth_outer_1mm"]] + \
             ([lib[insulation]] if insulation else []) + [lib["aluminum_2219_4mm"], lib["interior_panel_10mm"]]
    m.constructions["shell"] = Construction("shell", layers)
    m.constructions["end"] = Construction("end", layers)
    return m


if __name__ == "__main__":
    main()
