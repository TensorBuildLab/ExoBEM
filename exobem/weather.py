"""Planetary Weather Format (PWF): a documented text format for planetary site environments.

PWF plays the role that the EPW weather file plays for EnergyPlus, without EPW's Earth
assumptions (8760 one-hour records, a 24-hour day, Earth range checks, an atmosphere).
A PWF file is plain CSV preceded by ``#`` header lines; it is written by ExoBEM's
environment generators (``exobem weather ...``) and read by ExoBEM and by ExoBEM-Core.

Layout (full specification: docs/weather_format.md)::

    # PWF 1.0
    # body: mars
    # site_name: Jezero crater
    # latitude_deg: 18.44
    # longitude_deg: 77.45            (planetocentric, east positive)
    # start_utc: 2030-01-01T00:00:00
    # timestep_s: 1800
    # n_records: 1488
    # solar_day_s: 88775.244147
    # gravity_m_s2: 3.721
    # atmosphere: mars_co2            (none | mars_co2 | earth_air)
    # clock: mars_lmst                (what local_time_h means: earth_utc | mars_lmst | earth_local)
    # sky_includes_air: false
    # generator: exobem 0.2.0 mars_site(...)
    time_s,local_time_h,day_index,zenith_deg,...
    1800,13.42,0,...

Conventions
-----------
* ``time_s`` is the END of each record's interval, counted from ``start_utc``; records are
  equally spaced by ``timestep_s``.
* Solar quantities (zenith, azimuth, irradiances, sun_visible) are evaluated at the
  MIDDLE of the interval; state quantities (temperatures, pressure, wind) at its END.
* Temperatures in K, irradiances in W/m2, pressure in Pa, angles in degrees, azimuth
  clockwise from north.  Missing or not-applicable values are written ``nan`` (for
  example the air temperature in vacuum).
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import numpy as np

from . import gas as _gas
from .constants import T_CMB

PWF_VERSION = "1.0"

# column name -> (Environment attribute or extra key, unit, description, required)
COLUMNS = [
    ("time_s", "time_s", "s", "end of the record interval, seconds since start_utc", True),
    ("local_time_h", "local_time_h", "h", "clock hour used by schedules (see header 'clock')", True),
    ("day_index", "day_index", "-", "integer day (Earth day or sol) used by schedules", True),
    ("zenith_deg", "zenith", "deg", "solar zenith angle at interval middle", True),
    ("sun_azimuth_deg", "sun_azimuth", "deg", "solar azimuth, clockwise from north", True),
    ("sun_visible", "sun_visible", "-", "fraction of the solar disk above the local horizon", True),
    ("dni_W_m2", "dni", "W/m2", "direct (beam) normal irradiance", True),
    ("dhi_W_m2", "dhi", "W/m2", "diffuse horizontal irradiance", True),
    ("ghi_W_m2", "ghi", "W/m2", "global horizontal irradiance", True),
    ("T_air_K", "T_air", "K", "near-surface air temperature (nan in vacuum)", True),
    ("T_sky_K", "T_sky", "K", "effective sky temperature for long-wave exchange", True),
    ("T_ground_K", "T_ground", "K", "ground (regolith) surface temperature", True),
    ("T_deep_K", "T_deep", "K", "deep-ground temperature for ground-contact surfaces", True),
    ("ground_albedo", "ground_albedo", "-", "ground solar reflectance", True),
    ("pressure_Pa", "pressure", "Pa", "ambient (outdoor) pressure, 0 in vacuum", True),
    ("wind_m_s", "wind_speed", "m/s", "wind speed at measurement height", True),
    ("wind_dir_deg", "wind_dir", "deg", "wind direction, clockwise from north", True),
    ("L_down_W_m2", "x:L_down", "W/m2", "downwelling long-wave radiation (optional)", False),
    ("Ls_deg", "x:Ls", "deg", "areocentric solar longitude, Mars (optional)", False),
    ("dust_tau", "x:tau", "-", "column dust optical depth, Mars (optional)", False),
    ("ltst_h", "x:ltst_h", "h", "local true solar time, Mars (optional)", False),
    ("lunar_local_time_h", "x:lunar_local_time_h", "h", "lunar local solar time (optional)", False),
    ("humidity_ratio", "humidity_ratio", "kg/kg", "outdoor humidity ratio, Earth (optional)", False),
]

GASES = {"none": None, "mars_co2": _gas.MARS_CO2, "earth_air": _gas.DRY_AIR}


def _gas_name(gas):
    if gas is None:
        return "none"
    for k, v in GASES.items():
        if v is not None and v.name == gas.name:
            return k
    raise ValueError(f"no PWF name for gas {gas.name}")


def _clock(env):
    if env.planet == "moon":
        return "earth_utc"
    if env.planet == "mars":
        return "mars_lmst"
    return "earth_local"


def write_pwf(env, path, site_name: str = "", start_utc=None, generator: str = "", horizon=None):
    """Write an :class:`~exobem.environment.Environment` to a PWF file."""
    from . import __version__
    if start_utc is None:
        start_utc = env.extra.get("start_utc")
    if start_utc is None:
        raise ValueError("start_utc is required (datetime)")
    if isinstance(start_utc, _dt.datetime):
        start_utc = start_utc.strftime("%Y-%m-%dT%H:%M:%S")
    head = {
        "body": env.planet, "site_name": site_name, "latitude_deg": f"{env.latitude:.6f}",
        "longitude_deg": f"{env.longitude:.6f}", "start_utc": start_utc, "timestep_s": f"{env.dt:g}",
        "n_records": str(env.n), "solar_day_s": f"{env.extra.get('solar_day_s', 86400.0):.6f}",
        "gravity_m_s2": f"{env.gravity:.5f}", "atmosphere": _gas_name(env.gas), "clock": _clock(env),
        "sky_includes_air": "true" if env.sky_includes_air else "false",
        "generator": generator or f"exobem {__version__}",
    }
    if horizon is not None:
        az, el = horizon
        head["horizon_azimuth_deg"] = " ".join(f"{a:g}" for a in az)
        head["horizon_elevation_deg"] = " ".join(f"{e:g}" for e in el)
    cols, data = [], []
    for name, attr, unit, _desc, required in COLUMNS:
        if attr.startswith("x:"):
            v = env.extra.get(attr[2:])
        else:
            v = getattr(env, attr)
        if v is None or (isinstance(v, np.ndarray) and v.shape != env.time_s.shape):
            if required:
                raise ValueError(f"environment lacks required column {name}")
            continue
        cols.append(name)
        data.append(np.asarray(v, float))
    lines = [f"# PWF {PWF_VERSION}"]
    lines += [f"# {k}: {v}" for k, v in head.items()]
    lines.append("# units: " + ",".join(next(u for n, _, u, _, _ in COLUMNS if n == c) for c in cols))
    lines.append(",".join(cols))
    arr = np.column_stack(data)
    for row in arr:
        lines.append(",".join("nan" if not np.isfinite(x) else (f"{x:.0f}" if c in ("time_s", "day_index") else f"{x:.7g}")
                              for x, c in zip(row, cols)))
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return Path(path)


def read_header(path):
    head = {}
    with open(path, encoding="utf-8") as f:
        first = f.readline().strip()
        if not first.startswith("# PWF"):
            raise ValueError(f"{path} is not a PWF file (first line {first!r})")
        head["pwf_version"] = first.split()[2]
        for line in f:
            if not line.startswith("#"):
                break
            k, _, v = line[1:].partition(":")
            head[k.strip()] = v.strip()
    return head


def read_pwf(path):
    """Read a PWF file into an :class:`~exobem.environment.Environment`."""
    from .environment import Environment
    head = read_header(path)
    with open(path, encoding="utf-8") as f:
        lines = [ln for ln in f if not ln.startswith("#")]
    names = lines[0].strip().split(",")
    arr = np.array([[float(x) for x in ln.strip().split(",")] for ln in lines[1:] if ln.strip()])
    col = {n: arr[:, i] for i, n in enumerate(names)}
    for name, _a, _u, _d, required in COLUMNS:
        if required and name not in col:
            raise ValueError(f"{path}: missing required column {name}")
    dt = float(head["timestep_s"])
    t = col["time_s"]
    if len(t) > 1 and np.max(np.abs(np.diff(t) - dt)) > 1e-6 * dt:
        raise ValueError(f"{path}: records are not equally spaced by timestep_s")
    start = _dt.datetime.fromisoformat(head["start_utc"])
    from .ephemeris import jd_from_datetime
    jd0 = jd_from_datetime(start)
    extra = {"solar_day_s": float(head.get("solar_day_s", 86400.0)), "start_utc": start,
             "site_name": head.get("site_name", ""), "pwf_header": head}
    for name, attr, _u, _d, _r in COLUMNS:
        if attr.startswith("x:") and name in col:
            extra[attr[2:]] = col[name]
    atm = head.get("atmosphere", "none")
    if atm not in GASES:
        raise ValueError(f"{path}: unknown atmosphere {atm!r}")
    env = Environment(
        planet=head["body"], latitude=float(head["latitude_deg"]), longitude=float(head["longitude_deg"]), dt=dt,
        time_s=t, jd_utc=jd0 + t / 86400.0, zenith=col["zenith_deg"], sun_azimuth=col["sun_azimuth_deg"],
        dni=col["dni_W_m2"], dhi=col["dhi_W_m2"], ghi=col["ghi_W_m2"], sun_visible=col["sun_visible"],
        T_air=col["T_air_K"], T_sky=col["T_sky_K"], T_ground=col["T_ground_K"], T_deep=col["T_deep_K"],
        wind_speed=col["wind_m_s"], wind_dir=col["wind_dir_deg"], pressure=col["pressure_Pa"],
        ground_albedo=col["ground_albedo"], gravity=float(head["gravity_m_s2"]), gas=GASES[atm],
        humidity_ratio=col.get("humidity_ratio"), local_time_h=col["local_time_h"],
        day_index=col["day_index"].astype(int), sky_includes_air=head.get("sky_includes_air", "false") == "true",
        extra=extra)
    validate(env)
    return env


def validate(env):
    """Physical sanity checks (not Earth range checks): raise ValueError on impossible values."""
    problems = []
    if np.any(env.dni < -1e-9) or np.any(env.dhi < -1e-9) or np.any(env.ghi < -1e-9):
        problems.append("negative irradiance")
    if np.any((env.zenith < 0) | (env.zenith > 180)):
        problems.append("zenith outside 0-180 deg")
    for nm in ("T_sky", "T_ground", "T_deep"):
        v = getattr(env, nm)
        if np.any(v < T_CMB - 1e-6) or np.any(v > 1000):
            problems.append(f"{nm} outside {T_CMB}-1000 K")
    if env.gas is None:
        if np.any(env.pressure != 0):
            problems.append("atmosphere 'none' but non-zero pressure")
    elif np.any(env.pressure <= 0):
        problems.append("atmosphere present but pressure <= 0")
    if np.any((env.sun_visible < -1e-9) | (env.sun_visible > 1 + 1e-9)):
        problems.append("sun_visible outside 0-1")
    if problems:
        raise ValueError("PWF validation failed: " + "; ".join(problems))
    return True


def generate(body: str, latitude: float, longitude: float, start_utc, days: float, timestep_s: float = 1800.0,
             site_name: str = "", **kw):
    """Generate a planetary environment with ExoBEM's models (Moon: days are Earth days;
    Mars: ``days`` is converted to sols)."""
    from .environment import sites
    if isinstance(start_utc, str):
        start_utc = _dt.datetime.fromisoformat(start_utc)
    body = body.lower()
    if body == "moon":
        env = sites.moon_site(latitude, longitude, start_utc, days, dt=timestep_s, **kw)
    elif body == "mars":
        from .ephemeris.mars import MARS_SOL_SECONDS
        env = sites.mars_site(latitude, longitude, start_utc, days * 86400.0 / MARS_SOL_SECONDS, dt=timestep_s, **kw)
    else:
        raise ValueError("generate() supports 'moon' and 'mars'; use earth_from_epw for Earth")
    env.extra["start_utc"] = start_utc
    env.extra["site_name"] = site_name
    return env
