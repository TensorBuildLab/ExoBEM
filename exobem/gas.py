"""Thermophysical properties of the gases that surround or fill a habitat.

Three gases matter for ExoBEM:

* ``earth_air``  - moist Earth air (used for Earth-mode verification runs),
* ``cabin_air``  - an N2/O2 cabin atmosphere at an arbitrary total pressure,
* ``mars_co2``   - the Martian atmosphere (95 % CO2) at ~400-1000 Pa.

Viscosity and conductivity follow Sutherland-type fits that are adequate
(+/- 3 %) between 150 K and 350 K; density follows the ideal-gas law, which
is essentially exact at these pressures.  On the Moon there is no gas at
all, which is expressed with :data:`VACUUM`.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from .constants import R_UNIVERSAL


@dataclass(frozen=True)
class Gas:
    name: str
    molar_mass: float        # kg/mol
    cp: float                # J/kg-K (treated as constant)
    mu_ref: float            # Pa-s at T_ref
    k_ref: float             # W/m-K at T_ref
    T_ref: float             # K
    S_mu: float              # Sutherland constant for viscosity, K
    S_k: float               # Sutherland constant for conductivity, K

    @property
    def R(self) -> float:
        return R_UNIVERSAL / self.molar_mass

    def density(self, T: float, P: float) -> float:
        return P / (self.R * T)

    def viscosity(self, T: float) -> float:
        return self.mu_ref * (T / self.T_ref) ** 1.5 * (self.T_ref + self.S_mu) / (T + self.S_mu)

    def conductivity(self, T: float) -> float:
        return self.k_ref * (T / self.T_ref) ** 1.5 * (self.T_ref + self.S_k) / (T + self.S_k)

    def prandtl(self, T: float) -> float:
        return self.cp * self.viscosity(T) / self.conductivity(T)

    def kinematic_viscosity(self, T: float, P: float) -> float:
        return self.viscosity(T) / self.density(T, P)

    def diffusivity(self, T: float, P: float) -> float:
        return self.conductivity(T) / (self.density(T, P) * self.cp)


# Dry air (Sutherland constants from White, Viscous Fluid Flow).
DRY_AIR = Gas("air", 0.0289647, 1005.0, 1.716e-5, 0.0241, 273.15, 110.4, 194.0)

# Carbon dioxide; Mars atmosphere is ~95 % CO2, 2.8 % N2, 2 % Ar (Franz et al. 2017).
# Reference values at 273.15 K: mu = 1.370e-5 Pa-s, k = 0.01465 W/m-K; cp at ~210 K
# is ~735 J/kg-K and at 240 K ~780 J/kg-K (NIST Webbook); 760 is used.  A blended molar mass of 43.34 g/mol is used.
MARS_CO2 = Gas("mars_co2", 0.04334, 760.0, 1.370e-5, 0.01465, 273.15, 222.0, 1800.0)


def cabin_gas(o2_fraction: float = 0.21) -> Gas:
    """N2/O2 mixture with the given O2 mole fraction (cabin atmospheres)."""
    x = o2_fraction
    M = x * 0.031999 + (1 - x) * 0.028014
    # O2 is slightly more viscous/conductive than N2; mixture rule kept linear.
    mu = 1.716e-5 * (1 + 0.12 * (x - 0.21))
    k = 0.0241 * (1 + 0.02 * (x - 0.21))
    cp = 1005.0 - 120.0 * (x - 0.21)
    return Gas(f"cabin_o2_{x:.3f}", M, cp, mu, k, 273.15, 110.4, 194.0)


VACUUM = None  # sentinel: no convective medium (lunar surface)


def humidity_ratio_from_dewpoint(T_dp_C: float, P: float) -> float:
    """Humidity ratio [kg/kg] from dew point [C] and total pressure [Pa] (Earth mode)."""
    T = T_dp_C + 273.15
    # Hyland-Wexler-like saturation pressure (Magnus fit is enough for loads work).
    if T_dp_C >= 0:
        pws = 610.94 * math.exp(17.625 * T_dp_C / (T_dp_C + 243.04))
    else:
        pws = 611.21 * math.exp(22.587 * T_dp_C / (T_dp_C + 273.86))
    pws = min(pws, 0.99 * P)
    return 0.621945 * pws / (P - pws)


def moist_air_cp(w: float) -> float:
    """Specific heat of moist air [J/kg-K] as used by EnergyPlus (PsyCpAirFnW)."""
    return 1.00484e3 + 1.85895e3 * w


def moist_air_density(P: float, T_C: float, w: float) -> float:
    """Moist air density [kg/m3] as used by EnergyPlus (PsyRhoAirFnPbTdbW)."""
    return P / (287.0 * (T_C + 273.15) * (1.0 + 1.6077687 * w))
