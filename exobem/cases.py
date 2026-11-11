"""Reference models used for verification and the paper's case studies."""
from __future__ import annotations

import numpy as np

from .geometry import box, dome, horizontal_cylinder, vertical_cylinder
from .materials import Construction, library
from .model import Model, Zone, InternalGain, Thermostat, ThermalControlSystem


def bestest_600_opaque(dt=600.0, heating=20.0, cooling=27.0, free_float=False, infiltration_ach=0.5,
                       heavy=False):
    """ASHRAE 140 Case 600 (lightweight) / Case 900 (``heavy=True``) envelope, without
    windows (opaque south wall).

    8 m x 6 m x 2.7 m, 200 W internal gain (60 % radiative), 0.5 ACH, 20/27 C ideal loads.
    The floor sits on R-25 insulation over ground held at 10 C.
    """
    from .materials import Material, NoMassMaterial
    m = library()
    if heavy:
        cons = {
            "wall": Construction("wall", [m["wood_siding_9mm"],
                                          Material("foam_615", 0.0615, 0.04, 10.0, 1400.0, 0.6, 0.9, "Rough"),
                                          Material("block_100", 0.100, 0.51, 1400.0, 1000.0, 0.6, 0.9, "Rough")]),
            "roof": Construction("roof", [m["roofdeck_19mm"], m["fiberglass_1118mm"], m["plasterboard_10mm"]]),
            "floor": Construction("floor", [NoMassMaterial("floor_ins_900", 25.175, 0.6, 0.9),
                                            Material("slab_80", 0.080, 1.13, 1400.0, 1000.0, 0.6, 0.9, "Rough")]),
        }
    else:
        cons = {
            "wall": Construction("wall", [m["wood_siding_9mm"], m["fiberglass_66mm"], m["plasterboard_12mm"]]),
            "roof": Construction("roof", [m["roofdeck_19mm"], m["fiberglass_1118mm"], m["plasterboard_10mm"]]),
            "floor": Construction("floor", [m["floor_insulation_R25"], m["timber_floor_25mm"]]),
        }
    geom = box(8.0, 6.0, 2.7, "wall", "roof", "floor")
    th = Thermostat(-100.0, 100.0) if free_float else Thermostat(heating, cooling)
    zone = Zone("case600", geom, gains=[InternalGain("other", 200.0, 0.6)], thermostat=th,
                infiltration_ach=infiltration_ach, interior_convection="tarp", cabin_pressure_Pa=0.0)
    return Model("BESTEST600_opaque", zone, cons, timestep_s=dt, terrain="Country")


# ----------------------------------------------------------------------------------
def crew_gains(n_crew=4, sensible_per_crew=85.1, latent_per_crew=53.8, equipment_W=2500.0,
               lighting_W=400.0, schedule="earth"):
    """Crew metabolic + equipment gains.

    Crew values are the NASA BVAD nominal crew member (Anderson et al. 2018, Table 3-33):
    12.0 MJ/d = 85.1 W sensible + 53.8 W latent (daily means).  Crew sleep 22:00-06:00
    local clock time; sleeping metabolic rate is ~0.65 of the awake rate (BVAD Table 3-22),
    so the schedule is normalised to a daily mean of 1.0.  Equipment runs continuously at
    70 % with a 30 % increase during work hours.
    """
    a = 24.0 / (16 + 8 * 0.65)
    occ = [0.65 * a] * 6 + [a] * 16 + [0.65 * a] * 2
    eq = [0.7] * 7 + [1.0] * 12 + [0.85] * 5
    lt = [0.2] * 6 + [1.0] * 16 + [0.2] * 2
    return [
        InternalGain("crew", n_crew * sensible_per_crew, 0.5, n_crew * latent_per_crew, occ),
        InternalGain("equipment", equipment_W, 0.3, 0.0, eq),
        InternalGain("lighting", lighting_W, 0.4, 0.0, lt),
    ]


