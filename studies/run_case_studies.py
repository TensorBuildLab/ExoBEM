"""Case studies for the ExoBEM paper.  Writes studies/results/*.json, *.npz and examples/weather/*.pwf.

    python studies/run_case_studies.py

Habitats: the four-crew Artemis-class lunar Surface Habitat and the six-crew DRA 5.0-class Mars habitat
(exobem.cases.artemis_surface_habitat / mars_surface_habitat; sources in docs/research/).
Sites: lunar south pole (main NASA site), lunar equator (contrast), Jezero crater with and without a global
dust storm.  Power options per site: PV + Li-ion, PV + regenerative fuel cell, 40 kWe fission.
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
from exobem import gas as G  # noqa: E402
from exobem.cases import artemis_surface_habitat, mars_surface_habitat  # noqa: E402
from exobem.convection import forced_physical, mixed_physical, natural_physical  # noqa: E402
from exobem.model import Thermostat  # noqa: E402
from exobem.environment.sites import mars_site, moon_site  # noqa: E402
from exobem.ephemeris import jd_from_datetime, mars as mars_eph  # noqa: E402
from exobem.materials import Construction  # noqa: E402
from exobem.model import ThermalControlSystem  # noqa: E402
from exobem.power import (Battery, FissionPower, PowerSystem, PVArray, RegenerativeFuelCell,  # noqa: E402
                          simulate_power, size_pv_for_balance, storage_requirement)
from exobem.thermal_control import evaluate_thermal_control  # noqa: E402
from exobem.weather import write_pwf  # noqa: E402

OUT = ROOT / "studies" / "results"
WX = ROOT / "examples" / "weather"
OUT.mkdir(parents=True, exist_ok=True)
WX.mkdir(parents=True, exist_ok=True)
SOL = mars_eph.MARS_SOL_SECONDS

MOON_EQ = dict(name="Moon - Mare Tranquillitatis (0.67N, 23.47E)", lat=0.674, lon=23.473, horizon=None)
MOON_SP = dict(name="Moon - south-polar ridge (89.5S)", lat=-89.5, lon=0.0, horizon=([0, 360], [-1.65, -1.65]))
MARS_JZ = dict(name="Mars - Jezero crater (18.44N, 77.45E)", lat=18.44, lon=77.45)

# power-system parameters (docs/research/habitat_eclss_power_dossier.md, section C)
PV_KW = dict(cell_efficiency=0.295, temp_coeff_per_K=-0.0023, alpha_front=0.91, array_factor=0.85)
LIION = dict(eta=0.97, soc_min=0.20, Wh_per_kg=160.0)        # packaged; round trip 0.94 (assumption)
RFC = dict(eta_el=0.85, eta_fc=0.60)                          # round trip 0.51 (50-55 % demonstrated)
FISSION_KWE, FISSION_EFF = 40.0, 0.181                        # NASA FSP (Kaldon et al. 2024; Oleson et al. 2022)
MARS_DUST = dict(dust_loss_per_day=0.0025 * 86400.0 / SOL, cleaning_interval_days=45.0 * SOL / 86400.0)


def mars_year_start(year_guess=2028):
    """UTC datetime when Ls crosses 0 near the given year."""
    t0 = jd_from_datetime(dt.datetime(year_guess, 1, 1))
    jd = t0 + np.arange(0, 800, 0.05)
    Ls = mars_eph.areocentric(jd)["Ls"]
    i = np.where(np.diff(Ls) < -300)[0][0] + 1
    return dt.datetime(2000, 1, 1, 12) + dt.timedelta(days=float(jd[i] - 2451545.0))


def metrics(res, env, model):
    days = env.n * env.dt / 86400.0
    s = res.summary()
    ne = res.n_envelope
    A = np.array([x.area for x in model.zone.geometry.surfaces])
    q_env = (res.q_cond_inside_W_m2[:, :ne] * A[None, :ne]).sum(axis=1)
    load = res.electric_internal_W + (res.electric_W if res.electric_W is not None else 0.0)
    Qtcs = res.Q_cooling_W + np.maximum(res.Q_latent_W, 0) + res.Q_coldplate_W
    s.update(duration_earth_days=days,
             heating_kWh_per_day=s["heating_kWh"] / days, cooling_kWh_per_day=s["cooling_kWh"] / days,
             latent_kWh_per_day=float(np.maximum(res.Q_latent_W, 0).sum() * env.dt / 3.6e6 / days),
             coldplate_kWh_per_day=float(res.Q_coldplate_W.sum() * env.dt / 3.6e6 / days),
             tcs_heat_kWh_per_day=float(Qtcs.sum() * env.dt / 3.6e6 / days), tcs_heat_peak_W=float(Qtcs.max()),
             thermal_control_kWh_per_day=s.get("thermal_control_electric_kWh", np.nan) / days,
             internal_electric_kWh_per_day=s["internal_electric_kWh"] / days,
             electric_mean_W=float(load.mean()), electric_peak_W=float(load.max()),
             envelope_gain_mean_W=float(q_env.mean()), envelope_gain_min_W=float(q_env.min()),
             envelope_gain_max_W=float(q_env.max()),
             T_out_min_K=float(res.T_outside_C[:, :ne].min() + 273.15), T_out_max_K=float(res.T_outside_C[:, :ne].max() + 273.15),
             T_in_surface_min_C=float(res.T_inside_C[:, :ne].min()), T_in_surface_max_C=float(res.T_inside_C[:, :ne].max()),
             gas_makeup_kg_per_day=model.zone.gas_loss_kg_per_day,
             condensate_kg_per_day=s.get("condensate_kg", 0.0) / days,
             mean_iterations=float(res.iterations.mean()))
    if res.cop_cooling is not None:
        c = res.cop_cooling[np.isfinite(res.cop_cooling)]
        s["heat_pump_hours_frac"] = float(np.isfinite(res.cop_cooling).mean())
        s["cop_min"] = float(c.min()) if len(c) else None
        s["radiator_sink_min_K"] = float(res.radiator_sink_K.min())
        s["radiator_sink_max_K"] = float(res.radiator_sink_K.max())
    return s


def save_series(name, res, env, extra=None):
    ne = res.n_envelope
    d = dict(t_days=env.time_s / 86400.0, T_zone=res.T_zone_C, Qh=res.Q_heating_W, Qc=res.Q_cooling_W,
             Qlat=res.Q_latent_W, Qcold=res.Q_coldplate_W, Tin=res.T_inside_C[:, :ne], Tout=res.T_outside_C[:, :ne],
             ghi=env.ghi, dni=env.dni, dhi=env.dhi, T_ground=env.T_ground, T_sky=env.T_sky, T_air=env.T_air,
             zenith=env.zenith, pressure=env.pressure, hco=res.h_conv_out[:, :ne], hci=res.h_conv_in[:, :ne],
             sun_visible=env.sun_visible, names=np.array(res.surface_names[:ne]), rh=res.rh_zone, dewpoint=res.dewpoint_C,
             P_int=res.electric_internal_W)
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
    print(f"[{time.time() - t:6.1f}s] {label}: heat {m['heating_kWh_per_day']:.2f}, cool {m['cooling_kWh_per_day']:.2f}, "
          f"TCS heat {m['tcs_heat_kWh_per_day']:.1f} kWh/d, TCS el. {m['thermal_control_kWh_per_day']:.2f} kWh/d, "
          f"RH {m.get('rh_min', 0):.2f}-{m.get('rh_max', 0):.2f}", flush=True)
    if store:
        save_series(label, res, env)
    return res, m


def variant(model, shell_layers, floor_layers=None):
    m = copy.deepcopy(model)
    m.constructions["shell"] = Construction("shell", shell_layers)
    m.constructions["roof"] = Construction("roof", shell_layers)
    if floor_layers is not None:
        m.constructions["floor"] = Construction("floor", floor_layers)
    return m


def power_options(key, env, load, tracking, mars):
    """Size and simulate three power systems that meet the habitat's electric load without shortfall."""
    out, series = {}, {}
    arr = PVArray(1.0, tracking=tracking, **PV_KW, **(MARS_DUST if mars else {}))
    peak = float(load.max())
    # A: PV + Li-ion
    rt = LIION["eta"] ** 2
    r = size_pv_for_balance(env, load, round_trip=rt, array=arr)
    if np.isfinite(r["pv_area_m2"]):
        cap = 1.03 * r["storage_kWh"] / (1.0 - LIION["soc_min"])
        area = 1.01 * r["pv_area_m2"]
        sysA = PowerSystem(pv=[PVArray(area, tracking=tracking, **PV_KW, **(MARS_DUST if mars else {}))],
                           battery=Battery(cap, LIION["eta"], LIION["eta"], LIION["soc_min"]))
        sA = simulate_power(sysA, env, load, repeat_cycles=2)
        out["PV + Li-ion"] = dict(pv_area_m2=area, pv_peak_kW=area * 1361.0 / 1e3 * PV_KW["cell_efficiency"] * PV_KW["array_factor"],
                                  storage_kWh=cap, storage_mass_t=cap / LIION["Wh_per_kg"], **sA["summary"])
        series["A_soc"] = sA["soc_battery_kWh"] / cap
        series["A_pv"] = sA["generation_pv_W"]
        series["T_cell"] = sA["pv_details"][0]["T_cell_K"]
        series["eff_cell"] = sA["pv_details"][0]["efficiency"]
    # B: PV + RFC
    rt = RFC["eta_el"] * RFC["eta_fc"]
    r = size_pv_for_balance(env, load, round_trip=rt, array=arr)
    if np.isfinite(r["pv_area_m2"]):
        cap = 1.03 * r["storage_kWh"] / 0.95
        area = 1.01 * r["pv_area_m2"]
        sysB = PowerSystem(pv=[PVArray(area, tracking=tracking, **PV_KW, **(MARS_DUST if mars else {}))],
                           rfc=RegenerativeFuelCell(cap, RFC["eta_el"], RFC["eta_fc"]))
        sB = simulate_power(sysB, env, load, repeat_cycles=2)
        out["PV + RFC"] = dict(pv_area_m2=area, storage_kWh=cap, **sB["summary"])
        series["B_soc"] = sB["soc_rfc_kWh"] / cap
    # Trade-off: storage needed versus PV area (multiples of the energy-balance area).  Sizing PV only for the
    # yearly energy balance shifts summer surplus into winter and demands seasonal storage; a larger array
    # leaves only the night / eclipse deficit to storage.
    g1 = arr.power(env)
    mult = [1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0]
    trade = {}
    for lab, rt, key_ in (("Li-ion", LIION["eta"] ** 2, "PV + Li-ion"), ("RFC", RFC["eta_el"] * RFC["eta_fc"], "PV + RFC")):
        if key_ not in out:
            continue
        A0 = out[key_]["pv_area_m2"] / 1.01
        trade[lab] = dict(pv_area_m2=[A0 * m for m in mult],
                          storage_kWh=[storage_requirement(g1 * A0 * m, load, env.dt, rt)["storage_kWh"] for m in mult])
    out["tradeoff"] = dict(multiplier=mult, **trade)
    if "PV + Li-ion" in out:      # design point: twice the energy-balance array
        A2 = 2.0 * out["PV + Li-ion"]["pv_area_m2"] / 1.01
        S2 = storage_requirement(g1 * A2, load, env.dt, LIION["eta"] ** 2)["storage_kWh"]
        cap2 = 1.03 * S2 / (1.0 - LIION["soc_min"])
        s2 = simulate_power(PowerSystem(pv=[PVArray(A2, tracking=tracking, **PV_KW, **(MARS_DUST if mars else {}))],
                                        battery=Battery(cap2, LIION["eta"], LIION["eta"], LIION["soc_min"])), env, load,
                            repeat_cycles=2)
        out["PV x2 + Li-ion"] = dict(pv_area_m2=A2, storage_kWh=cap2, storage_mass_t=cap2 / LIION["Wh_per_kg"], **s2["summary"])
        series["A2_soc"] = s2["soc_battery_kWh"] / cap2
    # nameplate, as in Table 11: usable energy / discharge efficiency / usable depth (1 - minimum state of charge)
    out["eclipse_100h_storage_kWh"] = float(load.mean() * 100.0 / 1e3 / LIION["eta"] / (1.0 - LIION["soc_min"]))
    # C: fission
    n_units = int(np.ceil(peak / (FISSION_KWE * 1e3)))
    sC = simulate_power(PowerSystem(fission=FissionPower(FISSION_KWE, FISSION_EFF, 1.0, n_units)), env, load)
    out["Fission 40 kWe"] = dict(units=n_units, waste_heat_kW=n_units * FISSION_KWE * (1 / FISSION_EFF - 1), **sC["summary"])
    for k, v in out.items():
        if not isinstance(v, dict) or k == "tradeoff":
            continue
        v.update(mean_load_kW=float(load.mean() / 1e3), peak_load_kW=peak / 1e3)
        print(f"   power {key} | {k}: " + ", ".join(f"{a}={b:.3g}" for a, b in v.items() if isinstance(b, float)), flush=True)
    np.savez_compressed(OUT / f"power_{key}.npz", t_days=env.time_s / 86400.0, load=load, **series)
    return out


