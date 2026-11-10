"""Builders that turn a site description into an :class:`Environment` time series."""
from __future__ import annotations

import datetime as _dt

import numpy as np

from . import Environment
from .regolith import RegolithColumn
from .twostream import delta_eddington_surface
from .. import gas as _gas
from ..constants import SIGMA, TSI_1AU, KELVIN, G0, T_CMB
from ..ephemeris import jd_from_datetime, mars as mars_eph, moon as moon_eph
from ..solar import horizon_visible_fraction

MOON_GRAVITY = 1.625
MARS_GRAVITY = 3.721


# =================================================================================
# Earth (EPW weather files) - used for verification against EnergyPlus
# =================================================================================

def read_epw(path):
    with open(path, "r", encoding="latin-1") as f:
        lines = f.read().splitlines()
    loc = lines[0].split(",")
    meta = dict(city=loc[1], lat=float(loc[6]), lon=float(loc[7]), tz=float(loc[8]), elev=float(loc[9]))
    rows = [l.split(",") for l in lines[8:] if l.strip()]
    a = np.array([[float(x) if i != 5 else 0.0 for i, x in enumerate(r[:35])] for r in rows if len(r) >= 35])
    cols = dict(year=0, month=1, day=2, hour=3, T_db=6, T_dp=7, RH=8, P=9, IR_h=12, GHI=13, DNI=14, DHI=15,
                wind_dir=20, wind=21)
    data = {k: a[:, i] for k, i in cols.items()}
    return meta, data


def earth_from_epw(path, dt=600.0, ground_reflectance=0.2, n_days=365, start_day=1,
                   ground_temperature_C=10.0, year=2023):
    meta, d = read_epw(path)
    n_per_day = int(round(86400.0 / dt))
    n = n_days * n_per_day
    t_end = (np.arange(n) + 1) * dt + (start_day - 1) * 86400.0  # seconds since Jan 1 00:00 LST
    t_mid = t_end - 0.5 * dt
    h_end = t_end / 3600.0
    h_mid = t_mid / 3600.0
    N = len(d["T_db"])
    hours = np.arange(1, N + 1, dtype=float)                 # EPW hour-ending stamps

    def interp_state(x, hh):  # instantaneous values at hour ends, periodic
        return np.interp(hh, np.concatenate([[0.0], hours]), np.concatenate([[x[-1]], x]))

    def interp_solar(x, hh):  # hourly integrals, centred on the half hour
        centres = hours - 0.5
        return np.interp(hh, np.concatenate([[-0.5], centres, [N + 0.5]]),
                         np.concatenate([[x[-1]], x, [x[0]]]))

    T_air = interp_state(d["T_db"], h_end) + KELVIN
    T_dp = interp_state(d["T_dp"], h_end)
    P = interp_state(d["P"], h_end)
    IR = interp_state(d["IR_h"], h_end)
    wind = interp_state(d["wind"], h_end)
    wdir = interp_state(d["wind_dir"], h_end)
    dni = interp_solar(d["DNI"], h_mid)
    dhi = interp_solar(d["DHI"], h_mid)
    # sun position at step midpoint (local standard time -> UTC)
    t0 = _dt.datetime(year, 1, 1) - _dt.timedelta(hours=meta["tz"])
    jd0 = jd_from_datetime(t0)
    jd_mid = jd0 + t_mid / 86400.0
    from ..ephemeris import earth as earth_eph
    sp = earth_eph.sun_position(jd_mid, meta["lat"], meta["lon"])
    up = sp.zenith_deg < 90.0
    dni = np.where(up, dni, 0.0)
    dhi = np.where(up, dhi, 0.0)
    ghi = dni * np.maximum(np.cos(np.radians(sp.zenith_deg)), 0.0) + dhi
    T_sky = (np.maximum(IR, 1.0) / SIGMA) ** 0.25
    w = np.array([_gas.humidity_ratio_from_dewpoint(a, b) for a, b in zip(T_dp, P)])
    env = Environment(
        planet="earth", latitude=meta["lat"], longitude=meta["lon"], dt=dt, time_s=t_end,
        jd_utc=jd0 + t_end / 86400.0, zenith=sp.zenith_deg, sun_azimuth=sp.azimuth_deg, dni=dni, dhi=dhi,
        ghi=ghi, sun_visible=up.astype(float), T_air=T_air, T_sky=T_sky, T_ground=T_air.copy(),
        T_deep=np.full(n, ground_temperature_C + KELVIN), wind_speed=wind, wind_dir=wdir, pressure=P,
        ground_albedo=np.full(n, ground_reflectance), gravity=G0, gas=_gas.DRY_AIR, humidity_ratio=w,
        local_time_h=(h_end % 24.0), day_index=(np.floor((t_end - 1e-6) / 86400.0)).astype(int),
        sky_includes_air=True, extra=dict(meta=meta))
    return env