def lunar_habitat(dt=1800.0, shield="lunar_regolith_cover_1m", insulation="mli_20layer_vacuum",
                  n_crew=4, radiator_area=40.0, radiator_azimuth=0.0, cabin_kPa=70.3, o2=0.265,
                  leak_kg_day=0.1, heating=18.0, cooling=27.0, interior_convection="physical"):
    """Horizontal-cylinder surface habitat (radius 3 m, length 10 m) on the lunar surface.

    Pressure shell (Al-2219) + MLI + optional regolith radiation-shielding cover.
    Cabin at 70.3 kPa / 26.5 % O2 (NASA exploration atmosphere, Artemis surface habitats).
    """
    m = library()
    layers = []
    if shield:
        layers.append(m[shield])
    layers += [m["beta_cloth_outer_1mm"], m[insulation], m["aluminum_2219_4mm"], m["interior_panel_10mm"]]
    cons = {
        "shell": Construction("shell", layers),
        "end": Construction("end", layers),
        "floor": Construction("floor", [m["lunar_ground_3m"], m[insulation], m["aluminum_2219_4mm"],
                                        m["interior_panel_10mm"]]),
    }
    geom = horizontal_cylinder(3.0, 10.0, "shell", "end", "floor", axis_azimuth=90.0, n_facets=16)
    zone = Zone("lunar_hab", geom, gains=crew_gains(n_crew), thermostat=Thermostat(heating, cooling),
                cabin_pressure_Pa=cabin_kPa * 1000.0, cabin_o2_fraction=o2, leakage_kg_per_day=leak_kg_day,
                interior_convection=interior_convection, initial_temperature_C=21.0)
    tcs = ThermalControlSystem(radiator_area_m2=radiator_area, radiator_azimuth=radiator_azimuth)
    return Model("lunar_habitat", zone, cons, timestep_s=dt, thermal_control=tcs)


def mars_habitat(dt=1800.0, shield="mars_regolith_cover_1m", insulation="aerogel_blanket_20mm",
                 n_crew=4, radiator_area=40.0, cabin_kPa=70.3, o2=0.265, leak_kg_day=0.1,
                 heating=18.0, cooling=27.0, interior_convection="physical", geometry="cylinder"):
    m = library()
    layers = []
    if shield:
        layers.append(m[shield])
    layers += [m["beta_cloth_outer_1mm"], m[insulation], m["aluminum_2219_4mm"], m["interior_panel_10mm"]]
    cons = {
        "shell": Construction("shell", layers),
        "end": Construction("end", layers),
        "floor": Construction("floor", [m["mars_ground_3m"], m[insulation], m["aluminum_2219_4mm"],
                                        m["interior_panel_10mm"]]),
    }
    if geometry == "dome":
        geom = dome(5.0, "shell", "floor")
    else:
        geom = horizontal_cylinder(3.0, 10.0, "shell", "end", "floor", axis_azimuth=90.0, n_facets=16)
    zone = Zone("mars_hab", geom, gains=crew_gains(n_crew), thermostat=Thermostat(heating, cooling),
                cabin_pressure_Pa=cabin_kPa * 1000.0, cabin_o2_fraction=o2, leakage_kg_per_day=leak_kg_day,
                interior_convection=interior_convection, initial_temperature_C=21.0)
    tcs = ThermalControlSystem(radiator_area_m2=radiator_area, radiator_azimuth=0.0)
    return Model("mars_habitat", zone, cons, timestep_s=dt, thermal_control=tcs)


# ==================================================================================
# Reference habitats for the first crews (sourced parameters: docs/research/habitat_eclss_power_dossier.md)
# ==================================================================================
def _crew_schedule(sleep, awake, exercise, mean, hours=(22.0, 6.0), exercise_hours=(17.0, 18.5),
                   eva_days=(), eva_hours=(9.0, 17.0), eva_fraction_absent=0.5):
    """Callable schedule (local clock hour, day index) -> fraction of the design (daily mean) value.

    Per-person levels for sleep / awake / exercise are divided by the daily ``mean`` so that the
    schedule averages 1.0 on a day without EVA.  On EVA days (day index modulo 7 in ``eva_days``) the
    fraction ``eva_fraction_absent`` of the crew is outside between ``eva_hours``.
    """
    s0, s1 = hours
    e0, e1 = exercise_hours
    v0, v1 = eva_hours

    def f(t, day):
        t = np.asarray(t, float) % 24.0
        day = np.asarray(day)
        asleep = (t >= s0) | (t < s1)
        exer = (t >= e0) & (t < e1)
        lvl = np.where(asleep, sleep, np.where(exer, exercise, awake)) / mean
        if eva_days:
            on_eva = np.isin(day % 7, eva_days) & (t >= v0) & (t < v1)
            lvl = np.where(on_eva, lvl * (1.0 - eva_fraction_absent), lvl)
        return lvl
    return f


