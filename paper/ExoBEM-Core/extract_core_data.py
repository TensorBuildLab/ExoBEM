"""Collect the ExoBEM-Core (C++) verification results used by the ExoBEM-Core and combined manuscripts.

    set EXOBEM_CORE=<ExoBEM-Core checkout>      (default ../exo-fork)
    set EXOBEM_CORE_RUNS=<run folder>            (default ../exo-runs; contains moon/out and mars/out)
    python paper/ExoBEM-Core/extract_core_data.py

Writes paper/ExoBEM-Core/data/core_<case>_hourly.csv (hourly C++ and Python series) and paper/ExoBEM-Core/data/core_summary.json.
The papers are then built from these files only, so the fork does not have to be present.
"""
from __future__ import annotations

import csv
import json
import os
import sqlite3
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CORE = Path(os.environ.get("EXOBEM_CORE", ROOT.parent / "exo-fork"))
RUNS = Path(os.environ.get("EXOBEM_CORE_RUNS", ROOT.parent / "exo-runs"))
OUT = HERE / "data"

CASES = {"moon_equator": "moon", "mars_jezero": "mars"}


def sql_series(db, name, key=None):
    q = ("SELECT rd.Value FROM ReportData rd JOIN ReportDataDictionary d ON rd.ReportDataDictionaryIndex=d.ReportDataDictionaryIndex "
         "JOIN Time t ON rd.TimeIndex=t.TimeIndex WHERE d.Name=? AND (t.WarmupFlag=0 OR t.WarmupFlag IS NULL) "
         "AND t.EnvironmentPeriodIndex=(SELECT MAX(EnvironmentPeriodIndex) FROM Time)")
    args = [name]
    if key is not None:
        q += " AND UPPER(d.KeyValue)=UPPER(?)"
        args.append(key)
    q += " ORDER BY rd.TimeIndex"
    return np.array([r[0] for r in db.execute(q, args)], float)


def hourly(x, sph):
    n = len(x) // sph
    return x[: n * sph].reshape(n, sph).mean(axis=1)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {}
    for case, run in CASES.items():
        ref = np.load(CORE / "planetary" / "cases" / case / "python_ref.npz")
        sph = int(round(3600.0 / (ref["time_s"][1] - ref["time_s"][0])))
        names = [str(n) for n in ref["names"]]
        i = names.index("shell_00")
        db = sqlite3.connect(RUNS / run / "out" / "eplusout.sql")
        zone = db.execute("SELECT ZoneName FROM Zones").fetchone()[0]
        ep = dict(
            Qc=sql_series(db, "Zone Ideal Loads Zone Sensible Cooling Rate"),
            Tz=sql_series(db, "Zone Mean Air Temperature", zone),
            Tg=sql_series(db, "Site Planetary Ground Surface Temperature"),
            Tsky=sql_series(db, "Site Sky Temperature"),
            Tair=sql_series(db, "Site Outdoor Air Drybulb Temperature"),
            beam=sql_series(db, "Site Direct Solar Radiation Rate per Area"),
            dif=sql_series(db, "Site Diffuse Solar Radiation Rate per Area"),
            alt=sql_series(db, "Site Solar Altitude Angle"),
            top=sql_series(db, "Surface Outside Face Temperature", "SHELL_00"),
            tin=sql_series(db, "Surface Inside Face Temperature", "SHELL_00"),
            hin=sql_series(db, "Surface Inside Face Convection Heat Transfer Coefficient", "SHELL_00"),
            hout=sql_series(db, "Surface Outside Face Convection Heat Transfer Coefficient", "SHELL_00"),
        )
        py = dict(
            Qc=hourly(ref["Q_cooling_W"], sph), Tz=hourly(ref["T_zone_C"], sph),
            Tg=hourly(ref["T_ground"] - 273.15, sph), Tsky=hourly(ref["T_sky"] - 273.15, sph),
            Tair=hourly(ref["T_air"] - 273.15, sph),
            beam=hourly(ref["dni"], sph), dif=hourly(ref["dhi"], sph), alt=hourly(90.0 - ref["zenith"], sph),
            top=hourly(ref["T_outside_C"][:, i], sph), tin=hourly(ref["T_inside_C"][:, i], sph),
            hin=hourly(ref["h_conv_in"][:, i], sph), hout=hourly(ref["h_conv_out"][:, i], sph),
        )
        n = min(len(ep["Qc"]), len(py["Qc"]))
        cols = ["hour"] + [f"{s}_{k}" for k in ep for s in ("cpp", "py")]
        with open(OUT / f"core_{case}_hourly.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            for h in range(n):
                w.writerow([h] + [f"{d[k][h]:.6g}" for k in ep for d in (ep, py)])
        cmp = json.loads((CORE / "planetary" / "cases" / case / "comparison.json").read_text())
        summary[case] = dict(hours_total=n, steps_per_hour=sph, comparison=cmp)
        print(case, n, "hours")
    summary["meta"] = dict(source="ExoBEM-Core M1 (branch exobem-core, commit f17b0171d) and Python ExoBEM v0.1",
                           moon_window="second lunation (hours 696-1416 of the run)", mars_window="days 16-31")
    (OUT / "core_summary.json").write_text(json.dumps(summary, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
