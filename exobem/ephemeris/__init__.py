"""Solar ephemerides for Earth, the Moon and Mars.

Every ephemeris exposes ``sun_position(jd_utc, lat_deg, lon_east_deg)`` that returns
a :class:`SunPosition` (zenith, azimuth from north clockwise, and Sun distance in AU)
so the rest of the engine is planet-agnostic.
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class SunPosition:
    zenith_deg: np.ndarray
    azimuth_deg: np.ndarray      # clockwise from local north
    distance_au: np.ndarray
    declination_deg: np.ndarray  # planetocentric solar declination / subsolar latitude
    hour_angle_deg: np.ndarray   # local solar hour angle, positive in the afternoon
    extra: dict

    @property
    def elevation_deg(self):
        return 90.0 - self.zenith_deg


def horizontal_geometry(lat_deg, decl_deg, hour_angle_deg):
    """Zenith and azimuth (N=0, E=90) from latitude, declination and hour angle."""
    lat = np.radians(lat_deg)
    dec = np.radians(decl_deg)
    H = np.radians(hour_angle_deg)
    cosz = np.sin(lat) * np.sin(dec) + np.cos(lat) * np.cos(dec) * np.cos(H)
    cosz = np.clip(cosz, -1.0, 1.0)
    zen = np.arccos(cosz)
    # azimuth measured clockwise from north
    sin_az = -np.cos(dec) * np.sin(H)
    cos_az = (np.sin(dec) * np.cos(lat) - np.cos(dec) * np.sin(lat) * np.cos(H))
    az = np.degrees(np.arctan2(sin_az, cos_az)) % 360.0
    return np.degrees(zen), az


def jd_from_datetime(dt):
    """Julian date (UTC) of a timezone-aware or naive-UTC :class:`datetime`."""
    import datetime as _dt
    if dt.tzinfo is not None:
        dt = dt.astimezone(_dt.timezone.utc).replace(tzinfo=None)
    epoch = _dt.datetime(2000, 1, 1, 12, 0, 0)
    return 2451545.0 + (dt - epoch).total_seconds() / 86400.0