def main():
    only_power = "--only-power" in sys.argv
    report = json.loads((OUT / "case_studies.json").read_text()) if only_power else {}
    t0 = time.time()
    # ------------------------------------------------------------------ sites (and PWF weather files)
    start_moon = dt.datetime(2030, 1, 1)
    env_meq = moon_site(MOON_EQ["lat"], MOON_EQ["lon"], start_moon, 2 * 29.530589, dt=1800.0)
    env_msp = moon_site(MOON_SP["lat"], MOON_SP["lon"], start_moon, 365.0, dt=3600.0, horizon=MOON_SP["horizon"])
    my_start = mars_year_start(2028)
    dt_mars = SOL / 24.0
    env_mjz = mars_site(MARS_JZ["lat"], MARS_JZ["lon"], my_start, 668.6, dt=dt_mars)
    env_mjz_storm = mars_site(MARS_JZ["lat"], MARS_JZ["lon"], my_start, 668.6, dt=dt_mars,
                              tau_kwargs=dict(storm=(190.0, 270.0, 6.0)))
    for e, st in ((env_meq, start_moon), (env_msp, start_moon), (env_mjz, my_start), (env_mjz_storm, my_start)):
        e.extra["start_utc"] = st
    write_pwf(env_meq, WX / "moon_equator_2lunations.pwf", site_name=MOON_EQ["name"])
    write_pwf(env_msp, WX / "moon_south_pole_1year.pwf", site_name=MOON_SP["name"], horizon=MOON_SP["horizon"])
    write_pwf(env_mjz, WX / "mars_jezero_1marsyear.pwf", site_name=MARS_JZ["name"])
    print(f"[{time.time() - t0:6.1f}s] environments and PWF files", flush=True)
    report["sites"] = dict(moon_equator=dict(name=MOON_EQ["name"], start=str(start_moon), days=2 * 29.53, dt=1800),
                           moon_pole=dict(name=MOON_SP["name"], lat=MOON_SP["lat"], horizon_deg=-1.65,
                                          start=str(start_moon), days=365, dt=3600),
                           mars_jezero=dict(name=MARS_JZ["name"], start=str(my_start), sols=668.6, dt=dt_mars))
    envs = {"moon_equator": env_meq, "moon_pole": env_msp, "mars_jezero": env_mjz, "mars_jezero_storm": env_mjz_storm}
    for key, e in envs.items():
        report.setdefault("environment", {})[key] = dict(
            T_ground_min_K=float(e.T_ground.min()), T_ground_max_K=float(e.T_ground.max()),
            T_ground_mean_K=float(e.T_ground.mean()), T_deep_K=float(e.T_deep[0]),
            ghi_max=float(e.ghi.max()), ghi_mean=float(e.ghi.mean()), dni_max=float(e.dni.max()),
            T_air_min_K=float(np.nanmin(e.T_air)) if not np.all(np.isnan(e.T_air)) else None,
            T_air_max_K=float(np.nanmax(e.T_air)) if not np.all(np.isnan(e.T_air)) else None,
            P_min=float(e.pressure.min()), P_max=float(e.pressure.max()),
            T_sky_min_K=float(e.T_sky.min()), T_sky_max_K=float(e.T_sky.max()),
            sunlit_fraction=float((e.sun_visible > 0.5).mean()),
            L_down_mean=float(np.mean(e.extra["L_down"])) if "L_down" in e.extra else None,
            L_down_min=float(np.min(e.extra["L_down"])) if "L_down" in e.extra else None,
            L_down_max=float(np.max(e.extra["L_down"])) if "L_down" in e.extra else None,
            L_down_clear_mean=(float(np.mean(e.extra["L_down"][(e.extra["Ls"] > 30) & (e.extra["Ls"] < 150)]))
                               if "L_down" in e.extra else None),
            tau_max=float(np.max(e.extra["tau"])) if "tau" in e.extra else None,
            longest_dark_days=_longest_dark(e))

    # ------------------------------------------------------------------ baseline habitats
    base = {}
    cases = (("moon_pole", artemis_surface_habitat(dt=3600.0), env_msp),
             ("moon_equator", artemis_surface_habitat(dt=1800.0), env_meq),
             ("mars_jezero", mars_surface_habitat(dt=dt_mars), env_mjz),
             ("mars_jezero_storm", mars_surface_habitat(dt=dt_mars), env_mjz_storm))
    for key, mdl, env in cases:
        res, m = run(key, mdl, env)
        base[key] = (res, env, mdl)
        report.setdefault("baseline", {})[key] = m
    h = artemis_surface_habitat()
    hm = mars_surface_habitat()
    report["habitats"] = {
        "moon": dict(volume_m3=h.zone.geometry.volume, crew=4, gains={g.name: g.power_W for g in h.zone.gains},
                     latent_W=sum(g.latent_W for g in h.zone.gains), leak_kg_d=h.zone.leakage_kg_per_day,
                     airlock_kg_cycle=h.zone.airlock_loss_kg_per_cycle, airlock_cycles_d=h.zone.airlock_cycles_per_day,
                     area_exposed_m2=sum(s.area for s in h.zone.geometry.surfaces)),
        "mars": dict(volume_m3=hm.zone.geometry.volume, crew=6, gains={g.name: g.power_W for g in hm.zone.gains},
                     latent_W=sum(g.latent_W for g in hm.zone.gains), leak_kg_d=hm.zone.leakage_kg_per_day,
                     airlock_kg_cycle=hm.zone.airlock_loss_kg_per_cycle, airlock_cycles_d=hm.zone.airlock_cycles_per_day,
                     area_exposed_m2=sum(s.area for s in hm.zone.geometry.surfaces))}

    if only_power:
        return power_section(report, base)

    # ------------------------------------------------------------------ envelope variants
    def lunar_variants(dtt):
        mb = artemis_surface_habitat(dt=dtt)
        L = {k: c for k, c in ((l.name, l) for c in mb.constructions.values() for l in c.layers)}
        from exobem.cases import _habitat_materials, LUNAR_MLI_R
        M = _habitat_materials(LUNAR_MLI_R)
        sh = lambda t: artemis_surface_habitat(dt=dtt, shield=f"lunar_regolith_cover_{t}m")  # noqa: E731
        no_mli = artemis_surface_habitat(dt=dtt, shield="lunar_regolith_cover_1m")
        no_mli = variant(no_mli, [M["lunar_regolith_cover_1m"], M["beta_cloth_sh"], M["aluminum_2219_4mm"], M["interior_panel_10mm"]])
        return {"MLI on legs (baseline)": mb, "MLI + 0.5 m regolith": sh("0.5"), "MLI + 1 m regolith": sh("1"),
                "MLI + 2 m regolith": sh("2"), "1 m regolith, no MLI": no_mli}
    for site, env, dtt in (("moon_pole", env_msp, 3600.0), ("moon_equator", env_meq, 1800.0)):
        for lab, mdl in lunar_variants(dtt).items():
            _, m = run(f"{site}|{lab}", mdl, env, store=False)
            report.setdefault("envelope_" + site, {})[lab] = m
    from exobem.cases import _habitat_materials
    M = _habitat_materials()
    mars_var = {
        "Aerogel 40 mm on legs (baseline)": mars_surface_habitat(dt=dt_mars),
        "Aerogel + 1 m regolith": mars_surface_habitat(dt=dt_mars, shield="mars_regolith_cover_1m"),
        "1 m regolith, no insulation": variant(mars_surface_habitat(dt=dt_mars, shield="mars_regolith_cover_1m"),
                                               [M["mars_regolith_cover_1m"], M["beta_cloth_sh"], M["aluminum_2219_4mm"],
                                                M["interior_panel_10mm"]]),
        "Polyimide foam 50 mm on legs": variant(mars_surface_habitat(dt=dt_mars),
                                                [M["beta_cloth_sh"], M["polyimide_foam_50mm"], M["aluminum_2219_4mm"],
                                                 M["interior_panel_10mm"]]),
        "MLI (in CO2) on legs": variant(mars_surface_habitat(dt=dt_mars),
                                        [M["beta_cloth_sh"], M["mli_20layer_mars"], M["aluminum_2219_4mm"],
                                         M["interior_panel_10mm"]]),
    }
    for lab, mdl in mars_var.items():
        _, m = run(f"mars|{lab}", mdl, env_mjz, store=False)
        report.setdefault("envelope_mars_jezero", {})[lab] = m

    # ------------------------------------------------------------------ condensation vs cabin set-points (Mars)
    # The baseline cabin sits at the top of its control band (25 C, 60 % RH) because the habitat always needs
    # cooling and the crew always adds water; lower humidity limits or a cooler cabin lower the dew point.
    for t_c, rh in ((25.0, 0.60), (25.0, 0.50), (25.0, 0.40), (22.0, 0.60), (22.0, 0.50)):
        mdl = mars_surface_habitat(dt=dt_mars)
        mdl.zone.thermostat = Thermostat(min(20.0, t_c - 2.0), t_c)
        mdl.zone.rh_max = rh
        _, m = run(f"mars|cabin {t_c:.0f} C, RH <= {rh:.0%}", mdl, env_mjz, store=False)
        report.setdefault("condensation_setpoints", {})[f"{t_c:.0f} C, {rh:.0%}"] = dict(
            cabin_C=t_c, rh_max=rh, condensation_risk_hours=m["condensation_risk_hours"],
            min_surface_minus_dewpoint_K=m["min_surface_minus_dewpoint_K"], latent_kWh_per_day=m["latent_kWh_per_day"],
            tcs_heat_kWh_per_day=m["tcs_heat_kWh_per_day"])

    # ------------------------------------------------------------------ radiator options (lunar equator)
    res, env, mdl = base["moon_equator"]
    for lab, tcs in (("Vertical, faces N/S (baseline, 96 m2)", ThermalControlSystem(radiator_area_m2=96.0, radiator_azimuth=0.0)),
                     ("Vertical, faces E/W", ThermalControlSystem(radiator_area_m2=96.0, radiator_azimuth=90.0)),
                     ("Horizontal, faces up (48 m2 one side)", ThermalControlSystem(radiator_area_m2=48.0, radiator_tilt=0.0,
                                                                                    radiator_two_sided=False)),
                     ("Horizontal, dust-degraded (alpha = 0.35)",
                      ThermalControlSystem(radiator_area_m2=48.0, radiator_tilt=0.0, radiator_two_sided=False,
                                           radiator_absorptance=0.35)),
                     ("Vertical N/S, 2x area", ThermalControlSystem(radiator_area_m2=192.0, radiator_azimuth=0.0))):
        r2 = copy.copy(res)
        evaluate_thermal_control(r2, tcs)
        days = env.n * env.dt / 86400
        report.setdefault("radiator_moon_equator", {})[lab] = dict(
            tcs_kWh_per_day=float(r2.electric_W.sum() * env.dt / 3.6e6 / days),
            peak_W=float(r2.electric_W.max()), sink_max_K=float(r2.radiator_sink_K.max()),
            sink_min_K=float(r2.radiator_sink_K.min()), heat_pump_frac=float(np.isfinite(r2.cop_cooling).mean()))
        if lab.startswith("Vertical, faces E/W") or lab.startswith("Horizontal, faces up"):
            np.savez_compressed(OUT / f"radiator_{'EW' if 'E/W' in lab else 'H'}.npz", T_sink=r2.radiator_sink_K,
                                elec=r2.electric_W, t_days=env.time_s / 86400)

    power_section(report, base, write=False)
    finish(report, t0)


