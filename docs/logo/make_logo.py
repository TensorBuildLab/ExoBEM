"""Draw the ExoBEM logo and icon (SVG + PNG).

    python docs/logo/make_logo.py
Design: a regolith-covered habitat module on a planetary horizon under the Sun, with heat leaving the roof as
infrared arcs; the wordmark follows.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Arc, Circle, FancyBboxPatch, Polygon, Wedge  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
NAVY, SKY, SUN, REGO, REGO_D, SHELL, IR, INK = "#0f2a4a", "#173b66", "#f3a33a", "#c8a27a", "#9c7a55", "#e9eef5", "#eb6834", "#0f2a4a"


def emblem(ax, cx=0.0, cy=0.0, r=1.0, core=False):
    # night-sky disc
    ax.add_patch(Circle((cx, cy), r, color=NAVY, zorder=0))
    # stars
    rng = np.random.default_rng(7)
    for _ in range(14):
        a, d = rng.uniform(0.35, 2.8), rng.uniform(0.45, 0.92)
        x, y = cx + d * r * np.cos(a), cy + d * r * np.sin(a)
        if y > cy + 0.05 * r and not (abs(x - cx) < 0.5 * r and y < cy + 0.75 * r) and np.hypot(x - cx - 0.48 * r, y - cy - 0.5 * r) > 0.25 * r:
            ax.add_patch(Circle((x, y), r * rng.uniform(0.008, 0.018), color="white", alpha=0.85, zorder=1))
    # Sun
    ax.add_patch(Circle((cx + 0.48 * r, cy + 0.50 * r), 0.15 * r, color=SUN, zorder=2))
    # planet surface (lower part of the disc), clipped to the disc
    ground = Wedge((cx, cy), r, 180, 360, color=REGO, zorder=3)
    ax.add_patch(ground)
    horizon = Polygon([[cx - r, cy], [cx + r, cy], [cx + r, cy - 0.04 * r], [cx - r, cy - 0.04 * r]], color=REGO_D, zorder=4)
    ax.add_patch(horizon)
    # habitat: half-buried module with a regolith berm
    berm = Polygon([[cx - 0.62 * r, cy], [cx - 0.42 * r, cy + 0.30 * r], [cx + 0.42 * r, cy + 0.30 * r], [cx + 0.62 * r, cy]],
                   closed=True, color=REGO_D, zorder=5)
    ax.add_patch(berm)
    shell = FancyBboxPatch((cx - 0.40 * r, cy + 0.02 * r), 0.80 * r, 0.24 * r, boxstyle=f"round,pad=0,rounding_size={0.12 * r}",
                           fc=SHELL, ec=NAVY, lw=1.2, zorder=6)
    ax.add_patch(shell)
    for k in (-0.2, 0.0, 0.2):    # port lights
        ax.add_patch(Circle((cx + k * r, cy + 0.14 * r), 0.03 * r, color=SUN, zorder=7))
    # infrared arcs leaving the habitat
    for i, rr in enumerate((0.42, 0.55, 0.68)):
        ax.add_patch(Arc((cx, cy + 0.26 * r), 2 * rr * r * 0.62, 2 * rr * r * 0.62, theta1=55, theta2=125, color=IR,
                         lw=2.2 - 0.5 * i, alpha=0.95 - 0.2 * i, zorder=6))
    # rim
    ax.add_patch(Circle((cx, cy), r, fill=False, ec=NAVY, lw=2.5, zorder=8))
    if core:
        ring = Circle((cx, cy), 1.10 * r, fill=False, ec=IR, lw=2.0, zorder=8)
        ax.add_patch(ring)
        for a in np.radians(np.arange(0, 360, 30)):
            x0, y0 = cx + 1.10 * r * np.cos(a), cy + 1.10 * r * np.sin(a)
            x1, y1 = cx + 1.22 * r * np.cos(a), cy + 1.22 * r * np.sin(a)
            ax.plot([x0, x1], [y0, y1], color=IR, lw=2.0, zorder=8, solid_capstyle="round")
            ax.add_patch(Circle((x1, y1), 0.035 * r, color=IR, zorder=8))


def draw(name, word, sub, core=False, square=False):
    if square:
        fig = plt.figure(figsize=(3.0, 3.0))
        ax = fig.add_axes([0, 0, 1, 1])
        emblem(ax, 0, 0, 1.0, core)
        lim = 1.3 if core else 1.05
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
    else:
        fig = plt.figure(figsize=(6.4, 2.0))
        ax = fig.add_axes([0, 0, 1, 1])
        emblem(ax, 0, 0, 1.0, core)
        ax.text(1.55 if core else 1.35, 0.18, word, fontsize=38, fontweight="bold", color=INK, va="center", family="DejaVu Sans")
        ax.text(1.58 if core else 1.38, -0.55, sub, fontsize=10.5, color="#52514e", va="center", family="DejaVu Sans")
        ax.set_xlim(-1.3 if core else -1.05, 7.4 if core else 6.3)
        ax.set_ylim(-1.3 if core else -1.05, 1.3 if core else 1.05)
    ax.set_aspect("equal")
    ax.set_axis_off()
    for ext in ("svg", "png"):
        fig.savefig(HERE / f"{name}.{ext}", dpi=300, transparent=True)
    plt.close(fig)
    print("wrote", name)


if __name__ == "__main__":
    draw("exobem_logo", "ExoBEM", "Building energy simulation for the Moon and Mars")
    draw("exobem_icon", "", "", square=True)
