"""Surface convection coefficients.

Two families are implemented:

``tarp``     - The EnergyPlus TARP algorithm (Walton 1983): natural convection from the
               Walton correlations plus, outdoors, the Sparrow windward/leeward forced term
               2.537 W_f R_f sqrt(P V_z / A).  Used for Earth-mode verification.
``physical`` - Gas- and gravity-aware Nusselt correlations (Churchill-Chu for vertical
               faces, McAdams/Lloyd-Moran for horizontal faces, flat-plate forced
               convection) combined as (h_n^3 + h_f^3)^(1/3).  Valid for any gas, pressure
               and gravity - e.g. a 600 Pa CO2 atmosphere at 3.71 m/s2, or a 70 kPa cabin
               at 1.62 m/s2.  In vacuum (Moon exterior) h = 0.

All functions are vectorised over surfaces.  ``cos_up`` is the cosine of the angle
between the outward normal of the *face* and the local vertical (+1 facing up).
"""
from __future__ import annotations

import numpy as np

from .constants import G0
from .gas import Gas


# ------------------------------------------------------------------ TARP (EnergyPlus)
def walton_natural(dT, cos_up):
    """Walton natural convection [W/m2-K]; dT = T_surface - T_air."""
    dT = np.asarray(dT, float)
    c = np.asarray(cos_up, float)
    a = np.abs(dT) ** (1.0 / 3.0)
    enhanced = ((dT > 0) & (c > 0)) | ((dT < 0) & (c < 0))
    h_enh = 9.482 * a / (7.238 - np.abs(c))
    h_red = 1.810 * a / (1.382 + np.abs(c))
    return np.where(enhanced, h_enh, h_red)


def tarp_exterior(dT, cos_up, wind_local, perimeter, area, rough_mult, windward):
    hf = 2.537 * np.where(windward, 1.0, 0.5) * rough_mult * np.sqrt(perimeter * np.maximum(wind_local, 0.0) / area)
    return hf + walton_natural(dT, cos_up)


def local_wind_speed(v_met, z, alpha=0.14, delta=270.0, alpha_met=0.14, delta_met=270.0, z_met=10.0):
    """EnergyPlus wind-profile correction (power law), from met-station to height z."""
    z = np.maximum(np.asarray(z, float), 0.0)
    return v_met * (delta_met / z_met) ** alpha_met * (z / delta) ** alpha


def is_windward(surface_azimuth, cos_up, wind_dir):
    horizontal = np.abs(cos_up) > 0.98
    diff = np.abs(((np.asarray(surface_azimuth) - wind_dir) + 180.0) % 360.0 - 180.0)
    return horizontal | (diff <= 100.0)


# ------------------------------------------------------------------ physical correlations
def _gas_numbers(gas: Gas, T_film, P):
    k = gas.conductivity(T_film)
    nu = gas.kinematic_viscosity(T_film, P)
    alpha = gas.diffusivity(T_film, P)
    return k, nu, alpha, nu / alpha


def natural_physical(gas: Gas, T_surf, T_air, P, g, cos_up, L_vert, L_horiz):
    T_surf = np.asarray(T_surf, float)
    T_air = np.asarray(T_air, float) * np.ones_like(T_surf)
    Tf = 0.5 * (T_surf + T_air)
    dT = T_surf - T_air
    k, nu, alpha, Pr = _gas_numbers(gas, Tf, P)
    beta = 1.0 / Tf
    gb = g * beta * np.abs(dT) / (nu * alpha)
    # vertical (Churchill & Chu 1975, all Ra)
    Ra_v = gb * L_vert ** 3
    psi = (1.0 + (0.492 / Pr) ** (9.0 / 16.0)) ** (8.0 / 27.0)
    Nu_v = (0.825 + 0.387 * Ra_v ** (1.0 / 6.0) / psi) ** 2
    h_v = Nu_v * k / L_vert
    # horizontal, L = A/P
    Ra_h = gb * L_horiz ** 3
    c = np.asarray(cos_up, float)
    enhanced = ((dT > 0) & (c > 0)) | ((dT < 0) & (c < 0))
    Nu_up = np.where(Ra_h < 1e7, 0.54 * Ra_h ** 0.25, 0.15 * Ra_h ** (1.0 / 3.0))
    Nu_dn = 0.27 * Ra_h ** 0.25
    Nu_h = np.maximum(np.where(enhanced, Nu_up, Nu_dn), 1.0)
    h_h = Nu_h * k / L_horiz
    w = np.abs(c)
    return (1.0 - w) * h_v + w * h_h


def forced_physical(gas: Gas, T_surf, T_air, P, V, L):
    T_surf = np.asarray(T_surf, float)
    Tf = 0.5 * (T_surf + T_air)
    k, nu, alpha, Pr = _gas_numbers(gas, Tf, P)
    Re = np.maximum(V, 1e-6) * L / nu
    Nu_lam = 0.664 * Re ** 0.5 * Pr ** (1.0 / 3.0)
    Nu_tur = (0.037 * Re ** 0.8 - 871.0) * Pr ** (1.0 / 3.0)
    Nu = np.where(Re < 5e5, Nu_lam, np.maximum(Nu_tur, Nu_lam))
    return Nu * k / L


def mixed_physical(gas, T_surf, T_air, P, g, cos_up, V, L_vert, L_horiz, L_forced):
    hn = natural_physical(gas, T_surf, T_air, P, g, cos_up, L_vert, L_horiz)
    hf = forced_physical(gas, T_surf, T_air, P, V, L_forced)
    return np.cbrt(hn ** 3 + hf ** 3)


def tarp_scale_factor(gas: Gas, T, P, g, ref_gas: Gas, T_ref=293.15, P_ref=101325.0):
    """Factor that maps Earth-air Walton correlations to another gas/pressure/gravity.

    For turbulent natural convection h = C k (g beta dT /(nu alpha))^(1/3), so
    h / h_ref = (k/k0) [ (g/g0) (T0/T) (nu0 alpha0)/(nu alpha) ]^(1/3).
    """
    k, nu, a = gas.conductivity(T), gas.kinematic_viscosity(T, P), gas.diffusivity(T, P)
    k0, nu0, a0 = (ref_gas.conductivity(T_ref), ref_gas.kinematic_viscosity(T_ref, P_ref),
                   ref_gas.diffusivity(T_ref, P_ref))
    return (k / k0) * ((g / G0) * (T_ref / T) * (nu0 * a0) / (nu * a)) ** (1.0 / 3.0)