# =================================================================================
# Moon
# =================================================================================

def moon_site(latitude, longitude, start_utc, duration_days, dt=1800.0, horizon=None,
              regolith: RegolithColumn | None = None, spinup_lunations=6, deep_depth=3.0, equilibrate=True):
    """Lunar surface environment: vacuum, Sun as a finite disk, 3 K sky, regolith ground."""
    n = int(round(duration_days * 86400.0 / dt))
    t_end = (np.arange(n) + 1) * dt
    jd0 = jd_from_datetime(start_utc)
    jd_mid = jd0 + (t_end - 0.5 * dt) / 86400.0
    sp = moon_eph.sun_position(jd_mid, latitude, longitude)
    elev = 90.0 - sp.zenith_deg
    vis = horizon_visible_fraction(elev, sp.azimuth_deg, horizon, 0.2666 / np.mean(sp.distance_au))
    dni = TSI_1AU / sp.distance_au ** 2
    dni = dni * vis
    mu = np.maximum(np.cos(np.radians(sp.zenith_deg)), 0.0)
    ghi = dni * mu
    col = regolith or RegolithColumn()
    A = col.albedo(sp.zenith_deg)
    # 1) periodic equilibrium of the whole column for the year before the start (1 h steps): metre depths
    #    need decades to forget an initial guess, so they are set from the geothermal-flux profile below
    #    the reach of the lunar-day wave (RegolithColumn.equilibrate)
    T0 = None
    if equilibrate:
        dty = 3600.0
        ny = int(round(365.25 * 86400.0 / dty))
        jd_y = jd0 - 365.25 + (np.arange(ny) + 0.5) * dty / 86400.0
        spy = moon_eph.sun_position(jd_y, latitude, longitude)
        vis_y = horizon_visible_fraction(90 - spy.zenith_deg, spy.azimuth_deg, horizon)
        g_y = TSI_1AU / spy.distance_au ** 2 * vis_y * np.maximum(np.cos(np.radians(spy.zenith_deg)), 0)
        T0, _, _ = col.equilibrate(dty, (1 - col.albedo(spy.zenith_deg)) * g_y, np.zeros(ny), z_skin=0.15)
    # 2) spin up the near-surface layer on the synodic month preceding the start at the run's time step
    n_cyc = int(round(moon_eph.SYNODIC_MONTH_DAYS * 86400.0 / dt))
    jd_spin = jd0 - moon_eph.SYNODIC_MONTH_DAYS + (np.arange(n_cyc) + 0.5) * dt / 86400.0
    sps = moon_eph.sun_position(jd_spin, latitude, longitude)
    vis_s = horizon_visible_fraction(90 - sps.zenith_deg, sps.azimuth_deg, horizon)
    g_s = TSI_1AU / sps.distance_au ** 2 * vis_s * np.maximum(np.cos(np.radians(sps.zenith_deg)), 0)
    spin = col.run(dt, (1 - col.albedo(sps.zenith_deg)) * g_s, np.zeros(n_cyc), T_init=T0,
                   spinup_cycles=1 if equilibrate else spinup_lunations, cycle_steps=n_cyc)
    res = col.run(dt, (1 - A) * ghi, np.zeros(n), T_init=spin["T_final"], record_depths=(0.0, deep_depth))
    T_g = res["T_depths"][:, 0]
    T_deep = np.full(n, float(np.mean(res["T_depths"][:, 1])))
    lunar_time = sp.extra["lunar_time_h"] % 24.0
    # crew schedules on the Moon run on Earth (UTC) time
    utc_h = ((jd0 + t_end / 86400.0 + 0.5) % 1.0) * 24.0
    env = Environment(
        planet="moon", latitude=latitude, longitude=longitude, dt=dt, time_s=t_end, jd_utc=jd0 + t_end / 86400.0,
        zenith=sp.zenith_deg, sun_azimuth=sp.azimuth_deg, dni=dni, dhi=np.zeros(n), ghi=ghi, sun_visible=vis,
        T_air=np.full(n, np.nan), T_sky=np.full(n, T_CMB), T_ground=T_g, T_deep=T_deep,
        wind_speed=np.zeros(n), wind_dir=np.zeros(n), pressure=np.zeros(n),
        ground_albedo=A, gravity=MOON_GRAVITY, gas=None, local_time_h=utc_h,
        day_index=np.floor(t_end / 86400.0 - 1e-9).astype(int),
        extra=dict(lunar_local_time_h=lunar_time, subsolar_lat=sp.declination_deg,
                   solar_day_s=moon_eph.SYNODIC_MONTH_DAYS * 86400.0))
    return env


