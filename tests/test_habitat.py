"""Tests for the sealed-habitat physics, the PWF weather format, the power system and geometry."""
import datetime as dt

import numpy as np
import pytest

from exobem import gas as G
from exobem import weather as W
from exobem.checks import ModelError
from exobem.constants import SIGMA
from exobem.geometry import box, dome, horizontal_cylinder, vertical_cylinder
from exobem.materials import Construction, library
from exobem.model import InternalGain, InternalMass, Model, Thermostat, Zone
from exobem.power import Battery, FissionPower, PowerSystem, PVArray, RegenerativeFuelCell, simulate_power
from exobem.simulation import simulate


@pytest.fixture(scope="module")
def moon_env():
    return W.generate("moon", 0.674, 23.473, "2030-01-01T00:00:00", 4, 1800.0)


def small_habitat(**zkw):
    m = library()
    layers = [m["lunar_regolith_cover_1m"], m["beta_cloth_outer_1mm"], m["mli_20layer_vacuum"],
              m["aluminum_2219_4mm"], m["interior_panel_10mm"]]
    cons = {"shell": Construction("shell", layers), "floor": Construction("floor", [m["lunar_ground_3m"]] + layers[2:]),
            "rack": Construction("rack", [m["aluminum_2219_4mm"]])}
    geom = horizontal_cylinder(2.0, 6.0, "shell", "shell", "floor", n_facets=8)
    kw = dict(cabin_pressure_Pa=70300.0, cabin_o2_fraction=0.265, interior_convection="physical",
              initial_temperature_C=22.0)
    kw.update(zkw)
    z = Zone("hab", geom, [InternalGain("crew", 340.0, 0.5, 215.0), InternalGain("eq", 1500.0, 0.3, electric=True)],
             Thermostat(18.0, 27.0), **kw)
    return Model("hab", z, cons, timestep_s=1800.0)


# ------------------------------------------------------------------------------ sealed habitat checks
def test_infiltration_forbidden_off_earth(moon_env):
    with pytest.raises(ModelError, match="infiltration"):
        simulate(small_habitat(infiltration_ach=0.5), moon_env)


def test_hypoxic_cabin_rejected(moon_env):
    with pytest.raises(ModelError, match="hypoxic"):
        simulate(small_habitat(cabin_pressure_Pa=40000.0, cabin_o2_fraction=0.21), moon_env)


def test_tarp_exterior_rejected_off_earth(moon_env):
    m = small_habitat()
    m.exterior_convection = "tarp"
    with pytest.raises(ModelError, match="TARP"):
        simulate(m, moon_env)


def test_gas_loss_includes_airlock():
    z = small_habitat(leakage_kg_per_day=0.15, airlock_cycles_per_day=0.5, airlock_loss_kg_per_cycle=0.6).zone
    assert z.gas_loss_kg_per_day == pytest.approx(0.15 + 0.3)


# ------------------------------------------------------------------------------ humidity
def test_cabin_humidity_ratio_uses_cabin_gas():
    cab = G.cabin_gas(0.265)
    w = G.humidity_ratio(1000.0, 70300.0, cab)
    assert w == pytest.approx(G.M_WATER / cab.molar_mass * 1000.0 / 69300.0)
    assert G.vapour_pressure(w, 70300.0, cab) == pytest.approx(1000.0)


def test_saturation_pressure_reference_points():
    # Hyland-Wexler / ASHRAE Fundamentals: 611.2 Pa at 0 C, 2339 Pa at 20 C, 7384 Pa at 40 C
    assert float(G.saturation_pressure(0.0)) == pytest.approx(611.2, rel=2e-3)
    assert float(G.saturation_pressure(20.0)) == pytest.approx(2339.0, rel=4e-3)
    assert float(G.saturation_pressure(40.0)) == pytest.approx(7384.0, rel=6e-3)


def test_condensing_hx_removes_crew_moisture_at_steady_state(moon_env):
    res = simulate(small_habitat(humidity_control=True, rh_max=0.5, initial_rh=0.5), moon_env)
    # after the cabin reaches its RH limit, the condensate equals the crew moisture production
    assert res.rh_zone.max() <= 0.5 + 1e-9
    assert np.allclose(res.Q_latent_W[-48:], 215.0, rtol=2e-3)


# ------------------------------------------------------------------------------ internal mass
def test_internal_mass_is_adiabatic_and_damps(moon_env):
    base = simulate(small_habitat(), moon_env)
    mass = simulate(small_habitat(internal_mass=[InternalMass("racks", "rack", 20.0)]), moon_env)
    assert mass.T_inside_C.shape[1] == base.T_inside_C.shape[1] + 1
    assert mass.n_envelope == base.n_envelope
    # same total energy over the period within 1 % (internal mass stores but does not create heat)
    assert mass.Q_cooling_W.sum() == pytest.approx(base.Q_cooling_W.sum(), rel=0.01)


