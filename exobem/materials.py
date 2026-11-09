"""Materials and layered constructions.

Mirrors the EnergyPlus ``Material``, ``Material:NoMass`` and ``Construction`` objects
and adds what extraterrestrial envelopes need:

* temperature-dependent conductivity and specific heat (lunar regolith after
  Hayne et al. 2017, JGR Planets 122, doi:10.1002/2017JE005387),
* massless resistive layers whose R-value depends on the ambient gas pressure
  (multi-layer insulation works in vacuum but degrades in the 600 Pa Martian
  CO2 atmosphere),
* a library of habitat materials.

Layers are always listed from the outside face to the inside face.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

import numpy as np


ROUGHNESS_MULT = {"VeryRough": 2.17, "Rough": 1.67, "MediumRough": 1.52,
                  "MediumSmooth": 1.13, "Smooth": 1.11, "VerySmooth": 1.00}


@dataclass
class Material:
    name: str
    thickness: float                 # m
    conductivity: float              # W/m-K (reference value)
    density: float                   # kg/m3
    specific_heat: float             # J/kg-K (reference value)
    solar_absorptance: float = 0.7
    thermal_emissivity: float = 0.9
    roughness: str = "MediumRough"
    k_of_T: Optional[Callable[[np.ndarray], np.ndarray]] = None
    cp_of_T: Optional[Callable[[np.ndarray], np.ndarray]] = None

    @property
    def is_massless(self) -> bool:
        return False

    @property
    def temperature_dependent(self) -> bool:
        return self.k_of_T is not None or self.cp_of_T is not None

    def k(self, T):
        return self.k_of_T(T) if self.k_of_T is not None else np.full_like(np.asarray(T, float), self.conductivity)

    def cp(self, T):
        return self.cp_of_T(T) if self.cp_of_T is not None else np.full_like(np.asarray(T, float), self.specific_heat)

    @property
    def resistance(self) -> float:
        return self.thickness / self.conductivity

    def with_thickness(self, t: float, name: str | None = None) -> "Material":
        from dataclasses import replace
        return replace(self, thickness=t, name=name or f"{self.name}_{t:g}m")


@dataclass
class NoMassMaterial:
    """Purely resistive layer (EnergyPlus Material:NoMass)."""
    name: str
    resistance: float                # m2-K/W
    solar_absorptance: float = 0.7
    thermal_emissivity: float = 0.9
    roughness: str = "MediumRough"
    thickness: float = 0.0

    @property
    def is_massless(self) -> bool:
        return True

    @property
    def temperature_dependent(self) -> bool:
        return False


@dataclass
class Construction:
    name: str
    layers: Sequence  # outside -> inside

    @property
    def outside(self):
        return self.layers[0]

    @property
    def inside(self):
        return self.layers[-1]

    def r_value(self) -> float:
        return sum(l.resistance for l in self.layers)

    def u_factor(self, h_in: float = 8.29, h_out: float = 34.0) -> float:
        return 1.0 / (1.0 / h_out + self.r_value() + 1.0 / h_in)

    def heat_capacity(self) -> float:
        return sum(l.density * l.specific_heat * l.thickness for l in self.layers if not l.is_massless)


# ---------------------------------------------------------------------------------
# Temperature-dependent property models
# ---------------------------------------------------------------------------------

def hayne_conductivity(k_contact: float, chi: float = 2.7):
    """Lunar regolith conductivity  k(T) = k_c [1 + chi (T/350)^3]  (Hayne et al. 2017)."""
    def f(T):
        T = np.asarray(T, float)
        return k_contact * (1.0 + chi * (T / 350.0) ** 3)
    return f


_HAYNE_CP = (-3.6125, 2.7431, 2.3616e-3, -1.2340e-5, 8.9093e-9)


def hayne_specific_heat(T):
    """Lunar regolith specific heat [J/kg-K] (Hayne et al. 2017 fit to Hemingway et al. 1981)."""
    T = np.clip(np.asarray(T, float), 20.0, 450.0)
    c0, c1, c2, c3, c4 = _HAYNE_CP
    return c0 + c1 * T + c2 * T**2 + c3 * T**3 + c4 * T**4


# ---------------------------------------------------------------------------------
# Library
# ---------------------------------------------------------------------------------

def library() -> dict:
    m = {}

    def add(mat):
        m[mat.name] = mat
        return mat

    # --- ASHRAE 140 (BESTEST) lightweight case 600 materials -------------------
    add(Material("plasterboard_12mm", 0.012, 0.160, 950.0, 840.0, 0.6, 0.9, "Smooth"))
    add(Material("fiberglass_66mm", 0.066, 0.040, 12.0, 840.0, 0.6, 0.9, "Rough"))
    add(Material("wood_siding_9mm", 0.009, 0.140, 530.0, 900.0, 0.6, 0.9, "Rough"))
    add(Material("plasterboard_10mm", 0.010, 0.160, 950.0, 840.0, 0.6, 0.9, "Smooth"))
    add(Material("fiberglass_1118mm", 0.1118, 0.040, 12.0, 840.0, 0.6, 0.9, "Rough"))
    add(Material("roofdeck_19mm", 0.019, 0.140, 530.0, 900.0, 0.6, 0.9, "Rough"))
    add(Material("timber_floor_25mm", 0.025, 0.140, 650.0, 1200.0, 0.6, 0.9, "Rough"))
    add(NoMassMaterial("floor_insulation_R25", 25.075, 0.6, 0.9))

    # --- habitat structure ------------------------------------------------------
    add(Material("aluminum_2219_4mm", 0.004, 120.0, 2840.0, 864.0, 0.3, 0.1, "Smooth"))
    add(Material("vectran_restraint_5mm", 0.005, 0.20, 1400.0, 1100.0, 0.5, 0.85, "MediumSmooth"))
    add(Material("bladder_polyurethane_3mm", 0.003, 0.20, 1100.0, 1700.0, 0.5, 0.9, "Smooth"))
    add(Material("nomex_liner_2mm", 0.002, 0.04, 400.0, 1200.0, 0.5, 0.9, "Smooth"))
    add(Material("polyimide_foam_50mm", 0.05, 0.030, 10.0, 1100.0, 0.5, 0.9, "Rough"))
    add(Material("hdpe_shield_50mm", 0.05, 0.45, 950.0, 1900.0, 0.4, 0.9, "Smooth"))
    add(Material("water_wall_100mm", 0.10, 0.60, 1000.0, 4180.0, 0.5, 0.95, "Smooth"))
    add(Material("interior_panel_10mm", 0.010, 0.20, 1200.0, 1200.0, 0.5, 0.9, "Smooth"))
    # Silica aerogel blanket, conductivity in ~600-900 Pa CO2 (aerogel retains most of its
    # performance at Mars pressure, unlike MLI); e.g. Mars rover WEB insulation.
    add(Material("aerogel_blanket_20mm", 0.02, 0.012, 150.0, 1000.0, 0.5, 0.9, "MediumRough"))
    # Multi-layer insulation, 20 layers.  Effective emittance ~0.01-0.03 in high vacuum
    # gives R ~ 10-20 m2K/W around 250 K; at Mars pressure gas conduction dominates.
    add(NoMassMaterial("mli_20layer_vacuum", 15.0, 0.12, 0.70, "Smooth"))
    add(NoMassMaterial("mli_20layer_mars", 0.35, 0.12, 0.70, "Smooth"))
    add(Material("beta_cloth_outer_1mm", 0.001, 0.15, 1400.0, 900.0, 0.32, 0.86, "MediumSmooth"))

    # --- regolith covers --------------------------------------------------------
    for t in (0.5, 1.0, 2.0, 3.0):
        add(Material(f"lunar_regolith_cover_{t:g}m", t, 3.4e-3, 1800.0, 600.0, 0.88, 0.95, "VeryRough",
                     k_of_T=hayne_conductivity(3.4e-3), cp_of_T=hayne_specific_heat))
        add(Material(f"mars_regolith_cover_{t:g}m", t, 0.085, 1500.0, 800.0, 0.80, 0.95, "VeryRough"))
    add(Material("lunar_regolith_loose_0.1m", 0.1, 7.4e-4, 1100.0, 600.0, 0.88, 0.95, "VeryRough",
                 k_of_T=hayne_conductivity(7.4e-4), cp_of_T=hayne_specific_heat))
    add(Material("lunar_sintered_regolith_0.3m", 0.3, 0.6, 2400.0, 800.0, 0.85, 0.95, "Rough"))
    add(Material("lunar_ground_3m", 3.0, 3.4e-3, 1800.0, 600.0, 0.88, 0.95, "VeryRough",
                 k_of_T=hayne_conductivity(3.4e-3), cp_of_T=hayne_specific_heat))
    add(Material("mars_ground_3m", 3.0, 0.085, 1500.0, 800.0, 0.80, 0.95, "VeryRough"))
    add(Material("earth_soil_2m", 2.0, 1.2, 1600.0, 1000.0, 0.7, 0.9, "VeryRough"))
    return m
