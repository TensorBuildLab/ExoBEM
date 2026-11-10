"""Zone heat-balance simulation engine.

The algorithm follows the EnergyPlus heat-balance method (Engineering Reference,
"Surface Heat Balance Manager" and "Zone Air Heat Balance"):

1. Outside-face heat balance  q_sol + q_LW(sky, ground[, air]) + q_conv = q_cond
2. Transient conduction through every construction (finite volumes, implicit)
3. Inside-face heat balance   q_cond + q_LW,int(ScriptF) + q_rad,gains + q_conv = 0
4. Zone air heat balance      C dTz/dt = sum h_i A_i (T_si - Tz) + Q_conv,gains
                                         + m_inf c_p (T_supply - Tz) + Q_sys
5. Ideal loads: Q_sys is whatever keeps Tz inside the heating/cooling set-point band.

Steps 2-4 are solved *simultaneously* each iteration: the banded conduction system is
solved for several right-hand sides by superposition, which reduces the coupled
air-node / inside-face / interior-radiation problem to a small dense system.  The only
lagged quantities are the non-linear coefficients (radiation linearisation, convection
coefficients, temperature-dependent properties), which are refreshed by fixed-point
iteration within each step.

Extraterrestrial extensions: vacuum (no exterior convection), CO2 atmosphere at
~600 Pa, gravity- and pressure-aware convection, regolith ground boundary,
non-24 h days.
"""
from __future__ import annotations

from dataclasses import dataclass
import time

import numpy as np
from scipy.linalg import solve_banded

from .constants import SIGMA, KELVIN
from . import convection as cv
from . import gas as _gas
from .checks import check_model
from .conduction import GlobalGrid
from .geometry import Surface
from .materials import ROUGHNESS_MULT
from .model import Model, evaluate_schedule
from .solar import incident_solar

TERRAIN = {"Country": (0.14, 270.0), "Suburbs": (0.22, 370.0), "City": (0.33, 460.0),
           "Ocean": (0.10, 210.0), "Urban": (0.22, 370.0)}


# ------------------------------------------------------------------------------------
def approximate_view_factors(surfs):
    """EnergyPlus-style area-weighted view factors (no self-view, no view between faces
    with identical orientation), with reciprocity enforced."""
    n = len(surfs)
    A = np.array([s.area for s in surfs])
    F = np.zeros((n, n))
    for i, si in enumerate(surfs):
        for j, sj in enumerate(surfs):
            if i == j:
                continue
            same = abs(si.tilt - sj.tilt) < 1e-3 and (abs(si.tilt) < 1e-3 or abs(si.tilt - 180) < 1e-3 or
                                                       abs((si.azimuth - sj.azimuth + 180) % 360 - 180) < 1e-3)
            same = same and not (si.is_internal_mass or sj.is_internal_mass)
            if not same:
                F[i, j] = A[j]
        F[i] /= F[i].sum()
    for _ in range(50):
        AF = 0.5 * (A[:, None] * F + (A[:, None] * F).T)
        F = AF / A[:, None]
        F /= F.sum(axis=1, keepdims=True)
    return F


def script_f(F, eps):
    """Hottel gray-interchange factors (EnergyPlus ScriptF); returns matrix with zero diagonal."""
    e = np.clip(np.asarray(eps, float), 1e-4, 0.9999)
    n = len(e)
    M = np.eye(n) - (1 - e)[:, None] * F
    Minv_e = np.linalg.solve(M, np.diag(e))
    K = (e / (1 - e))[:, None] * (np.eye(n) - Minv_e)
    SF = -K
    np.fill_diagonal(SF, 0.0)
    return SF


