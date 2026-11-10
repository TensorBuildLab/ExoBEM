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
    """A heat source inside the pressurized volume.

    ``power_W`` is the design power (multiplied by the schedule): for crew the sensible metabolic heat,
    for equipment its electric power.  ``latent_W`` is released as water vapour.
    ``electric=True`` marks electrical consumers (equipment, life support, lighting, fans): their
    power is counted as electric demand by the power system.
    ``heat_fraction`` is the share of ``power_W`` released as heat inside the habitat (1 for nearly all
    equipment in a sealed cabin; ~0.2 for water electrolysis, whose energy leaves as H2/O2 chemical energy).
    ``coldplate_fraction`` is the share of that heat collected directly by cold plates into the coolant
    loop (it bypasses the cabin air and goes straight to the thermal control system).
    """
    name: str
    power_W: float                      # sensible design power
    radiant_fraction: float = 0.5
    latent_W: float = 0.0
    schedule: ScheduleLike = 1.0
    electric: bool = False
    category: str = ""                  # e.g. crew | eclss | equipment | lighting | fans
    heat_fraction: float = 1.0
    coldplate_fraction: float = 0.0


@dataclass
class InternalMass:
    """Furniture, racks and stowage exposed to the cabin (EnergyPlus InternalMass): one face
    exchanges heat with the zone, the other is adiabatic."""
    name: str
    construction: str
    area_m2: float


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
    infiltration_ach: float = 0.0           # Earth only: outdoor-air exchange [1/h]; must be 0 off-Earth
    leakage_kg_per_day: float = 0.0         # habitats: cabin-gas loss to the outside, made up from storage
    airlock_cycles_per_day: float = 0.0     # airlock depress/repress cycles (EVA) per day
    airlock_loss_kg_per_cycle: float = 0.0  # cabin gas vented overboard per cycle
    makeup_gas_temperature_C: Optional[float] = None   # None: make-up gas enters at cabin temperature
    air_capacitance_multiplier: float = 1.0
    interior_convection: str = "tarp"       # tarp | tarp_scaled | physical
    cabin_air_velocity: float = 0.15        # m/s (NASA-STD-3001: 0.076-0.2 m/s)
    initial_temperature_C: float = 20.0
    internal_mass: List[InternalMass] = field(default_factory=list)
    # cabin humidity control by a condensing heat exchanger (NASA-STD-3001: RH 25-75 %)
    humidity_control: bool = False          # Earth verification runs keep EnergyPlus' sensible-only loads
    rh_max: float = 0.60
    rh_min: float = 0.25
    initial_rh: float = 0.45

    @property
    def gas_loss_kg_per_day(self) -> float:
        """Cabin gas lost overboard per day (leakage + airlock venting)."""
        return self.leakage_kg_per_day + self.airlock_cycles_per_day * self.airlock_loss_kg_per_cycle


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
    curvature: str = "auto"                 # auto: curved shells as cylinders/spheres | off: planar layers (EnergyPlus)
    thermal_control: Optional[ThermalControlSystem] = None
