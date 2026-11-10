"""Calibrate the effective MLI resistance of the lunar Surface Habitat to NASA's thermal analysis.

Schunk et al. (2022, IEEE Aerospace, doi:10.1109/AERO53065.2022.9843698) report for the Artemis lunar
Surface Habitat a night-time heat leak of about 1550 W with the cabin at 293 K, and a daylight net loss of
about 850 W.  The night value calibrates the effective resistance of the 10-layer MLI; the daylight value
is then an independent check.

    python studies/calibrate_lunar_mli.py   -> studies/results/lunar_mli_calibration.json
"""
from __future__ import annotations

import copy
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from exobem import simulate  # noqa: E402
from exobem.cases import artemis_surface_habitat  # noqa: E402
from exobem.environment.sites import moon_site  # noqa: E402
from exobem.model import Thermostat  # noqa: E402

OUT = ROOT / "studies" / "results"
T_CABIN_C = 293.15 - 273.15
NIGHT_TARGET_W, DAY_TARGET_W = 1550.0, 850.0


def envelope_loss(env, mli_R):
    """Heat lost through the envelope [W] with the cabin held at 293 K and no internal gains."""
    m = artemis_surface_habitat(dt=env.dt, mli_R=mli_R)
    m.zone.gains = []
    m.zone.leakage_kg_per_day = 0.0
    m.zone.airlock_cycles_per_day = 0.0
    m.zone.internal_mass = []
    m.zone.humidity_control = False
    m.zone.thermostat = Thermostat(T_CABIN_C, T_CABIN_C)
    m.thermal_control = None
    r = simulate(m, env)
    return r.Q_heating_W - r.Q_cooling_W


def main():
    # south-polar site: one year at 2 h steps, then pick steady dark and steady sunlit stretches
    env = moon_site(-89.45, -137.3, dt.datetime(2030, 1, 1), 360.0, dt=7200.0, horizon=([0, 360], [-1.0, -1.0]))
    sun = env.dni > 1.0
    # mask the first 3 days of each period (thermal settling of the shell)
    def settled(mask, hours=72):
        k = int(hours * 3600 / env.dt)
        out = mask.copy()
        run = 0
        for i, v in enumerate(mask):
            run = run + 1 if v else 0
            out[i] = v and run > k
        return out
    night, day = settled(~sun), settled(sun)

    def night_loss(R):
        return float(envelope_loss(env, R)[night].mean())

    R = brentq(lambda R: night_loss(R) - NIGHT_TARGET_W, 0.5, 40.0, xtol=0.01)
    q = envelope_loss(env, R)
    res = dict(mli_R_m2K_W=R, night_loss_W=float(q[night].mean()), day_loss_W=float(q[day].mean()),
               night_target_W=NIGHT_TARGET_W, day_target_W=DAY_TARGET_W,
               day_error_pct=100 * (float(q[day].mean()) / DAY_TARGET_W - 1),
               night_hours=float(night.sum() * env.dt / 3600), day_hours=float(day.sum() * env.dt / 3600),
               site="Moon, 89.45 S 137.3 W (Connecting Ridge area), uniform horizon -1 deg, year 2030")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "lunar_mli_calibration.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