@dataclass
class Results:
    time_s: np.ndarray
    T_zone_C: np.ndarray
    Q_heating_W: np.ndarray
    Q_cooling_W: np.ndarray
    Q_latent_W: np.ndarray
    T_inside_C: np.ndarray
    T_outside_C: np.ndarray
    q_cond_inside_W_m2: np.ndarray
    h_conv_in: np.ndarray
    h_conv_out: np.ndarray
    absorbed_solar_out_W: np.ndarray
    surface_names: list
    env: object
    model: object
    wall_time_s: float = 0.0
    iterations: np.ndarray = None
    electric_W: np.ndarray = None
    radiator_T_K: np.ndarray = None
    radiator_sink_K: np.ndarray = None
    cop_cooling: np.ndarray = None
    rh_zone: np.ndarray = None           # cabin relative humidity [-] (humidity control on)
    w_zone: np.ndarray = None            # cabin humidity ratio [kg/kg dry gas]
    condensate_kg_s: np.ndarray = None   # water removed by the condensing heat exchanger (negative: added)
    electric_internal_W: np.ndarray = None   # electric power of gains marked electric=True
    n_envelope: int = 0                  # surfaces [0, n_envelope) are the envelope; the rest internal mass
    dewpoint_C: np.ndarray = None        # cabin dew point (humidity control on)
    Q_coldplate_W: np.ndarray = None     # equipment heat collected by cold plates (bypasses the cabin air)
    n_unconverged: int = 0               # steps that reached max_iterations without meeting the tolerance

    def summary(self):
        dt = self.env.dt
        J2kWh = 1.0 / 3.6e6
        s = dict(
            heating_kWh=float(self.Q_heating_W.sum() * dt * J2kWh),
            cooling_kWh=float(self.Q_cooling_W.sum() * dt * J2kWh),
            latent_kWh=float(self.Q_latent_W.sum() * dt * J2kWh),
            peak_heating_W=float(self.Q_heating_W.max()),
            peak_cooling_W=float(self.Q_cooling_W.max()),
            T_zone_min_C=float(self.T_zone_C.min()),
            T_zone_max_C=float(self.T_zone_C.max()),
            T_zone_mean_C=float(self.T_zone_C.mean()),
            n_steps=int(len(self.time_s)),
            wall_time_s=self.wall_time_s,
        )
        if self.electric_W is not None:
            s["thermal_control_electric_kWh"] = float(self.electric_W.sum() * dt * J2kWh)
            s["thermal_control_peak_electric_W"] = float(self.electric_W.max())
        if self.electric_internal_W is not None:
            s["internal_electric_kWh"] = float(self.electric_internal_W.sum() * dt * J2kWh)
        if self.Q_coldplate_W is not None:
            s["coldplate_kWh"] = float(self.Q_coldplate_W.sum() * dt * J2kWh)
        if self.rh_zone is not None:
            s.update(rh_min=float(self.rh_zone.min()), rh_max=float(self.rh_zone.max()),
                     condensate_kg=float(np.sum(np.maximum(self.condensate_kg_s, 0)) * dt))
            margin = self.T_inside_C.min(axis=1) - self.dewpoint_C
            s["min_surface_minus_dewpoint_K"] = float(margin.min())
            s["condensation_risk_hours"] = float(np.sum(margin < 0.0) * dt / 3600.0)
        s["unconverged_steps"] = int(self.n_unconverged)
        z = self.model.zone
        days = len(self.time_s) * dt / 86400.0
        s["cabin_gas_makeup_kg"] = float(z.gas_loss_kg_per_day * days)
        return s

    def to_csv(self, path):
        import csv
        names = self.surface_names
        hdr = ["time_s", "T_zone_C", "Q_heating_W", "Q_cooling_W", "Q_latent_W"]
        hdr += [f"Tin_{n}_C" for n in names] + [f"Tout_{n}_C" for n in names]
        if self.electric_W is not None:
            hdr += ["thermal_control_electric_W", "radiator_T_K", "radiator_sink_K"]
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(hdr)
            for i in range(len(self.time_s)):
                row = [self.time_s[i], self.T_zone_C[i], self.Q_heating_W[i], self.Q_cooling_W[i], self.Q_latent_W[i]]
                row += list(self.T_inside_C[i]) + list(self.T_outside_C[i])
                if self.electric_W is not None:
                    row += [self.electric_W[i], self.radiator_T_K[i], self.radiator_sink_K[i]]
                w.writerow([f"{x:.6g}" for x in row])


