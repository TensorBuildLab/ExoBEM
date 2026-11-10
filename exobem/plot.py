"""Plots of model geometry, constructions and results (requires matplotlib).

    from exobem.plot import plot_geometry
    plot_geometry(model, "habitat.png")
"""
from __future__ import annotations

import numpy as np

# validated categorical palette (same as the paper figures)
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BOUNDARY_COLOR = {"outdoors": "#c9d7ea", "ground": "#c8a27a", "adiabatic": "#dddddd"}


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def plot_geometry(model_or_geometry, path=None, ax=None, title=None, show_normals=False, cover_m=None,
                  elev=22, azim=-58):
    """3-D view of the heat-transfer surfaces.  Outdoor surfaces are blue-grey, ground-contact
    surfaces brown.  ``cover_m`` draws a translucent outline of a regolith cover of that thickness."""
    plt = _plt()
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    geom = getattr(getattr(model_or_geometry, "zone", None), "geometry", model_or_geometry)
    own = ax is None
    if own:
        fig = plt.figure(figsize=(5.0, 4.0))
        ax = fig.add_subplot(projection="3d")
    pts = []
    for s in geom.surfaces:
        if not s.vertices:
            raise ValueError(f"surface {s.name} has no vertices; use a built-in shape generator")
        v = np.array(s.vertices)
        pts.append(v)
        pc = Poly3DCollection([v], facecolor=BOUNDARY_COLOR.get(s.boundary, "#dddddd"), edgecolor="#3d3d3a",
                              linewidth=0.5, alpha=0.95)
        ax.add_collection3d(pc)
        if show_normals:
            c = v.mean(axis=0)
            t, a = np.radians(s.tilt), np.radians(s.azimuth)
            n = np.array([np.sin(t) * np.sin(a), np.sin(t) * np.cos(a), np.cos(t)])
            ax.quiver(*c, *n, length=0.8, color=C[1], linewidth=0.8)
    allp = np.vstack(pts)
    if cover_m:
        ctr = allp.mean(axis=0)
        for v in pts:
            vv = ctr + (v - ctr) * (1 + cover_m / max(np.ptp(allp[:, 2]) / 2, 1e-6))
            vv[:, 2] = np.maximum(vv[:, 2], allp[:, 2].min())
            ax.add_collection3d(Poly3DCollection([vv], facecolor="#a07a52", edgecolor="none", alpha=0.10))
    lo, hi = allp.min(axis=0), allp.max(axis=0)
    span = (hi - lo).max() * 0.55
    mid = 0.5 * (lo + hi)
    ax.set_xlim(mid[0] - span, mid[0] + span)
    ax.set_ylim(mid[1] - span, mid[1] + span)
    ax.set_zlim(lo[2], lo[2] + 2 * span)
    ax.set_box_aspect((1, 1, 1))
    ax.set_xlabel("x, east (m)", fontsize=7, labelpad=-2)
    ax.set_ylabel("y, north (m)", fontsize=7, labelpad=-2)
    ax.set_zlabel("z (m)", fontsize=7, labelpad=-2)
    ax.tick_params(labelsize=6, pad=-2)
    ax.view_init(elev=elev, azim=azim)
    if title:
        ax.set_title(title, fontsize=8.5, loc="left", fontweight="bold")
    if own:
        fig.tight_layout()
        if path:
            fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
            plt.close(fig)
    return ax


def plot_construction(construction, path=None, ax=None, title=None, log=True):
    """Layer stack of a construction, outside (left) to inside (right), widths ~ thickness."""
    plt = _plt()
    own = ax is None
    if own:
        fig, ax = plt.subplots(figsize=(6.0, 1.6))
    x = 0.0
    for i, m in enumerate(construction.layers):
        t = getattr(m, "thickness", 0.0) or 0.0
        w = np.log10(1 + 1000 * t) if log else t
        w = max(w, 0.06 if log else 1e-3)
        ax.barh(0, w, left=x, color=C[i % len(C)], edgecolor="white", linewidth=1.5, height=0.6)
        lab = f"{m.name}\n{t*1000:.0f} mm" if t else f"{m.name}\n(no mass)"
        ax.text(x + w / 2, -0.42, lab, ha="center", va="top", fontsize=5.6, color=INK2, rotation=0)
        x += w
    ax.set_xlim(0, x)
    ax.set_ylim(-1.2, 0.5)
    ax.set_axis_off()
    ax.text(0, 0.42, "outside", fontsize=6.5, color=MUTED)
    ax.text(x, 0.42, "cabin", fontsize=6.5, color=MUTED, ha="right")
    if title:
        ax.set_title(title, fontsize=8.5, loc="left", fontweight="bold")
    if own:
        fig.tight_layout()
        if path:
            fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
            plt.close(fig)
    return ax
