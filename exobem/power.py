"""Electric power generation and storage for a planetary habitat.

Components
----------
* :class:`PVArray` - photovoltaic array with tracking, dust soiling and a cell temperature from an
  energy balance that works in vacuum (radiation only) and in the Martian CO2 atmosphere
  (radiation + convection).
* :class:`FissionPower` - fission surface power unit (constant electric output, waste heat to its
  own radiator).
* :class:`Battery` - electrochemical storage with charge/discharge efficiency, depth-of-discharge
  and power limits.
* :class:`RegenerativeFuelCell` - H2/O2 electrolyser + fuel cell storage for long nights.

:func:`simulate_power` steps the system through time with a fixed dispatch rule and returns the
state of charge, unmet and curtailed energy.  :func:`size_pv_for_balance` and
:func:`storage_requirement` (sizing helpers) are kept from ExoBEM 0.1.

Sign convention: powers in W, positive = generation or discharge; energies in kWh.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

from .constants import SIGMA
from .geometry import Surface
from .solar import incident_solar

J2KWH = 1.0 / 3.6e6


# ------------------------------------------------------------------------------------- PV
@dataclass
class PVArray:
    area_m2: float
    tracking: str = "two_axis"          # two_axis | vertical_single_axis | horizontal | fixed
    tilt_deg: float = 90.0              # fixed arrays only
    azimuth_deg: float = 0.0            # fixed arrays only
    cell_efficiency: float = 0.30       # at 28 C, AM0, beginning of life (triple-junction GaInP/GaAs/Ge)
    array_factor: float = 0.85          # packing, wiring, mismatch and power-conditioning losses
    temp_coeff_per_K: float = -0.0022   # relative change of efficiency per K
    T_ref_K: float = 301.15
    degradation_per_year: float = 0.0   # radiation / UV / thermal-cycling degradation (relative)
    alpha_front: float = 0.92           # solar absorptance of the cell side
    eps_front: float = 0.85
    eps_back: float = 0.85
    dust_loss_per_day: float = 0.0      # Mars soiling: relative loss per (Earth) day, e.g. 0.002-0.003
    cleaning_interval_days: Optional[float] = None   # dust removed every N days (None = never)
    dust_factor: float = 1.0            # constant transmission factor (e.g. lunar dust scenario)

    def orientation(self, env):
        """Panel tilt and azimuth time series [deg]."""
        n = env.n
        if self.tracking == "two_axis":
            return np.minimum(env.zenith, 90.0), env.sun_azimuth.copy()
        if self.tracking == "vertical_single_axis":
            return np.full(n, 90.0), env.sun_azimuth.copy()
        if self.tracking == "horizontal":
            return np.zeros(n), np.full(n, 180.0)
        if self.tracking == "fixed":
            return np.full(n, self.tilt_deg), np.full(n, self.azimuth_deg)
        raise ValueError(f"unknown tracking {self.tracking}")

    def plane_of_array(self, env):
        """Incident solar irradiance on the cell side [W/m2] (isotropic sky, ground reflection)."""
        tilt, az = self.orientation(env)
        z, t = np.radians(env.zenith), np.radians(tilt)          # element-wise (time-varying orientation)
        ci = np.maximum(np.cos(z) * np.cos(t) + np.sin(z) * np.sin(t) * np.cos(np.radians(env.sun_azimuth - az)), 0.0)
        ct = np.cos(np.radians(tilt))
        beam = env.dni * ci                       # dni already includes the visible disk fraction
        sky = env.dhi * 0.5 * (1 + ct)
        gnd = env.ground_albedo * env.ghi * 0.5 * (1 - ct)
        return beam + sky + gnd, tilt

    def cell_temperature(self, env, G, tilt, eta):
        """Steady energy balance of a thin panel (both faces radiate; convection on Mars):

            alpha G - eta G = eps_f sigma (T^4 - T_f^4) + eps_b sigma (T^4 - T_b^4) + 2 h (T - T_air)

        T_f^4, T_b^4: view-weighted sky/ground temperatures seen by the front and the back."""
        ct = np.cos(np.radians(tilt))
        Fs_f, Fg_f = 0.5 * (1 + ct), 0.5 * (1 - ct)
        Fs_b, Fg_b = 0.5 * (1 - ct), 0.5 * (1 + ct)
        Tf4 = Fs_f * env.T_sky ** 4 + Fg_f * env.T_ground ** 4
        Tb4 = Fs_b * env.T_sky ** 4 + Fg_b * env.T_ground ** 4
        q_abs = (self.alpha_front - eta) * G
        if env.gas is not None and np.all(np.isfinite(env.T_air)):
            from .convection import mixed_physical
            T_air = env.T_air
            # flat plate, characteristic length 1 m; convection on both faces
            h = np.array([float(mixed_physical(env.gas, np.array([Ta + 10.0]), Ta, P, env.gravity,
                                               np.array([ct_i]), w, np.array([1.0]), np.array([0.5]),
                                               np.array([1.0]))[0])
                          for Ta, P, ct_i, w in zip(T_air, env.pressure, ct, env.wind_speed)])
        else:
            T_air, h = np.zeros(env.n), np.zeros(env.n)
        T = np.full(env.n, 300.0)
        for _ in range(40):                      # Newton iterations
            f = (self.eps_front * SIGMA * (T ** 4 - Tf4) + self.eps_back * SIGMA * (T ** 4 - Tb4)
                 + 2 * h * (T - T_air) - q_abs)
            df = 4 * (self.eps_front + self.eps_back) * SIGMA * T ** 3 + 2 * h
            dT = f / df
            T = np.maximum(T - dT, 3.0)
            if np.max(np.abs(dT)) < 1e-4:
                break
        return T

    def soiling(self, env):
        if self.dust_loss_per_day <= 0:
            return np.full(env.n, self.dust_factor)
        days = env.time_s / 86400.0
        if self.cleaning_interval_days:
            days = np.mod(days, self.cleaning_interval_days)
        return self.dust_factor * np.maximum(1.0 - self.dust_loss_per_day * days, 0.0)

    def power(self, env, return_details=False):
        G, tilt = self.plane_of_array(env)
        eta0 = self.cell_efficiency * (1 - self.degradation_per_year * env.time_s / 3.15576e7)
        T = self.cell_temperature(env, G, tilt, eta0 * self.array_factor)
        for _ in range(2):                       # efficiency depends on T, T on extracted power
            eta = np.clip(eta0 * (1 + self.temp_coeff_per_K * (T - self.T_ref_K)), 0.0, None)
            T = self.cell_temperature(env, G, tilt, eta * self.array_factor)
        eta = np.clip(eta0 * (1 + self.temp_coeff_per_K * (T - self.T_ref_K)), 0.0, None)
        soil = self.soiling(env)
        P = G * soil * eta * self.array_factor * self.area_m2
        if return_details:
            return P, dict(G_poa=G, T_cell_K=T, efficiency=eta * self.array_factor, soiling=soil)
        return P


# -------------------------------------------------------------------------------- fission
@dataclass
class FissionPower:
    rated_kWe: float = 40.0             # NASA Fission Surface Power class
    efficiency: float = 0.25            # Stirling / Brayton conversion, electric / thermal
    availability: float = 1.0           # fraction of rated output available
    n_units: int = 1

    def power(self, env):
        return np.full(env.n, self.rated_kWe * 1000.0 * self.availability * self.n_units)

    def waste_heat(self, env):
        P = self.power(env)
        return P * (1.0 / self.efficiency - 1.0)


# -------------------------------------------------------------------------------- storage
@dataclass
class Battery:
    capacity_kWh: float                 # nameplate energy
    eta_charge: float = 0.97
    eta_discharge: float = 0.97         # round trip ~0.94 (Li-ion)
    soc_min: float = 0.20               # depth-of-discharge limit for cycle life
    soc_max: float = 1.0
    soc_init: float = 1.0
    max_power_kW: Optional[float] = None

    @property
    def usable_kWh(self):
        return self.capacity_kWh * (self.soc_max - self.soc_min)


@dataclass
class RegenerativeFuelCell:
    capacity_kWh: float                 # electric energy the fuel cell can deliver from full tanks
    eta_electrolyser: float = 0.80      # electric -> stored chemical (H2/O2)
    eta_fuel_cell: float = 0.60         # stored chemical -> electric (round trip ~0.48)
    soc_min: float = 0.05
    soc_max: float = 1.0
    soc_init: float = 1.0
    max_charge_kW: Optional[float] = None
    max_discharge_kW: Optional[float] = None


@dataclass
class PowerSystem:
    pv: List[PVArray] = field(default_factory=list)
    fission: Optional[FissionPower] = None
    battery: Optional[Battery] = None
    rfc: Optional[RegenerativeFuelCell] = None


def _store(storage, soc_kwh, P_W, dt, charge):
    """Charge (P_W > 0 available surplus) or discharge (P_W > 0 needed) one storage device.
    Returns (new_soc_kWh, electric power absorbed or delivered [W])."""
    if storage is None or P_W <= 0:
        return soc_kwh, 0.0
    cap = storage.capacity_kWh
    if isinstance(storage, Battery):
        eta_in, eta_out = storage.eta_charge, storage.eta_discharge
        p_in_max = p_out_max = (storage.max_power_kW or np.inf) * 1000.0
    else:
        eta_in, eta_out = storage.eta_electrolyser, storage.eta_fuel_cell
        p_in_max = (storage.max_charge_kW or np.inf) * 1000.0
        p_out_max = (storage.max_discharge_kW or np.inf) * 1000.0
    if isinstance(storage, RegenerativeFuelCell):
        # capacity is defined as deliverable electric energy; internal store in "delivered" units
        eta_in = eta_in * eta_out
        eta_out = 1.0
    if charge:
        room = (storage.soc_max * cap - soc_kwh) / eta_in       # kWh of electricity it can accept
        p = min(P_W, p_in_max, max(room, 0.0) / (dt * J2KWH))
        return soc_kwh + p * dt * J2KWH * eta_in, p
    avail = (soc_kwh - storage.soc_min * cap) * eta_out
    p = min(P_W, p_out_max, max(avail, 0.0) / (dt * J2KWH))
    return soc_kwh - p * dt * J2KWH / eta_out, p


def simulate_power(system: PowerSystem, env, load_W, repeat_cycles: int = 1):
    """Dispatch: generation serves the load; surplus charges the battery, then the RFC, then is
    curtailed (shunted to a radiator); deficits are met by the battery, then the RFC, then counted as
    unmet.  ``repeat_cycles`` > 1 repeats the period to remove the dependence on the initial charge."""
    load = np.asarray(load_W, float)
    n, dt = env.n, env.dt
    gen_pv = np.zeros(n)
    pv_details = []
    for a in system.pv:
        P, d = a.power(env, return_details=True)
        gen_pv += P
        pv_details.append(d)
    gen_f = system.fission.power(env) if system.fission else np.zeros(n)
    gen = gen_pv + gen_f
    b, r = system.battery, system.rfc
    sb = b.soc_init * b.capacity_kWh if b else 0.0
    sr = r.soc_init * r.capacity_kWh if r else 0.0
    for cycle in range(repeat_cycles):
        soc_b, soc_r = np.zeros(n), np.zeros(n)
        unmet, curt = np.zeros(n), np.zeros(n)
        p_b, p_r = np.zeros(n), np.zeros(n)
        for i in range(n):
            net = gen[i] - load[i]
            if net >= 0:
                sb, pb = _store(b, sb, net, dt, True)
                sr, pr = _store(r, sr, net - pb, dt, True)
                curt[i] = net - pb - pr
                p_b[i], p_r[i] = -pb, -pr
            else:
                need = -net
                sb, pb = _store(b, sb, need, dt, False)
                sr, pr = _store(r, sr, need - pb, dt, False)
                unmet[i] = need - pb - pr
                p_b[i], p_r[i] = pb, pr
            soc_b[i], soc_r[i] = sb, sr
    E = lambda x: float(np.sum(x) * dt * J2KWH)  # noqa: E731
    res = dict(
        generation_pv_W=gen_pv, generation_fission_W=gen_f, load_W=load, battery_W=p_b, rfc_W=p_r,
        soc_battery_kWh=soc_b, soc_rfc_kWh=soc_r, unmet_W=unmet, curtailed_W=curt, pv_details=pv_details,
        summary=dict(load_kWh=E(load), pv_kWh=E(gen_pv), fission_kWh=E(gen_f), unmet_kWh=E(unmet),
                     curtailed_kWh=E(curt), fraction_met=1.0 - E(unmet) / max(E(load), 1e-12),
                     hours_unmet=float(np.sum(unmet > 1e-6) * dt / 3600.0),
                     battery_min_soc=float(soc_b.min() / b.capacity_kWh) if b else None,
                     rfc_min_soc=float(soc_r.min() / r.capacity_kWh) if r else None),
    )
    return res


# ------------------------------------------------------------------------- sizing helpers
def pv_power(env, area_m2, efficiency=0.30, tracking="vertical_single_axis", dust_factor=1.0,
             temperature_coeff=0.0):
    """Electrical PV output [W] with a constant efficiency (ExoBEM 0.1 sizing model)."""
    if tracking == "two_axis":
        G = env.dni + env.dhi
    elif tracking == "vertical_single_axis":
        elev = np.radians(90.0 - env.zenith)
        G = env.dni * np.maximum(np.cos(elev), 0.0) + 0.5 * env.dhi
    elif tracking == "horizontal":
        s = [Surface("pv", "", 1.0, 0.0, 180.0, 4.0, 1.0)]
        b, d, g, _ = incident_solar(env, s, "isotropic")
        G = (b + d + g)[:, 0]
    else:
        raise ValueError(tracking)
    return np.maximum(G, 0.0) * area_m2 * efficiency * dust_factor


def storage_requirement(generation_W, load_W, dt_s, round_trip=0.85):
    """Minimum usable storage [kWh] so the load is always met over a periodic cycle, and the net
    energy (negative: generation insufficient even with unlimited storage)."""
    net = (np.asarray(generation_W) - np.asarray(load_W)) * dt_s / 3.6e6   # kWh per step
    eta_c = np.sqrt(round_trip)
    eta_d = np.sqrt(round_trip)
    flow = np.where(net > 0, net * eta_c, net / eta_d)
    flow2 = np.concatenate([flow, flow])      # repeat to reach the periodic state
    peak_deficit = 0.0
    level = 0.0
    hi = 0.0
    for f in flow2:
        level += f
        hi = max(hi, level)
        peak_deficit = max(peak_deficit, hi - level)
    surplus = float(flow.sum())
    return dict(storage_kWh=float(peak_deficit), net_energy_kWh=surplus, energy_positive=surplus >= 0)


def size_pv_for_balance(env, load_W, efficiency=0.30, tracking="vertical_single_axis", dust_factor=1.0,
                        round_trip=0.85, array: Optional[PVArray] = None):
    """PV area that makes the cycle energy-neutral (including storage losses).  If ``array`` is
    given its full model (cell temperature, soiling) is used per square metre."""
    if array is not None:
        a1 = PVArray(**{**array.__dict__, "area_m2": 1.0})
        g1 = a1.power(env)
    else:
        g1 = pv_power(env, 1.0, efficiency, tracking, dust_factor)
    if g1.sum() <= 0:
        return dict(storage_kWh=np.inf, net_energy_kWh=-np.inf, energy_positive=False, pv_area_m2=np.inf,
                    pv_mean_W_per_m2=0.0)
    lo, hi = 0.0, 1e5
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        r = storage_requirement(g1 * mid, load_W, env.dt, round_trip)
        if r["energy_positive"]:
            hi = mid
        else:
            lo = mid
    r = storage_requirement(g1 * hi, load_W, env.dt, round_trip)
    r["pv_area_m2"] = hi
    r["pv_mean_W_per_m2"] = float(g1.mean())
    return r