# ------------------------------------------------------------------------------ PWF
def test_pwf_round_trip(tmp_path, moon_env):
    moon_env.extra["start_utc"] = dt.datetime(2030, 1, 1)
    p = W.write_pwf(moon_env, tmp_path / "m.pwf", site_name="test")
    e2 = W.read_pwf(p)
    for a in ("dni", "T_ground", "T_sky", "zenith", "pressure", "local_time_h"):
        assert np.allclose(getattr(e2, a), getattr(moon_env, a), rtol=1e-6, atol=1e-6)
    assert e2.gas is None and e2.gravity == pytest.approx(1.625)


def test_pwf_rejects_bad_data(tmp_path, moon_env):
    moon_env.extra["start_utc"] = dt.datetime(2030, 1, 1)
    p = W.write_pwf(moon_env, tmp_path / "m.pwf")
    txt = p.read_text().splitlines()
    i = next(k for k, l in enumerate(txt) if not l.startswith("#")) + 1
    cells = txt[i].split(",")
    cells[11] = "1.0"             # T_ground_K below the cosmic background
    txt[i] = ",".join(cells)
    p.write_text("\n".join(txt))
    with pytest.raises(ValueError, match="T_ground"):
        W.read_pwf(p)


# ------------------------------------------------------------------------------ power
def test_pv_cell_temperature_vacuum_analytic(moon_env):
    """Horizontal panel, sky and ground at the 2.7 K background: (alpha - eta) G = 2 eps sigma T^4."""
    env = moon_env
    env2 = W.generate("moon", 0.674, 23.473, "2030-01-01T00:00:00", 1, 1800.0)
    env2.T_ground = np.full(env2.n, 2.725)
    a = PVArray(1.0, tracking="horizontal", temp_coeff_per_K=0.0)
    G_ = np.full(env2.n, 1000.0)
    T = a.cell_temperature(env2, G_, np.zeros(env2.n), 0.25)
    T_exact = ((a.alpha_front - 0.25) * 1000.0 / ((a.eps_front + a.eps_back) * SIGMA) + 2.725 ** 4) ** 0.25
    assert np.allclose(T, T_exact, rtol=1e-6)


def test_battery_energy_bookkeeping(moon_env):
    env = moon_env
    load = np.full(env.n, 5000.0)
    sysm = PowerSystem(pv=[PVArray(60.0)], battery=Battery(300.0, eta_charge=0.95, eta_discharge=0.95, soc_init=0.6))
    r = simulate_power(sysm, env, load)
    dtk = env.dt / 3.6e6
    b = r["battery_W"]
    stored_in = -np.sum(np.minimum(b, 0)) * dtk * 0.95
    taken_out = np.sum(np.maximum(b, 0)) * dtk / 0.95
    soc0 = 0.6 * 300.0
    assert r["soc_battery_kWh"][-1] == pytest.approx(soc0 + stored_in - taken_out, rel=1e-9)
    # power balance at every step
    lhs = r["generation_pv_W"] + b + r["rfc_W"] + r["unmet_W"] - r["curtailed_W"]
    assert np.allclose(lhs, load)


def test_fission_and_rfc():
    env = W.generate("moon", 0.674, 23.473, "2030-01-01T00:00:00", 30, 3600.0)
    load = np.full(env.n, 30e3)
    r = simulate_power(PowerSystem(fission=FissionPower(40.0)), env, load)
    assert r["summary"]["unmet_kWh"] == 0.0
    assert FissionPower(40.0, efficiency=0.25).waste_heat(env)[0] == pytest.approx(120e3)
    # PV alone cannot carry a lunar-equator night; an RFC can
    pv = PVArray(400.0, tracking="two_axis")
    r1 = simulate_power(PowerSystem(pv=[pv]), env, load)
    r2 = simulate_power(PowerSystem(pv=[pv], rfc=RegenerativeFuelCell(12000.0)), env, load, repeat_cycles=2)
    assert r1["summary"]["unmet_kWh"] > 1000.0
    assert r2["summary"]["unmet_kWh"] < r1["summary"]["unmet_kWh"]


# ------------------------------------------------------------------------------ geometry
@pytest.mark.parametrize("geo", [horizontal_cylinder(3, 10, "s", "e", "f", axis_azimuth=37), vertical_cylinder(3, 4, "w", "r", "f"),
                                 box(8, 6, 2.7, "w", "r", "f", north_axis=15), dome(5, "s", "f")])
def test_vertices_match_orientation(geo):
    for s in geo.surfaces:
        v = np.array(s.vertices)
        n = sum(np.cross(v[i], v[(i + 1) % len(v)]) for i in range(len(v)))
        n = n / np.linalg.norm(n)
        tilt = np.degrees(np.arccos(np.clip(n[2], -1, 1)))
        assert abs(tilt - s.tilt) < 3.0, s.name
        if 1.0 < s.tilt < 179.0:                      # outward normal also points to the surface azimuth
            az = np.degrees(np.arctan2(n[0], n[1])) % 360.0
            assert abs((az - s.azimuth + 180.0) % 360.0 - 180.0) < 3.0, s.name
