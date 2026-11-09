"""Analytical and reference-data verification tests for ExoBEM."""
import datetime as dt
import math

import numpy as np
import pytest
from scipy.special import erfc

from exobem.ephemeris import jd_from_datetime, mars, moon, earth
from exobem.environment.regolith import RegolithColumn
from exobem.environment.twostream import delta_eddington_surface
from exobem.conduction import GlobalGrid
from exobem.materials import Construction, Material, NoMassMaterial
from exobem.simulation import approximate_view_factors, script_f
from exobem.geometry import box
from exobem.constants import TSI_1AU, SIGMA


# ------------------------------------------------------------------ ephemerides
def test_mars24_worked_example():
    """Mars24 / Allison & McEwen (2000) example: 2000-01-06 00:00 UTC (TT-UTC = 64.184 s)."""
    a = mars.areocentric(jd_from_datetime(dt.datetime(2000, 1, 6)), tt_minus_utc=64.184)
    assert abs(float(a["Ls"]) - 277.18758) < 2e-4
    assert abs(float(a["eot_deg"]) - (-5.18774)) < 2e-3
    assert abs(float(a["r_au"]) - 1.39358) < 2e-4
    assert abs(float(a["mst_h"]) - 23.99425) < 2e-4


def test_mars_sol_length():
    jd0 = 2460000.0
    a0 = mars.areocentric(jd0)["mars_sol_date"]
    a1 = mars.areocentric(jd0 + mars.MARS_SOL_SECONDS / 86400.0)["mars_sol_date"]
    assert abs((a1 - a0) - 1.0) < 1e-9


def test_moon_subsolar_full_and_new_moon():
    full = moon.subsolar_point(jd_from_datetime(dt.datetime(2024, 1, 25, 17, 54)))
    new = moon.subsolar_point(jd_from_datetime(dt.datetime(2024, 1, 11, 11, 57)))
    assert abs(float(full[0])) < 8.0                  # near-side centre, within libration
    assert abs(abs(float(new[0])) - 180.0) < 8.0
    assert abs(float(full[1])) <= 1.55


def test_earth_solar_noon_zenith():
    # Golden CO, summer solstice, ~local solar noon
    s = earth.sun_position(jd_from_datetime(dt.datetime(2024, 6, 21, 19, 7)), 39.74, -105.18)
    assert abs(float(s.zenith_deg) - (39.74 - 23.44)) < 0.3


# ------------------------------------------------------------------ conduction
def _single_slab(L=0.2, k=1.0, rho=2000.0, cp=1000.0, dt=600.0):
    mat = Material("slab", L, k, rho, cp)
    return GlobalGrid([Construction("c", [mat])], dt, 0.0), mat


def test_steady_state_conduction_matches_resistance():
    lay = [Material("a", 0.1, 0.5, 1000, 1000), NoMassMaterial("r", 2.0), Material("b", 0.05, 0.05, 30, 1200)]
    g = GlobalGrid([Construction("c", lay)], 3600.0, 0.0)
    R = sum(l.resistance for l in lay)
    for _ in range(3000):
        ab, rhs = g.base_matrix()
        ab[1, 0] = 1.0; ab[0, 1] = 0.0; rhs[0] = 1.0           # Dirichlet 1 K outside
        ab[1, -1] = 1.0; ab[2, -2] = 0.0; rhs[-1] = 0.0        # 0 K inside
        from scipy.linalg import solve_banded
        g.T = solve_banded((1, 1), ab, rhs)
    q_out, q_in = g.heat_flux_in()
    assert abs(q_in[0] - 1.0 / R) / (1.0 / R) < 1e-3


def test_semi_infinite_step_response():
    """Thick slab, surface stepped to 1 K: T(x,t) = erfc(x / 2 sqrt(alpha t))."""
    from scipy.linalg import solve_banded
    L, k, rho, cp = 2.0, 1.0, 2000.0, 1000.0
    g, _ = _single_slab(L, k, rho, cp, dt=300.0)
    alpha = k / (rho * cp)
    nsteps = int(2 * 86400 / 300)
    for _ in range(nsteps):
        ab, rhs = g.base_matrix()
        ab[1, 0] = 1.0; ab[0, 1] = 0.0; rhs[0] = 1.0
        g.T = solve_banded((1, 1), ab, rhs)
    x = np.concatenate([[0.0], np.cumsum(g.seg_h)])
    t = nsteps * 300.0
    exact = erfc(x / (2 * math.sqrt(alpha * t)))
    mask = x < 0.5
    assert np.max(np.abs(g.T[mask] - exact[mask])) < 0.01


# ------------------------------------------------------------------ interior radiation
def test_view_factors_reciprocity_and_closure():
    geom = box(8, 6, 2.7, "w", "r", "f")
    F = approximate_view_factors(geom.surfaces)
    A = np.array([s.area for s in geom.surfaces])
    assert np.allclose(F.sum(1), 1.0, atol=1e-6)
    assert np.allclose(A[:, None] * F, (A[:, None] * F).T, atol=1e-3)


def test_scriptf_two_parallel_plates_limit():
    """Two infinite parallel grey plates: ScriptF = 1/(1/e1 + 1/e2 - 1)."""
    F = np.array([[0.0, 1.0], [1.0, 0.0]])
    e1, e2 = 0.9, 0.5
    SF = script_f(F, [e1, e2])
    assert abs(SF[0, 1] - 1.0 / (1 / e1 + 1 / e2 - 1)) < 1e-6


# ------------------------------------------------------------------ planetary environment
def test_lunar_regolith_matches_diviner_equator():
    """Hayne et al. (2017): equatorial noon ~385-395 K, pre-dawn ~90-100 K, ~250-260 K at 0.5-1 m."""
    dtt = 1800.0
    P = moon.SYNODIC_MONTH_DAYS * 86400
    n = int(P / dtt)
    jd = 2460000.5 + np.arange(n) * dtt / 86400
    s = moon.sun_position(jd, 0.0, 0.0)
    mu = np.cos(np.radians(s.zenith_deg))
    G = np.where(mu > 0, TSI_1AU / s.distance_au ** 2 * mu, 0)
    col = RegolithColumn()
    r = col.run(dtt, (1 - col.albedo(s.zenith_deg)) * G, np.zeros(n), spinup_cycles=6, cycle_steps=n,
                record_depths=(0.0, 0.5, 1.0))
    assert 380 < r["T_surface"].max() < 398
    assert 88 < r["T_surface"].min() < 102
    assert 245 < r["T_depths"][:, 2].mean() < 265


def test_delta_eddington_limits():
    d, s = delta_eddington_surface(1e-6, 0.8)
    assert abs(d - 1.0) < 1e-4 and abs(s) < 1e-4
    taus = [0.2, 0.5, 1.0, 2.0, 4.0]
    direct = [float(delta_eddington_surface(t, 0.8)[0]) for t in taus]
    assert all(a > b for a, b in zip(direct, direct[1:]))
    # global (direct + diffuse) can never exceed the TOA flux
    for t in taus:
        dd, ss = delta_eddington_surface(t, 0.5)
        assert 0 < dd + ss <= 1.0 + 1e-9
