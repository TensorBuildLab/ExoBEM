"""Figures for the Thermonaut and combined manuscripts (reads paper/Thermonaut/data, writes paper/Thermonaut/figures/core_*.png).

    python paper/Thermonaut/build_figures_thermonaut.py
Same style and palette as studies/make_figures.py.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
FIG = HERE / "figures"

C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE_RAMP = ["#0d3d7a", "#2a78d6", "#a9c8ef"]  # P0, P1, P2 (one hue, dark -> light)

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8.5, "axes.titlesize": 9, "axes.labelsize": 8.5,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 1.4,
    "legend.frameon": True, "legend.facecolor": "white", "legend.edgecolor": "none", "legend.framealpha": 0.9,
    "legend.fontsize": 7.5, "savefig.dpi": 300, "figure.dpi": 110,
    "axes.titlecolor": INK, "axes.titleweight": "bold", "axes.titlelocation": "left",
})
PY = dict(color=C[0], lw=1.7, label="ExoBEM (Python)")
CPP = dict(color=C[1], lw=1.0, ls=(0, (3, 1.5)), label="Thermonaut (C++)")


def save(fig, name):
    fig.savefig(FIG / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", name)


def load(case):
    with open(DATA / f"core_{case}_hourly.csv") as fh:
        rows = list(csv.reader(fh))
    head, vals = rows[0], np.array(rows[1:], float)
    return {h: vals[:, i] for i, h in enumerate(head)}


def window(case, n):
    skip = (n // 48) * 24  # same rule as planetary/cases/compare.py
    return skip, n


# --------------------------------------------------------------------------- hook map
def fig_hooks():
    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    ax.set_axis_off()
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 60)

    def box(x, y, w, h, title, body, color, fc="white", tsize=7.2, bsize=5.8):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.35,rounding_size=1.0", fc=fc, ec=color, lw=1.3))
        ax.text(x + w / 2, y + h - 1.4, title, ha="center", va="top", fontsize=tsize, weight="bold", color=INK)
        if body:
            ax.text(x + w / 2, y + h - 4.6, body, ha="center", va="top", fontsize=bsize, color=INK2, linespacing=1.3)

    # EnergyPlus engine column (reused code in grey, hook text in orange)
    ax.text(30, 59.3, "EnergyPlus v26.2 engine (reused)", ha="center", va="top", fontsize=7.6, weight="bold", color=INK2)
    steps = [
        ("Input processing", "SimulationManager.cc", "read Site:PlanetaryBody;\nvalidator refuses outdoor-air objects"),
        ("Weather manager", "WeatherManager.cc", "overwrite tomorrow's weather;\nhour-angle rate; cabin pressure"),
        ("Solar and shading", "SolarShading.cc", "daily sun fit, rate·(12−t−EoT);\nisotropic sky, no Perez"),
        ("Outside surface balance", "ConvectionCoefficients.cc", "h = 0 (Moon) / CO2 mixed (Mars);\nall sky LW to sky; ground = regolith"),
        ("Conduction (CTF / CondFD)", "HeatBalFiniteDiffManager.cc", "−270 °C limit; steady k(T) start-up\nprofile + warm-up-aware correction"),
        ("Inside balance, zone air", "HeatBalanceSurfaceManager.cc", "cabin-gas convection at cabin\npressure and body gravity"),
    ]
    y0, hgt, gap = 50.5, 6.9, 1.35
    ys = []
    for i, (t, fn, hook) in enumerate(steps):
        y = y0 - i * (hgt + gap)
        ys.append(y)
        ax.add_patch(FancyBboxPatch((3, y), 54, hgt, boxstyle="round,pad=0.3,rounding_size=0.8", fc="#f6f5f1", ec=AXIS, lw=1.0))
        ax.text(4.2, y + hgt - 1.1, t, ha="left", va="top", fontsize=7.0, weight="bold", color=INK)
        ax.text(4.2, y + 1.3, fn, ha="left", va="bottom", fontsize=5.4, color=MUTED, family="DejaVu Sans Mono")
        ax.text(33.0, y + hgt / 2, hook, ha="left", va="center", fontsize=5.6, color=C[1], linespacing=1.25)
        if i < len(steps) - 1:
            ax.annotate("", (30, y - gap + 0.15), (30, y - 0.15),
                        arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=0.9, mutation_scale=7))
    # loop arrow
    ax.annotate("", (1.6, ys[1] + hgt / 2), (1.6, ys[-1] + hgt / 2),
                arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=0.9, mutation_scale=7, connectionstyle="arc3,rad=-0.0"))
    ax.text(0.4, (ys[1] + ys[-1]) / 2 + hgt / 2, "time-step loop", rotation=90, ha="center", va="center", fontsize=5.6, color=MUTED)

    # planetary module
    box(64, 22.5, 34, 34.5, "PlanetaryBody module (new)",
        "Ephemerides: Mars24; lunar subsolar point\n\nEnvironment generator (whole run period):\n"
        "Moon: vacuum, 2.725 K sky\nMars: delta-Eddington dust two-stream,\nτ(Ls), P(Ls), sky IR, air surrogate, wind\n\n"
        "Regolith column (Hayne 2017 / thermal\ninertia) in periodic equilibrium\n\n"
        "Gas properties: cabin N2/O2, Mars CO2\nPhysical mixed convection (g, p, gas)", C[1], bsize=5.7)
    box(64, 3.5, 34, 15.5, "Earth (no Site:PlanetaryBody)",
        "every hook is gated on planet.active or\nreplaces a literal by a variable with the\nsame Earth value → results bit-for-bit\nidentical to v26.2.0 (14 example files)",
        C[0], bsize=5.7)
    for y in ys:
        ax.annotate("", (57.6, y + hgt / 2), (63.4, 39.5),
                    arrowprops=dict(arrowstyle="-|>", color=C[1], lw=0.7, mutation_scale=6, alpha=0.75,
                                    shrinkA=0, shrinkB=1))
    save(fig, "core_fig1_hooks.png")


# --------------------------------------------------------------------------- audit
def fig_audit():
    facts = json.loads((DATA / "core_facts.json").read_text(encoding="utf-8-sig"))
    areas = facts["audit"]["areas"][::-1]
    labels = [a["label"] for a in areas]
    fig, ax = plt.subplots(figsize=(7.2, 2.7))
    left = np.zeros(len(areas))
    names = {"P0": "P0: first habitat run", "P1": "P1: windows, HVAC, plant, PV", "P2": "P2: fence off"}
    for k, col in zip(("P0", "P1", "P2"), BLUE_RAMP):
        v = np.array([a[k] for a in areas], float)
        ax.barh(labels, v, left=left, color=col, edgecolor="white", linewidth=1.6, height=0.62, label=names[k])
        for i, (l0, vi) in enumerate(zip(left, v)):
            if vi >= 4:
                ax.text(l0 + vi / 2, i, f"{vi:.0f}", ha="center", va="center", fontsize=6.6,
                        color="white" if k != "P2" else INK)
        left += v
    for i, tot in enumerate(left):
        ax.text(tot + 0.8, i, f"{tot:.0f}", va="center", fontsize=7, color=INK2)
    ax.set_xlabel("Findings (each with file and line in EnergyPlus v26.2.0)")
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, max(left) * 1.12)
    ax.legend(loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=3, fontsize=6.8)
    ax.tick_params(axis="y", labelsize=7.2, colors=INK2, length=0)
    save(fig, "core_fig2_audit.png")


# --------------------------------------------------------------------------- environment
def fig_environment():
    mo, ma = load("moon_equator_gen"), load("mars_jezero_gen")
    fig, axs = plt.subplots(3, 2, figsize=(7.4, 5.6), sharex="col")
    tm = mo["hour"] / 24
    sl = slice(16 * 24, 19 * 24)  # three Earth days on Mars
    ta = ma["hour"][sl] / 24
    # (a) solar altitude
    for ax, t, d, s in ((axs[0, 0], tm, mo, slice(None)), (axs[0, 1], ta, ma, sl)):
        ax.plot(t, d["py_alt"][s], **PY)
        ax.plot(t, d["cpp_alt"][s], **CPP)
        ax.axhline(0, color=AXIS, lw=0.8)
    axs[0, 0].set_ylabel("Solar altitude (°)")
    axs[0, 0].set_title("(a) Moon, equator: solar altitude")
    axs[0, 1].set_title("(b) Mars, Jezero: solar altitude")
    # (c,d) irradiance
    axs[1, 0].plot(tm, mo["py_beam"], **PY)
    axs[1, 0].plot(tm, mo["cpp_beam"], **CPP)
    axs[1, 0].set_ylabel("Irradiance (W/m²)")
    axs[1, 0].set_title("(c) Direct normal irradiance")
    axs[1, 0].set_ylim(-60, 1950)
    axs[1, 0].legend(loc="upper center", ncol=2, fontsize=6.8)
    axs[1, 1].plot(ta, ma["py_beam"][sl], **PY)
    axs[1, 1].plot(ta, ma["cpp_beam"][sl], **CPP)
    axs[1, 1].plot(ta, ma["py_dif"][sl], color=C[2], lw=1.7, label="diffuse horizontal (Python)")
    axs[1, 1].plot(ta, ma["cpp_dif"][sl], color=C[3], lw=1.0, ls=(0, (3, 1.5)), label="diffuse horizontal (C++)")
    axs[1, 1].set_title("(d) Direct normal and diffuse irradiance")
    axs[1, 1].set_ylim(-10, 560)
    axs[1, 1].legend(loc="upper center", ncol=2, fontsize=6.0)
    # (e,f) regolith and sky temperatures
    axs[2, 0].plot(tm, mo["py_Tg"], **PY)
    axs[2, 0].plot(tm, mo["cpp_Tg"], **CPP)
    axs[2, 0].set_ylabel("Temperature (°C)")
    axs[2, 0].set_title("(e) Regolith surface temperature")
    axs[2, 1].plot(ta, ma["py_Tg"][sl], **{**PY, "label": "regolith (Python)"})
    axs[2, 1].plot(ta, ma["cpp_Tg"][sl], **{**CPP, "label": "regolith (C++)"})
    axs[2, 1].plot(ta, ma["py_Tsky"][sl], color=C[2], lw=1.7, label="sky (Python)")
    axs[2, 1].plot(ta, ma["cpp_Tsky"][sl], color=C[3], lw=1.0, ls=(0, (3, 1.5)), label="sky (C++)")
    axs[2, 1].set_title("(f) Regolith surface and sky temperature")
    axs[2, 1].set_ylim(-165, 5)
    axs[2, 1].legend(loc="lower center", ncol=2, fontsize=6.0)
    axs[2, 0].set_xlabel("Elapsed time (Earth days)")
    axs[2, 1].set_xlabel("Elapsed time (Earth days)")
    fig.tight_layout(h_pad=0.8)
    save(fig, "core_fig3_environment.png")


# --------------------------------------------------------------------------- habitat response
def fig_response():
    mo, ma = load("moon_equator"), load("mars_jezero")
    S = json.loads((DATA / "core_summary.json").read_text(encoding="utf-8-sig"))
    fig, axs = plt.subplots(3, 2, figsize=(7.4, 5.8), sharex="col")
    for j, (d, case, title) in enumerate(((mo, "moon_equator", "Moon, equator"), (ma, "mars_jezero", "Mars, Jezero"))):
        t = d["hour"] / 24
        a, b = window(case, len(t))
        e = S[case]["comparison"]["energy"]
        for i, (k, lab, sc) in enumerate((("Qc", "Sensible cooling (kW)", 1e-3), ("top", "Top facet outer face (°C)", 1),
                                          ("tin", "Top facet inner face (°C)", 1))):
            ax = axs[i, j]
            ax.axvspan(t[a], t[b - 1], color="#f1efe8", lw=0, zorder=0)
            ax.plot(t, d[f"py_{k}"] * sc, **PY)
            ax.plot(t, d[f"cpp_{k}"] * sc, **CPP)
            ax.set_ylabel(lab)
        axs[0, j].set_title(f"({'ab'[j]}) {title}: sensible cooling")
        axs[1, j].set_title(f"({'cd'[j]}) Outer face of the top facet")
        axs[2, j].set_title(f"({'ef'[j]}) Inner face of the top facet")
        diff = 100 * (e["ep_cooling_kWh"] / e["py_cooling_kWh"] - 1)
        axs[0, j].text(t[a] + 0.4, axs[0, j].get_ylim()[1], f"comparison window\n{e['ep_cooling_kWh']:.1f} vs "
                       f"{e['py_cooling_kWh']:.1f} kWh ({diff:+.2f} %)", fontsize=6.3, color=INK2, va="top")
        axs[2, j].set_xlabel("Elapsed time (Earth days)")
    # data-driven limits (both curves fully visible, room for the window label at the top)
    for i, (k, sc, minspan) in ((0, ("Qc", 1e-3, 0.5)), (2, ("tin", 1, 1.0))):
        for j, d in enumerate((mo, ma)):
            v = np.concatenate([d[f"py_{k}"], d[f"cpp_{k}"]]) * sc
            lo, hi = float(np.nanmin(v)), float(np.nanmax(v))
            span = max(hi - lo, minspan)
            axs[i, j].set_ylim(lo - 0.25 * span, hi + (0.9 if i == 0 else 0.3) * span)
    for j in range(2):  # re-place the window labels after the y-limits change
        for txt in list(axs[0, j].texts):
            txt.set_y(axs[0, j].get_ylim()[1])
    axs[1, 0].set_ylim(top=210)
    axs[1, 0].legend(loc="upper left", ncol=2, fontsize=6.8)
    fig.tight_layout(h_pad=0.8)
    save(fig, "core_fig4_response.png")


def fig_habitats():
    """Geometry of the two verification habitats and the NASA-class habitat comparison."""
    import sys
    sys.path.insert(0, str(HERE.parents[1]))
    from exobem.cases import artemis_surface_habitat, lunar_habitat
    from exobem.plot import plot_geometry
    h = load("lunar_habitat")
    fig = plt.figure(figsize=(7.4, 6.0))
    ax1 = fig.add_subplot(2, 2, 1, projection="3d")
    ax2 = fig.add_subplot(2, 2, 2, projection="3d")
    plot_geometry(lunar_habitat(), ax=ax1, title="(a) Regolith-shielded module", elev=24, azim=-60)
    plot_geometry(artemis_surface_habitat(), ax=ax2, title="(b) NASA-class lunar habitat", elev=22, azim=-58)
    ax1.text2D(0.5, 0.95, "r 3 m, L 10 m, 1 m regolith over MLI;\nbottom facets rest on the regolith (hidden)",
               transform=ax1.transAxes, ha="center", va="top", fontsize=6.3, color=INK2)
    ax2.text2D(0.5, 0.95, "D 6.5 m, H 5.25 m, 174 m³, on legs;\nbeta cloth / MLI / aluminium",
               transform=ax2.transAxes, ha="center", va="top", fontsize=6.3, color=INK2)
    t = h["hour"] / 24
    ax3 = fig.add_subplot(2, 2, 3)
    ax3.plot(t, h["py_Qc"] / 1000, **PY)
    ax3.plot(t, h["cpp_Qc"] / 1000, **CPP)
    ax3.plot(t, h["py_Ql"] / 1000, color=C[2], lw=1.6, label="latent, ExoBEM")
    ax3.plot(t, h["cpp_Ql"] / 1000, color=C[3], lw=1.0, ls=(0, (3, 1.5)), label="latent, Thermonaut")
    ax3.set_ylabel("Cooling load (kW)")
    ax3.set_xlabel("Elapsed time (Earth days)")
    ax3.set_title("(c) Habitat (b): sensible and latent cooling")
    ax3.set_ylim(0, 9.8)
    ax3.legend(fontsize=6.0, ncol=2, loc="upper left", frameon=True, framealpha=0.95)
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.plot(t, h["py_To_s"], color=C[0], lw=1.6, label="south wall, ExoBEM")
    ax4.plot(t, h["cpp_To_s"], color=C[1], lw=1.0, ls=(0, (3, 1.5)), label="south wall, Thermonaut")
    ax4.plot(t, h["py_To_f"], color=C[2], lw=1.6, label="floor, ExoBEM")
    ax4.plot(t, h["cpp_To_f"], color=C[3], lw=1.0, ls=(0, (3, 1.5)), label="floor, Thermonaut")
    ax4.set_ylabel("Outer face (°C)")
    ax4.set_xlabel("Elapsed time (Earth days)")
    ax4.set_title("(d) Habitat (b): outer-face temperatures")
    ax4.set_ylim(-170, 230)
    ax4.legend(fontsize=6.0, loc="upper left", ncol=2, frameon=True, framealpha=0.95)
    fig.tight_layout(h_pad=1.0)
    save(fig, "core_fig5_habitats.png")


if __name__ == "__main__":
    fig_habitats()
    fig_hooks()
    fig_audit()
    fig_environment()
    fig_response()
