"""Site environment ("weather") time series for Earth, the Moon and Mars.

An :class:`Environment` plays the role of the EnergyPlus weather file plus the Site
objects.  All arrays have one value per simulation time step (evaluated at the step
midpoint for solar quantities and at the step end for state variables).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class Environment:
    planet: str
    latitude: float
    longitude: float
    dt: float                       # time step [s]
    time_s: np.ndarray              # seconds since start, at step end
    jd_utc: np.ndarray              # Julian date at step end
    zenith: np.ndarray              # deg, at step midpoint
    sun_azimuth: np.ndarray         # deg from north
    dni: np.ndarray                 # beam normal irradiance [W/m2]
    dhi: np.ndarray                 # diffuse horizontal [W/m2]
    ghi: np.ndarray                 # global horizontal [W/m2]
    sun_visible: np.ndarray         # fraction of solar disk above local horizon
    T_air: np.ndarray               # K (NaN in vacuum)
    T_sky: np.ndarray               # effective sky temperature for LW exchange [K]
    T_ground: np.ndarray            # ground (regolith) surface temperature [K]
    T_deep: np.ndarray              # ground temperature at the bottom of ground-contact constructions [K]
    wind_speed: np.ndarray          # m/s at met height (10 m Earth, ~1.5-2 m Mars)
    wind_dir: np.ndarray            # deg
    pressure: np.ndarray            # Pa (0 in vacuum)
    ground_albedo: np.ndarray       # -
    gravity: float                  # m/s2
    gas: Optional[object] = None    # exobem.gas.Gas or None (vacuum)
    humidity_ratio: Optional[np.ndarray] = None   # Earth only
    local_time_h: Optional[np.ndarray] = None     # local (solar / clock) time for schedules
    day_index: Optional[np.ndarray] = None        # integer day (Earth day or sol) for schedules
    sky_includes_air: bool = False  # EnergyPlus-style split of sky view into sky+air (Earth)
    extra: dict = field(default_factory=dict)

    @property
    def n(self) -> int:
        return len(self.time_s)

    @property
    def vacuum(self) -> bool:
        return self.gas is None

    def to_csv(self, path):
        import csv
        cols = dict(time_s=self.time_s, jd_utc=self.jd_utc, zenith_deg=self.zenith,
                    sun_azimuth_deg=self.sun_azimuth, dni_W_m2=self.dni, dhi_W_m2=self.dhi,
                    ghi_W_m2=self.ghi, sun_visible=self.sun_visible, T_air_K=self.T_air,
                    T_sky_K=self.T_sky, T_ground_K=self.T_ground, T_deep_K=self.T_deep,
                    wind_m_s=self.wind_speed, pressure_Pa=self.pressure)
        for k, v in self.extra.items():
            if isinstance(v, np.ndarray) and v.shape == self.time_s.shape:
                cols[k] = v
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(cols.keys())
            for row in zip(*cols.values()):
                w.writerow([f"{x:.6g}" for x in row])
