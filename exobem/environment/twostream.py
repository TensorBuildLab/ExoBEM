"""Delta-Eddington two-stream solar transfer through a dusty atmosphere.

Used to split Martian surface insolation into direct and diffuse parts as a function
of dust optical depth tau, dust single-scattering albedo w0 and asymmetry parameter g,
and surface albedo.  Formulation: Joseph, Wiscombe & Weinman (1976, J. Atmos. Sci.
33, 2452) delta scaling with the Eddington two-stream coefficients of Meador &
Weaver (1980, J. Atmos. Sci. 37, 630) / Toon et al. (1989, JGR 94, 16287):

    dF+/dtau = g1 F+ - g2 F- - g3 w0 Fs exp(-tau/mu0)
    dF-/dtau = g2 F+ - g1 F- + g4 w0 Fs exp(-tau/mu0)

with F-(0) = 0 and F+(tau*) = A_s [F-(tau*) + mu0 Fs exp(-tau*/mu0)].
"""
from __future__ import annotations

import numpy as np


def delta_eddington_surface(tau, mu0, w0=0.93, g=0.65, surface_albedo=0.2, delta=True):
    """Return (direct_horizontal_fraction, diffuse_down_fraction) of the TOA horizontal flux.

    Fractions are relative to mu0*Fs (TOA flux on a horizontal plane).  The direct term is
    the delta-scaled beam (includes the strongly forward-scattered aureole), which is the
    natural "beam" for a building model.
    """
    tau = np.asarray(tau, float)
    mu0 = np.clip(np.asarray(mu0, float), 1e-3, 1.0)
    tau, mu0 = np.broadcast_arrays(tau, mu0)
    if delta:
        f = g * g
        tau_s = (1 - w0 * f) * tau
        w = (1 - f) * w0 / (1 - w0 * f)
        gs = (g - f) / (1 - f)
    else:
        tau_s, w, gs = tau, w0, g
    w = min(w, 1 - 1e-9)
    g1 = (7 - w * (4 + 3 * gs)) / 4.0
    g2 = -(1 - w * (4 - 3 * gs)) / 4.0
    g3 = (2 - 3 * gs * mu0) / 4.0
    g4 = 1 - g3
    lam = np.sqrt(max(g1 * g1 - g2 * g2, 1e-12))
    Fs = 1.0
    # particular solution C+ e^{-t/mu0}, C- e^{-t/mu0}
    # (g1 + 1/mu0) C+ - g2 C- = g3 w Fs ;  g2 C+ - (g1 - 1/mu0) C- = -g4 w Fs
    a11 = g1 + 1 / mu0
    a12 = -g2
    a21 = g2
    a22 = -(g1 - 1 / mu0)
    b1 = g3 * w * Fs
    b2 = -g4 * w * Fs
    det = a11 * a22 - a12 * a21
    det = np.where(np.abs(det) < 1e-10, 1e-10, det)
    Cp = (b1 * a22 - a12 * b2) / det
    Cm = (a11 * b2 - a21 * b1) / det
    # homogeneous: e^{-lam t} with v/u = (g1 + lam)/g2 ... from k u = g1 u - g2 v, k=-lam
    # => v = (g1 + lam) u / g2 ; for e^{+lam t}: v = (g1 - lam) u / g2.
    # use scaled basis: P = e^{-lam t}, Q = e^{-lam (T - t)}
    r1 = (g1 + lam) / g2   # F-/F+ ratio for decaying mode
    r2 = (g1 - lam) / g2   # for growing mode
    T = tau_s
    E = np.exp(-lam * T)
    eT = np.exp(-T / mu0)
    As = surface_albedo
    # unknowns a (decaying), b (growing, scaled by e^{-lam T})
    # F+(t) = a e^{-lam t} + b e^{-lam(T-t)} + Cp e^{-t/mu0}
    # F-(t) = a r1 e^{-lam t} + b r2 e^{-lam(T-t)} + Cm e^{-t/mu0}
    # top: F-(0) = 0 -> a r1 + b r2 E + Cm = 0
    # bottom: F+(T) - As F-(T) = As mu0 Fs eT
    m11, m12, c1 = r1, r2 * E, -Cm
    m21 = E - As * r1 * E
    m22 = 1 - As * r2
    c2 = As * mu0 * Fs * eT - (Cp - As * Cm) * eT
    d = m11 * m22 - m12 * m21
    a = (c1 * m22 - m12 * c2) / d
    b = (m11 * c2 - m21 * c1) / d
    Fdn_bottom = a * r1 * E + b * r2 + Cm * eT
    direct = mu0 * Fs * eT
    return direct / mu0, Fdn_bottom / mu0


def appelbaum_net_flux_function(tau, zenith_deg, w0=0.93, g=0.65, albedo=0.1):
    """Normalised net flux f(z,tau) = (1-A) G_h / (G_ob cos z) for comparison with
    Appelbaum & Flood (1990)."""
    mu0 = np.cos(np.radians(zenith_deg))
    d, s = delta_eddington_surface(tau, mu0, w0, g, albedo)
    return (1 - albedo) * (d + s)