# =================================================================================
# Mars
# =================================================================================

def mars_dust_tau(Ls, tau_aphelion=0.45, tau_perihelion=0.85, Ls_peak=245.0, width=55.0,
                  storm=None):
    """Seasonal column dust optical depth (visible) - smooth climatology.

    ``storm`` = (Ls_start, Ls_end, tau_peak) adds a global-dust-storm episode.
    Defaults are representative of Jezero crater in Mars Years 36-37 (aphelion
    season tau ~0.4-0.5, dusty season ~0.8-1.0; Lemmon et al. 2022, Smith et al. 2023).
    """
    Ls = np.asarray(Ls, float)
    d = (Ls - Ls_peak + 180.0) % 360.0 - 180.0
    tau = tau_aphelion + (tau_perihelion - tau_aphelion) * np.exp(-0.5 * (d / width) ** 2)
    if storm is not None:
        a, b, tp = storm
        mid, half = 0.5 * (a + b), 0.5 * (b - a)
        ds = (Ls - mid + 180.0) % 360.0 - 180.0
        tau = np.maximum(tau, np.where(np.abs(ds) < half, tp * np.clip(np.cos(0.5 * np.pi * ds / half), 0, 1) ** 0.5, 0.0))
    return tau


def mars_surface_pressure(Ls, P_mean=720.0, a1=0.074, phi1=154.0, a2=0.055, phi2=290.0):
    """Seasonal surface pressure [Pa] as a two-harmonic fit (Viking-type CO2 cycle).

    P = P_mean [1 + a1 sin(Ls + phi1) + a2 sin(2 Ls + phi2)].  The default shape puts the
    minimum at Ls = 157 (growth of the southern seasonal CO2 cap), the maximum at Ls = 269 and a
    secondary maximum at Ls = 64, matching Viking/REMS/MEDA climatology (range 0.89-1.12 P_mean);
    P_mean is site dependent (Jezero ~710 Pa, Gale ~800 Pa).
    """
    L = np.radians(np.asarray(Ls, float))
    return P_mean * (1 + a1 * np.sin(L + np.radians(phi1)) + a2 * np.sin(2 * L + np.radians(phi2)))