def _equal_area_radius(R, n):
    """Circumradius of an n-sided prism with the floor area (and volume) of a cylinder of radius R."""
    return R * np.sqrt(np.pi / (0.5 * n * np.sin(2 * np.pi / n)))


def _equipment_schedule(night=0.7, hours=(22.0, 6.0)):
    def f(t, day):
        t = np.asarray(t, float) % 24.0
        asleep = (t >= hours[0]) | (t < hours[1])
        mean = (8 * night + 16) / 24.0
        return np.where(asleep, night, 1.0) / mean
    return f


def _habitat_materials(mli_R=5.0):
    from .materials import Material, NoMassMaterial
    m = library()
    # NASA lunar Surface Habitat outer layer: beta cloth, alpha 0.40, eps 0.90 (Schunk et al. 2022)
    m["beta_cloth_sh"] = Material("beta_cloth_sh", 0.001, 0.15, 1400.0, 900.0, 0.40, 0.90, "MediumSmooth")
    # 10-layer MLI blanket; effective R calibrated to the NASA night heat leak (1550 W at 293 K)
    m["mli_10layer_sh"] = NoMassMaterial("mli_10layer_sh", mli_R, 0.40, 0.90, "Smooth")
    # Load-bearing floor insulation (MLI loses its performance when compressed): polyimide foam
    m["floor_foam_50mm"] = Material("floor_foam_50mm", 0.05, 0.030, 10.0, 1100.0, 0.5, 0.9, "Rough")
    # Equipment racks and stowage, aluminium-equivalent 6 mm (internal thermal mass, assumption)
    m["rack_al_6mm"] = Material("rack_al_6mm", 0.006, 120.0, 2700.0, 900.0, 0.5, 0.85, "Smooth")
    # Mars: aerogel blanket under a beta-cloth dust cover (MLI is ineffective in 0.7 kPa CO2)
    m["aerogel_blanket_40mm"] = Material("aerogel_blanket_40mm", 0.04, 0.012, 150.0, 1000.0, 0.5, 0.9, "MediumRough")
    return m


LUNAR_MLI_R = 19.2    # m2K/W, effective R of the 10-layer MLI: calibrated to NASA's 1550 W night heat leak (studies/calibrate_lunar_mli.py)


