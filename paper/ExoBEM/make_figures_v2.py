"""New figures for the revised ExoBEM paper (flow of a simulation, habitat geometry, power systems).

    python paper/ExoBEM/make_figures_v2.py [flow|geometry|power|all]
Results for the geometry and power figures come from studies/results (python studies/run_case_studies.py).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
FIG = HERE / "figures"
RES = ROOT / "studies" / "results"

C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8.5, "axes.titlesize": 9, "axes.labelsize": 8.5,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 1.4,
    "legend.frameon": True, "legend.facecolor": "white", "legend.edgecolor": "none", "legend.framealpha": 0.9,
    "legend.fontsize": 7.5, "savefig.dpi": 300, "figure.dpi": 110,
    "axes.titlecolor": INK, "axes.titleweight": "bold", "axes.titlelocation": "left",
})


def save(fig, name):
    fig.savefig(FIG / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", name)


# ----------------------------------------------------------------------------------------- flow
def fig_flow():
    fig, ax = plt.subplots(figsize=(7.4, 6.4))
    ax.set_axis_off()
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    def box(x, y, w, h, title, body, color, fc="white", tsize=7.0, bsize=5.7):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=0.9", fc=fc, ec=color, lw=1.2))
        ax.text(x + 1.2, y + h - 1.0, title, ha="left", va="top", fontsize=tsize, weight="bold", color=INK)
        if body:
            ax.text(x + 1.2, y + h - 4.2, body, ha="left", va="top", fontsize=bsize, color=INK2, linespacing=1.3)

    def arrow(x0, y0, x1, y1, color=MUTED, rad=0.0):
        ax.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", color=color, lw=0.9, mutation_scale=7,
                                                            connectionstyle=f"arc3,rad={rad}"))

    ax.text(1, 99, "ExoBEM", fontsize=8.5, weight="bold", color=C[0], va="top")
    ax.text(72, 99, "EnergyPlus counterpart", fontsize=8.5, weight="bold", color=MUTED, va="top")
    # inputs
    box(1, 85, 30.5, 11, "1  Model input", "JSON file or Python objects: materials,\nconstructions, geometry, zone, gains,\nthermal control, power system", C[0])
    box(34.5, 85, 30.5, 11, "2  Site environment", "PWF weather file, or generated: ephemeris,\nsky / dust radiation, regolith column\n(spun up), ambient gas, wind", C[0])
    # pre-processing
    box(1, 63, 64, 19, "3  Pre-processing (once)",
        "• check the model against the environment (sealed cabin, O2 limits,\n   Earth-only options refused)\n"
        "• surfaces + internal mass; all construction layers -> one stacked\n   finite-volume grid (stretched in thick layers)\n"
        "• interior view factors -> ScriptF; radiant-gain distribution\n"
        "• incident solar on every surface for every step; schedules -> gains,\n   set-points; cabin-gas properties",
        C[0], fc="#f6f8fc")
    # warm-up
    box(1, 50, 64, 10.5, "4  Initialization",
        "pseudo-transient steady solve with period-mean boundary conditions\n(steps growing to 10⁹ s), then one repetition of the first solar day\n"
        "(a lunation on the Moon, a sol on Mars); results discarded", C[0], fc="#f6f8fc")
    # time loop
    box(1, 17, 64, 30.5, "5  Time-step loop  (n = 1 … N)", "", C[1], fc="#fdf6f1")
    steps = [
        "a  update k(T), cp(T); assemble the banded conduction matrix",
        "b  outside faces: convection h(gas, p, g, wind), 0 in vacuum; long-wave\n    to sky and regolith, linearized; ground contact at deep regolith",
        "c  inside faces: cabin convection h(cabin gas, p, g, air speed);\n    ScriptF long-wave; radiant gains",
        "d  one banded solve for n+2 right-hand sides -> dense (n+1) system\n    for inside faces + zone air; solve free-floating first",
        "e  zone outside the set-point band: fix it at the set-point;\n    ideal load = air-balance residual",
        "f  repeat b–e until the change < 0.005 K (2–3 iterations)",
        "g  cabin vapour balance: crew moisture, gas lost overboard,\n    condensing heat exchanger -> latent load",
    ]
    y = 43.5
    for s_ in steps:
        ax.text(3, y, s_, fontsize=5.8, color=INK2, va="top", linespacing=1.25)
        y -= 4.1 if "\n" in s_ else 2.9
    arrow(61.5, 25.5, 61.5, 39.5, C[1], rad=-0.5)
    ax.text(62.6, 32.5, "iterate", fontsize=5.5, color=C[1], rotation=90, va="center")
    # post
    box(1, 1, 30.5, 13, "6  Thermal control", "radiator sink temperature from sky,\nregolith and Sun; passive rejection or\nheat-pump lift (COP); pump power", C[2])
    box(34.5, 1, 30.5, 13, "7  Power system", "electric load = equipment + life support\n+ lighting + thermal control; PV, fission,\nbattery, RFC dispatch; unmet energy", C[2])
    for (x0, y0, x1, y1) in ((16, 85, 16, 82.3), (50, 85, 50, 82.3), (33, 63, 33, 60.8), (33, 50, 33, 47.8),
                             (16, 17, 16, 14.3), (31.8, 7.5, 34.3, 7.5)):
        arrow(x0, y0, x1, y1)
    # EnergyPlus column
    ep = [(84, 93.0, "InputProcessor\n(IDF / epJSON)"), (84, 85.5, "WeatherManager\n(EPW, read day by day)"),
          (84, 72.5, "SurfaceGeometry,\nHeatBalanceManager (CTF /\nCondFD set-up), SolarShading"),
          (84, 55.0, "Warm-up: repeat day 1\nuntil zone temperatures\nconverge"),
          (84, 41.5, "HeatBalanceSurface-\nManager, Convection-\nCoefficients"),
          (84, 30.0, "ZoneTempPredictor-\nCorrector (3rd-order\nbackward difference)"),
          (84, 21.0, "ZoneEquipmentManager:\nideal loads"),
          (84, 7.5, "HVAC, plant, Electric-\nPowerServiceManager")]
    for x, yy, t in ep:
        ax.text(x, yy, t, fontsize=5.6, color=MUTED, ha="center", va="center", linespacing=1.2,
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=AXIS, lw=0.8))
    for yy in (90.5, 72.5, 55.0, 32.0, 7.5):
        ax.plot([66.2, 70.5], [yy, yy], color=AXIS, lw=0.7, ls=(0, (2, 2)))
    save(fig, "fig_flow.png")


# ----------------------------------------------------------------------------------------- geometry
def fig_geometry():
    from exobem.cases import artemis_surface_habitat, mars_surface_habitat
    from exobem.plot import plot_geometry, plot_construction
    moon = artemis_surface_habitat()
    mars = mars_surface_habitat()
    fig = plt.figure(figsize=(7.4, 5.4))
    ax1 = fig.add_subplot(2, 2, 1, projection="3d")
    ax2 = fig.add_subplot(2, 2, 2, projection="3d")
    plot_geometry(moon, ax=ax1, title="(a) Lunar surface habitat (4 crew)", cover_m=None)
    plot_geometry(mars, ax=ax2, title="(b) Mars surface habitat (6 crew)", cover_m=None)
    for ax, m in ((ax1, moon), (ax2, mars)):
        g = m.zone.geometry
        a_out = sum(s.area for s in g.surfaces if s.boundary == "outdoors")
        a_gnd = sum(s.area for s in g.surfaces if s.boundary == "ground")
        ax.text2D(0.5, 0.97, f"pressurized volume {g.volume:.0f} m³, envelope {a_out:.0f} m²,\non legs 1.5 m above the regolith",
                  transform=ax.transAxes, fontsize=6.3, color=INK2, ha="center", va="top")
    ax3 = fig.add_subplot(4, 1, 3)
    plot_construction(moon.constructions["shell"], ax=ax3, title="(c) Lunar shell, outside → cabin (bar width ∝ log thickness)")
    ax4 = fig.add_subplot(4, 1, 4)
    plot_construction(mars.constructions["shell"], ax=ax4, title="(d) Mars shell")
    fig.tight_layout(h_pad=0.6)
    save(fig, "fig_geometry.png")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("flow", "all"):
        fig_flow()
    if which in ("geometry", "all"):
        fig_geometry()
