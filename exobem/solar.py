"""Incident solar radiation on exterior surfaces.

Beam: DNI * cos(theta) for sunlit surfaces; the Sun is blocked by an optional
azimuth-dependent horizon mask and is treated as a finite disk near the horizon
(important at the lunar poles where the Sun grazes the horizon).
Sky diffuse: isotropic, or the Perez et al. (1990) anisotropic model used by
EnergyPlus (Earth verification).  Ground-reflected: rho_g * GHI * F_ground.
"""
from __future__ import annotations

import numpy as np

# Perez et al. (1990) "allsitescomposite" coefficients, as used by EnergyPlus.
_PEREZ = np.array([
    [-0.0083117, 0.5877285, -0.0620636, -0.0596012, 0.0721249, -0.0220216],
    [0.1299457, 0.6825954, -0.1513752, -0.0189325, 0.0659650, -0.0288748],
    [0.3296958, 0.4868735, -0.2210958, 0.0554140, -0.0639588, -0.0260542],
    [0.5682053, 0.1874525, -0.2951290, 0.1088631, -0.1519229, -0.0139754],
    [0.8730280, -0.3920403, -0.3616149, 0.2255647, -0.4620442, 0.0012448],
    [1.1326077, -1.2367284, -0.4118494, 0.2877813, -0.8230357, 0.0558225],
    [1.0601591, -1.5999137, -0.3589221, 0.2642124, -1.1272340, 0.1310694],
    [0.6777470, -0.3272588, -0.2504286, 0.1561313, -1.3765031, 0.2506212],
])
_EPS_BINS = np.array([1.065, 1.230, 1.500, 1.950, 2.800, 4.500, 6.200])


def cos_incidence(zen_deg, sun_az_deg, tilt_deg, surf_az_deg):
    """cos(theta) for arrays zen/sun_az of shape (n_t,) and tilt/surf_az of shape (n_s,)."""
    z = np.radians(np.asarray(zen_deg))[:, None]
    a = np.radians(np.asarray(sun_az_deg))[:, None]
    t = np.radians(np.asarray(tilt_deg))[None, :]
    s = np.radians(np.asarray(surf_az_deg))[None, :]
    return np.cos(z) * np.cos(t) + np.sin(z) * np.sin(t) * np.cos(a - s)


def perez_coefficients(dhi, dni, zen_deg):
    """Return (F1, F2) for each time step (EnergyPlus formulation)."""
    zen = np.radians(np.minimum(zen_deg, 89.999))
    cosz = np.cos(zen)
    zdeg = np.degrees(zen)
    airmass = 1.0 / (cosz + 0.15 * (93.9 - zdeg) ** -1.253)
    with np.errstate(divide="ignore", invalid="ignore"):
        eps = ((dhi + dni) / dhi + 1.041 * zen ** 3) / (1.0 + 1.041 * zen ** 3)
    eps = np.where(dhi > 0, eps, 1.0)
    delta = dhi * airmass / 1353.0
    b = np.searchsorted(_EPS_BINS, eps, side="right")
    c = _PEREZ[b]
    F1 = np.maximum(0.0, c[:, 0] + c[:, 1] * delta + c[:, 2] * zen)
    F2 = c[:, 3] + c[:, 4] * delta + c[:, 5] * zen
    return F1, F2


def horizon_visible_fraction(elev_deg, sun_az_deg, horizon=None, sun_radius_deg=0.2666):
    """Fraction of the solar disk above the (possibly azimuth-dependent) horizon."""
    if horizon is None:
        h = 0.0
    elif callable(horizon):
        h = horizon(np.asarray(sun_az_deg))
    else:
        az_pts, el_pts = np.asarray(horizon[0], float), np.asarray(horizon[1], float)
        h = np.interp(np.asarray(sun_az_deg) % 360.0, az_pts, el_pts, period=360.0)
    x = (np.asarray(elev_deg) - h + sun_radius_deg) / (2.0 * sun_radius_deg)
    return np.clip(x, 0.0, 1.0)


def incident_solar(env, surfaces, model: str = "isotropic"):
    """Beam, sky-diffuse and ground-reflected incident irradiance [W/m2] (n_t x n_s)."""
    tilt = np.array([s.tilt for s in surfaces])
    saz = np.array([s.azimuth for s in surfaces])
    Fsky = np.array([s.F_sky for s in surfaces])
    Fgnd = np.array([s.F_ground for s in surfaces])
    cth = cos_incidence(env.zenith, env.sun_azimuth, tilt, saz)
    dni = env.dni[:, None]
    beam = dni * np.maximum(cth, 0.0) * env.sun_visible[:, None]
    dhi = env.dhi[:, None]
    if model == "perez":
        F1, F2 = perez_coefficients(env.dhi, env.dni, env.zenith)
        cosz = np.cos(np.radians(env.zenith))
        a = np.maximum(0.0, cth)
        bb = np.maximum(np.cos(np.radians(85.0)), cosz)[:, None]
        up = env.zenith[:, None] < 90.0
        sint = np.sin(np.radians(tilt))[None, :]
        aniso = ((1 - F1[:, None]) * Fsky[None, :] + F1[:, None] * a / bb + F2[:, None] * sint)
        sky = np.where(up, dhi * np.maximum(aniso, 0.0), dhi * Fsky[None, :])
    else:
        sky = dhi * Fsky[None, :]
    ghi = env.ghi[:, None]
    gnd = ghi * env.ground_albedo[:, None] * Fgnd[None, :]
    return beam, sky, gnd, cth
