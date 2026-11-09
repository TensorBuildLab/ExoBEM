"""Model definition objects (the ExoBEM equivalent of an EnergyPlus input file)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Union

import numpy as np

from .geometry import Geometry
from .materials import Construction


ScheduleLike = Union[float, Sequence[float], Callable]


def evaluate_schedule(sched: ScheduleLike, local_time_h, day_index):
    """Schedules are constants, 24 hourly fractions (by local clock hour), or callables
    ``f(local_time_h, day_index) -> fraction``."""
    lt = np.asarray(local_time_h)
    if callable(sched):
        return np.asarray(sched(lt, np.asarray(day_index)), float) * np.ones_like(lt, dtype=float)
    if np.isscalar(sched):
        return np.full(lt.shape, float(sched))
    arr = np.asarray(sched, float)
    idx = np.clip(np.floor(lt - 1e-9).astype(int) % len(arr), 0, len(arr) - 1)
    return arr[idx]


@dataclass
class InternalGain:
    name: str
    power_W: float                      # sensible design power
    radiant_fraction: float = 0.5
    latent_W: float = 0.0
    schedule: ScheduleLike = 1.0


@dataclass
class Thermostat:
    heating_setpoint_C: ScheduleLike = 20.0
    cooling_setpoint_C: ScheduleLike = 27.0


@dataclass
class Zone:
    name: str
    geometry: Geometry
    gains: List[InternalGain] = field(default_factory=list)
    thermostat: Thermostat = field(default_factory=Thermostat)
    cabin_pressure_Pa: float = 101325.0
    cabin_o2_fraction: float = 0.21
    infiltration_ach: float = 0.0           # Earth: outdoor-air exchange [1/h]
    leakage_kg_per_day: float = 0.0         # habitats: cabin-gas loss, made up from storage
    makeup_gas_temperature_C: Optional[float] = None
    air_capacitance_multiplier: float = 1.0
    interior_convection: str = "tarp"       # tarp | tarp_scaled | physical
    cabin_air_velocity: float = 0.15        # m/s (ISS requirement 0.076-0.2 m/s)
    initial_temperature_C: float = 20.0


@dataclass
class ThermalControlSystem:
    """Habitat active thermal control (post-processed from the ideal loads).

    Heating: electric resistance / heat pump with COP ``heating_cop``.
    Cooling: vapour-compression heat pump that lifts cabin heat to a radiator, or
    passive pumped-loop rejection when the radiator sink is cold enough.
    """
    radiator_area_m2: float = 40.0
    radiator_emissivity: float = 0.80
    radiator_absorptance: float = 0.10      # silver-Teflon, mid-life (0.07 BOL -> 0.14 EOL, BVAD)
    radiator_tilt: float = 90.0             # vertical
    radiator_azimuth: float = 0.0           # facing north (pole-facing) by default
    radiator_two_sided: bool = True
    cabin_loop_temperature_C: float = 2.0   # cold-plate / condensing HX coolant temperature
    approach_K: float = 5.0
    carnot_fraction: float = 0.40
    heating_cop: float = 1.0
    pump_fan_W: float = 150.0


@dataclass
class Model:
    name: str
    zone: Zone
    constructions: Dict[str, Construction]
    timestep_s: float = 600.0
    solar_model: str = "auto"               # auto | isotropic | perez
    exterior_convection: str = "auto"       # auto | tarp | physical | none
    terrain: str = "Country"                # Earth wind profile terrain class
    max_iterations: int = 6
    tolerance_K: float = 0.005
    initialize: str = "auto"                # auto | steady | none
    thermal_control: Optional[ThermalControlSystem] = None
