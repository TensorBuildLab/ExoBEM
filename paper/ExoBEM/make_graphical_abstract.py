"""Graphical abstract for the ExoBEM paper (Applied Energy: landscape, readable at about 13 x 5 cm).

    python paper/ExoBEM/make_graphical_abstract.py  ->  paper/ExoBEM/ExoBEM_graphical_abstract.png

Numbers come from studies/results/case_studies.json, the same file the paper's tables use.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from exobem.cases import artemis_surface_habitat  # noqa: E402
from exobem.plot import plot_geometry  # noqa: E402

C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, MUTED, GRID, PANEL = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#f6f5f1"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": "#c3c2b7",
                     "xtick.color": MUTED, "ytick.color": INK2})

R = json.loads((ROOT / "studies" / "results" / "case_studies.json").read_text(encoding="utf-8-sig"))
P = R["power"]
CASES = [("Moon, south pole", "moon_pole"), ("Moon, equator", "moon_equator"),
         ("Mars, Jezero", "mars_jezero"), ("Mars, dust storm", "mars_jezero_storm")]


def panel(fig, x, y, w, h):
    fig.patches.append(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.004,rounding_size=0.015",
                                      transform=fig.transFigure, facecolor=PANEL, edgecolor="none", zorder=-5))


def arrow(fig, x0, x1, y):
    fig.patches.append(FancyArrowPatch((x0, y), (x1, y), transform=fig.transFigure, arrowstyle="-|>",
                                       mutation_scale=16, color=MUTED, lw=1.6))


def main():
    fig = plt.figure(figsize=(10.0, 4.0))

    # ---------------------------------------------------------------- 1: what differs off-Earth
    panel(fig, 0.01, 0.04, 0.30, 0.92)
    fig.text(0.025, 0.89, "Earth tools assume Earth", fontsize=11.5, weight="bold", color=INK)
    rows = [("Day", "24 h", "709 h  /  24.7 h"), ("Outside", "air, 1 atm", "vacuum  /  0.7 kPa CO₂"),
            ("Fresh air", "ventilation", "none: sealed cabin"), ("Ground", "air temp.", "regolith −180…120 °C"),
            ("Power", "grid", "PV, storage, fission")]
    fig.text(0.098, 0.79, "Earth", fontsize=8, color=MUTED, weight="bold")
    fig.text(0.172, 0.79, "Moon  /  Mars", fontsize=8, color=C[1], weight="bold")
    for i, (k, e, m) in enumerate(rows):
        yy = 0.70 - i * 0.135
        fig.text(0.022, yy, k, fontsize=8, color=INK2, weight="bold")
        fig.text(0.098, yy, e, fontsize=8, color=MUTED)
        fig.text(0.172, yy, m, fontsize=8, color=INK)
    arrow(fig, 0.313, 0.342, 0.5)

    # ---------------------------------------------------------------- 2: ExoBEM
    panel(fig, 0.345, 0.04, 0.30, 0.92)
    fig.text(0.36, 0.89, "ExoBEM", fontsize=11.5, weight="bold", color=INK)
    fig.text(0.44, 0.895, "open-source Python, pip install", fontsize=8, color=MUTED)
    ax3 = fig.add_axes([0.34, 0.20, 0.17, 0.66], projection="3d")
    ax3.set_facecolor("none")
    plot_geometry(artemis_surface_habitat(), ax=ax3, elev=20, azim=-58)
    ax3.set_axis_off()
    ax3.set_title("")
    fig.text(0.425, 0.22, "4-crew lunar habitat, 174 m³", fontsize=7.5, color=INK2, ha="center")
    items = ["EnergyPlus\nheat balance", "Planetary sun, sky\nand regolith", "Sealed cabin:\nhumidity, leakage",
             "PV, batteries,\nfuel cells, fission"]
    for i, t in enumerate(items):
        yy = 0.76 - i * 0.165
        fig.text(0.51, yy, "■", fontsize=8, color=C[i % 4], va="top")
        fig.text(0.525, yy, t, fontsize=8.3, color=INK, va="top", linespacing=1.15)
    fig.text(0.36, 0.075, "Verified against EnergyPlus (within 0.7 %)\nand Mars24, Diviner and MEDA data",
             fontsize=7.6, color=INK2, linespacing=1.2)
    arrow(fig, 0.65, 0.677, 0.5)

    # ---------------------------------------------------------------- 3: results
    panel(fig, 0.68, 0.04, 0.31, 0.92)
    fig.text(0.695, 0.89, "Storage drives solar power", fontsize=11.5, weight="bold", color=INK)
    fig.text(0.695, 0.82, "Li-ion storage with twice the minimum PV array", fontsize=8, color=MUTED)
    ax = fig.add_axes([0.80, 0.27, 0.165, 0.50])
    labels = [l for l, _ in CASES][::-1]
    vals = [P[k]["PV x2 + Li-ion"]["storage_kWh"] / 1000 for _, k in CASES][::-1]
    mass = [P[k]["PV x2 + Li-ion"]["storage_mass_t"] for _, k in CASES][::-1]
    cols = [C[7], C[1], C[0], C[0]]
    ax.barh(range(4), vals, color=cols, height=0.62)
    for i, (v, mt) in enumerate(zip(vals, mass)):
        txt = f"{v:.1f} MWh" if v >= 1 else f"{v:.2f} MWh"
        inside = v > 20
        ax.text(v - 1 if inside else v + 0.8, i, f"{txt}\n{mt:.0f} t" if mt >= 2 else f"{txt}\n{mt:.1f} t",
                va="center", ha="right" if inside else "left", fontsize=7.6,
                color="white" if inside else INK, linespacing=1.0)
    ax.set_yticks(range(4), labels, fontsize=8.3)
    ax.set_xlim(0, max(vals) * 1.05)
    ax.set_xticks([0, 10, 20, 30])
    ax.tick_params(axis="x", labelsize=7.5)
    ax.set_xlabel("MWh", fontsize=7.5, color=MUTED, labelpad=1)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    fig.text(0.695, 0.10, "One 40 kWe fission unit covers every case,\nindependent of night and dust.",
             fontsize=8.5, color=INK, weight="bold", linespacing=1.2)

    out = HERE / "ExoBEM_graphical_abstract.png"
    fig.savefig(out, dpi=300, facecolor="white")
    print("wrote", out)


if __name__ == "__main__":
    main()