def artemis_surface_habitat(dt=1800.0, n_crew=4, cabin_kPa=56.5, o2=0.34, shield=None, mli_R=None,
                            heating=20.0, cooling=25.0, radiator_area=96.0, radiator_azimuth=0.0,
                            electric_kW=14.0, elevation_m=1.5, eva_per_week=2):
    """Four-crew lunar surface habitat (Artemis Base Camp class; NASA concept values).

    * Vertical cylinder D = 6.5 m, H = 5.25 m: 174 m3 pressurized (Stromgren et al. 2023; Schunk et al. 2021),
      standing on lander legs ``elevation_m`` above the regolith; floor exposed to the ground.
    * Envelope: beta cloth (alpha 0.40, eps 0.90) over 10-layer MLI over an aluminium structure
      (Schunk et al. 2022); ``shield`` adds a regolith cover (e.g. 'lunar_regolith_cover_1m').
    * Cabin 56.5 kPa / 34 % O2 (exploration atmosphere for frequent EVA; Anderson et al. 2018),
      20-25 C control band, RH 30-60 % (NASA-STD-3001).
    * Leakage 0.05 %/day of the cabin gas mass (Anderson et al. 2018); EVA airlock cycles with the gas
      left at 6.9 kPa (1 psia) in a 12 m3 airlock vented per cycle (assumption).
    * Crew per person (BVAD nominal): sleep 62 W + 26 W latent, awake 91 W + 48 W, daily mean 85.1 + 53.8.
    * Electric power inside the pressure shell ``electric_kW`` (daytime design; the NASA habitat is
      sized for 15 kWe including thermal control), split as life support 25 % (ISS ratio, assumption),
      O2 electrolysis 0.9 kW (22 % released as heat), fans 0.5 kW, lighting 7 W/m2 of deck, the rest
      avionics and crew equipment; 60 % of avionics and 50 % of life-support heat goes to cold plates.
    """
    from .model import InternalMass
    from .gas import cabin_gas
    m = _habitat_materials(LUNAR_MLI_R if mli_R is None else mli_R)
    shell = [m["beta_cloth_sh"], m["mli_10layer_sh"], m["aluminum_2219_4mm"], m["interior_panel_10mm"]]
    if shield:
        shell = [m[shield]] + shell
    # on legs the floor carries no load, so it has the same MLI as the shell; on the ground MLI would be
    # crushed, so a load-bearing foam is used instead
    floor = ([m["beta_cloth_sh"], m["mli_10layer_sh"], m["aluminum_2219_4mm"], m["interior_panel_10mm"]] if not shield
             else [m["lunar_ground_3m"], m["floor_foam_50mm"], m["aluminum_2219_4mm"], m["interior_panel_10mm"]])
    cons = {"shell": Construction("shell", shell), "roof": Construction("roof", shell),
            "floor": Construction("floor", floor), "rack": Construction("rack", [m["rack_al_6mm"]])}
    geom = vertical_cylinder(_equal_area_radius(3.25, 12), 5.25, "shell", "roof", "floor", n_facets=12,
                             floor_boundary="ground" if shield else "outdoors", z0=0.0 if shield else elevation_m)
    deck_area = 2 * np.pi * 3.25 ** 2                                    # two decks
    cabin = cabin_gas(o2)
    m_gas = cabin.density(295.0, cabin_kPa * 1e3) * geom.volume
    eva = (1, 4)[:eva_per_week]
    sens = _crew_schedule(62.0, 91.0, 151.0, 85.1, exercise_hours=(17.0, 18.5), eva_days=eva)
    lat = _crew_schedule(26.0, 48.0, 258.0, 53.8, exercise_hours=(17.0, 18.5), eva_days=eva)
    P = electric_kW * 1000.0
    eclss, oga, fans, light = 0.25 * P, 900.0, 500.0, 7.0 * deck_area
    avionics = P - eclss - oga - fans - light
    eq = _equipment_schedule(0.7)
    lt = [0.05] * 6 + [1.0] * 16 + [0.05] * 2
    gains = [
        InternalGain("crew_sensible", n_crew * 85.1, 0.5, 0.0, sens, category="crew"),
        InternalGain("crew_latent", 0.0, 0.5, n_crew * 53.8, lat, category="crew"),
        InternalGain("life_support", eclss, 0.3, 0.0, 1.0, True, "eclss", 1.0, 0.5),
        InternalGain("o2_electrolysis", oga, 0.3, 0.0, 1.0, True, "eclss", 0.22, 0.5),
        InternalGain("cabin_fans", fans, 0.1, 0.0, 1.0, True, "fans"),
        InternalGain("lighting", light, 0.4, 0.0, lt, True, "lighting"),
        InternalGain("avionics_equipment", avionics, 0.3, 0.0, eq, True, "equipment", 1.0, 0.6),
    ]
    zone = Zone("lunar_surface_habitat", geom, gains, Thermostat(heating, cooling), cabin_pressure_Pa=cabin_kPa * 1e3,
                cabin_o2_fraction=o2, leakage_kg_per_day=0.0005 * m_gas,
                airlock_cycles_per_day=eva_per_week / 7.0,
                airlock_loss_kg_per_cycle=6900.0 * 12.0 / (cabin.R * 295.0),
                interior_convection="physical", cabin_air_velocity=0.15, initial_temperature_C=22.0,
                internal_mass=[InternalMass("racks_stowage", "rack", 2.0 * deck_area)],
                humidity_control=True, rh_max=0.60, rh_min=0.30, initial_rh=0.45)
    tcs = ThermalControlSystem(radiator_area_m2=radiator_area, radiator_azimuth=radiator_azimuth)
    return Model("lunar_surface_habitat", zone, cons, timestep_s=dt, thermal_control=tcs)


