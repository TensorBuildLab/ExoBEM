"""Low-precision selenographic solar coordinates.

The subsolar point on the Moon is obtained from mean lunar elements (Meeus, 1998,
*Astronomical Algorithms*, ch. 22, 25 and 47) and Cassini's laws:

* The lunar prime meridian points, on average, toward the Earth, i.e. it follows the
  Moon's *mean* geocentric longitude L'.  The Sun's selenocentric ecliptic longitude
  is (to <0.15 deg) the Sun's geocentric apparent longitude lambda_sun.  The subsolar
  selenographic longitude is therefore 180 deg - (L' - lambda_sun).  Using the mean
  (not true) lunar longitude automatically accounts for the optical libration in
  longitude, which can shift local solar time by ~0.5 Earth day.
* The lunar equator is inclined I = 1.5424 deg to the ecliptic and its descending
  node coincides with the ascending node Omega of the orbit, so the subsolar latitude
  is  b_sun = I sin(lambda_sun - Omega)  (period: one eclipse year, 346.62 d).

Accuracy is ~0.3 deg in subsolar longitude/latitude, which corresponds to ~35 min of
lunar local time - ample for building-energy work.
"""
from __future__ import annotations

import numpy as np

from . import SunPosition, horizontal_geometry
from .earth import sun_ecliptic

LUNAR_INCLINATION_DEG = 1.5424
SYNODIC_MONTH_DAYS = 29.530588853


def subsolar_point(jd_utc):
    T = (np.asarray(jd_utc, dtype=float) - 2451545.0) / 36525.0
    Lp = (218.3164477 + 481267.88123421 * T - 0.0015786 * T**2) % 360.0
    Om = (125.0445479 - 1934.1362891 * T + 0.0020754 * T**2) % 360.0
    lam_sun, r_au = sun_ecliptic(jd_utc)
    lon_ss = (180.0 - (Lp - lam_sun)) % 360.0
    lon_ss = np.where(lon_ss > 180.0, lon_ss - 360.0, lon_ss)
    lat_ss = LUNAR_INCLINATION_DEG * np.sin(np.radians(lam_sun - Om))
    # Sun-Moon distance ~ Sun-Earth distance (+/- 0.0026 AU); keep Earth value.
    return lon_ss, lat_ss, r_au


def sun_position(jd_utc, lat_deg, lon_east_deg) -> SunPosition:
    lon_ss, lat_ss, r = subsolar_point(jd_utc)
    H = (lon_east_deg - lon_ss + 180.0) % 360.0 - 180.0  # + afternoon
    zen, az = horizontal_geometry(lat_deg, lat_ss, H)
    lunar_local_time_h = 12.0 + H / 15.0  # in "lunar hours" (1/24 of a synodic day)
    return SunPosition(zen, az, r, lat_ss, H, dict(subsolar_lon=lon_ss,
                                                   lunar_time_h=lunar_local_time_h))
