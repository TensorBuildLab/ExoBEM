"""ExoBEM - Extraterrestrial Building Energy Modeling.

An open-source building energy simulation engine for lunar and Martian habitats.
Its zone heat-balance core re-implements the algorithms documented in the
EnergyPlus(TM) Engineering Reference (U.S. DOE) and extends them with planetary
ephemerides, airless and thin-CO2 environments, regolith thermophysics,
gravity-aware convection and radiator-based heat rejection.

ExoBEM is not EnergyPlus and is not endorsed by the U.S. Department of Energy.
"""
__version__ = "0.2.0"

from .model import Model, Zone, InternalGain, Thermostat, ThermalControlSystem  # noqa: F401
from .simulation import simulate  # noqa: F401
from . import geometry, materials, environment  # noqa: F401
