"""Write the example model files (examples/*.json and the copies shipped in exobem/data/examples).

    python examples/make_examples.py

The JSON models are the tutorial versions of the paper's reference habitats (exobem.cases): the same
geometry, envelope, cabin atmosphere and loads, with 24-hour schedules instead of Python callables (no EVA
days).  Crew values per person from the NASA BVAD (Anderson et al. 2018, Table 3-22 / 3-28).
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent / "exobem" / "data" / "examples"


def day_profile(sleep, awake, exercise, mean):
    """Hourly fractions: sleep 22-06, exercise 17:00-18:30, awake otherwise (mean = 1)."""
    s, a, e = sleep / mean, awake / mean, exercise / mean
    p = [s] * 6 + [a] * 11 + [e] + [0.5 * (e + a)] + [a] * 3 + [s] * 2
    return [round(x, 4) for x in p]


def equal_area_radius(R, n=12):
    return R * math.sqrt(math.pi / (0.5 * n * math.sin(2 * math.pi / n)))


EQUIP = [round(0.7 / 0.9, 4)] * 6 + [round(1 / 0.9, 4)] * 16 + [round(0.7 / 0.9, 4)] * 2
LIGHT = [0.05] * 6 + [1.0] * 16 + [0.05] * 2

MATERIALS = {
    "beta_cloth_sh": {"thickness": 0.001, "conductivity": 0.15, "density": 1400, "specific_heat": 900,
                      "solar_absorptance": 0.40, "thermal_emissivity": 0.90},
    "mli_10layer_sh": {"resistance": 19.2, "solar_absorptance": 0.40, "thermal_emissivity": 0.90},
    "aerogel_blanket_40mm": {"thickness": 0.04, "conductivity": 0.012, "density": 150, "specific_heat": 1000},
    "rack_al_6mm": {"thickness": 0.006, "conductivity": 120, "density": 2700, "specific_heat": 900},
}


def lunar():
    deck = 2 * math.pi * 3.25 ** 2
    P = 14000.0
    eclss, oga, fans, light = 0.25 * P, 900.0, 500.0, round(7.0 * deck)
    return {
        "simulation": {"name": "lunar_surface_habitat", "timestep_s": 3600},
        "site": {"weather_file": "south_pole_30d.pwf"},
        "materials": {k: MATERIALS[k] for k in ("beta_cloth_sh", "mli_10layer_sh", "rack_al_6mm")},
        "constructions": {
            "shell": ["beta_cloth_sh", "mli_10layer_sh", "aluminum_2219_4mm", "interior_panel_10mm"],
            "rack": ["rack_al_6mm"]},
        "geometry": {"type": "vertical_cylinder", "radius": round(equal_area_radius(3.25), 4), "height": 5.25,
                     "wall": "shell", "roof": "shell", "floor": "shell", "n_facets": 12,
                     "floor_boundary": "outdoors", "z0": 1.5},
        "zone": {"cabin_pressure_kPa": 56.5, "o2_fraction": 0.34, "heating_setpoint_C": 20, "cooling_setpoint_C": 25,
                 "leakage_kg_per_day": 0.056, "airlock_cycles_per_day": 0.286, "airlock_loss_kg_per_cycle": 0.99,
                 "humidity_control": True, "rh_min": 0.30, "rh_max": 0.60, "interior_convection": "physical",
                 "cabin_air_velocity": 0.15, "internal_mass": [{"name": "racks_stowage", "construction": "rack",
                                                                "area_m2": round(2 * deck, 1)}]},
        "gains": [
            {"name": "crew_sensible", "power_W": 4 * 85.1, "radiant_fraction": 0.5, "category": "crew",
             "schedule": day_profile(62.0, 91.0, 151.0, 85.1)},
            {"name": "crew_latent", "power_W": 0, "latent_W": 4 * 53.8, "category": "crew",
             "schedule": day_profile(26.0, 48.0, 258.0, 53.8)},
            {"name": "life_support", "power_W": eclss, "radiant_fraction": 0.3, "electric": True, "category": "eclss",
             "coldplate_fraction": 0.5},
            {"name": "o2_electrolysis", "power_W": oga, "radiant_fraction": 0.3, "electric": True, "category": "eclss",
             "heat_fraction": 0.22, "coldplate_fraction": 0.5},
            {"name": "cabin_fans", "power_W": fans, "radiant_fraction": 0.1, "electric": True, "category": "fans"},
            {"name": "lighting", "power_W": light, "radiant_fraction": 0.4, "electric": True, "category": "lighting",
             "schedule": LIGHT},
            {"name": "avionics_equipment", "power_W": P - eclss - oga - fans - light, "radiant_fraction": 0.3,
             "electric": True, "category": "equipment", "coldplate_fraction": 0.6, "schedule": EQUIP}],
        "thermal_control": {"radiator_area_m2": 96, "radiator_azimuth": 0},
        "power": {"pv": [{"area_m2": 100, "tracking": "vertical_single_axis", "cell_efficiency": 0.295,
                          "temp_coeff_per_K": -0.0023, "alpha_front": 0.91}],
                  "battery": {"capacity_kWh": 600, "soc_min": 0.2}},
    }


def mars():
    deck = 2 * math.pi * 3.6 ** 2
    P = 12000.0
    eclss, oga, fans, light = 0.25 * P, 1350.0, 500.0, round(7.0 * deck)
    return {
        "simulation": {"name": "mars_surface_habitat", "timestep_s": 3699.0},
        "site": {"planet": "mars", "name": "Jezero crater", "latitude": 18.44, "longitude": 77.45,
                 "start_utc": "2030-01-01T00:00:00", "duration_sols": 30},
        "materials": {k: MATERIALS[k] for k in ("beta_cloth_sh", "aerogel_blanket_40mm", "rack_al_6mm")},
        "constructions": {
            "shell": ["beta_cloth_sh", "aerogel_blanket_40mm", "aluminum_2219_4mm", "interior_panel_10mm"],
            "rack": ["rack_al_6mm"]},
        "geometry": {"type": "vertical_cylinder", "radius": round(equal_area_radius(3.6), 4), "height": 5.5,
                     "wall": "shell", "roof": "shell", "floor": "shell", "n_facets": 12,
                     "floor_boundary": "outdoors", "z0": 1.5},
        "zone": {"cabin_pressure_kPa": 56.5, "o2_fraction": 0.34, "heating_setpoint_C": 20, "cooling_setpoint_C": 25,
                 "leakage_kg_per_day": 0.072, "airlock_cycles_per_day": 1.43, "airlock_loss_kg_per_cycle": 0.35,
                 "humidity_control": True, "rh_min": 0.30, "rh_max": 0.60, "interior_convection": "physical",
                 "internal_mass": [{"name": "racks_stowage", "construction": "rack", "area_m2": round(2 * deck, 1)}]},
        "gains": [
            {"name": "crew_sensible", "power_W": 6 * 76.5, "radiant_fraction": 0.5, "category": "crew",
             "schedule": day_profile(44.0, 85.0, 147.0, 76.5)},
            {"name": "crew_latent", "power_W": 0, "latent_W": 6 * 76.3, "category": "crew",
             "schedule": day_profile(44.0, 54.0, 361.6, 76.3)},
            {"name": "life_support", "power_W": eclss, "radiant_fraction": 0.3, "electric": True, "coldplate_fraction": 0.5},
            {"name": "o2_electrolysis", "power_W": oga, "radiant_fraction": 0.3, "electric": True, "heat_fraction": 0.22,
             "coldplate_fraction": 0.5},
            {"name": "cabin_fans", "power_W": fans, "radiant_fraction": 0.1, "electric": True},
            {"name": "lighting", "power_W": light, "radiant_fraction": 0.4, "electric": True, "schedule": LIGHT},
            {"name": "avionics_equipment", "power_W": P - eclss - fans - light, "radiant_fraction": 0.3, "electric": True,
             "coldplate_fraction": 0.6, "schedule": EQUIP}],
        "thermal_control": {"radiator_area_m2": 80, "radiator_azimuth": 0},
        "power": {"fission": {"rated_kWe": 40, "efficiency": 0.181}},
    }


if __name__ == "__main__":
    PKG.mkdir(parents=True, exist_ok=True)
    for name, cfg in (("lunar_surface_habitat", lunar()), ("mars_surface_habitat", mars())):
        txt = json.dumps(cfg, indent=2)
        for d in (HERE, PKG):
            (d / f"{name}.json").write_text(txt + "\n", encoding="utf-8")
        print("wrote", name)
