"""Collect the Thermonaut (C++) verification results used by the Thermonaut and combined manuscripts.

    set THERMONAUT=<Thermonaut checkout>      (default ../exo-fork)
    set THERMONAUT_RUNS=<run folder>            (default ../exo-runs/m2d; contains <case>_pwf and <case>_gen run folders
                                                  with eplusout.sql and the comparison.json written by planetary/cases/compare.py)
    python paper/Thermonaut/extract_thermonaut_data.py

Writes paper/Thermonaut/data/core_<case>_hourly.csv (hourly C++ and Python series) and paper/Thermonaut/data/core_summary.json.
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
CORE = Path(os.environ.get("THERMONAUT", ROOT.parent / "exo-fork"))
RUNS = Path(os.environ.get("THERMONAUT_RUNS", ROOT.parent / "exo-runs" / "m2d"))
OUT = HERE / "data"

CASES = {"moon_equator": "moon_equator_pwf", "mars_jezero": "mars_jezero_pwf"}


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
        db = sqlite3.connect(RUNS / run / "eplusout.sql")
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
        # environment from the engine's own generator (no weather file): tests the C++ port of the models
        dbg = sqlite3.connect(RUNS / f"{case}_gen" / "eplusout.sql")
        eg = dict(Tg=sql_series(dbg, "Site Planetary Ground Surface Temperature"), Tsky=sql_series(dbg, "Site Sky Temperature"),
                  beam=sql_series(dbg, "Site Direct Solar Radiation Rate per Area"),
                  dif=sql_series(dbg, "Site Diffuse Solar Radiation Rate per Area"), alt=sql_series(dbg, "Site Solar Altitude Angle"))
        with open(OUT / f"core_{case}_gen_hourly.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["hour"] + [f"{s}_{k}" for k in eg for s in ("cpp", "py")])
            for h in range(n):
                w.writerow([h] + [f"{d[k][h]:.6g}" for k in eg for d in (eg, py)])
        cmp = json.loads((RUNS / f"{case}_pwf" / "comparison.json").read_text())
        cmp_gen = json.loads((RUNS / f"{case}_gen" / "comparison.json").read_text())
        summary[case] = dict(hours_total=n, steps_per_hour=sph, comparison=cmp, comparison_generator=cmp_gen)
        print(case, n, "hours")
    # NASA-class lunar habitat: hourly C++ and Python series
    hd = CORE / "planetary" / "cases" / "lunar_habitat"
    ref = np.load(hd / "python_ref.npz")
    db = sqlite3.connect(hd / "out" / "eplusout.sql")
    names = [str(n) for n in ref["names"]]
    sph = 20
    ep = dict(Qc=sql_series(db, "Zone Ideal Loads Zone Sensible Cooling Rate"), Ql=sql_series(db, "Zone Ideal Loads Zone Latent Cooling Rate"),
              rh=sql_series(db, "Zone Air Relative Humidity") / 100.0,
              To_s=sql_series(db, "Surface Outside Face Temperature", "WALL_05"), To_f=sql_series(db, "Surface Outside Face Temperature", "FLOOR"),
              Ti_s=sql_series(db, "Surface Inside Face Temperature", "WALL_05"))
    py = dict(Qc=hourly(ref["Q_cooling_W"], sph), Ql=hourly(ref["Q_latent_W"], sph), rh=hourly(ref["rh"], sph),
              To_s=hourly(ref["T_outside_C"][:, names.index("wall_05")], sph), To_f=hourly(ref["T_outside_C"][:, names.index("floor")], sph),
              Ti_s=hourly(ref["T_inside_C"][:, names.index("wall_05")], sph))
    n = min(len(ep["Qc"]), len(py["Qc"]))
    with open(OUT / "core_lunar_habitat_hourly.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["hour"] + [f"{s_}_{k}" for k in ep for s_ in ("cpp", "py")])
        for h in range(n):
            w.writerow([h] + [f"{d[k][h]:.6g}" for k in ep for d in (ep, py)])
    summary["lunar_habitat"] = json.loads((CORE / "planetary" / "cases" / "lunar_habitat" / "comparison.json").read_text())
    summary["pv_vacuum"] = json.loads((CORE / "planetary" / "cases" / "pv_vacuum" / "pv_vacuum_check.json").read_text())
    # checks against independent references (JPL Horizons, Diviner) and closed-form boundary balances
    cases = CORE / "planetary" / "cases"
    summary["horizons"] = json.loads((cases / "horizons" / "horizons_check.json").read_text())
    summary["boundary"] = json.loads((cases / "boundary_check.json").read_text())
    summary["moon_regolith"] = json.loads((cases / "moon_regolith_check.json").read_text())
    summary["meta"] = dict(source="Thermonaut M2d (branch thermonaut) and Python ExoBEM v0.2",
                           moon_window="second lunation (720 h)", mars_window="days 16-31 (384 h)",
                           modes="comparison = engine reading the PWF file; comparison_generator = engine's own environment generator")
    (OUT / "core_summary.json").write_text(json.dumps(summary, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
