"""One-dimensional thermophysical model of the planetary ground (regolith).

Provides the ground-surface temperature that habitat surfaces exchange long-wave
radiation with, and the deep-ground temperature used as the boundary of floors and
regolith berms.  The lunar model follows Hayne et al. (2017, JGR Planets 122,
2371-2400, doi:10.1002/2017JE005387):

* density  rho(z) = rho_d - (rho_d - rho_s) exp(-z/H)
* contact conductivity k_c(z) scales linearly with density between k_s and k_d,
  and k(T) = k_c [1 + chi (T/350 K)^3]   (radiative conduction between grains)
* specific heat c_p(T): 4th-order polynomial (Hemingway et al. 1981)
* albedo A(i) = A0 + a (i/45)^3 + b (i/90)^8,  emissivity 0.95,
  geothermal heat flux at the base.

For Mars a homogeneous column is parameterised by its thermal inertia
I = sqrt(k rho c) (gas-filled pores at ~600 Pa make k nearly T-independent).

The surface energy balance is
    (1 - A) G_h + eps L_down + h_c (T_air - T_s) = eps sigma T_s^4 + q_cond
and is solved implicitly (Newton-linearised emission) on a stretched grid.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.linalg import solve_banded

from ..constants import SIGMA
from ..materials import hayne_specific_heat


@dataclass
class RegolithColumn:
    depth: float = 3.0
    n: int = 60
    dz0: float = 2.0e-3
    rho_s: float = 1100.0
    rho_d: float = 1800.0
    H: float = 0.06
    k_s: float = 7.4e-4
    k_d: float = 3.4e-3
    chi: float = 2.7
    cp_const: float | None = None     # None -> Hayne cp(T)
    emissivity: float = 0.95
    albedo0: float = 0.12
    albedo_a: float = 0.06
    albedo_b: float = 0.25
    q_geo: float = 0.018              # W/m2

    @classmethod
    def mars(cls, thermal_inertia=300.0, rho=1500.0, cp=800.0, albedo=0.2, emissivity=0.97,
             q_geo=0.02, depth=4.0):
        k = thermal_inertia ** 2 / (rho * cp)
        return cls(depth=depth, rho_s=rho, rho_d=rho, H=1.0, k_s=k, k_d=k, chi=0.0, cp_const=cp,
                   emissivity=emissivity, albedo0=albedo, albedo_a=0.0, albedo_b=0.0, q_geo=q_geo)

    def grid(self):
        # geometric stretching; first cell dz0, last reaching `depth`
        r = 1.0 + 1e-3
        lo, hi = 1.0 + 1e-6, 2.0
        for _ in range(100):
            r = 0.5 * (lo + hi)
            L = self.dz0 * (r ** (self.n - 1) - 1) / (r - 1)
            if L > self.depth:
                hi = r
            else:
                lo = r
        dz = self.dz0 * r ** np.arange(self.n - 1)
        z = np.concatenate([[0.0], np.cumsum(dz)])
        return z

    def albedo(self, incidence_deg):
        i = np.clip(incidence_deg, 0.0, 90.0)
        return self.albedo0 + self.albedo_a * (i / 45.0) ** 3 + self.albedo_b * (i / 90.0) ** 8

    def equilibrate(self, dt, absorbed_short, L_down, z_skin=0.5, n_iter=6, tol=0.02, T_init=None):
        """Periodic equilibrium of the column for a forcing that repeats with its own length (one year).

        A metre-scale column needs decades to forget its initial state, so plain spin-up is not enough.
        Each iteration runs one forcing period, takes the period-mean temperature at ``z_skin`` (below
        the depth reached by the diurnal wave) and rebuilds the deeper profile so that it carries the
        geothermal flux:  dT/dz = q_geo / k(z, T).  Returns (final state, period-mean profile, z).
        """
        z = self.grid()
        dz = np.diff(z)
        zc = 0.5 * (z[:-1] + z[1:])
        kc_seg = self.k_d - (self.k_d - self.k_s) * np.exp(-zc / self.H)
        i_s = int(np.argmin(np.abs(z - z_skin)))
        T = T_init
        prev = None
        # the layer above z_skin relaxes in ~100 days: run at least one Earth year of forcing per iteration
        reps = max(1, int(np.ceil(3.15e7 / (len(absorbed_short) * dt))))
        for _ in range(n_iter):
            for _r in range(reps):
                r = self.run(dt, absorbed_short, L_down, T_init=T)
                T = r["T_final"]
            mean = r["T_mean_profile"]
            T = r["T_final"].copy()
            prof = mean.copy()
            for j in range(i_s, len(z) - 1):      # integrate the conductive profile downward
                kk = kc_seg[j] * (1.0 + self.chi * (prof[j] / 350.0) ** 3)
                prof[j + 1] = prof[j] + self.q_geo * dz[j] / kk
            T[i_s:] += prof[i_s:] - mean[i_s:]     # shift the deep part, keep the periodic wave above
            if prev is not None and abs(prof[-1] - prev) < tol:
                break
            prev = prof[-1]
        r = self.run(dt, absorbed_short, L_down, T_init=T)
        return r["T_final"], r["T_mean_profile"], z

    def run(self, dt, absorbed_short, L_down, T_air=None, h_conv=None, T_init=None,
            spinup_cycles=0, cycle_steps=None, record_depths=(0.0,), return_state_only=False):
        """Integrate the column.

        ``absorbed_short`` is (1-A) G_h [W/m2] per step.  Returns dict with surface
        temperature, temperature at requested depths and the mean temperature profile.
        """
        z = self.grid()
        dz = np.diff(z)
        zc = 0.5 * (z[:-1] + z[1:])
        rho_n = self.rho_d - (self.rho_d - self.rho_s) * np.exp(-z / self.H)
        kc_seg = self.k_d - (self.k_d - self.k_s) * np.exp(-zc / self.H)
        n = len(z)
        nsteps = len(absorbed_short)
        if T_init is None:
            Teq = (np.mean(absorbed_short + L_down) / (self.emissivity * SIGMA)) ** 0.25
            T = np.full(n, 0.9 * Teq)
        else:
            T = np.full(n, float(T_init)) if np.isscalar(T_init) else np.array(T_init, float)
        Tair = np.zeros(nsteps) if T_air is None else np.nan_to_num(np.asarray(T_air, float))
        hc = np.zeros(nsteps) if h_conv is None else np.asarray(h_conv, float)
        eps = self.emissivity

        def step(T, q_abs, Ld, Ta, h):
            Tseg = 0.5 * (T[:-1] + T[1:])
            k = kc_seg * (1.0 + self.chi * (Tseg / 350.0) ** 3)
            cp = hayne_specific_heat(T) if self.cp_const is None else np.full(n, self.cp_const)
            C = np.zeros(n)
            C[:-1] += 0.5 * rho_n[:-1] * cp[:-1] * dz
            C[1:] += 0.5 * rho_n[1:] * cp[1:] * dz
            K = k / dz
            Ts = T[0]
            for _ in range(3):
                ab = np.zeros((3, n))
                diag = C / dt
                diag[:-1] += K
                diag[1:] += K
                rhs = C / dt * T
                # surface: emission linearised about Ts, absorbed flux, convection
                hr = 4 * eps * SIGMA * Ts ** 3
                diag[0] += hr + h
                rhs[0] += q_abs + eps * Ld + 3 * eps * SIGMA * Ts ** 4 + h * Ta
                rhs[-1] += self.q_geo
                ab[1] = diag
                ab[0, 1:] = -K
                ab[2, :-1] = -K
                Tn = solve_banded((1, 1), ab, rhs)
                if abs(Tn[0] - Ts) < 1e-3:
                    break
                Ts = Tn[0]
            return Tn

        if spinup_cycles and cycle_steps:
            for _ in range(spinup_cycles):
                for i in range(min(cycle_steps, nsteps)):
                    T = step(T, absorbed_short[i], L_down[i], Tair[i], hc[i])
        if return_state_only:
            return T
        idx = [int(np.argmin(np.abs(z - d))) for d in record_depths]
        out = np.zeros((nsteps, len(idx)))
        Tsum = np.zeros(n)
        for i in range(nsteps):
            T = step(T, absorbed_short[i], L_down[i], Tair[i], hc[i])
            out[i] = T[idx]
            Tsum += T
        return dict(z=z, T_depths=out, T_mean_profile=Tsum / nsteps, T_final=T,
                    T_surface=out[:, 0])
