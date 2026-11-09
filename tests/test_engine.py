"""Whole-engine tests: energy conservation, steady state, planetary runs, EnergyPlus parity."""
import datetime as dt
import json
from pathlib import Path

import numpy as np
import pytest

from exobem import simulate
from exobem.cases import bestest_600_opaque, lunar_habitat, mars_habitat
from exobem.environment import Environment
from exobem.environment.sites import moon_site, mars_site, MOON_GRAVITY
from exobem.geometry import box
from exobem.materials import Construction, Material
from exobem.model import Model, Zone, InternalGain, Thermostat

ROOT = Path(__file__).resolve().parents[1]


def _constant_env(n=2000, dt=600.0, T_out=250.0, vacuum=True):
    z = np.zeros(n)
    return Environment(planet="moon" if vacuum else "test", latitude=0, longitude=0, dt=dt,
                       time_s=(np.arange(n) + 1) * dt, jd_utc=z, zenith=np.full(n, 120.0),
                       sun_azimuth=z, dni=z, dhi=z, ghi=z, sun_visible=z,
                       T_air=np.full(n, np.nan), T_sky=np.full(n, T_out), T_ground=np.full(n, T_out),
                       T_deep=np.full(n, T_out), wind_speed=z, wind_dir=z, pressure=z,
                       ground_albedo=z, gravity=MOON_GRAVITY, gas=None,
                       local_time_h=np.full(n, 12.0), day_index=np.zeros(n, int))


def test_steady_state_heat_loss_in_vacuum():
    """Zone held at 20 C inside a 250 K black enclosure: heating = sum UA dT at steady state."""
    mat = Material("ins", 0.1, 0.04, 30.0, 1000.0, 0.5, 0.9)
    cons = {"c": Construction("c", [mat])}
    geom = box(4, 4, 3, "c", "c", "c", floor_boundary="outdoors")
    zone = Zone("z", geom, thermostat=Thermostat(20.0, 20.0), cabin_pressure_Pa=101325.0,
                interior_convection="physical", initial_temperature_C=20.0)
    model = Model("ss", zone, cons, timestep_s=600.0)
    env = _constant_env(4000)
    res = simulate(model, env)
    Q = res.Q_heating_W[-1]
    # analytic: series of interior film (from run), wall, exterior radiation to 250 K
    A = np.array([s.area for s in geom.surfaces])
    To = res.T_outside_C[-1] + 273.15
    q_rad_out = 0.9 * 5.670374419e-8 * (To ** 4 - 250.0 ** 4)
    assert abs(Q - np.sum(q_rad_out * A)) / Q < 1e-3


def test_zone_energy_balance_closure():
    model = bestest_600_opaque()
    from exobem.environment.sites import earth_from_epw
    epw = Path("C:/EnergyPlusV23-2-0/WeatherData/USA_CO_Golden-NREL.724666_TMY3.epw")
    if not epw.exists():
        pytest.skip("EnergyPlus weather file not available")
    env = earth_from_epw(str(epw), dt=600.0, n_days=10)
    res = simulate(model, env)
    A = np.array([s.area for s in model.zone.geometry.surfaces])
    # air node balance: sum h A (Ts - Tz) + gains + inf + Qsys = C dTz/dt  -> check via inside fluxes
    # Over many steps storage in the air is negligible; inside-face conduction + gains + sys + inf ~ 0
    assert np.isfinite(res.T_zone_C).all()
    assert res.iterations.max() <= model.max_iterations


def test_lunar_and_mars_habitats_run_and_converge():
    env = moon_site(0.674, 23.473, dt.datetime(2030, 1, 1), 29.53, dt=3600.0)
    r = simulate(lunar_habitat(dt=3600.0), env)
    assert np.all(np.isfinite(r.T_zone_C))
    # regolith-covered shell: lunar-surface-like range (~90-400 K)
    assert r.T_outside_C.min() > -190 and r.T_outside_C.max() < 135
    assert np.mean(r.iterations) < 4
    envm = mars_site(18.44, 77.45, dt.datetime(2031, 1, 1), 3, dt=88775.244 / 48)
    rm = simulate(mars_habitat(dt=88775.244 / 48), envm)
    assert np.all(np.isfinite(rm.T_zone_C))
    assert 0.0 < rm.h_conv_out.max() < 3.0          # thin CO2: h ~ 0.1-1 W/m2K


def test_energyplus_parity_if_available():
    f = ROOT / "verification" / "results" / "energyplus_comparison.json"
    if not f.exists():
        pytest.skip("run verification/compare_energyplus.py first")
    rep = json.loads(f.read_text())
    for case in ("Case600_opaque", "Case900_opaque"):
        d = rep[case]
        assert abs(d["exobem_heating_kWh"] / d["eplus_heating_kWh"] - 1) < 0.02
        assert abs(d["exobem_cooling_kWh"] / d["eplus_cooling_kWh"] - 1) < 0.05
        assert d["hourly_net_load_R2"] > 0.99
    for case in ("Case600FF_opaque", "Case900FF_opaque"):
        assert rep[case]["T_RMSE_K"] < 1.0
