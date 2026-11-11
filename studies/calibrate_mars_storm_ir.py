"""Calibrate the Martian downwelling long-wave model (sky emissivity e0 + e1*tau, dust re-emission f_re).

Targets (observations):
  * clear-season (Ls 30-150) daily-mean downwelling long-wave at Jezero ~30 W/m2 (MEDA/TIRS, Martinez et al. 2023);
  * during the 2018 global dust storm the diurnal-mean air temperature at Gale dropped only ~4 K while the diurnal
    air-temperature range collapsed (Viudez-Moreiras et al. 2019; Guzewich et al. 2019).

A first coarse grid (f_re 0-0.2, e0 0.08-0.2, e1 0.04-0.1) showed the storm-time change of sol-mean air temperature
going from about -36 K (f_re = 0) to -23 K (f_re = 0.2) and +18 K at the previous f_re = 0.45; this grid brackets -4 K.
With e1 = 0.10 the sky emissivity reaches its 0.6 cap at tau >= 5, so e1 matters little for the storm.

The storm case of the paper (tau = 6 between Ls 190 and 270) is compared with the nominal year over the ten sols of
peak opacity.  Writes studies/results/mars_storm_ir_calibration.json.

    python studies/calibrate_mars_storm_ir.py
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "studies"))
from exobem.environment.sites import mars_site  # noqa: E402
from run_case_studies import MARS_JZ, SOL, mars_year_start  # noqa: E402

DT = SOL / 24.0
STORM = dict(storm=(190.0, 270.0, 6.0))


def sol_stats(env):
    i = np.floor((env.time_s - 1e-6) / SOL).astype(int)
    n = i.max()
    mean = np.bincount(i, env.T_air, n + 1)[:n] / np.bincount(i, None, n + 1)[:n]
    rng = np.array([np.ptp(env.T_air[i == k]) for k in range(n)])
    Ls = np.bincount(i, env.extra["Ls"], n + 1)[:n] / np.bincount(i, None, n + 1)[:n]
    return mean, rng, Ls


def evaluate(e0, e1, fre):
    start = mars_year_start(2028)
    kw = dict(sky_emissivity=(e0, e1), dust_reemission=fre)
    nom = mars_site(MARS_JZ["lat"], MARS_JZ["lon"], start, 668.6, dt=DT, **kw)
    sto = mars_site(MARS_JZ["lat"], MARS_JZ["lon"], start, 668.6, dt=DT, tau_kwargs=STORM, **kw)
    Ls = nom.extra["Ls"]
    clear = (Ls > 30) & (Ls < 150)
    mn, rn, Lsol = sol_stats(nom)
    ms, rs, _ = sol_stats(sto)
    peak = np.argsort(np.abs(Lsol - 230.0))[:10]              # ten sols of peak opacity
    return dict(e0=e0, e1=e1, f_re=fre,
                L_clear_mean=float(nom.extra["L_down"][clear].mean()),
                L_annual_mean=float(nom.extra["L_down"].mean()),
                L_min=float(nom.extra["L_down"].min()), L_max=float(nom.extra["L_down"].max()),
                L_storm_max=float(sto.extra["L_down"].max()),
                dT_mean_storm_K=float((ms[peak] - mn[peak]).mean()),
                range_nominal_K=float(rn[peak].mean()), range_storm_K=float(rs[peak].mean()))


def main():
    rows = []
    for e0, e1, fre in itertools.product((0.08, 0.10, 0.12), (0.10,), (0.20, 0.25, 0.30, 0.35)):
        r = evaluate(e0, e1, fre)
        rows.append(r)
        print({k: round(v, 2) for k, v in r.items()}, flush=True)
    for r in rows:
        r["score"] = ((r["L_clear_mean"] - 30.0) / 3.0) ** 2 + ((r["dT_mean_storm_K"] + 4.0) / 2.0) ** 2
    best = min(rows, key=lambda r: r["score"])
    old = evaluate(0.08, 0.125, 0.45)
    out = dict(targets=dict(L_clear_mean_W_m2=30.0, dT_mean_storm_K=-4.0),
               previous=old, best=best, grid=rows)
    (ROOT / "studies" / "results" / "mars_storm_ir_calibration.json").write_text(json.dumps(out, indent=1))
    print("previous", {k: round(v, 2) for k, v in old.items()})
    print("best", {k: round(v, 2) for k, v in best.items()})


if __name__ == "__main__":
    main()