def power_section(report, base, write=True):
    for key, track, mars in (("moon_pole", "vertical_single_axis", False), ("moon_equator", "two_axis", False),
                             ("mars_jezero", "two_axis", True), ("mars_jezero_storm", "two_axis", True)):
        res, env, mdl = base[key]
        load = res.electric_internal_W + res.electric_W
        report.setdefault("power", {})[key] = power_options(key, env, load, track, mars)
        report["power"][key]["tracking"] = track
        report["power"][key]["thermal_control_share"] = float(res.electric_W.mean() / load.mean())
    if write:
        (OUT / "case_studies.json").write_text(json.dumps(report, indent=2, default=float))
        print("power section updated")


def finish(report, t0):
    # ------------------------------------------------------------------ convection vs gravity/pressure
    gs = np.linspace(0.5, 10.0, 60)
    conv = {}
    for P_kPa, o2 in ((101.3, 0.21), (70.3, 0.265), (56.5, 0.34)):
        gas = G.cabin_gas(o2)
        conv[f"{P_kPa}"] = [float(natural_physical(gas, 297.15, 294.15, P_kPa * 1e3, g, 0.0, 2.5, 1.0)) for g in gs]
    conv["forced_0.15"] = float(forced_physical(G.cabin_gas(0.34), 297.15, 294.15, 56.5e3, 0.15, 2.5))
    winds = np.linspace(0.5, 20, 40)
    conv["mars_ext_mixed"] = [float(mixed_physical(G.MARS_CO2, 240.0, 210.0, 700.0, 3.721, 0.0, v, 3.0, 1.5, 3.0))
                              for v in winds]
    conv["earth_ext_mixed"] = [float(mixed_physical(G.DRY_AIR, 300.0, 290.0, 101325.0, 9.81, 0.0, v, 3.0, 1.5, 3.0))
                               for v in winds]
    conv["g"] = gs.tolist()
    conv["wind"] = winds.tolist()
    report["convection"] = conv
    report["calibration"] = json.loads((OUT / "lunar_mli_calibration.json").read_text())

    (OUT / "case_studies.json").write_text(json.dumps(report, indent=2, default=float))
    print(f"done in {time.time() - t0:.0f} s")


def _longest_dark(e):
    dark = (e.sun_visible <= 0.5).astype(int)
    d = np.diff(np.concatenate([[0], dark, [0]]))
    st, en = np.where(d == 1)[0], np.where(d == -1)[0]
    return float((en - st).max() * e.dt / 86400.0) if len(st) else 0.0


if __name__ == "__main__":
    main()