def mars_surface_habitat(dt=None, n_crew=6, cabin_kPa=56.5, o2=0.34, shield=None, heating=20.0, cooling=25.0,
                         radiator_area=80.0, electric_kW=12.0, oga_kW=1.35, elevation_m=1.5, eva_per_week=5):
    """Six-crew Mars surface habitat (NASA DRA 5.0 class).

    * Vertical two-deck cylinder D = 7.2 m, H = 5.5 m: 224 m3 pressurized (25 m3 net habitable volume per
      person, Whitmire et al. 2014, over the 0.73 habitable/pressurized ratio of the lunar habitat).
    * Envelope: beta cloth over 40 mm silica aerogel (MLI is ineffective in 0.7 kPa CO2) over aluminium.
    * Cabin 56.5 kPa / 34 % O2; 20-25 C; RH 30-60 %.  Leakage 0.05 %/day; one 2-person EVA per workday (5 airlock cycles a week,
      Anderson et al. 2018) through a 4.25 m3 airlock vented from 6.9 kPa.
    * Crew per person (BVAD long-duration): sleep 44 + 44 W latent, awake 85 + 54 W, daily mean 76.5 + 76.3.
    * Electric power inside the shell: 12 kWe (DRA 5.0) + 1.35 kW O2 electrolysis (22 % heat).
    * Schedules follow local mean solar time (a 24.66 h sol); the time step defaults to 1/24 sol.
    """
    from .model import InternalMass
    from .gas import cabin_gas
    from .ephemeris.mars import MARS_SOL_SECONDS
    dt = dt or MARS_SOL_SECONDS / 24.0
    m = _habitat_materials()
    shell = [m["beta_cloth_sh"], m["aerogel_blanket_40mm"], m["aluminum_2219_4mm"], m["interior_panel_10mm"]]
    if shield:
        shell = [m[shield]] + shell
    floor = ([m["beta_cloth_sh"], m["aerogel_blanket_40mm"], m["aluminum_2219_4mm"], m["interior_panel_10mm"]] if not shield
             else [m["mars_ground_3m"], m["floor_foam_50mm"], m["aluminum_2219_4mm"], m["interior_panel_10mm"]])
    cons = {"shell": Construction("shell", shell), "roof": Construction("roof", shell),
            "floor": Construction("floor", floor), "rack": Construction("rack", [m["rack_al_6mm"]])}
    geom = vertical_cylinder(_equal_area_radius(3.6, 12), 5.5, "shell", "roof", "floor", n_facets=12,
                             floor_boundary="ground" if shield else "outdoors", z0=0.0 if shield else elevation_m)
    deck_area = 2 * np.pi * 3.6 ** 2
    cabin = cabin_gas(o2)
    m_gas = cabin.density(295.0, cabin_kPa * 1e3) * geom.volume
    workdays = (0, 1, 2, 3, 4)
    sens = _crew_schedule(44.0, 85.0, 147.0, 76.5, exercise_hours=(17.0, 19.0), eva_days=workdays,
                          eva_fraction_absent=2.0 / n_crew)
    lat = _crew_schedule(44.0, 54.0, 361.6, 76.3, exercise_hours=(17.0, 19.0), eva_days=workdays,
                         eva_fraction_absent=2.0 / n_crew)
    P = electric_kW * 1000.0
    eclss, fans, light = 0.25 * P, 500.0, 7.0 * deck_area
    avionics = P - eclss - fans - light
    eq = _equipment_schedule(0.7)
    lt = [0.05] * 6 + [1.0] * 16 + [0.05] * 2
    gains = [
        InternalGain("crew_sensible", n_crew * 76.5, 0.5, 0.0, sens, category="crew"),
        InternalGain("crew_latent", 0.0, 0.5, n_crew * 76.3, lat, category="crew"),
        InternalGain("life_support", eclss, 0.3, 0.0, 1.0, True, "eclss", 1.0, 0.5),
        InternalGain("o2_electrolysis", oga_kW * 1000.0, 0.3, 0.0, 1.0, True, "eclss", 0.22, 0.5),
        InternalGain("cabin_fans", fans, 0.1, 0.0, 1.0, True, "fans"),
        InternalGain("lighting", light, 0.4, 0.0, lt, True, "lighting"),
        InternalGain("avionics_equipment", avionics, 0.3, 0.0, eq, True, "equipment", 1.0, 0.6),
    ]
    zone = Zone("mars_surface_habitat", geom, gains, Thermostat(heating, cooling), cabin_pressure_Pa=cabin_kPa * 1e3,
                cabin_o2_fraction=o2, leakage_kg_per_day=0.0005 * m_gas,
                airlock_cycles_per_day=eva_per_week / 7.0,
                airlock_loss_kg_per_cycle=6900.0 * 4.25 / (cabin.R * 295.0),
                interior_convection="physical", cabin_air_velocity=0.15, initial_temperature_C=22.0,
                internal_mass=[InternalMass("racks_stowage", "rack", 2.0 * deck_area)],
                humidity_control=True, rh_max=0.60, rh_min=0.30, initial_rh=0.45)
    tcs = ThermalControlSystem(radiator_area_m2=radiator_area, radiator_azimuth=0.0)
    return Model("mars_surface_habitat", zone, cons, timestep_s=dt, thermal_control=tcs)