def mars_site(latitude, longitude, start_utc, duration_sols, dt=1800.0, tau=None, tau_kwargs=None,
              P_mean=710.0, thermal_inertia=350.0, albedo=0.14, dust_w0=0.885, dust_g=0.74,
              air_coupling=0.6, air_lag_h=0.5, sky_emissivity=(0.08, 0.125), dust_reemission=0.45,
              wind_mean=3.2, wind_amp=2.0,
              spinup_sols=30, deep_depth=3.0, horizon=None, equilibrate=True):
    """Martian surface environment.

    * Sun from Mars24 (Allison & McEwen 2000); TOA irradiance 1361/r^2.
    * Direct/diffuse split from the delta-Eddington model with seasonal dust optical depth.
    * Ground temperature from a homogeneous regolith column with the given thermal inertia.
    * Near-surface (1.5 m) air temperature: T_air = <T_g>_sol + kappa (T_g(t-lag) - <T_g>_sol),
      an empirical surrogate for the convective boundary layer, kappa ~ 0.6 reproducing the
      ~2:1 ratio of ground-to-air diurnal amplitude measured by MEDA/REMS.
    * Downwelling long-wave: L = eps_sky(tau) sigma T_air^4 + f_re <G_toa,h - G_h>_sol with
      eps_sky = min(0.08 + 0.125 tau, 0.6) and f_re = 0.45: gas/dust emission plus re-emission of
      the sunlight removed by dust (sol-running mean; a one-layer-atmosphere energy term).
      Calibrated to MEDA/TIRS (Martinez et al. 2023): clear-season daily mean ~30 W/m2; in a global
      dust storm the sol-mean temperature drops by ~10 K while the diurnal range collapses, as
      observed in 2018 (Guzewich et al. 2019).
    * Dust scattering: effective broadband w0 = 0.885, g = 0.74, fitted to the Appelbaum &
      Flood (1990) net-flux tables (RMSE 0.014).  Defaults for the site: Jezero (MEDA:
      P 625-790 Pa, albedo 0.14, thermal inertia ~350 SI, mean wind 3.2 m/s).
    """
    sol = mars_eph.MARS_SOL_SECONDS
    n = int(round(duration_sols * sol / dt))
    t_end = (np.arange(n) + 1) * dt
    jd0 = jd_from_datetime(start_utc)

    def sun_and_flux(jd_mid):
        sp = mars_eph.sun_position(jd_mid, latitude, longitude)
        Ls = sp.extra["Ls"]
        tt = mars_dust_tau(Ls, **(tau_kwargs or {})) if tau is None else np.broadcast_to(np.asarray(tau, float), Ls.shape)
        S = TSI_1AU / sp.distance_au ** 2
        mu = np.cos(np.radians(sp.zenith_deg))
        # spherical-shell air mass (scale height 11 km, R = 3390 km)
        Rh = 3390.0 / 11.0
        m = np.sqrt((Rh * np.maximum(mu, 0.0)) ** 2 + 2 * Rh + 1) - Rh * np.maximum(mu, 0.0)
        mu_eff = 1.0 / m
        dfrac, sfrac = delta_eddington_surface(tt, mu_eff, dust_w0, dust_g, albedo)
        vis = horizon_visible_fraction(90 - sp.zenith_deg, sp.azimuth_deg, horizon, 0.2666 / sp.distance_au)
        up = (mu > 0).astype(float)
        G_top = S * np.maximum(mu, 0.0)
        # The delta-Eddington solution gives the total (direct + diffuse) flux; its "direct" part contains
        # the forward-scattering peak (delta scaling).  The beam a surface sees from the solar disk follows
        # Beer's law with the true optical depth; the forward-scattered peak is counted as diffuse.
        total_h = G_top * (dfrac + sfrac) * up
        beer = np.exp(-tt * m)
        direct_h = G_top * beer * vis * up
        diffuse_h = np.maximum(total_h - G_top * beer * up, 0.0)
        dni = np.where(mu > 0.0, direct_h / np.maximum(mu, 1e-6), 0.0)
        return sp, Ls, tt, dni, diffuse_h, direct_h + diffuse_h, vis, G_top

    jd_mid = jd0 + (t_end - 0.5 * dt) / 86400.0
    sp, Ls, tau_t, dni, dhi, ghi, vis, G_top = sun_and_flux(jd_mid)
    P = mars_surface_pressure(Ls, P_mean)
    col = RegolithColumn.mars(thermal_inertia=thermal_inertia, albedo=albedo, depth=4.0)
    e0, e1 = sky_emissivity

    n_sol = int(round(sol / dt))

    k = max(1, n_sol)
    lag = int(round(air_lag_h * 3600.0 / dt))
    eps_sky = np.clip(e0 + e1 * tau_t, 0.05, 0.6)
    deficit = np.concatenate([np.full(k, np.mean(G_top[:k] - ghi[:k])), G_top - ghi])
    cdef = np.cumsum(deficit)
    L_dust = dust_reemission * (cdef[k:] - cdef[:-k]) / k     # sol-running mean re-emission

    def air_from_ground(T_g):
        pad = np.concatenate([np.full(k, T_g[:k].mean()), T_g])
        csum = np.cumsum(pad)
        Tg_mean = (csum[k:] - csum[:-k]) / k                    # sol-running mean
        Tg_lag = np.concatenate([np.full(lag, T_g[0]), T_g[:-lag]]) if lag > 0 else T_g
        return Tg_mean + air_coupling * (Tg_lag - Tg_mean)

    # 1) periodic equilibrium of the whole column for the Mars year before the start (1 h steps); the
    #    annual wave reaches ~1.3 m, so metre depths need several Mars years to forget an initial guess
    T0 = None
    if equilibrate:
        dty = 3600.0
        ny = int(round(668.6 * sol / dty))
        jd_y = jd0 - ny * dty / 86400.0 + (np.arange(ny) + 0.5) * dty / 86400.0
        _, _, tau_y, _, _, ghi_y, _, Gtop_y = sun_and_flux(jd_y)
        ky = max(1, int(round(sol / dty)))
        dy = np.concatenate([np.full(ky, np.mean(Gtop_y[:ky] - ghi_y[:ky])), Gtop_y - ghi_y])
        cy = np.cumsum(dy)
        Ld_y = dust_reemission * (cy[ky:] - cy[:-ky]) / ky + np.clip(e0 + e1 * tau_y, 0.05, 0.6) * SIGMA * 210.0 ** 4
        T0, _, _ = col.equilibrate(dty, (1 - albedo) * ghi_y, Ld_y, z_skin=0.25)
    # 2) spin-up on the first sol (repeated), then fixed-point iteration ground <-> air <-> sky emission
    L_down = eps_sky * SIGMA * 210.0 ** 4 + L_dust
    spin = col.run(dt, (1 - albedo) * ghi[:n_sol], L_down[:n_sol], T_init=T0,
                   spinup_cycles=min(spinup_sols, 5) if equilibrate else spinup_sols, cycle_steps=n_sol)
    for _ in range(4):
        res = col.run(dt, (1 - albedo) * ghi, L_down, T_init=spin["T_final"], record_depths=(0.0, deep_depth))
        T_g = res["T_surface"]
        T_air = air_from_ground(T_g)
        L_new = eps_sky * SIGMA * T_air ** 4 + L_dust
        converged = np.max(np.abs(L_new - L_down)) < 0.05
        L_down = L_new
        if converged:
            break
        spin = col.run(dt, (1 - albedo) * ghi[:n_sol], L_down[:n_sol], T_init=spin["T_final"],
                       spinup_cycles=spinup_sols, cycle_steps=n_sol)
    T_sky = (L_down / SIGMA) ** 0.25
    ltst = sp.extra["ltst_h"]
    lmst = sp.extra["lmst_h"]
    wind = np.maximum(0.3, wind_mean + wind_amp * np.sin(2 * np.pi * (ltst - 9.0) / 24.0))
    msd = sp.extra["msd"]
    env = Environment(
        planet="mars", latitude=latitude, longitude=longitude, dt=dt, time_s=t_end, jd_utc=jd0 + t_end / 86400.0,
        zenith=sp.zenith_deg, sun_azimuth=sp.azimuth_deg, dni=dni, dhi=dhi, ghi=ghi, sun_visible=vis,
        T_air=T_air, T_sky=T_sky, T_ground=T_g, T_deep=np.full(n, float(np.mean(res["T_depths"][:, 1]))),
        wind_speed=wind, wind_dir=np.full(n, 180.0), pressure=P, ground_albedo=np.full(n, albedo),
        gravity=MARS_GRAVITY, gas=_gas.MARS_CO2, local_time_h=lmst,
        day_index=np.floor(msd - msd[0]).astype(int),
        extra=dict(Ls=Ls, tau=tau_t, ltst_h=ltst, L_down=L_down, solar_day_s=sol))
    return env