# ------------------------------------------------------------------------------------
def simulate(model: Model, env, verbose: bool = False) -> Results:
    t_start = time.time()
    zone = model.zone
    check_model(model, env)
    n_env = len(zone.geometry.surfaces)
    surfs = list(zone.geometry.surfaces)
    for im in zone.internal_mass:          # one face to the zone, the other adiabatic
        surfs.append(Surface(im.name, im.construction, im.area_m2, 90.0, 0.0, 4.0 * np.sqrt(im.area_m2), 1.0,
                             "adiabatic", char_length=min(2.0, float(np.sqrt(im.area_m2))), is_internal_mass=True))
    ns = len(surfs)
    dt = env.dt
    if abs(model.timestep_s - dt) > 1e-6:
        raise ValueError("Environment time step and model time step differ")
    cons = [model.constructions[s.construction] for s in surfs]
    nT = env.n

    # --- static surface properties ---------------------------------------------------
    A = np.array([s.area for s in surfs])
    cos_tilt = np.array([s.cos_tilt for s in surfs])
    out_bc = np.array([s.boundary for s in surfs])
    is_out = out_bc == "outdoors"
    is_gnd = out_bc == "ground"
    eps_o = np.array([c.outside.thermal_emissivity for c in cons])
    alpha_o = np.array([c.outside.solar_absorptance for c in cons])
    eps_i = np.array([c.inside.thermal_emissivity for c in cons])
    rough = np.array([ROUGHNESS_MULT[c.outside.roughness] for c in cons])
    Fsky = np.array([s.F_sky for s in surfs])
    Fgnd = np.array([s.F_ground for s in surfs])
    beta = np.sqrt(0.5 * (1 + cos_tilt))
    perim = np.array([s.perimeter for s in surfs])
    zc = np.array([s.centroid_height for s in surfs])
    Lv = np.array([s.length_vertical for s in surfs])
    Lh = np.array([s.length_horizontal for s in surfs])
    az = np.array([s.azimuth for s in surfs])

    # --- interior radiation ------------------------------------------------------------
    F = approximate_view_factors(surfs)
    SF = script_f(F, eps_i)
    rad_dist = A * eps_i / np.sum(A * eps_i)        # radiant internal gains distribution

    # --- exterior solar ----------------------------------------------------------------
    solar_model = model.solar_model
    if solar_model == "auto":
        solar_model = "perez" if env.planet == "earth" else "isotropic"
    beam, sky, gnd, _ = incident_solar(env, surfs, solar_model)
    q_sol_out = alpha_o[None, :] * (beam + sky + gnd) * is_out[None, :]

    # --- internal gains ---------------------------------------------------------------
    Qc_int = np.zeros(nT)
    Qr_int = np.zeros(nT)
    Q_lat = np.zeros(nT)
    P_elec_int = np.zeros(nT)
    Q_cold = np.zeros(nT)
    for g in zone.gains:
        f = evaluate_schedule(g.schedule, env.local_time_h, env.day_index)
        heat = g.power_W * g.heat_fraction * f
        to_zone = heat * (1.0 - g.coldplate_fraction)
        Qr_int += to_zone * g.radiant_fraction
        Qc_int += to_zone * (1 - g.radiant_fraction)
        Q_cold += heat * g.coldplate_fraction
        Q_lat += g.latent_W * f
        if g.electric:
            P_elec_int += g.power_W * f
    T_heat = evaluate_schedule(zone.thermostat.heating_setpoint_C, env.local_time_h, env.day_index) + KELVIN
    T_cool = evaluate_schedule(zone.thermostat.cooling_setpoint_C, env.local_time_h, env.day_index) + KELVIN

    # --- exterior convection mode ------------------------------------------------------
    ext_mode = model.exterior_convection
    if ext_mode == "auto":
        ext_mode = "none" if env.vacuum else ("tarp" if env.planet == "earth" else "physical")
    if env.planet == "earth":
        a_t, d_t = TERRAIN[model.terrain]
        wind_local = cv.local_wind_speed(env.wind_speed[:, None], zc[None, :], a_t, d_t)
    else:
        wind_local = np.repeat(env.wind_speed[:, None], ns, axis=1)

    # --- cabin gas ---------------------------------------------------------------------
    if env.planet == "earth":
        cabin = _gas.DRY_AIR
    else:
        cabin = _gas.cabin_gas(zone.cabin_o2_fraction)
    P_cab = zone.cabin_pressure_Pa
    cos_up_in = -cos_tilt                       # inside face normal points opposite

    # --- grid --------------------------------------------------------------------------
    T0 = zone.initial_temperature_C + KELVIN
    curv = [s.curvature if (model.curvature == "auto" and not s.is_internal_mass) else None for s in surfs]
    grid = GlobalGrid(cons, dt, T0, curvatures=curv)
    ao = grid.outer_area_factor                  # outer / inner face area (1 for planar layers)
    q_sol_out = q_sol_out * ao[None, :]          # absorbed solar per unit INNER area
    if is_gnd.any():   # start ground-contact constructions on a linear profile
        for s in np.where(is_gnd)[0]:
            o, nn = grid.surface_offsets[s], grid.surface_nnodes[s]
            grid.T[o:o + nn] = np.linspace(env.T_deep[0], T0, nn)
        grid.update_properties()
    oi, ii = grid.outside_idx, grid.inside_idx
    Tz = T0

    # --- outputs -----------------------------------------------------------------------
    out_Tz = np.zeros(nT)
    out_Qh = np.zeros(nT)
    out_Qc = np.zeros(nT)
    out_Ti = np.zeros((nT, ns))
    out_To = np.zeros((nT, ns))
    out_qci = np.zeros((nT, ns))
    out_hci = np.zeros((nT, ns))
    out_hco = np.zeros((nT, ns))
    out_it = np.zeros(nT, dtype=int)
    n_unconv = 0

    has_tdep = len(grid._tdep) > 0

    # --- cabin humidity (condensing heat exchanger) ---------------------------------------
    hum = zone.humidity_control
    out_rh = np.zeros(nT) if hum else None
    out_w = np.zeros(nT) if hum else None
    out_cond = np.zeros(nT) if hum else None
    out_dp = np.zeros(nT) if hum else None
    Q_lat_chx = np.zeros(nT) if hum else None
    if hum:
        P_h = zone.cabin_pressure_Pa if zone.cabin_pressure_Pa else 101325.0
        w_z = float(_gas.humidity_ratio(zone.initial_rh * _gas.saturation_pressure(T0 - KELVIN), P_h, cabin))
        m_out_dot = zone.gas_loss_kg_per_day / 86400.0     # dry gas lost overboard, replaced dry

    # --- warm-up rows ------------------------------------------------------------------
    # (1) pseudo-transient steady-state solve with period-mean boundary conditions
    #     (time steps growing to 1e9 s) - needed because metre-thick regolith covers have
    #     time constants of years; (2) one repetition of the first solar day (EnergyPlus-
    #     style warm-up).  Warm-up rows are discarded from the results.
    init = model.initialize
    if init == "auto":
        init = "none" if env.planet == "earth" else "steady"
    rows = np.arange(nT)
    n_steady = 0
    if init == "steady":
        n_steady = 30
        n_cycle = min(nT, int(round(env.extra.get("solar_day_s", 86400.0) / dt)))
        rows = np.concatenate([np.full(n_steady, -1), np.arange(n_cycle), np.arange(nT)])
    n_warm = len(rows) - nT
    dts = np.full(len(rows), dt)
    if n_steady:
        dts[:n_steady] = np.geomspace(dt, 1e9, n_steady)

    def mean4(x):
        return float(np.mean(x ** 4) ** 0.25)

    means = dict(Tair=float(np.nanmean(env.T_air)) if not np.all(np.isnan(env.T_air)) else np.nan,
                 Tsky=mean4(env.T_sky), Tgnd=mean4(env.T_ground), Tdeep=float(np.mean(env.T_deep)),
                 P=float(np.mean(env.pressure)), qsol=q_sol_out.mean(axis=0), Qr=float(Qr_int.mean()),
                 Qc=float(Qc_int.mean()), Th=float(T_heat.mean()), Tc=float(T_cool.mean()),
                 wind=wind_local.mean(axis=0), wdir=float(np.mean(env.wind_dir)),
                 w=float(np.mean(env.humidity_ratio)) if env.humidity_ratio is not None else 0.0)

    for k, n_src in enumerate(rows):
        steady = n_src < 0
        n = 0 if steady else int(n_src)
        dt = dts[k]
        if has_tdep:
            grid.update_properties()
        ab0, rhs0 = grid.base_matrix(dt)
        if steady:
            Tair, Tsky, Tgnd, Tdeep, Pout = means["Tair"], means["Tsky"], means["Tgnd"], means["Tdeep"], means["P"]
            qsol_n, Qr_n, Qc_n, Th_n, Tc_n = means["qsol"], means["Qr"], means["Qc"], means["Th"], means["Tc"]
            wind_n, wdir_n, w_n = means["wind"], means["wdir"], means["w"]
        else:
            Tair, Tsky, Tgnd, Tdeep, Pout = env.T_air[n], env.T_sky[n], env.T_ground[n], env.T_deep[n], env.pressure[n]
            qsol_n, Qr_n, Qc_n, Th_n, Tc_n = q_sol_out[n], Qr_int[n], Qc_int[n], T_heat[n], T_cool[n]
            wind_n, wdir_n = wind_local[n], env.wind_dir[n]
            w_n = env.humidity_ratio[n] if env.humidity_ratio is not None else 0.0
        # infiltration / leakage heat-transfer coefficient (W/K) and supply temperature
        if env.planet == "earth" and zone.infiltration_ach > 0:
            w_out = w_n
            rho_o = _gas.moist_air_density(Pout, Tair - KELVIN, w_out)
            mcp = zone.infiltration_ach * zone.geometry.volume / 3600.0 * rho_o * _gas.moist_air_cp(w_out)
            T_sup = Tair
        elif zone.gas_loss_kg_per_day > 0:
            # cabin gas lost overboard (leakage + airlock venting) is replaced from storage at T_sup
            mcp = zone.gas_loss_kg_per_day / 86400.0 * cabin.cp
            T_sup = (zone.makeup_gas_temperature_C + KELVIN) if zone.makeup_gas_temperature_C is not None else Tz
        else:
            mcp, T_sup = 0.0, Tz
        if env.planet == "earth":
            w_z = w_n
            rho_z = _gas.moist_air_density(P_cab if P_cab else Pout, Tz - KELVIN, w_z)
            cp_z = _gas.moist_air_cp(w_z)
        else:
            rho_z = cabin.density(Tz, P_cab)
            cp_z = cabin.cp
        Cz = rho_z * zone.geometry.volume * cp_z * zone.air_capacitance_multiplier
        Tz_old = Tz

        To_g = grid.T[oi].copy()
        Ti_g = grid.T[ii].copy()
        Tz_g = Tz
        for it in range(model.max_iterations):
            ab = ab0.copy()
            rhs = rhs0.copy()
            # ---------------- outside faces
            if ext_mode == "none":
                hco = np.zeros(ns)
            elif ext_mode == "tarp":
                windward = cv.is_windward(az, cos_tilt, wdir_n)
                hco = cv.tarp_exterior(To_g - Tair, cos_tilt, wind_n, perim, A, rough, windward)
            else:
                hco = cv.mixed_physical(env.gas, To_g, Tair, Pout, env.gravity, cos_tilt, wind_n,
                                        Lv, Lh, np.sqrt(A))
            hco = np.where(is_out, hco, 0.0)
            if env.sky_includes_air:
                Fs_sky, Fs_air = Fsky * beta, Fsky * (1 - beta)
            else:
                Fs_sky, Fs_air = Fsky, np.zeros(ns)
            # long-wave exchange with sky, ground (and air, Earth), Newton-linearised about To_g:
            #   eps sigma sum_k F_k (T_k^4 - T^4) ~= E - 4 eps sigma F_tot To_g^3 (T - To_g)
            Tair_eff = 0.0 if np.isnan(Tair) else Tair
            F_tot = Fs_sky + Fgnd + Fs_air
            E_in = eps_o * SIGMA * (Fs_sky * Tsky ** 4 + Fgnd * Tgnd ** 4 + Fs_air * Tair_eff ** 4)
            hr_lin = 4.0 * eps_o * SIGMA * F_tot * To_g ** 3
            add_diag = np.where(is_out, (hco + hr_lin) * ao, 0.0)
            add_rhs = np.where(is_out, qsol_n + (hco * Tair_eff + E_in
                                                  + 3.0 * eps_o * SIGMA * F_tot * To_g ** 4) * ao, 0.0)
            ab[1, oi] += add_diag
            rhs[oi] += add_rhs
            # ground: Dirichlet
            if is_gnd.any():
                gi = oi[is_gnd]
                ab[1, gi] = 1.0
                ab[0, gi + 1] = 0.0
                rhs[gi] = Tdeep
            # ---------------- inside faces
            dTi = Ti_g - Tz_g
            if zone.interior_convection == "tarp":
                hci = cv.walton_natural(dTi, cos_up_in)
            elif zone.interior_convection == "tarp_scaled":
                hci = cv.walton_natural(dTi, cos_up_in) * cv.tarp_scale_factor(cabin, Tz_g, P_cab, env.gravity,
                                                                                 _gas.DRY_AIR)
            else:
                hci = cv.mixed_physical(cabin, Ti_g, Tz_g, P_cab, env.gravity, cos_up_in, zone.cabin_air_velocity,
                                        Lv, Lh, np.sqrt(A))
            hci = np.maximum(hci, 0.1 if env.planet == "earth" else 0.05)
            hr_ij = SIGMA * SF * (Ti_g[:, None] ** 2 + Ti_g[None, :] ** 2) * (Ti_g[:, None] + Ti_g[None, :])
            ab[1, ii] += hci + hr_ij.sum(axis=1)
            rhs[ii] += Qr_n * rad_dist / A
            # superposition RHS: [b, unit couplings to each inside face, coupling to Tz]
            B = np.zeros((grid.N, ns + 2))
            B[:, 0] = rhs
            B[ii, 1:ns + 1] = hr_ij           # B[node_i, j] = h_r,ij
            B[ii, ns + 1] = hci
            X = solve_banded((1, 1), ab, B, overwrite_ab=True, check_finite=False)
            X0 = X[:, 0]
            XB_in = X[ii, 1:ns + 1]
            XB_z = X[ii, ns + 1]
            M = np.eye(ns) - XB_in
            hA = hci * A
            a_z = Cz / dt + hA.sum() + mcp
            b_z = Cz / dt * Tz_old + mcp * T_sup + Qc_n
            # free-floating solve
            Msys = np.zeros((ns + 1, ns + 1))
            Msys[:ns, :ns] = M
            Msys[:ns, ns] = -XB_z
            Msys[ns, :ns] = -hA
            Msys[ns, ns] = a_z
            rsys = np.concatenate([X0[ii], [b_z]])
            sol = np.linalg.solve(Msys, rsys)
            Tz_new = sol[ns]
            Qsys = 0.0
            if Tz_new < Th_n or Tz_new > Tc_n:
                Tz_new = Th_n if Tz_new < Th_n else Tc_n
                Ti_new = np.linalg.solve(M, X0[ii] + XB_z * Tz_new)
                Qsys = a_z * Tz_new - hA @ Ti_new - b_z
            else:
                Ti_new = sol[:ns]
            Tnodes = X0 + X[:, 1:ns + 1] @ Ti_new + X[:, ns + 1] * Tz_new
            change = max(np.max(np.abs(Tnodes[oi] - To_g)), np.max(np.abs(Ti_new - Ti_g)), abs(Tz_new - Tz_g))
            To_g, Ti_g, Tz_g = Tnodes[oi], Ti_new, Tz_new
            if change < model.tolerance_K:
                break
        else:
            n_unconv += 1
        grid.T = Tnodes
        Tz = Tz_new
        if hum:
            # water-vapour balance of the sealed cabin (implicit):  m_d dw/dt = G - m_out w - R
            m_d = cabin.density(Tz, P_h) * zone.geometry.volume
            G_w = (float(Q_lat.mean()) if steady else Q_lat[n]) / _gas.H_FG
            w_free = (m_d * w_z / dt + G_w) / (m_d / dt + m_out_dot)
            psat = float(_gas.saturation_pressure(Tz - KELVIN))
            w_hi = float(_gas.humidity_ratio(zone.rh_max * psat, P_h, cabin))
            w_lo = float(_gas.humidity_ratio(zone.rh_min * psat, P_h, cabin))
            w_new = min(max(w_free, w_lo), w_hi)
            R_chx = m_d * (w_z - w_new) / dt + G_w - m_out_dot * w_new     # kg/s removed (<0: humidified)
            w_z = w_new
        if k < n_warm:
            continue
        if hum:
            out_w[n] = w_z
            pv = float(_gas.vapour_pressure(w_z, P_h, cabin))
            out_rh[n] = pv / psat
            lnr = np.log(max(pv, 1e-6) / 610.94)                 # inverse Magnus (over water)
            out_dp[n] = 243.04 * lnr / (17.625 - lnr)
            out_cond[n] = R_chx
            Q_lat_chx[n] = R_chx * _gas.H_FG
        # inside-face conduction flux (into zone, W/m2)
        q_in = hci * (Ti_g - Tz) + (hr_ij * (Ti_g[:, None] - Ti_g[None, :])).sum(axis=1) - Qr_n * rad_dist / A
        out_Tz[n] = Tz - KELVIN
        out_Qh[n] = max(Qsys, 0.0)
        out_Qc[n] = max(-Qsys, 0.0)
        out_Ti[n] = Ti_g - KELVIN
        out_To[n] = To_g - KELVIN
        out_qci[n] = q_in
        out_hci[n] = hci
        out_hco[n] = hco
        out_it[n] = it + 1
        if verbose and n % max(1, nT // 10) == 0:
            print(f"  step {n}/{nT}  Tz={Tz - KELVIN:7.2f} C  Q={Qsys:9.1f} W  it={it + 1}")

    dt = env.dt
    res = Results(env.time_s, out_Tz, out_Qh, out_Qc, Q_lat_chx if hum else Q_lat, out_Ti, out_To, out_qci, out_hci,
                  out_hco, (q_sol_out * A[None, :]).sum(axis=1), [s.name for s in surfs], env, model,
                  wall_time_s=time.time() - t_start, iterations=out_it, rh_zone=out_rh, w_zone=out_w,
                  condensate_kg_s=out_cond, electric_internal_W=P_elec_int, n_envelope=n_env, dewpoint_C=out_dp,
                  Q_coldplate_W=Q_cold,
                  n_unconverged=n_unconv)
    if n_unconv:
        import warnings
        warnings.warn(f"{n_unconv} time steps did not converge to {model.tolerance_K} K in {model.max_iterations} "
                      "iterations; consider a smaller time step or more iterations", stacklevel=2)
    if model.thermal_control is not None:
        from .thermal_control import evaluate_thermal_control
        evaluate_thermal_control(res, model.thermal_control)
    return res
