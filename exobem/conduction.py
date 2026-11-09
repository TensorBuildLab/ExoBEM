"""Finite-volume transient conduction through layered constructions.

The scheme is the node-centred, fully implicit formulation of the EnergyPlus
Conduction Finite Difference (CondFD) algorithm (EnergyPlus Engineering Reference,
"Conduction Finite Difference Solution Algorithm"): nodes sit on both faces of every
layer and inside layers; each node carries half of the heat capacity of the adjacent
cells; temperature-dependent properties are lagged by one time step.

Unlike CondFD, thick layers (e.g. a 2 m regolith shield whose diffusivity is ~1e-9
m2/s) use a geometrically stretched grid that is fine near the layer faces and coarse
in the interior, so that metre-scale covers remain cheap.

All surfaces of a model are stacked into one tri-diagonal system, which is solved
with a single banded LU call per iteration (``scipy.linalg.solve_banded``).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np

from .materials import Construction


def layer_cells(L: float, alpha: float, dt: float, growth: float = 1.3, max_cells: int = 40):
    """Cell widths for one layer: stretched from both faces toward the layer centre."""
    h0 = 0.5 * np.sqrt(alpha * dt)
    h0 = float(np.clip(h0, 2.0e-4, L))
    if L <= 3.0 * h0:
        n = max(1, int(round(L / h0)))
        return np.full(n, L / n)
    half = []
    total = 0.0
    h = h0
    while total + h < L / 2.0 and len(half) < max_cells // 2:
        half.append(h)
        total += h
        h *= growth
    half = np.array(half)
    rem = L / 2.0 - half.sum()
    if rem > 0.5 * half[-1]:
        half = np.append(half, rem)
    else:
        half[-1] += rem
    cells = np.concatenate([half, half[::-1]])
    return cells * (L / cells.sum())


@dataclass
class _Cell:
    mat: object
    h: float


class GlobalGrid:
    """Stacked node grid for all heat-transfer surfaces of a model."""

    def __init__(self, constructions: List[Construction], dt: float, T_init):
        self.dt = dt
        self.surface_offsets = []
        self.surface_nnodes = []
        seg_mat, seg_h, seg_left = [], [], []
        node_count = 0
        for c in constructions:
            off = node_count
            cells = []
            for lay in c.layers:
                if lay.is_massless:
                    cells.append(_Cell(lay, 0.0))
                else:
                    a = lay.conductivity / (lay.density * lay.specific_heat)
                    for h in layer_cells(lay.thickness, a, dt):
                        cells.append(_Cell(lay, float(h)))
            for i, cell in enumerate(cells):
                seg_mat.append(cell.mat)
                seg_h.append(cell.h)
                seg_left.append(off + i)
            n_nodes = len(cells) + 1
            self.surface_offsets.append(off)
            self.surface_nnodes.append(n_nodes)
            node_count += n_nodes
        self.N = node_count
        self.seg_left = np.array(seg_left, dtype=int)
        self.seg_h = np.array(seg_h)
        self.seg_mat = seg_mat
        self.n_seg = len(seg_mat)
        self.outside_idx = np.array(self.surface_offsets, dtype=int)
        self.inside_idx = self.outside_idx + np.array(self.surface_nnodes) - 1
        # static property arrays
        self.seg_massless = np.array([m.is_massless for m in seg_mat])
        self.seg_k = np.array([0.0 if m.is_massless else m.conductivity for m in seg_mat])
        self.seg_R = np.array([m.resistance if m.is_massless else 0.0 for m in seg_mat])
        self.seg_rho = np.array([0.0 if m.is_massless else m.density for m in seg_mat])
        self.seg_cp = np.array([0.0 if m.is_massless else m.specific_heat for m in seg_mat])
        # group temperature-dependent segments by material object
        self._tdep = {}
        for i, m in enumerate(seg_mat):
            if not m.is_massless and m.temperature_dependent:
                self._tdep.setdefault(id(m), [m, []])[1].append(i)
        self._tdep = [(m, np.array(ix)) for m, ix in self._tdep.values()]
        self.T = np.full(self.N, float(np.mean(T_init))) if np.isscalar(T_init) else np.array(T_init, float)
        self.update_properties()

    # ------------------------------------------------------------------------------
    def update_properties(self):
        T = self.T
        k = self.seg_k.copy()
        cp_left = self.seg_cp.copy()
        cp_right = self.seg_cp.copy()
        for m, ix in self._tdep:
            Tl = T[self.seg_left[ix]]
            Tr = T[self.seg_left[ix] + 1]
            if m.k_of_T is not None:
                k[ix] = m.k(0.5 * (Tl + Tr))
            if m.cp_of_T is not None:
                cp_left[ix] = m.cp(Tl)
                cp_right[ix] = m.cp(Tr)
        K = np.where(self.seg_massless, 1.0 / np.where(self.seg_R > 0, self.seg_R, 1.0),
                     k / np.where(self.seg_h > 0, self.seg_h, 1.0))
        self.K = K
        C = np.zeros(self.N)
        np.add.at(C, self.seg_left, 0.5 * self.seg_rho * cp_left * self.seg_h)
        np.add.at(C, self.seg_left + 1, 0.5 * self.seg_rho * cp_right * self.seg_h)
        self.C = C

    def base_matrix(self, dt=None):
        """Banded matrix (3 x N) and RHS for the conduction part only (per unit area)."""
        dt = self.dt if dt is None else dt
        N = self.N
        ab = np.zeros((3, N))
        diag = self.C / dt
        diag = diag.copy()
        i = self.seg_left
        np.add.at(diag, i, self.K)
        np.add.at(diag, i + 1, self.K)
        ab[1] = diag
        ab[0, i + 1] = -self.K       # upper diagonal: element (i, i+1)
        ab[2, i] = -self.K           # lower diagonal: element (i+1, i)
        rhs = self.C / dt * self.T
        return ab, rhs

    def heat_flux_in(self, T=None):
        """Conduction flux [W/m2] leaving each surface's outside node toward the inside, and
        arriving at the inside node (positive = toward the zone)."""
        T = self.T if T is None else T
        first_seg = np.searchsorted(self.seg_left, self.outside_idx)
        last_seg = np.searchsorted(self.seg_left, self.inside_idx - 1)
        q_outside_face = self.K[first_seg] * (T[self.outside_idx] - T[self.outside_idx + 1])
        q_inside_face = self.K[last_seg] * (T[self.inside_idx - 1] - T[self.inside_idx])
        return q_outside_face, q_inside_face
