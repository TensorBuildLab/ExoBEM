"""Reference models used for verification and the paper's case studies."""
from __future__ import annotations

from .geometry import box, horizontal_cylinder, dome
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
