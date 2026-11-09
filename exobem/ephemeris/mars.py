"""Mars solar coordinates after Allison & McEwen (2000), as implemented in NASA GISS Mars24.

Reference: Allison, M., McEwen, M. (2000). A post-Pathfinder evaluation of areocentric
solar coordinates with improved timing recipes for Mars seasonal/diurnal climate
studies. Planetary and Space Science 48, 215-235. doi:10.1016/S0032-0633(99)00092-6
and the Mars24 algorithm notes (https://www.giss.nasa.gov/tools/mars24/help/algorithm.html).

Longitudes are planetocentric, east-positive (IAU 2000 convention).
"""
from __future__ import annotations

import numpy as np

from . import SunPosition, horizontal_geometry

MARS_SOL_SECONDS = 88775.244147
TT_MINUS_UTC = 69.184  # seconds, valid since 2017-01-01 (37 leap s + 32.184 s)

_A = np.array([0.0071, 0.0057, 0.0039, 0.0037, 0.0021, 0.0020, 0.0018])
_TAU = np.array([2.2353, 2.7543, 1.1177, 15.7866, 2.1354, 2.4694, 32.8493])
_PHI = np.array([49.409, 168.173, 191.837, 21.736, 15.704, 95.528, 49.095])


def _dt_j2000(jd_utc, tt_minus_utc=TT_MINUS_UTC):
    jd_tt = np.asarray(jd_utc, dtype=float) + tt_minus_utc / 86400.0
    return jd_tt - 2451545.0, jd_tt


def areocentric(jd_utc, tt_minus_utc=TT_MINUS_UTC):
    """Return dict with M, alpha_FMS, nu-M, Ls, EOT (deg), declination (deg), r (AU), MST (h)."""
    dt, jd_tt = _dt_j2000(jd_utc, tt_minus_utc)
    M = np.radians((19.3871 + 0.52402073 * dt) % 360.0)
    alpha_fms = (270.3871 + 0.524038496 * dt) % 360.0
    dt_ = np.atleast_1d(dt)[..., None]
    pbs = np.sum(_A * np.cos(np.radians(0.985626 * dt_ / _TAU + _PHI)), axis=-1)
    pbs = pbs.reshape(np.shape(dt))
    nu_m = ((10.691 + 3.0e-7 * dt) * np.sin(M) + 0.623 * np.sin(2 * M)
            + 0.050 * np.sin(3 * M) + 0.005 * np.sin(4 * M)
            + 0.0005 * np.sin(5 * M) + pbs)
    Ls = (alpha_fms + nu_m) % 360.0
    Lr = np.radians(Ls)
    eot = (2.861 * np.sin(2 * Lr) - 0.071 * np.sin(4 * Lr)
           + 0.002 * np.sin(6 * Lr) - nu_m)  # degrees
    decl = np.degrees(np.arcsin(0.42565 * np.sin(Lr))) + 0.25 * np.sin(Lr)
    r = 1.52367934 * (1.00436 - 0.09309 * np.cos(M) - 0.004336 * np.cos(2 * M)
                      - 0.00031 * np.cos(3 * M) - 0.00003 * np.cos(4 * M))
    mst = (24.0 * (((jd_tt - 2451549.5) / 1.0274912517) + 44796.0 - 0.0009626)) % 24.0
    msd = ((jd_tt - 2451549.5) / 1.0274912517) + 44796.0 - 0.0009626
    return dict(M_deg=np.degrees(M), alpha_fms=alpha_fms, nu_minus_M=nu_m, Ls=Ls,
                eot_deg=eot, decl_deg=decl, r_au=r, mst_h=mst, mars_sol_date=msd)


def local_true_solar_time(jd_utc, lon_east_deg, tt_minus_utc=TT_MINUS_UTC):
    a = areocentric(jd_utc, tt_minus_utc)
    lmst = (a["mst_h"] + lon_east_deg / 15.0) % 24.0
    ltst = (lmst + a["eot_deg"] / 15.0) % 24.0
    return ltst, lmst, a


def sun_position(jd_utc, lat_deg, lon_east_deg, tt_minus_utc=TT_MINUS_UTC) -> SunPosition:
    ltst, lmst, a = local_true_solar_time(jd_utc, lon_east_deg, tt_minus_utc)
    H = (ltst - 12.0) * 15.0  # hour angle, + afternoon
    zen, az = horizontal_geometry(lat_deg, a["decl_deg"], H)
    return SunPosition(zen, az, a["r_au"], a["decl_deg"], H,
                       dict(Ls=a["Ls"], ltst_h=ltst, lmst_h=lmst, msd=a["mars_sol_date"]))
