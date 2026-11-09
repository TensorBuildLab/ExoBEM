"""Photovoltaic supply and energy-storage sizing for habitat loads (post-processing).

PV output is computed from the same incident-radiation model as the envelope.  Storage
is sized as the largest cumulative energy deficit (charge-discharge round-trip loss
applied to stored energy), the critical quantity for the 354-hour equatorial lunar night.
"""
from __future__ import annotations

import numpy as np

from .geometry import Surface
from .solar import incident_solar


def pv_power(env, area_m2, efficiency=0.30, tracking="vertical_single_axis", dust_factor=1.0,
             temperature_coeff=0.0):
    """Electrical PV output [W].

    tracking: ``two_axis`` (normal incidence), ``vertical_single_axis`` (vertical panel
    rotating about the local vertical - the configuration proposed for lunar-polar masts),
    or ``horizontal`` (fixed, facing up).
    """
    if tracking == "two_axis":
        G = env.dni * env.sun_visible + env.dhi
    elif tracking == "vertical_single_axis":
        elev = np.radians(90.0 - env.zenith)
        G = env.dni * env.sun_visible * np.maximum(np.cos(elev), 0.0) + 0.5 * env.dhi
    elif tracking == "horizontal":
        s = [Surface("pv", "", 1.0, 0.0, 180.0, 4.0, 1.0)]
        b, d, g, _ = incident_solar(env, s, "isotropic")
        G = (b + d + g)[:, 0]
    else:
        raise ValueError(tracking)
    return np.maximum(G, 0.0) * area_m2 * efficiency * dust_factor


def storage_requirement(generation_W, load_W, dt_s, round_trip=0.85):
    """Minimum usable storage [kWh] so the load is always met, and the unmet energy if the
    PV is undersized (storage would then grow without bound)."""
    net = (np.asarray(generation_W) - np.asarray(load_W)) * dt_s / 3.6e6   # kWh per step
    eta_c = np.sqrt(round_trip)
    eta_d = np.sqrt(round_trip)
    flow = np.where(net > 0, net * eta_c, net / eta_d)
    # repeat twice to account for periodic steady state
    flow2 = np.concatenate([flow, flow])
    soc = 0.0
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
                        round_trip=0.85):
    """PV area that makes the cycle energy-neutral (including storage losses)."""
    g1 = pv_power(env, 1.0, efficiency, tracking, dust_factor)
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
