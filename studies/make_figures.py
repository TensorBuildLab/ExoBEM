"""Figures for the ExoBEM paper (reads studies/results and verification/results)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RES = ROOT / "studies" / "results"
VER = ROOT / "verification" / "results"
FIG = ROOT / "paper" / "ExoBEM" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

# validated reference palette (dataviz skill, light mode) - fixed categorical order
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8.5, "axes.titlesize": 9, "axes.labelsize": 8.5,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 1.4,
    "legend.frameon": True, "legend.facecolor": "white", "legend.edgecolor": "none", "legend.framealpha": 0.9, "legend.fontsize": 7.5, "savefig.dpi": 300, "figure.dpi": 110,
    "axes.titlecolor": INK, "axes.titleweight": "bold", "axes.titlelocation": "left",
})


def save(fig, name):
    fig.savefig(FIG / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", name)


def L(name):
    return np.load(RES / f"{name}.npz", allow_pickle=True)


# --------------------------------------------------------------------------- fig 1
def fig_architecture():
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.set_axis_off()
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 50)

    def box(x, y, w, h, title, body, color):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                    fc="white", ec=color, lw=1.4))
        ax.text(x + w / 2, y + h - 2.2, title, ha="center", va="top", fontsize=7.4, weight="bold", color=INK)
        ax.text(x + w / 2, y + h - 6.0, body, ha="center", va="top", fontsize=5.9, color=INK2, linespacing=1.35)

    box(1, 30, 22, 18, "Ephemeris", "Mars24 (Allison &\nMcEwen 2000)\nSelenographic Sun\nNOAA Earth (verification)", C[0])
    box(1, 6, 22, 20, "Site environment", "Moon: vacuum, 3 K sky,\nHayne regolith model\nMars: dust τ(Ls), two-\nstream, P(Ls), T_air, IR\nEarth: EPW reader", C[0])
    box(28, 6, 26, 42, "Heat-balance core", "EnergyPlus method,\nre-implemented\n\nOutside face: solar + LW (sky,\nregolith) + convection (none /\nCO2 600 Pa / TARP)\n\nConduction: implicit finite\nvolumes, stretched grid,\nk(T), cp(T)\n\nInside face: ScriptF LW +\ngravity/pressure-aware\nconvection\n\nZone air + ideal loads,\nsolved simultaneously", C[1])
    box(59, 30, 19, 18, "Thermal control", "Radiator sink\ntemperature\nHeat-pump lift,\npump power", C[2])
    box(59, 6, 19, 20, "Power system", "PV (fixed / 1-axis /\n2-axis), dust losses\nStorage sizing:\nlunar night,\ndust storms", C[2])
    box(82, 6, 17, 42, "Outputs", "Zone & surface\ntemperatures\n\nHeating / cooling /\nlatent loads\n\nElectric demand,\nradiator & storage\nsizing\n\nCSV / JSON", C[6])
    kw = dict(arrowstyle="-|>", color=MUTED, lw=1.0, mutation_scale=9)
    for (x0, y0, x1, y1) in ((23, 39, 28, 39), (23, 16, 28, 16), (12, 30, 12, 26.6), (54, 39, 59, 39),
                             (54, 16, 59, 16), (78, 39, 82, 39), (78, 16, 82, 16), (68.5, 30, 68.5, 26.6)):
        ax.annotate("", (x1, y1), (x0, y0), arrowprops=kw)
    save(fig, "fig1_architecture.png")


# --------------------------------------------------------------------------- fig 2
def fig_verification():
    rep = json.loads((VER / "energyplus_comparison.json").read_text())
    s = np.load(VER / "energyplus_comparison_series.npz")
    fig, axs = plt.subplots(1, 3, figsize=(7.4, 2.6), gridspec_kw=dict(width_ratios=[1, 1.25, 1.25]))
    ax = axs[0]
    for i, case in enumerate(("Case600_opaque", "Case900_opaque")):
        ax.scatter(s[f"{case}_eplus"] / 1000, s[f"{case}_exobem"] / 1000, s=2, color=C[i], alpha=0.5, lw=0,
                   label=case.replace("_opaque", "").replace("Case", "Case "), rasterized=True)
    lim = [-1.5, 3.2]
    ax.plot(lim, lim, color=INK2, lw=0.8)
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("EnergyPlus 23.2 net load (kW)")
    ax.set_ylabel("ExoBEM net load (kW)")
    ax.set_title("(a) Hourly net load")
    ax.legend(loc="upper left", markerscale=4)
    for j, (case, lab, d0) in enumerate((("Case600FF_opaque", "(b) Case 600FF, January", 14),
                                         ("Case900FF_opaque", "(c) Case 900FF, July", 195))):
        ax = axs[j + 1]
        e, x = s[f"{case}_eplus"], s[f"{case}_exobem"]
        t = np.arange(len(e)) / 144.0
        sl = slice(int(d0 * 144), int((d0 + 7) * 144))
        ax.plot(t[sl], e[sl], color=C[0], label="EnergyPlus 23.2")
        ax.plot(t[sl], x[sl], color=C[1], lw=1.0, ls="--", label="ExoBEM")
        ax.set_xlabel("Day of year")
        ax.set_ylabel("Zone air temperature (°C)")
        ax.set_title(lab)
        r = rep[case]
        ax.text(0.02, 0.04, f"annual RMSE {r['T_RMSE_K']:.2f} K, R² {r['T_R2']:.3f}", transform=ax.transAxes,
                fontsize=7, color=INK2)
        if j == 0:
            ax.legend(loc="upper right")
    fig.tight_layout()
    save(fig, "fig2_verification.png")


# --------------------------------------------------------------------------- fig 3
def fig_environment_models():
    from exobem.ephemeris import moon
    from exobem.environment.regolith import RegolithColumn
    from exobem.environment.twostream import appelbaum_net_flux_function
    from exobem.constants import TSI_1AU
    dtt = 1800.0
    n = int(moon.SYNODIC_MONTH_DAYS * 86400 / dtt)
    jd = 2460000.5 + np.arange(n) * dtt / 86400
    fig, axs = plt.subplots(1, 3, figsize=(7.4, 2.5))
    ax = axs[0]
    for i, lat in enumerate((0.0, 45.0, 75.0)):
        sp = moon.sun_position(jd, lat, 0.0)
        mu = np.cos(np.radians(sp.zenith_deg))
        G = np.where(mu > 0, TSI_1AU / sp.distance_au ** 2 * mu, 0)
        col = RegolithColumn()
        r = col.run(dtt, (1 - col.albedo(sp.zenith_deg)) * G, np.zeros(n), spinup_cycles=6, cycle_steps=n,
                    record_depths=(0.0, 0.3))
        lt = sp.extra["lunar_time_h"] % 24
        o = np.argsort(lt)
        ax.plot(lt[o], r["T_surface"][o], color=C[i], label=f"{lat:.0f}°")
    ax.axhspan(385, 395, color=C[3], alpha=0.25, lw=0)
    ax.axhspan(90, 100, color=C[3], alpha=0.25, lw=0)
    ax.text(0.3, 400, "Diviner equator, noon", fontsize=6.5, color=INK2)
    ax.text(0.3, 105, "Diviner equator, pre-dawn", fontsize=6.5, color=INK2)
    ax.set_xlabel("Lunar local time (h)")
    ax.set_ylabel("Surface temperature (K)")
    ax.set_xlim(0, 24); ax.set_xticks([0, 6, 12, 18, 24])
    ax.set_title("(a) Lunar regolith model")
    ax.legend(title="latitude", loc="center right", fontsize=7, title_fontsize=7)

    ax = axs[1]
    taus = np.linspace(0.01, 6, 100)
    for i, z in enumerate((0, 30, 60, 80)):
        ax.plot(taus, [float(appelbaum_net_flux_function(t, z)) for t in taus], color=C[i], label=f"z = {z}°")
    ref = _appelbaum_table()
    if ref:
        for i, z in enumerate((0, 30, 60, 80)):
            if z in ref:
                tt, ff = zip(*ref[z])
                ax.scatter(tt, ff, s=14, color=C[i], edgecolor="white", lw=0.8, zorder=3)
    ax.set_xlabel("Dust optical depth τ")
    ax.set_ylabel("Normalised net flux f(z, τ)")
    ax.set_title("(b) Mars surface insolation")
    ax.legend(loc="upper right")
    ax.text(0.03, 0.04, "lines: delta-Eddington\ndots: Appelbaum & Flood (1990)" if ref else "lines: delta-Eddington",
            transform=ax.transAxes, fontsize=6.5, color=INK2)

    ax = axs[2]
    d = L("mars_jezero")
    Ls, tau = d["Ls"], d["tau"]
    ds = L("mars_jezero_storm")
    o = np.argsort(Ls)
    ax.plot(Ls[o], ds["tau"][o], color=C[1], label="with 2018-type storm")
    ax.plot(Ls[o], tau[o], color=C[0], label="nominal")
    ax.set_xlabel("Solar longitude Ls (°)")
    ax.set_ylabel("Dust optical depth τ")
    ax.set_xlim(0, 360); ax.set_xticks([0, 90, 180, 270, 360])
    ax.set_title("(c) Jezero dust scenarios")
    ax.legend(loc="upper left")
    fig.tight_layout()
    save(fig, "fig3_environment_models.png")


def _appelbaum_table():
    f = ROOT / "docs" / "research" / "appelbaum_table.json"
    if f.exists():
        raw = json.loads(f.read_text())
        return {int(k): v for k, v in raw.items()}
    return None


# --------------------------------------------------------------------------- fig 4
def fig_environments():
    me, mp, ma = L("moon_equator"), L("moon_pole"), L("mars_jezero")
    fig, axs = plt.subplots(2, 3, figsize=(7.4, 4.0), sharex="col")
    SOL = 88775.244 / 86400
    sets = [(me, "Moon, equator (2 lunations)", 1.0, "Earth days"),
            (mp, "Moon, south-polar ridge (60 d)", 1.0, "Earth days"),
            (ma, "Mars, Jezero (5 sols, Ls ≈ 0°)", 1 / SOL, "Sols")]
    for j, (d, title, scale, xl) in enumerate(sets):
        t = d["t_days"] * scale
        if j == 1:
            m = t < 60
        elif j == 2:
            m = t < 5
        else:
            m = np.ones_like(t, bool)
        ax = axs[0, j]
        ax.plot(t[m], d["ghi"][m], color=C[3], label="global horizontal")
        ax.plot(t[m], (d["dni"] * d["sun_visible"])[m], color=C[0], lw=1.0, label="beam normal")
        if j == 2:
            ax.plot(t[m], d["dhi"][m], color=C[2], lw=1.0, label="diffuse horizontal")
        ax.set_title(title, fontsize=8.5)
        ax.set_ylabel("Irradiance (W/m²)" if j == 0 else "")
        ax.legend(loc="upper right", fontsize=6.5)
        ax.set_ylim(0, 1500 if j < 2 else 700)
        ax = axs[1, j]
        ax.plot(t[m], d["T_ground"][m], color=C[1], label="ground surface")
        ax.plot(t[m], d["T_sky"][m], color=C[6], label="effective sky")
        if np.isfinite(d["T_air"]).any():
            ax.plot(t[m], d["T_air"][m], color=C[2], label="air (1.5 m)")
        ax.set_xlabel(xl)
        ax.set_ylabel("Temperature (K)" if j == 0 else "")
        ax.set_ylim(0, 420)
        ax.legend(loc="center right" if j < 2 else "upper right", fontsize=6.5)
    fig.tight_layout()
    save(fig, "fig4_environments.png")


# --------------------------------------------------------------------------- fig 5
def fig_moon_habitat():
    d = L("moon_equator")
    names = list(d["names"])
    t = d["t_days"]
    fig, axs = plt.subplots(3, 1, figsize=(7.2, 5.4), sharex=True)
    ax = axs[0]
    for i, (nm, lab) in enumerate((("shell_00", "top facet (tilt 11°)"), ("shell_03", "side facet, south (tilt 79°)"),
                                   ("end_a", "end cap, east"), ("end_b", "end cap, west"))):
        k = names.index(nm)
        ax.plot(t, d["Tout"][:, k] + 273.15, color=C[i], label=lab)
    ax.set_ylabel("Outer surface (K)")
    ax.set_title("(a) Regolith-cover surface temperatures")
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.0), fontsize=6.8)
    ax.set_ylim(80, 470)
    ax = axs[1]
    ax.plot(t, d["Qc"] / 1000, color=C[0], label="sensible cooling")
    ax.plot(t, d["Qh"] / 1000, color=C[1], label="heating")
    ax.plot(t, d["Qlat"] / 1000, color=C[2], lw=1.0, label="latent (crew)")
    ax.set_ylabel("Load (kW)")
    ax.set_title("(b) Ideal thermal loads (cabin 18–27 °C)")
    ax.set_ylim(-0.1, 4.2)
    ax.legend(ncol=3, loc="upper right")
    ax = axs[2]
    ax.plot(t, d["T_sink"], color=C[6], label="radiator sink (N/S-facing, vertical)")
    rew = np.load(RES / "radiator_EW.npz")
    ax.plot(rew["t_days"], rew["T_sink"], color=C[4], label="radiator sink (E/W-facing, vertical)")
    ax.axhline(273.15 + 2 - 5, color=INK2, lw=0.8, ls=":")
    ax.text(0.5, 273.15 - 3 + 6, "evaporator 270 K", ha="left", fontsize=6.5, color=INK2)
    ax.set_ylabel("Temperature (K)")
    ax.set_xlabel("Elapsed time (Earth days from 2030-01-01)")
    ax.set_title("(c) Radiator sink temperature")
    ax.set_ylim(60, 400)
    ax.legend(loc="upper right", fontsize=6.8, ncol=2)
    fig.tight_layout()
    save(fig, "fig5_moon_habitat.png")


# --------------------------------------------------------------------------- fig 6
def fig_mars_year():
    a, b = L("mars_jezero"), L("mars_jezero_storm")
    SOL = 88775.244
    fig, axs = plt.subplots(3, 1, figsize=(7.2, 5.4), sharex=True)

    def daily(d, key):
        sol_idx = np.floor(d["t_days"] * 86400 / SOL).astype(int)
        n = sol_idx.max()
        v = np.bincount(sol_idx, weights=d[key], minlength=n + 1) / np.bincount(sol_idx, minlength=n + 1)
        Ls = np.bincount(sol_idx, weights=d["Ls"], minlength=n + 1) / np.bincount(sol_idx, minlength=n + 1)
        return np.arange(n + 1)[1:-1], Ls[1:-1], v[1:-1]

    s, Ls, g1 = daily(a, "ghi")
    _, _, g2 = daily(b, "ghi")
    ax = axs[0]
    ax.plot(s, g1, color=C[0], label="nominal dust")
    ax.plot(s, g2, color=C[1], label="global dust storm (τ_max = 6)")
    ax.set_ylabel("Sol-mean GHI (W/m²)")
    ax.set_title("(a) Insolation at Jezero over one Mars year")
    ax.legend(loc="lower left")
    ax = axs[1]
    _, _, ta = daily(a, "T_air")
    _, _, tg = daily(a, "T_ground")
    ax.plot(s, ta - 273.15, color=C[2], label="air, sol mean")
    ax.plot(s, tg - 273.15, color=C[1], lw=1.0, label="ground, sol mean")
    _, _, tas = daily(b, "T_air")
    ax.plot(s, tas - 273.15, color=C[2], lw=1.0, ls="--", label="air, sol mean, dust storm")
    ax.set_ylabel("Temperature (°C)")
    ax.set_title("(b) Near-surface temperatures")
    ax.legend(loc="lower left")
    ax = axs[2]
    for i, (d, lab) in enumerate(((a, "nominal"), (b, "dust storm"))):
        _, _, qh = daily(d, "Qh")
        _, _, qc = daily(d, "Qc")
        ax.plot(s, qc / 1000, color=C[i], label=f"cooling, {lab}")
        ax.plot(s, qh / 1000, color=C[i], ls="--", lw=1.0, label=f"heating, {lab}")
    ax.set_ylabel("Sol-mean load (kW)")
    ax.set_xlabel("Sol of Mars year (Ls = 0° at sol 0)")
    ax.set_title("(c) Habitat ideal loads")
    ax.set_ylim(-0.1, 2.6)
    ax.legend(ncol=2, loc="lower right", fontsize=6.8)
    # secondary Ls ticks as text on top axis
    top = axs[0].secondary_xaxis("top")
    ticks = [0] + [int(s[np.argmin(np.abs(((Ls - x) + 180) % 360 - 180))]) for x in (90, 180, 270)]
    top.set_xticks(ticks)
    top.set_xticklabels(["Ls 0°", "90°", "180°", "270°"], fontsize=7, color=MUTED)
    fig.tight_layout()
    save(fig, "fig6_mars_year.png")


# --------------------------------------------------------------------------- fig 7
def fig_envelopes():
    rep = json.loads((RES / "case_studies.json").read_text())
    fig, axs = plt.subplots(1, 3, figsize=(7.4, 3.0), sharey=False)
    for j, (key, title) in enumerate((("envelope_moon_equator", "(a) Moon, equator"),
                                      ("envelope_moon_pole", "(b) Moon, south pole"),
                                      ("envelope_mars_jezero", "(c) Mars, Jezero"))):
        d = rep[key]
        labs = list(d.keys())
        y = np.arange(len(labs))
        h = [d[l]["heating_kWh_per_day"] for l in labs]
        c = [d[l]["cooling_kWh_per_day"] for l in labs]
        ax = axs[j]
        ax.barh(y + 0.2, c, height=0.36, color=C[0], label="cooling")
        ax.barh(y - 0.2, h, height=0.36, color=C[1], label="heating")
        for yy, v in zip(y, c):
            if v > 0.5:
                ax.text(v + 0.5, yy + 0.2, f"{v:.0f}", va="center", fontsize=6.5, color=INK2)
        for yy, v in zip(y, h):
            if v > 0.5:
                ax.text(v + 0.5, yy - 0.2, f"{v:.0f}", va="center", fontsize=6.5, color=INK2)
        ax.set_yticks(y)
        ax.set_yticklabels(labs, fontsize=6.8)
        ax.invert_yaxis()
        ax.set_xlabel("Load (kWh per Earth day)")
        ax.set_title(title)
        ax.grid(axis="y", visible=False)
        if j == 0:
            ax.legend(loc="lower right")
    fig.tight_layout()
    save(fig, "fig7_envelopes.png")


# --------------------------------------------------------------------------- fig 8
def fig_convection():
    rep = json.loads((RES / "case_studies.json").read_text())["convection"]
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.7))
    ax = axs[0]
    g = np.array(rep["g"])
    for i, (k, lab) in enumerate((("101.3", "101.3 kPa, 21% O2"), ("70.3", "70.3 kPa, 26.5% O2"),
                                  ("56.5", "56.5 kPa, 34% O2"))):
        ax.plot(g, rep[k], color=C[i], label=lab)
    ax.axhline(rep["forced_0.15"], color=INK2, lw=0.8, ls=":")
    ax.text(9.8, rep["forced_0.15"] + 0.05, "forced, 0.15 m/s", ha="right", fontsize=6.5, color=INK2)
    for gv, nm in ((1.625, "Moon"), (3.721, "Mars"), (9.807, "Earth")):
        ax.axvline(gv, color=GRID, lw=1.0, zorder=0)
        ax.text(gv, ax.get_ylim()[1] if False else 2.25, nm, ha="center", fontsize=6.8, color=MUTED)
    ax.set_xlabel("Gravity (m/s²)")
    ax.set_ylabel("h (W/m²K)")
    ax.set_title("(a) Cabin natural convection")
    ax.set_ylim(0, 2.4)
    ax.legend(loc="lower right")
    ax = axs[1]
    w = np.array(rep["wind"])
    ax.plot(w, rep["earth_ext_mixed"], color=C[0], label="Earth air, 101 kPa")
    ax.plot(w, rep["mars_ext_mixed"], color=C[1], label="Mars CO2, 700 Pa")
    ax.set_yscale("log")
    ax.set_xlabel("Wind speed (m/s)")
    ax.set_ylabel("h (W/m²K)")
    ax.set_title("(b) Exterior convection")
    ax.legend(loc="center right")
    fig.tight_layout()
    save(fig, "fig8_convection.png")


if __name__ == "__main__":
    fig_architecture()
    fig_verification()
    fig_environment_models()
    fig_environments()
    fig_moon_habitat()
    fig_mars_year()
    fig_envelopes()
    fig_convection()
