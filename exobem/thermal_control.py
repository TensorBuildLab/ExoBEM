"""Habitat active thermal control: radiator heat rejection and heat-pump lift.

On the Moon (and, to a large degree, on Mars) a habitat cannot reject heat to outdoor
air; cabin heat is collected by a coolant loop and radiated to space.  The radiator
sink temperature depends on what the radiator sees:

    eps sigma T_sink^4 = alpha_r (beam + sky + ground-reflected)
                         + eps (F_sky sigma T_sky^4 + F_ground sigma T_ground^4)

At lunar noon a vertical radiator sees ~390 K regolith over half its view, which pushes
the sink above cabin temperature: a heat pump must lift the rejection temperature.
The heat-pump COP is a fixed fraction of the Carnot COP between the evaporator
(cabin loop minus approach) and condenser (radiator plus approach).
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import brentq

from .constants import SIGMA, KELVIN
from .geometry import Surface
from .solar import incident_solar


def radiator_sink(env, tcs):
    sides = [(tcs.radiator_tilt, tcs.radiator_azimuth)]
    if tcs.radiator_two_sided:
        sides.append((180.0 - tcs.radiator_tilt if tcs.radiator_tilt != 90.0 else 90.0,
                      (tcs.radiator_azimuth + 180.0) % 360.0))
    surfs = [Surface(f"rad{i}", "", 1.0, t, a, 4.0, 1.0) for i, (t, a) in enumerate(sides)]
    beam, sky, gnd, _ = incident_solar(env, surfs, "isotropic")
    Fsky = np.array([s.F_sky for s in surfs])
    Fgnd = np.array([s.F_ground for s in surfs])
    q_env = (tcs.radiator_absorptance * (beam + sky + gnd)
             + tcs.radiator_emissivity * SIGMA * (Fsky[None, :] * env.T_sky[:, None] ** 4
                                                  + Fgnd[None, :] * env.T_ground[:, None] ** 4))
    T_sink = (q_env / (tcs.radiator_emissivity * SIGMA)) ** 0.25
    return T_sink                       # (n_t, n_sides)


def evaluate_thermal_control(res, tcs):
    env = res.env
    T_sink = radiator_sink(env, tcs)
    nside = T_sink.shape[1]
    A_side = tcs.radiator_area_m2 / nside
    eps = tcs.radiator_emissivity
    Te = tcs.cabin_loop_temperature_C + KELVIN - tcs.approach_K
    Qc = res.Q_cooling_W + res.Q_latent_W            # latent heat also ends in the coolant loop
    W = np.zeros(env.n)
    T_r = np.zeros(env.n)
    cop = np.full(env.n, np.inf)
    for n in range(env.n):
        ts4 = T_sink[n] ** 4
        if Qc[n] <= 0:
            T_r[n] = (ts4.mean()) ** 0.25
            continue
        Tp = ((Qc[n] / (A_side * eps * SIGMA) + ts4.sum()) / nside) ** 0.25
        if Tp + tcs.approach_K <= Te + tcs.approach_K:   # passive rejection possible
            T_r[n] = Tp
            continue

        def f(Tr):
            c = tcs.carnot_fraction * Te / max(Tr + tcs.approach_K - Te, 1e-3)
            return A_side * eps * SIGMA * np.sum(Tr ** 4 - ts4) - Qc[n] * (1 + 1 / c)

        # f(Te - approach) < 0 because rejection there is below Qc; for a two-sided radiator the
        # root may lie below the sunlit side's sink (that side then absorbs while the other rejects).
        Tr = brentq(f, Te - tcs.approach_K, 900.0)
        c = tcs.carnot_fraction * Te / max(Tr + tcs.approach_K - Te, 1e-3)
        T_r[n] = Tr
        cop[n] = c
        W[n] = Qc[n] / c
    res.electric_W = res.Q_heating_W / tcs.heating_cop + W + tcs.pump_fan_W
    res.radiator_T_K = T_r
    res.radiator_sink_K = T_sink.mean(axis=1)
    res.cop_cooling = cop
    return res
