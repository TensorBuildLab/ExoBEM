"""Comparative verification: ExoBEM (Earth mode) vs EnergyPlus 23.2.

Usage:  python verification/compare_energyplus.py [path/to/energyplus/runs]
Requires the EnergyPlus runs produced by verification/energyplus/run_all.ps1 (or the
bash loop in the README).  Writes verification/results/*.json/csv and figures.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from exobem import simulate  # noqa: E402
from exobem.cases import bestest_600_opaque  # noqa: E402
from exobem.environment.sites import earth_from_epw  # noqa: E402

EPW = Path("C:/EnergyPlusV23-2-0/WeatherData/USA_CO_Golden-NREL.724666_TMY3.epw")
RUNS = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "verification" / "energyplus" / "runs"
OUT = ROOT / "verification" / "results"


def read_eplus_csv(path):
    with open(path, newline="") as f:
        r = csv.reader(f)
        hdr = next(r)
        rows = list(r)
    cols = {h.strip(): i for i, h in enumerate(hdr)}

    def col(substr, freq="TimeStep"):
        keys = [k for k in cols if substr.upper() in k.upper() and f"({freq})".upper() in k.upper()]
        if not keys:
            return None
        i = cols[keys[0]]
        v = np.array([float(row[i]) if row[i].strip() else np.nan for row in rows])
        return v[~np.isnan(v)]
    return col


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    env = earth_from_epw(str(EPW), dt=600.0, n_days=365)
    # 30-day warm-up (EnergyPlus also warms up on the first day until convergence)
    report = {}
    series = {}
    for case, heavy in (("600", False), ("900", True)):
        for ff in (False, True):
            name = f"Case{case}{'FF' if ff else ''}_opaque"
            model = bestest_600_opaque(free_float=ff, heavy=heavy)
            # warm-up: run December first, then the year
            res = simulate(model, env)
            # second pass starting from the end state is approximated by re-running with the
            # initial temperature equal to the year-end zone temperature
            model.zone.initial_temperature_C = float(res.T_zone_C[-1])
            res = simulate(model, env)
            ep = read_eplus_csv(RUNS / name / "eplusout.csv")
            Tz_ep = ep("ZONE1:Zone Mean Air Temperature")
            ex_T = res.T_zone_C
            d = dict(exobem_wall_time_s=res.wall_time_s)
            if not ff:
                Qh_ep = ep("Zone Ideal Loads Zone Sensible Heating Rate")
                Qc_ep = ep("Zone Ideal Loads Zone Sensible Cooling Rate")
                dt_h = 600.0 / 3600.0
                d.update(
                    eplus_heating_kWh=float(Qh_ep.sum() * dt_h / 1000), exobem_heating_kWh=float(res.Q_heating_W.sum() * dt_h / 1000),
                    eplus_cooling_kWh=float(Qc_ep.sum() * dt_h / 1000), exobem_cooling_kWh=float(res.Q_cooling_W.sum() * dt_h / 1000),
                    eplus_peak_heating_W=float(Qh_ep.max()), exobem_peak_heating_W=float(res.Q_heating_W.max()),
                    eplus_peak_cooling_W=float(Qc_ep.max()), exobem_peak_cooling_W=float(res.Q_cooling_W.max()),
                )
                # hourly load comparison
                qh = (res.Q_heating_W - res.Q_cooling_W).reshape(-1, 6).mean(1)
                qe = (Qh_ep - Qc_ep).reshape(-1, 6).mean(1)
                d["hourly_net_load_RMSE_W"] = float(np.sqrt(np.mean((qh - qe) ** 2)))
                d["hourly_net_load_MBE_W"] = float(np.mean(qh - qe))
                d["hourly_net_load_CVRMSE_pct"] = float(100 * np.sqrt(np.mean((qh - qe) ** 2)) / np.mean(np.abs(qe)))
                d["hourly_net_load_R2"] = float(1 - np.sum((qh - qe) ** 2) / np.sum((qe - qe.mean()) ** 2))
                series[name] = dict(exobem=qh, eplus=qe)
            else:
                d.update(eplus_Tmin=float(Tz_ep.min()), exobem_Tmin=float(ex_T.min()),
                         eplus_Tmax=float(Tz_ep.max()), exobem_Tmax=float(ex_T.max()),
                         eplus_Tmean=float(Tz_ep.mean()), exobem_Tmean=float(ex_T.mean()),
                         T_RMSE_K=float(np.sqrt(np.mean((ex_T - Tz_ep) ** 2))),
                         T_MBE_K=float(np.mean(ex_T - Tz_ep)),
                         T_R2=float(1 - np.sum((ex_T - Tz_ep) ** 2) / np.sum((Tz_ep - Tz_ep.mean()) ** 2)))
                series[name] = dict(exobem=ex_T, eplus=Tz_ep)
            report[name] = d
            print(name, json.dumps(d, indent=1))
    (OUT / "energyplus_comparison.json").write_text(json.dumps(report, indent=2))
    np.savez_compressed(OUT / "energyplus_comparison_series.npz",
                        **{f"{k}_{s}": v for k, dd in series.items() for s, v in dd.items()})
    return report


if __name__ == "__main__":
    main()
