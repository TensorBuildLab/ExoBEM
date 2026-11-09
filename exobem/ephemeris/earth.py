"""Earth solar position (NOAA / Meeus low-precision algorithm, ~0.01 deg)."""
from __future__ import annotations

import numpy as np

from . import SunPosition, horizontal_geometry


def sun_ecliptic(jd_utc):
    """Apparent ecliptic longitude of the Sun [deg] and Earth-Sun distance [AU]."""
    T = (np.asarray(jd_utc, dtype=float) - 2451545.0) / 36525.0
    L0 = (280.46646 + 36000.76983 * T + 0.0003032 * T**2) % 360.0
    M = np.radians((357.52911 + 35999.05029 * T - 0.0001537 * T**2) % 360.0)
    e = 0.016708634 - 0.000042037 * T
    C = ((1.914602 - 0.004817 * T - 0.000014 * T**2) * np.sin(M)
         + (0.019993 - 0.000101 * T) * np.sin(2 * M) + 0.000289 * np.sin(3 * M))
    true_long = L0 + C
    nu = M + np.radians(C)
    r = 1.000001018 * (1 - e**2) / (1 + e * np.cos(nu))
    omega = 125.04 - 1934.136 * T
    lam = true_long - 0.00569 - 0.00478 * np.sin(np.radians(omega))
    return lam % 360.0, r


def sun_equatorial(jd_utc):
    T = (np.asarray(jd_utc, dtype=float) - 2451545.0) / 36525.0
    lam, r = sun_ecliptic(jd_utc)
    omega = 125.04 - 1934.136 * T
    eps0 = 23.0 + (26.0 + (21.448 - T * (46.815 + T * (0.00059 - T * 0.001813))) / 60.0) / 60.0
    eps = np.radians(eps0 + 0.00256 * np.cos(np.radians(omega)))
    lr = np.radians(lam)
    decl = np.degrees(np.arcsin(np.sin(eps) * np.sin(lr)))
    # equation of time (minutes), NOAA formulation
    L0 = np.radians((280.46646 + 36000.76983 * T) % 360.0)
    M = np.radians((357.52911 + 35999.05029 * T) % 360.0)
    e = 0.016708634 - 0.000042037 * T
    y = np.tan(eps / 2) ** 2
    eot = 4 * np.degrees(y * np.sin(2 * L0) - 2 * e * np.sin(M) + 4 * e * y * np.sin(M) * np.cos(2 * L0)
                         - 0.5 * y * y * np.sin(4 * L0) - 1.25 * e * e * np.sin(2 * M))
    return decl, eot, r


def sun_position(jd_utc, lat_deg, lon_east_deg) -> SunPosition:
    jd = np.asarray(jd_utc, dtype=float)
    decl, eot_min, r = sun_equatorial(jd)
    utc_min = ((jd + 0.5) % 1.0) * 1440.0
    true_solar_min = (utc_min + eot_min + 4.0 * lon_east_deg) % 1440.0
    H = true_solar_min / 4.0 - 180.0
    zen, az = horizontal_geometry(lat_deg, decl, H)
    return SunPosition(zen, az, r, decl, H, dict(eot_min=eot_min))
