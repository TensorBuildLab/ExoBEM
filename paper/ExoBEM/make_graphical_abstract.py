"""Graphical abstract for the ExoBEM paper (Applied Energy: landscape, shown at about 13 x 5 cm).

    python paper/ExoBEM/make_graphical_abstract.py  ->  paper/ExoBEM/ExoBEM_graphical_abstract.png

One story, left to right: the planetary environment (Moon night, Mars dust storm) -> the sealed habitat
(outer surfaces coloured by simulated temperature) -> what it means for the energy system (battery charge).
All data come from studies/results, the same files as the paper's figures and tables.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import cm, colors  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RES = ROOT / "studies" / "results"
sys.path.insert(0, str(ROOT))
from exobem.cases import artemis_surface_habitat  # noqa: E402

C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, MUTED, GRID, PANEL, NIGHT = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#f6f5f1", "#e4e6ee"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": "#c3c2b7",
                     "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 7, "ytick.labelsize": 7,
                     "axes.labelcolor": INK2, "axes.labelsize": 7.5})
SOL = 88775.244 / 86400.0

R = json.loads((RES / "case_studies.json").read_text(encoding="utf-8-sig"))
P, B = R["power"], R["baseline"]
L = lambda n: np.load(RES / f"{n}.npz", allow_pickle=True)  # noqa: E731


def panel(fig, x, y, w, h):
    fig.patches.append(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.003,rounding_size=0.012",
                                      transform=fig.transFigure, facecolor=PANEL, edgecolor="none", zorder=-5))


def arrow(fig, x0, x1, y):
    fig.patches.append(FancyArrowPatch((x0, y), (x1, y), transform=fig.transFigure, arrowstyle="-|>",
                                       mutation_scale=14, color=MUTED, lw=1.5))


def tidy(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=GRID, lw=0.5)
    ax.set_axisbelow(True)
    ax.tick_params(length=2, pad=1.5)


def shade_night(ax, t, up, ymax):
    ax.fill_between(t, 0, ymax, where=~up, color=NIGHT, lw=0, step="mid", zorder=0)


def sol_mean(t_days, y):
    k = np.floor(t_days / SOL).astype(int)
    n = k.max() + 1
    return np.arange(n), np.bincount(k, y, n) / np.maximum(np.bincount(k, None, n), 1)


def main():
    me, ms = L("moon_equator"), L("mars_jezero_storm")
    mn = L("mars_jezero")
    pe, ps = L("power_moon_equator"), L("power_mars_jezero_storm")

    fig = plt.figure(figsize=(7.4, 3.0))
    fig.text(0.012, 0.955, "ExoBEM: energy simulation of sealed habitats on the Moon and Mars", fontsize=11.5,
             weight="bold", color=INK, va="top")

    cols = [(0.008, 0.315), (0.345, 0.305), (0.678, 0.314)]
    top, bot = 0.86, 0.13
    for x, w in cols:
        panel(fig, x, bot, w, top - bot)
    arrow(fig, 0.325, 0.343, 0.5)
    arrow(fig, 0.652, 0.676, 0.5)
    heads = ["1  Planetary environment", "2  Sealed habitat", "3  Energy system"]
    for (x, w), h in zip(cols, heads):
        fig.text(x + 0.012, top - 0.02, h, fontsize=9.5, weight="bold", color=INK, va="top")

    # ------------------------------------------------------------------ 1: environment
    TK = dict(loc="left", fontsize=7.6, weight="bold", color=INK, pad=3)
    up_e = me["sun_visible"] > 0
    t = me["t_days"]
    ax = fig.add_axes([0.068, 0.525, 0.24, 0.195])
    shade_night(ax, t, up_e, 1500)
    ax.plot(t, me["ghi"], color=C[3], lw=1.3)
    ax.set_xlim(0, 59); ax.set_ylim(0, 1500); ax.set_yticks([0, 1000])
    ax.set_xticks([0, 20, 40]); ax.set_xticklabels(["0", "20", "40 days"])
    ax.set_ylabel("W/m²", labelpad=1)
    ax.set_title("Moon, equator: sunlight", **TK)
    ax.text(31.5, 750, "354-h\nnight", fontsize=7, color=INK2, ha="center", va="center", linespacing=1.0)
    tidy(ax)

    ax = fig.add_axes([0.068, 0.215, 0.24, 0.195])
    s, gn = sol_mean(mn["t_days"], mn["ghi"])
    s2, gs = sol_mean(ms["t_days"], ms["ghi"])
    s, gn, s2, gs = s[:-1], gn[:-1], s2[:-1], gs[:-1]          # drop the partial last sol
    ax.plot(s, gn, color=C[0], lw=1.2)
    ax.plot(s2, gs, color=C[7], lw=1.3)
    ax.set_xlim(0, 668); ax.set_ylim(0, 180); ax.set_yticks([0, 100])
    ax.set_xticks([0, 200, 400, 600]); ax.set_xticklabels(["0", "200", "400", "600 sols"])
    ax.set_ylabel("W/m²", labelpad=1)
    ax.set_title("Mars, Jezero: sol-mean sunlight", **TK)
    ax.text(380, 40, "global\ndust storm", fontsize=7, color=C[7], ha="right", va="center", linespacing=1.0)
    ax.annotate("nominal", xy=(470, 112), xytext=(600, 45), fontsize=7, color=C[0], ha="center",
                arrowprops=dict(arrowstyle="-", color=C[0], lw=0.7))
    tidy(ax)

    # ------------------------------------------------------------------ 2: habitat
    llt = me["lunar_local_time_h"]
    names = [str(n) for n in me["names"]]
    norm = colors.Normalize(-160, 120)
    cmap = plt.get_cmap("RdYlBu_r")
    geo = artemis_surface_habitat().zone.geometry
    v = np.array([q for srf in geo.surfaces if srf.vertices for q in srf.vertices])
    c0, r = v.mean(axis=0), (v.max(axis=0) - v.min(axis=0)).max() / 2
    shown = {}
    for k, (hour, x0, label) in enumerate([(12.0, 0.348, "lunar noon"), (0.0, 0.497, "lunar night")]):
        i = int(np.argmin(np.abs(llt - hour) + 100 * (t < 30)))      # second lunation
        Tout = dict(zip(names, me["Tout"][i]))
        shown[label] = [Tout[n] for n in names if n != "floor"]
        ax3 = fig.add_axes([x0, 0.33, 0.15, 0.43], projection="3d")
        ax3.set_facecolor("none")
        for srf in geo.surfaces:
            if srf.name == "floor" or not srf.vertices:
                continue
            ax3.add_collection3d(Poly3DCollection([srf.vertices], facecolor=cmap(norm(Tout[srf.name])),
                                                  edgecolor="#3d3d3a", lw=0.4))
        ax3.set_xlim(c0[0] - r, c0[0] + r); ax3.set_ylim(c0[1] - r, c0[1] + r); ax3.set_zlim(c0[2] - r, c0[2] + r)
        ax3.set_box_aspect((1, 1, 1))
        ax3.view_init(elev=18, azim=-62)
        ax3.set_axis_off()
        fig.text(x0 + 0.075, 0.37, label, fontsize=7.6, color=INK, weight="bold", ha="center")
        fig.text(x0 + 0.075, 0.33, f"walls {np.mean(shown[label]):+.0f} °C".replace("-", "−"), fontsize=7.2, color=INK2, ha="center")
    fig.text(0.423, 0.74, "☀", fontsize=15, color=C[3], ha="center", va="center")
    fig.text(0.572, 0.74, "sky 3 K", fontsize=7.2, color=C[0], weight="bold", ha="center", va="center")
    q = B["moon_equator"]["tcs_heat_kWh_per_day"] / 24
    fig.text(0.358, 0.275, f"4 crew, 14 kW inside\n→ {q:.0f} kW to reject\nno outdoor air", fontsize=7.2, color=INK,
             linespacing=1.15, va="top")
    cax = fig.add_axes([0.505, 0.205, 0.12, 0.022])
    cb = fig.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal")
    cb.set_ticks([-150, 0, 100]); cb.ax.tick_params(labelsize=6.5, length=1.5, pad=1)
    cb.outline.set_visible(False)
    cax.set_title("outer surface (°C)", fontsize=6.8, color=INK2, pad=2)

    # ------------------------------------------------------------------ 3: energy system
    a = fig.add_axes([0.733, 0.525, 0.24, 0.195])
    up_p = np.interp(pe["t_days"], t, up_e.astype(float)) > 0.5
    shade_night(a, pe["t_days"], up_p, 100)
    a.plot(pe["t_days"], 100 * pe["A2_soc"], color=C[2], lw=1.4)
    a.set_xlim(0, 59); a.set_ylim(0, 100); a.set_yticks([0, 50, 100])
    a.set_xticks([0, 20, 40]); a.set_xticklabels(["0", "20", "40 days"])
    a.set_ylabel("battery %", labelpad=1)
    mw = P["moon_equator"]["PV x2 + Li-ion"]
    a.set_title(f"Moon night: {mw['storage_kWh']/1000:.1f} MWh ({mw['storage_mass_t']:.0f} t)", **TK)
    tidy(a)

    a = fig.add_axes([0.733, 0.215, 0.24, 0.195])
    a.plot(ps["t_days"] / SOL, 100 * ps["A2_soc"], color=C[7], lw=1.3)
    a.set_xlim(0, 668); a.set_ylim(0, 100); a.set_yticks([0, 50, 100])
    a.set_xticks([0, 200, 400, 600]); a.set_xticklabels(["0", "200", "400", "600 sols"])
    a.set_ylabel("battery %", labelpad=1)
    ms2 = P["mars_jezero_storm"]["PV x2 + Li-ion"]
    a.set_title(f"Mars storm: {ms2['storage_kWh']/1000:.0f} MWh ({ms2['storage_mass_t']:.0f} t)", **TK)
    tidy(a)

    # ------------------------------------------------------------------ bottom line
    fig.text(0.012, 0.06, "Verified against EnergyPlus (within 0.7 %)  ·  open-source Python", fontsize=7.6,
             color=INK2, va="center")
    fig.text(0.992, 0.06, "Or one 40 kWe fission unit: no storage needed", fontsize=8.2, color=INK,
             weight="bold", ha="right", va="center")

    out = HERE / "ExoBEM_graphical_abstract.png"
    fig.savefig(out, dpi=400, facecolor="white")
    print("wrote", out, {k: (round(min(v)), round(max(v))) for k, v in shown.items()})


if __name__ == "__main__":
    main()
