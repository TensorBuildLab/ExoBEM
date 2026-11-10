"""Tests for the corrections made after the independent equation review (docs/VERIFICATION_LOG.md)."""
import numpy as np
import pytest

from exobem.conduction import GlobalGrid
from exobem.environment.sites import mars_surface_pressure
from exobem.environment.twostream import delta_eddington_surface
from exobem.gas import cabin_gas
from exobem.materials import Construction, Material
from exobem.solar import horizon_visible_fraction


def steady_flux(curv, k=0.1, L=1.0, Ti=300.0, To=200.0):
    """Steady conduction through one layer between two Dirichlet faces, per unit INNER area."""
    mat = Material("m", L, k, 1500.0, 800.0)
    g = GlobalGrid([Construction("c", [mat])], 1e12, 250.0, curvatures=[curv])
    ab, rhs = g.base_matrix(1e12)
    o, i = g.outside_idx[0], g.inside_idx[0]
    for idx, T in ((o, To), (i, Ti)):
        ab[1, idx] = 1.0
        if idx + 1 < g.N:
            ab[0, idx + 1] = 0.0
        if idx - 1 >= 0:
            ab[2, idx - 1] = 0.0
        rhs[idx] = T
    from scipy.linalg import solve_banded
    T = solve_banded((1, 1), ab, rhs)
    return g.K[-1] * (T[i - 1] - T[i]) * -1.0, g


@pytest.mark.parametrize("kind,exact", [(None, lambda ri, ro, k: k / (ro - ri)),
                                        ("cylinder", lambda ri, ro, k: k / (ri * np.log(ro / ri))),
                                        ("sphere", lambda ri, ro, k: k * ro / (ri * (ro - ri)))])
def test_curved_shell_steady_conduction(kind, exact):
    ri, L, k = 3.0, 1.0, 0.1
    q, g = steady_flux(None if kind is None else (kind, ri), k=k, L=L)
    assert q == pytest.approx(exact(ri, ri + L, k) * 100.0, rel=1e-6)
    if kind == "cylinder":
        assert g.outer_area_factor[0] == pytest.approx(4.0 / 3.0)
    if kind == "sphere":
        assert g.outer_area_factor[0] == pytest.approx(16.0 / 9.0)


def test_curved_shell_heat_capacity_is_shell_volume():
    ri, L = 3.0, 1.0
    mat = Material("m", L, 0.1, 1500.0, 800.0)
    for kind, vol in (("cylinder", ((ri + L) ** 2 - ri ** 2) / (2 * ri)), ("sphere", ((ri + L) ** 3 - ri ** 3) / (3 * ri ** 2))):
        g = GlobalGrid([Construction("c", [mat])], 600.0, 250.0, curvatures=[(kind, ri)])
        assert g.C.sum() == pytest.approx(1500.0 * 800.0 * vol, rel=2e-3)


def test_visible_disk_fraction_by_area():
    r = 0.2666
    f = horizon_visible_fraction(np.array([-r, -0.5 * r, 0.0, 0.5 * r, r]), 0.0, None, r)
    assert f == pytest.approx([0.0, 0.1955, 0.5, 0.8045, 1.0], abs=1e-4)


def test_mars_pressure_cycle_phase():
    Ls = np.arange(0, 360, 1.0)
    P = mars_surface_pressure(Ls, 710.0)
    assert 140 <= Ls[P.argmin()] <= 165          # southern winter: CO2 condenses on the south cap
    assert 250 <= Ls[P.argmax()] <= 275          # southern summer
    assert P.max() / P.min() == pytest.approx(1.25, abs=0.03)


def test_beer_law_beam_below_delta_scaled_direct():
    for tau in (0.3, 0.9, 3.0):
        for mu in (1.0, 0.5, 0.2):
            d, s = delta_eddington_surface(tau, mu, 0.885, 0.74, 0.14)
            beer = np.exp(-tau / mu)
            assert beer <= d + 1e-12
            assert d + s - beer >= 0.0           # diffuse part stays non-negative


def test_cabin_cp_mass_weighted():
    # N2 1040 J/kgK and O2 918 J/kgK at 300 K, weighted by mass
    x = 0.34
    M = x * 0.031999 + (1 - x) * 0.028014
    y = x * 0.031999 / M
    assert cabin_gas(x).cp == pytest.approx(y * 918 + (1 - y) * 1040)


def test_regolith_equilibrium_matches_brute_force():
    """The accelerated equilibrium agrees with brute-force integration (checked over 2,500 lunations to
    within 0.3 K at 3 m); here: the result does not depend on the initial guess."""
    import datetime as dt
    from exobem.constants import TSI_1AU
    from exobem.environment.regolith import RegolithColumn
    from exobem.ephemeris import jd_from_datetime, moon as me
    col = RegolithColumn()
    dtc = 3600.0
    n = int(round(me.SYNODIC_MONTH_DAYS * 86400 / dtc))
    jd = jd_from_datetime(dt.datetime(2030, 1, 1)) - me.SYNODIC_MONTH_DAYS + (np.arange(n) + 0.5) * dtc / 86400
    sp = me.sun_position(jd, 0.674, 23.47)
    q = (1 - col.albedo(sp.zenith_deg)) * TSI_1AU / sp.distance_au ** 2 * np.maximum(np.cos(np.radians(sp.zenith_deg)), 0)
    z = col.grid()
    i3 = int(np.argmin(abs(z - 3.0)))
    deep = []
    for T0 in (200.0, 320.0):
        _, mean, _ = col.equilibrate(dtc, q, np.zeros(n), z_skin=0.15, n_iter=10, tol=0.005, T_init=T0)
        deep.append(mean[i3])
    assert abs(deep[0] - deep[1]) < 0.3
    assert 255.0 < deep[0] < 265.0
