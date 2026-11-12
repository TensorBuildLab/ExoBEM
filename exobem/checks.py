"""Input checks that encode what makes a planetary habitat different from an Earth building.

``check_model`` raises :class:`ModelError` for inputs that cannot be physically right off-Earth
and returns warnings for inputs that
are legal but outside NASA habitability limits.
"""
from __future__ import annotations

import warnings

import numpy as np


class ModelError(ValueError):
    pass


# NASA-STD-3001 Vol. 2 (Rev. B, 2019) and the Exploration Atmospheres Working Group (2010)
CABIN_T_RANGE_C = (18.0, 27.0)
CABIN_RH_RANGE = (0.25, 0.75)
MAX_O2_FRACTION = 0.34          # EAWG recommended upper limit for flammability (8.2 psia / 34 % O2)
MIN_PPO2_Pa = 15.8e3            # O2 partial pressure of air at 2,440 m (8,000 ft; 75.3 kPa x 0.2095), the cabin-
                                # altitude limit of transport aircraft (14 CFR 25.841); lower values are hypoxic


def check_model(model, env, strict: bool = True):
    """Validate a model against its environment.  Returns a list of warning strings."""
    z = model.zone
    errs, warns = [], []
    off_earth = env.planet != "earth"
    if off_earth:
        if z.infiltration_ach != 0.0:
            errs.append("infiltration_ach must be 0 off-Earth: a pressurized habitat is sealed and there is no "
                        "outdoor air to infiltrate (use leakage_kg_per_day for cabin gas lost to the outside)")
        if not z.cabin_pressure_Pa or z.cabin_pressure_Pa <= 0:
            errs.append("cabin_pressure_Pa must be > 0 for a habitat")
        else:
            ppo2 = z.cabin_pressure_Pa * z.cabin_o2_fraction
            if ppo2 < MIN_PPO2_Pa:
                errs.append(f"cabin O2 partial pressure {ppo2/1000:.1f} kPa is hypoxic (< {MIN_PPO2_Pa/1000:.1f} kPa)")
        if z.cabin_o2_fraction > MAX_O2_FRACTION:
            warns.append(f"O2 fraction {z.cabin_o2_fraction:.3f} exceeds the {MAX_O2_FRACTION} flammability limit")
        if model.exterior_convection == "tarp":
            errs.append("TARP exterior convection is an Earth-air correlation; use 'auto', 'physical' or 'none'")
        if env.vacuum and model.exterior_convection == "physical":
            errs.append("physical exterior convection requested in vacuum")
        if z.interior_convection == "tarp":
            warns.append("interior TARP convection assumes air at 1 atm and 1 g; 'physical' is recommended off-Earth")
        for s in z.geometry.surfaces:
            if s.boundary not in ("outdoors", "ground", "adiabatic"):
                errs.append(f"surface {s.name}: unknown boundary {s.boundary!r}")
        if model.solar_model == "perez":
            errs.append("the Perez sky model is fitted to Earth air masses; use 'auto' or 'isotropic' off-Earth")
        if any(g.name.lower().startswith(("infiltration", "ventilation")) for g in z.gains):
            warns.append("gain names suggest outdoor air; there is no outdoor air off-Earth")
    if model.timestep_s != env.dt:
        errs.append("model time step differs from the environment time step")
    for nm, sp in (("heating", model.zone.thermostat.heating_setpoint_C), ("cooling", model.zone.thermostat.cooling_setpoint_C)):
        if np.isscalar(sp) and off_earth and not (CABIN_T_RANGE_C[0] <= sp <= CABIN_T_RANGE_C[1]):
            warns.append(f"{nm} set-point {sp} C is outside the NASA-STD-3001 range {CABIN_T_RANGE_C} C")
    if z.humidity_control and not (0.0 < z.rh_min < z.rh_max < 1.0):
        errs.append("humidity limits must satisfy 0 < rh_min < rh_max < 1")
    if z.humidity_control and off_earth and (z.rh_min < CABIN_RH_RANGE[0] or z.rh_max > CABIN_RH_RANGE[1]):
        warns.append(f"humidity band outside the NASA-STD-3001 range {CABIN_RH_RANGE}")
    if errs and strict:
        raise ModelError("; ".join(errs))
    for w in warns:
        warnings.warn(w, stacklevel=2)
    return warns + errs
