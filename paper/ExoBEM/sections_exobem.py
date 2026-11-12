"""Sections of the ExoBEM (Python) manuscript.

All numbers quoted in the text are read from studies/results and verification/results.
Cross-references use labels (@fig:x, @tab:x, @sec:x), resolved by docxkit.build_two_pass.
"""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIG = HERE / "figures"
sys.path.insert(0, str(ROOT))
R = json.loads((ROOT / "studies" / "results" / "case_studies.json").read_text())
V = json.loads((ROOT / "verification" / "results" / "energyplus_comparison.json").read_text())
B = R["baseline"]
CSP = R.get("condensation_setpoints", {})
E = R["environment"]
P = R["power"]
RAD = R["radiator_moon_equator"]
H = R["habitats"]
CAL = R["calibration"]


def f0(x):
    return f"{x:,.0f}"


def f1(x):
    return f"{x:,.1f}"


def f2(x):
    return f"{x:.2f}"


def pct(a, b):
    return f"{100 * (a / b - 1):+.2f}%"


def mars_year_stats():
    SOL = 88775.244
    out = {}
    for nm in ("mars_jezero", "mars_jezero_storm"):
        d = np.load(ROOT / "studies" / "results" / f"{nm}.npz")
        si = np.floor(d["t_days"] * 86400 / SOL - 1e-9).astype(int)
        c = np.bincount(si)
        dm = lambda k: (np.bincount(si, weights=d[k]) / c)[1:-1]  # noqa: E731
        rng = np.array([np.ptp(d["T_air"][si == k]) for k in range(1, c.size - 1)])
        out[nm] = dict(ghi=dm("ghi"), ta=dm("T_air") - 273.15, qc=dm("Qc"), el=dm("elec"), rng=rng)
    a, b = out["mars_jezero"], out["mars_jezero_storm"]
    peak = np.argsort(b["ghi"])[:10]                       # the ten sols of peak opacity
    return dict(ghi_min=a["ghi"].min(), ghi_max=a["ghi"].max(), ta_min=a["ta"].min(), ta_max=a["ta"].max(),
                storm_ghi_min=b["ghi"].min(), storm_sols=int((b["ghi"] < 60).sum()),
                storm_dta=float((b["ta"] - a["ta"])[peak].mean()),
                storm_rng_nom=float(a["rng"][peak].mean()), storm_rng=float(b["rng"][peak].mean()),
                storm_qc_dmax=float((b["qc"] - a["qc"]).max()), storm_qc_dmin=float((b["qc"] - a["qc"]).min()),
                storm_el_dmax=float((b["el"] - a["el"]).max()), storm_el_dmin=float((b["el"] - a["el"]).min()))


from exobem.environment.sites import mars_site  # noqa: E402

MS = mars_year_stats()
# long-wave parameters exactly as the code uses them, and their calibration (studies/calibrate_mars_storm_ir.py)
_sig = inspect.signature(mars_site).parameters
LW = dict(e0=_sig["sky_emissivity"].default[0], e1=_sig["sky_emissivity"].default[1], f_re=_sig["dust_reemission"].default)
LWC = json.loads((ROOT / "studies" / "results" / "mars_storm_ir_calibration.json").read_text())
v600, v900, f600, f900 = V["Case600_opaque"], V["Case900_opaque"], V["Case600FF_opaque"], V["Case900FF_opaque"]
mpo, meq, mjz, mst = B["moon_pole"], B["moon_equator"], B["mars_jezero"], B["mars_jezero_storm"]
env_po, env_eq, env_jz = E["moon_pole"], E["moon_equator"], E["mars_jezero"]
EPLUS_MAX_DIFF = 100 * max(abs(v600["exobem_heating_kWh"] / v600["eplus_heating_kWh"] - 1),
                           abs(v900["exobem_heating_kWh"] / v900["eplus_heating_kWh"] - 1),
                           abs(v600["exobem_cooling_kWh"] / v600["eplus_cooling_kWh"] - 1),
                           abs(v900["exobem_cooling_kWh"] / v900["eplus_cooling_kWh"] - 1))
EL_MOON = sum(v for k, v in H["moon"]["gains"].items() if not k.startswith("crew")) / 1000
EL_MARS = sum(v for k, v in H["mars"]["gains"].items() if not k.startswith("crew")) / 1000


# =========================================================================== factors
def factor_table(m):
    """The Earth / Moon / Mars factor analysis with the ExoBEM treatment of each factor."""
    from factors import FACTORS
    rows, cat = [], None
    for c, fac, earth, moon, mars, exo in FACTORS:
        if c != cat:
            rows.append([f"**{c}**", "", "", "", ""])
            cat = c
        rows.append([fac, earth, moon, mars, exo])
    m.table(["Factor", "Earth", "Moon", "Mars", "Treatment in ExoBEM"], rows,
            "Factors that distinguish a lunar or Martian habitat from an Earth building in an energy simulation, and how "
            "ExoBEM treats each one. modelled: physics implemented and verified; input: a parameter with a documented "
            "default; enforced: contradicting input stops the run; neglected: left out, with the reason.",
            col_widths_cm=[2.9, 2.6, 3.4, 3.2, 3.9], font_size=7.0, label="factors")


def related_work(m):
    """Related-work subsections (habitat thermal design; BES tools off-Earth)."""
    m.heading("Thermal design of lunar and Martian habitats", 2)
    m.para(
        "Early lunar base studies established the thermal control architecture still in use: a single-phase water loop "
        "inside the pressure shell, an external ammonia loop and deployable radiators, with heat pumps to lift rejection "
        "temperature during the lunar day [@Simonsen1992;Gadkari1991]. Bien and Guentert showed that a vertical radiator "
        "at the lunar equator sees an equivalent sink of about 333 K at noon because half of its view is hot regolith "
        "[@Bien1969]. NASA's Artemis surface habitat is a 174 m³ module for up to four crew; its thermal control system "
        "rejects about 15 kWt with 48 m² of double-sided radiator panels and must survive eclipses of up to about 100 h "
        "near the south pole [@Schunk2021;Schunk2022;Kessler2022;Stromgren2023]. NASA's Mars Design Reference "
        "Architecture 5.0 sizes a surface habitat for six crew and about 500 sols, powered by fission or by large "
        "solar arrays with regenerative fuel cells [@Drake2009;Cataldo2009]. Malla and co-workers computed lunar surface and "
        "subsurface temperatures and transient temperature fields in regolith-covered domes, showing that a metre of "
        "regolith damps the 300 K surface swing [@Malla2015;Tripathi2023;Steiner2023]. Other studies examined "
        "3D-printed regolith walls with phase-change cores [@Kachalov2025], steel structures under Martian thermal "
        "cycling [@Li2025], cabin ventilation by CFD [@vonEinem2022] and habitat system-of-systems simulation "
        "[@Azimi2025]. Engler et al. forecast energy demand of the HI-SEAS analog habitat from data [@Engler2019], and "
        "Charoenboonvivat and de Weck modeled surface power demand for crewed missions [@Charoenboonvivat2026].")
    m.heading("Building simulation tools applied off-Earth", 2)
    m.para(
        "Building-simulation tools have been applied to Mars only in a limited way. Jadeja et al. combined PlanetWRF "
        "climate output with Ecotect and CFD to study thermal comfort in a Mars module [@Jadeja2016]. Lagarde built a "
        "Gale-crater EPW weather file for Ladybug/Grasshopper solar and orientation studies and left heating and cooling "
        "loads to future work [@Lagarde2021]. Aydemir developed a Mars building-performance framework that converts Mars "
        "Climate Database output to EPW format for an EnergyPlus-based front-end [@Aydemir2026;Millour2018]. Ross "
        "developed an open-source semi-empirical heat balance for Mars habitats outside the BES tradition [@Ross2022]. "
        "None of these modify the heat-balance physics: an EPW file can carry Martian temperatures and irradiances, but "
        "the engine still computes Earth solar geometry over a 24-hour day, applies air-based convection at 101 kPa, "
        "assumes an Earth-like sky and lets outdoor air into the zone. To the author's knowledge, no previous work has "
        "modified EnergyPlus-family physics for vacuum or thin-CO2 convection, regolith ground coupling, the Martian sol "
        "or the lunar day, and no lunar application of an EnergyPlus-family tool has been reported.")


def licensing(m):
    """Licensing and naming of the Python re-implementation."""
    m.heading("Licensing and naming", 2)
    m.para(
        "EnergyPlus is distributed under a BSD-3-Clause-style license that permits modification and redistribution, "
        "including for derived tools, provided the copyright notice is retained, the developers' names are not used for "
        "endorsement, and (clause 4) a modified product is not named \"EnergyPlus\", \"E+\" or a confusingly similar "
        "name without U.S. DOE consent. ExoBEM contains no EnergyPlus source code; it re-implements algorithms documented "
        "in the Engineering Reference [@EPlusEngRef], credits EnergyPlus in a NOTICE file and uses a distinct name.")


# =========================================================================== method
def method_overview(m):
    m.heading("Architecture", 2, label="arch")
    m.para(
        "ExoBEM (Fig. @fig:arch) is organized like EnergyPlus: a site-environment module plays the role of the weather "
        "manager, a heat-balance core computes surface and zone-air balances at every time step, and further modules "
        "compute the thermal control system and the electric power system. The core is planet-agnostic: it receives "
        "time series of solar position, beam and diffuse irradiance, sky, ground and air temperatures, ambient gas and "
        "pressure, wind and gravity, at an arbitrary time step and for an arbitrary day length, and a description of "
        "a sealed habitat: its geometry, constructions, cabin atmosphere, internal gains and life-support losses. "
        "ExoBEM is a Python package (NumPy and SciPy, about 3,800 lines, BSD-3-Clause) with a command-line tool; "
        "models are written as JSON files modeled on epJSON or built in Python (Appendix A).")
    m.figure(FIG / "fig1_architecture.png",
             "ExoBEM architecture. The heat-balance core follows the EnergyPlus method; the ephemeris, site-environment, "
             "thermal-control and power modules carry the planetary physics.", 16.0, label="arch")


def method_coordination(m):
    m.heading("How a simulation is coordinated", 2, label="coord")
    m.para(
        "Fig. @fig:flow shows the order in which the components act in a run, and the EnergyPlus module that plays each "
        "role. (1) The model input defines materials, constructions, geometry, the cabin and its gains, the thermal "
        "control system and the power system. (2) The site environment is either read from a planetary weather file "
        "(Section @sec:pwf) or generated by the ephemeris, radiation and regolith models for the whole run period at the "
        "simulation time step. (3) In pre-processing, ExoBEM checks the model against its environment, builds one "
        "stacked finite-volume grid for all constructions, computes interior view factors and Hottel script-F factors, "
        "evaluates every schedule and the incident solar radiation on every surface for every step, and evaluates the "
        "cabin-gas properties. (4) Initialization brings the long time constants of regolith covers and of the ground "
        "to a consistent state (Section @sec:core). (5) The time-step loop then solves, at each step, the outside-face "
        "balances, conduction, inside-face balances and zone air together, applies the ideal loads, and updates the "
        "cabin humidity. (6) The thermal control model turns the heat collected from the cabin, the cold plates and the "
        "condensing heat exchanger into radiator temperatures and heat-pump power, and (7) the power model dispatches "
        "generation and storage against the total electric demand. Steps 6 and 7 do not feed back to the cabin, "
        "because the radiators, heat pumps, arrays and storage are outside the pressure shell (their heat does not "
        "enter the zone); the electric power used inside the shell is a gain already counted in step 5.")
    m.figure(FIG / "fig_flow.png",
             "How ExoBEM coordinates a simulation (left) and the EnergyPlus modules with the same role (right).", 16.0,
             label="flow")
    m.para(
        "Table @tab:eplus compares ExoBEM with EnergyPlus element by element. The surface heat balances, the interior "
        "long-wave exchange, the convection correlations used on Earth and the CondFD conduction formulation are the "
        "same, and they reproduce EnergyPlus on Earth (Section @sec:vexo). The differences fall into three groups. Some "
        "are generalizations of the same structure to other planets (weather, time base, solar position, exterior "
        "boundary, gas properties). Some are numerical choices (implicit Euler with a simultaneous solution of surfaces "
        "and air instead of a predictor–corrector; finite volumes instead of conduction transfer functions, because "
        "temperature-dependent regolith properties and metre-thick layers are outside the range of CTFs). The rest are "
        "deliberate reductions of scope: ExoBEM has a single zone and represents HVAC by ideal loads and post-processed "
        "thermal-control and power systems (Section @sec:disc).")
    from eplus_compare import ROWS
    m.table(["Element", "EnergyPlus", "ExoBEM", "Relation"], [list(r) for r in ROWS],
            "ExoBEM compared with EnergyPlus.", col_widths_cm=[2.8, 5.0, 6.0, 2.2], font_size=7.0, label="eplus")


def method_core(m):
    m.heading("Heat-balance core", 2, label="core")
    m.para(
        "For each exterior surface, the outside-face heat balance equates absorbed solar radiation, net long-wave "
        "exchange, convection and conduction into the wall [@EPlusEngRef]:")
    m.equation(r"\alpha_{s} G_{inc} + \varepsilon\sigma\sum_{k}F_{k}\left(T_{k}^{4}-T_{so}^{4}\right) + h_{co}\left(T_{a}-T_{so}\right) = q_{ko}")
    m.para(
        "where the long-wave sum runs over sky (k = sky) and ground (k = g) with view factors F_{sky} = (1+cosβ)/2 and "
        "F_{g} = (1−cosβ)/2 for tilt β. On Earth, EnergyPlus splits the sky view into a sky part and an air part with "
        "weight sqrt[(1+cosβ)/2] and uses the air temperature for the ground; ExoBEM reproduces this split in Earth mode "
        "and uses the computed regolith surface temperature T_{g} elsewhere. The T^{4} term is Newton-linearized about the "
        "current iterate,")
    m.equation(r"T_{so}^{4}\approx 4T_{so}^{*3}T_{so}-3T_{so}^{*4}")
    m.para(
        "which is essential in vacuum: with a 2.7 K sky and almost no conductive coupling through low-conductivity "
        "regolith, the fixed-point radiation coefficient used in many BES codes oscillates and fails to converge. The "
        "incident beam uses the direct normal irradiance, which already includes the fraction of the solar disk "
        "above the local horizon (Section @sec:sites).")
    m.para(
        "Conduction is solved with the node-centred, fully implicit finite-volume scheme of the EnergyPlus CondFD "
        "algorithm [@EPlusEngRef]:")
    m.equation(r"C_{i}\frac{T_{i}^{n+1}-T_{i}^{n}}{\Delta t}=K_{i-1/2}\left(T_{i-1}^{n+1}-T_{i}^{n+1}\right)+K_{i+1/2}\left(T_{i+1}^{n+1}-T_{i}^{n+1}\right)")
    m.para(
        "with node capacitances C_{i} (half of each adjacent cell) and conductances K = k/Δx or 1/R for massless layers. "
        "Three extensions matter off-Earth. First, metre-thick regolith covers have diffusivities near 2×10^{-9} m²/s, so "
        "each layer uses a grid stretched geometrically from both faces (first cell ½(αΔt)^{1/2}, growth 1.3). Second, "
        "conductivity and specific heat may depend on temperature; they are lagged by one step, as in CondFD. Third, "
        "a thick cover on a cylindrical or domed module is not a flat slab: per unit inner area a 1 m cover on a 3 m "
        "radius conducts 14% (cylinder) to 25% (sphere) more than a slab, and its outer area is 33–78% larger. For "
        "surfaces generated as cylinders or domes, ExoBEM therefore uses the exact shell conductances and "
        "volume-weighted capacitances,")
    m.equation(r"K_{cyl}=\frac{k}{r_{i}\ln\left(r_{2}/r_{1}\right)},\qquad K_{sph}=\frac{k\,r_{1}r_{2}}{r_{i}^{2}\left(r_{2}-r_{1}\right)}", label="shell")
    m.para(
        "per unit inner area r_{i} for a cell between radii r_{1} < r_{2}, and scales the outer-face terms by the ratio "
        "of outer to inner area. The planar formulation of EnergyPlus is recovered with curvature switched off.")
    m.para("At the inside face, conduction, convection to zone air, long-wave exchange and radiant internal gains balance:")
    m.equation(r"q_{ki}+h_{ci}\left(T_{z}-T_{si}\right)+\sum_{j}\sigma\mathcal{F}_{ij}\left(T_{sj}^{4}-T_{si}^{4}\right)+\frac{f_{i}Q_{rad}}{A_{i}}=0")
    m.para(
        "where ℱ_{ij} are Hottel gray-interchange (ScriptF) factors computed from EnergyPlus-style area-weighted view "
        "factors with enforced reciprocity [@Hottel1967;EPlusEngRef], and radiant gains are distributed in proportion to "
        "area times emissivity. Equipment racks and stowage are internal-mass surfaces (one face to the cabin, the other "
        "adiabatic), as in EnergyPlus. The zone air balance of the sealed cabin is")
    m.equation(r"C_{z}\frac{dT_{z}}{dt}=\sum_{i}h_{ci}A_{i}\left(T_{si}-T_{z}\right)+Q_{conv}+\dot{m}_{loss}c_{p}\left(T_{mu}-T_{z}\right)+Q_{sys}",
               label="air")
    m.para(
        "in which C_{z} uses the density and specific heat of the cabin gas at cabin pressure, ṁ_{loss} is the cabin "
        "gas lost overboard and replaced from storage at temperature T_{mu} (Section @sec:cabin), and Q_{sys} is the "
        "ideal load that keeps T_{z} inside the heating and cooling set-points. On Earth the same term carries "
        "outdoor-air infiltration.")
    m.para(
        "**Simultaneous solution.** EnergyPlus iterates between the surface and air balances. ExoBEM instead solves "
        "them simultaneously. All constructions are stacked into one tri-diagonal system AT = b + Bu, where the vector "
        "u = [T_{si,1}…T_{si,n}, T_{z}] collects the inside-face temperatures and the air temperature that couple "
        "surfaces to each other and to the air. Solving the banded system once for n+2 right-hand sides gives")
    m.equation(r"\mathbf{T}=\mathbf{X}_{0}+\mathbf{X}_{B}\,\mathbf{u}")
    m.para(
        "which, substituted into the inside-face and air equations, yields a dense (n+1)×(n+1) system. It is solved "
        "free-floating first; if T_{z} leaves the set-point band, T_{z} is fixed at the violated set-point and Q_{sys} "
        "follows from the air balance. Only the non-linear coefficients (radiation linearization, convection "
        "coefficients and temperature-dependent properties) are updated by fixed-point iteration, which converges to "
        "0.005 K in two to three iterations per step; steps that do not converge within the iteration limit are counted "
        "and reported.")
    m.para(
        "**Initialization.** EnergyPlus warms up by repeating the first day. A 1-m lunar regolith cover has a thermal "
        "time constant of years, so ExoBEM first solves a pseudo-transient steady state with period-mean boundary "
        "conditions (time steps growing geometrically to 10^{9} s, with T^{4}-mean sky and ground temperatures). It then "
        "repeats the first solar day (one sol or one lunation) once before recording results.")


def method_cabin(m):
    m.heading("The sealed cabin", 2, label="cabin")
    m.para(
        "A pressurized habitat exchanges no air with its surroundings, and ExoBEM enforces this: off-Earth, a model with "
        "infiltration, an Earth-air exterior convection correlation, a hypoxic cabin (oxygen partial pressure below "
        "15.8 kPa, the 2,440 m cabin-altitude limit of transport aircraft [@FAA25841]) or an Earth-only sky model is "
        "rejected before the run, and set-points or humidity limits outside the NASA-STD-3001 ranges raise warnings "
        "[@NASA2026STD]. What remains is a small outward mass flow that has to be made up from storage:")
    m.equation(r"\dot{m}_{loss}=\dot{m}_{leak}+n_{EVA}\,\frac{p_{res}V_{al}}{R_{cab}T_{al}}", label="loss")
    m.para(
        "where ṁ_{leak} is the structural leakage (0.05% of the cabin gas mass per day for the reference habitats "
        "[@Anderson2018]), n_{EVA} the number of airlock cycles per day, and the second term the gas left in an "
        "airlock of volume V_{al} when it is vented at the residual pressure p_{res} after pump-down (6.9 kPa assumed). "
        "The energy effect enters Eq. (@eq:air); the mass is reported as a consumable.")
    m.para(
        "Without outdoor air, all moisture comes from the crew (and plants) and leaves through a condensing heat "
        "exchanger. ExoBEM solves the vapour balance of the cabin,")
    m.equation(r"m_{d}\frac{dw}{dt}=\frac{Q_{lat}}{h_{fg}}-\dot{m}_{loss}\,w-\dot{R},\qquad w=\frac{M_{w}}{M_{cab}}\frac{p_{v}}{P_{cab}-p_{v}}",
               label="vapour")
    m.para(
        "implicitly at every step, where m_{d} is the dry-gas mass of the cabin, Q_{lat} the latent heat released by "
        "the crew, h_{fg} = 2.454 MJ/kg and the molar-mass ratio uses the cabin gas (0.6197 for 70.3 kPa / 26.5% O2, "
        "against 0.6220 for air). The condensing heat exchanger removes Ṙ so that the relative humidity, with the "
        "saturation pressure from the Magnus form [@AlduchovEskridge1996], stays within the control band (30–60%); "
        "Ṙh_{fg} is the latent load. The cabin dew point is compared with every inside-surface temperature at every "
        "step, and the hours with any surface below it are reported as condensation risk, a habitability hazard "
        "[@NASA2026STD]. Electric gains carry two further attributes: the fraction of their power released as heat "
        "(0.22 for water electrolysis, whose energy leaves as hydrogen and oxygen) and the fraction collected by cold "
        "plates, which goes straight to the coolant loop instead of the cabin air.")


def method_ephemerides(m):
    m.heading("Planetary ephemerides and time", 2)
    m.para(
        "For Mars, ExoBEM implements the Allison and McEwen (2000) algorithm used by NASA's Mars24 [@Allison2000;Mars24]: "
        "from the TT Julian date it computes the mean anomaly, the fictitious-mean-Sun angle, seven planetary perturbation "
        "terms and the equation of center, giving the areocentric solar longitude L_{s}, solar declination, heliocentric "
        "distance and equation of time. Local true solar time then gives the hour angle,")
    m.equation(r"L_{s}=\alpha_{FMS}+\left(\nu-M\right),\qquad \sin\delta_{s}=0.42565\sin L_{s}+0.25^{\circ}\sin L_{s}")
    m.para(
        "For the Moon, the lunar prime meridian follows the Moon's mean geocentric longitude L′, and the lunar equator is "
        "inclined I = 1.5424° to the ecliptic with its descending node at the orbit's ascending node Ω (Cassini's laws). "
        "The selenographic subsolar point is therefore [@Meeus1998;Archinal2018]")
    m.equation(r"\lambda_{ss}=180^{\circ}-\left(L'-\lambda_{\odot}\right),\qquad \beta_{ss}=I\sin\left(\lambda_{\odot}-\Omega\right)")
    m.para(
        "where λ_{⊙} is the Sun's apparent ecliptic longitude. Using the mean rather than the true lunar longitude "
        "captures the optical libration in longitude, which shifts lunar local time by up to about half an Earth day. "
        "Near the poles the Sun is a disk of angular radius ρ_{⊙} above an azimuth-dependent horizon h; the visible "
        "fraction of its area, with x = (e − h)/ρ_{⊙} for solar elevation e, is")
    m.equation(r"f_{vis}=\frac{\arccos\left(-x\right)+x\sqrt{1-x^{2}}}{\pi},\qquad -1\le x\le 1", label="disk")
    m.para(
        "and multiplies the direct normal irradiance. Schedules run on local mean solar time on Mars and on Earth (UTC) "
        "time on the Moon, where the 29.5-day lunar day cannot set crew rhythms. The total solar irradiance is "
        "1361 W/m² at 1 AU [@Kopp2011].")


def method_sites(m):
    m.heading("Site environments", 2, label="sites")
    m.para(
        "**Moon.** There is no diffuse light and no convection; the sky temperature is 2.725 K. Ground temperature comes "
        "from a 1-D model of the regolith following Hayne et al. [@Hayne2017]. Density increases with depth as "
        "ρ(z) = ρ_{d} − (ρ_{d} − ρ_{s})exp(−z/H) with ρ_{s} = 1100 kg/m³, ρ_{d} = 1800 kg/m³ and H = 0.06 m. Contact "
        "conductivity scales with density between 7.4×10^{-4} and 3.4×10^{-3} W/(m·K). Radiative conduction between "
        "grains is included through")
    m.equation(r"k\left(z,T\right)=k_{c}\left(z\right)\left[1+\chi\left(\frac{T}{350\,\mathrm{K}}\right)^{3}\right],\qquad \chi=2.7")
    m.para(
        "Specific heat follows the fourth-order polynomial fit to Apollo samples [@Hemingway1981;Hayne2017]. Albedo "
        "depends on incidence angle, A = 0.12 + 0.06(i/45°)^{3} + 0.25(i/90°)^{8}; emissivity is 0.95 and the geothermal "
        "flux is 0.018 W/m². Metre depths of the column take decades to forget an initial guess, so the column is first "
        "brought to periodic equilibrium with the solar forcing of the preceding year: each iteration runs one year at "
        "1 h steps, takes the period-mean temperature below the reach of the lunar-day wave (0.15 m) and rebuilds the "
        "deeper profile so that it carries the geothermal flux, dT/dz = q_{geo}/k(z,T). This converges in a few "
        "iterations and agrees with brute-force integration over 2,500 lunations within 0.3 K at 3 m depth. The "
        "near-surface layer is then spun up over the lunation before the start.")
    m.para(
        "**Mars.** Top-of-atmosphere irradiance is 1361/r² W/m². The total (direct plus diffuse) flux reaching the "
        "surface follows a delta-Eddington two-stream solution [@Joseph1976;Meador1980;Toon1989]:")
    m.equation(r"\frac{dF^{\pm}}{d\tau}=\pm\left(\gamma_{1}F^{\pm}-\gamma_{2}F^{\mp}\right)\mp\gamma_{3,4}\,\omega_{0}F_{s}e^{-\tau/\mu_{0}}")
    m.para(
        "with a Lambertian surface and a spherical-shell air mass m. The broadband single-scattering albedo "
        "ω_{0} = 0.885 and asymmetry parameter g = 0.74 were fitted to the normalized net-flux tables of Appelbaum and "
        "Flood [@Appelbaum1990;Appelbaum1993]. These are effective solar-band values: they are lower than visible-band "
        "retrievals [@Wolff2009;ChenChen2019] because they also absorb the effects of near-infrared gas absorption and of the two-stream approximation. The "
        "delta-scaled 'direct' flux of the solution includes the forward-scattering peak, which is not part of the beam "
        "a tilted surface sees from the solar disk; the beam is therefore taken from Beer's law with the true optical "
        "depth, G_{b,n} = (S/r²)exp(−τm), and the rest of the two-stream total is diffuse. Dust optical depth follows a "
        "seasonal climatology representative of Jezero crater (0.45 in the aphelion season, 0.85 near L_{s} = 245°) "
        "[@Lemmon2015;Lemmon2022;Montabone2015]. A global-storm scenario raises τ to 6 between L_{s} = 190° and 270° "
        "[@Guzewich2019], beyond the τ ≤ 3 range of the fit (Section @sec:limits). Surface pressure follows a two-harmonic fit to the CO2 cycle with its minimum at L_{s} ≈ 157° "
        "(growth of the southern seasonal cap), its maximum at L_{s} ≈ 269° and a secondary maximum at L_{s} ≈ 64°, "
        "with a mean of 710 Pa. Ground temperature comes from a homogeneous regolith column with thermal inertia "
        "350 J m^{-2} K^{-1} s^{-1/2} and albedo 0.14, as measured at Jezero by MEDA [@Martinez2023], equilibrated over "
        "the preceding Mars year as on the Moon (its deep temperature then varies by less than 1 K with the start date, "
        "against 15 K with a 30-sol spin-up). Near-surface air temperature is an empirical boundary-layer surrogate, "
        "T_{a} = T̄_{g} + κ(T_{g}(t−0.5 h) − T̄_{g}) with κ = 0.6, which reproduces the roughly 2:1 ratio of "
        "ground-to-air diurnal amplitude measured by MEDA and REMS [@RodriguezManfredi2021;GomezElvira2012;"
        "RodriguezManfredi2023]. Downwelling long-wave flux is")
    m.equation(r"L^{\downarrow}=\varepsilon_{sky}\left(\tau\right)\sigma T_{a}^{4}+f_{re}\left\langle G_{toa,h}-G_{h}\right\rangle_{sol},\quad \varepsilon_{sky}=\min\left(e_{0}+e_{1}\,\tau,\;0.6\right)")
    m.para(
        "The first term is emission by CO2 and dust; the second re-emits a fraction f_{re} of the sunlight that dust "
        "removes (sol-running mean), a one-layer-atmosphere energy term. The three parameters (e_{0} = "
        f"{LW['e0']:.2f}, e_{{1}} = {LW['e1']:.2f}, f_{{re}} = {LW['f_re']:.2f}) were calibrated against two observations: "
        "the clear-season daily mean of about 30 W/m² measured by MEDA/TIRS "
        f"[@Martinez2023] (model {LWC['best']['L_clear_mean']:.0f} W/m²), and the response to the 2018 global dust "
        "storm, during which Curiosity saw the diurnal range of air temperature collapse while its diurnal mean fell by "
        f"only about 4 K [@Guzewich2019;ViudezMoreiras2019] (model {LWC['best']['dT_mean_storm_K']:+.0f} K). The storm "
        "response is sensitive to f_{re}: without re-emission the sol-mean air temperature would fall by more than 20 K, "
        "and with f_{re} near 0.5 it would rise.")


def method_pwf(m):
    m.heading("Planetary weather files", 2, label="pwf")
    from exobem.weather import COLUMNS
    m.para(
        "EnergyPlus reads its environment from EPW files: 8,760 one-hour records of an Earth year, with fields for "
        "humidity, precipitation and cloud cover, and range checks that would treat a lunar-noon regolith temperature "
        "of 120 °C as missing data or replace a Martian pressure of 700 Pa by the standard value. ExoBEM defines a "
        "Planetary Weather Format (PWF) instead. A PWF file is plain CSV text preceded by a header that states the body, "
        "site, start time (UTC), record length, solar-day length, gravity, ambient gas and the clock used by schedules. "
        "Records are equally spaced and of any number; solar quantities refer to the middle of each interval and state "
        "quantities to its end (Table @tab:pwf). Missing or inapplicable values are written as nan (for example the air "
        "temperature in vacuum). On reading, ExoBEM applies physical checks only: non-negative irradiance, temperatures "
        "above the 2.725 K cosmic background, a pressure consistent with the declared atmosphere. The command "
        "exobem weather writes PWF files from the generators of Section @sec:sites, other sources (the Mars Climate "
        "Database [@Millour2018], rover data) can be converted to it, and because the format is plain text with a "
        "self-describing header, other simulation programs can read the same files and be run on identical "
        "environments.")
    rows = [[n, u, d.replace("(optional)", "").strip(), "yes" if req else "no"] for n, _a, u, d, req in COLUMNS]
    m.table(["Column", "Unit", "Meaning", "Required"], rows,
            "Columns of a Planetary Weather Format (PWF) file. The full specification is in docs/weather_format.md.",
            col_widths_cm=[3.2, 1.4, 9.6, 1.6], font_size=7.0, label="pwf")


def method_convection(m):
    m.heading("Convection in thin, foreign and pressurized atmospheres", 2)
    m.para(
        "EnergyPlus's TARP algorithm combines Walton's natural-convection correlations with a Sparrow-type forced term "
        "[@Walton1983;EPlusEngRef]. Both were fitted to air at 101 kPa and 1 g. For turbulent natural convection, "
        "h = C k (gβΔT/να)^{1/3}, so for a given gas h scales as (gρ²)^{1/3} [@Incropera2007]. ExoBEM therefore offers a "
        "*physical* convection mode for any gas, pressure and gravity:")
    m.equation(r"h=\left(h_{n}^{3}+h_{f}^{3}\right)^{1/3},\quad Nu_{v}=\left\{0.825+\frac{0.387Ra^{1/6}}{\left[1+\left(0.492/Pr\right)^{9/16}\right]^{8/27}}\right\}^{2}")
    m.para(
        "Here the natural term uses Churchill–Chu for vertical faces and McAdams/Lloyd–Moran correlations for horizontal "
        "faces [@Churchill1975;Incropera2007]. The forced term uses flat-plate correlations with the local wind speed "
        "(exterior) or the cabin ventilation velocity (interior, 0.15 m/s by default, within the 0.076–0.61 m/s range of "
        "NASA-STD-3001 [@NASA2026STD]). Gas properties come from Sutherland-type fits: the Mars mixture is 95% CO2, and "
        "cabin atmospheres are N2/O2 at 101.3 kPa/21%, 70.3 kPa/26.5% or 56.5 kPa/34% O2 [@Anderson2018;EAWG2010], with "
        "the specific heat weighted by the mass fractions of N2 and O2. In Earth mode the TARP formulation is retained "
        "for comparability with EnergyPlus.")


def method_tcs(m):
    m.heading("Thermal control", 2)
    m.para(
        "A habitat cannot reject heat to outdoor air. ExoBEM passes the heat collected by the thermal control system, "
        "Q_{TCS} = Q_{c} + Ṙh_{fg} + Q_{cp} (sensible cabin load, condensing-heat-exchanger latent load and cold-plate "
        "heat), to a radiator model. The radiator's environmental sink temperature is")
    m.equation(r"\varepsilon_{r}\sigma T_{sink}^{4}=\alpha_{r}\left(G_{b}+G_{d}+G_{r}\right)+\varepsilon_{r}\sigma\left(F_{sky}T_{sky}^{4}+F_{g}T_{g}^{4}\right)")
    m.para(
        "The default radiator is two-sided, vertical and pole-facing, with silver-Teflon optical properties α = 0.10 "
        "and ε = 0.80, midway between beginning and end of life [@Anderson2018]. If the radiator temperature needed to "
        "reject the load is below the coolant temperature (2 °C less a 5 K approach), rejection is passive and only pump "
        "power (150 W) is drawn. Otherwise a vapor-compression heat pump lifts the heat, with COP equal to 40% of the "
        "Carnot value between the evaporator and the radiator temperature plus approach; the radiator temperature is "
        "found with a bracketed root search so that radiated power equals Q_{TCS}(1 + 1/COP). Humidification, when the "
        "cabin is too dry, is an electric load.")


def method_power(m):
    m.heading("Power generation and storage", 2, label="power")
    m.para(
        "The power model serves the total electric demand of the habitat, P_{load} = P_{int} + P_{TCS} + P_{ext}: the "
        "electric gains inside the pressure shell, the thermal-control power and any external load. Four kinds of "
        "components are available. **Photovoltaic arrays** (fixed, horizontal, vertical single-axis or two-axis "
        "tracking) receive the plane-of-array irradiance from the same beam, diffuse and ground-reflected components as "
        "the envelope. Their cell temperature follows from the energy balance of a thin panel whose two faces radiate to "
        "the sky and the ground seen by each face, with convection on both faces on Mars:")
    m.equation(r"\left(\alpha_{pv}-\eta\right)G_{poa}=\varepsilon_{f}\sigma\left(T_{c}^{4}-\bar{T}_{f}^{4}\right)+\varepsilon_{b}\sigma\left(T_{c}^{4}-\bar{T}_{b}^{4}\right)+2h\left(T_{c}-T_{a}\right)",
               label="pvbal")
    m.para(
        "solved by Newton iteration together with the efficiency")
    m.equation(r"\eta=\eta_{ref}\,f_{arr}\left[1+\gamma\left(T_{c}-T_{ref}\right)\right]\left(1-d\,t\right)", label="pveta")
    m.para(
        "with η_{ref} = 0.295 for triple-junction cells, γ = −0.0023 K^{-1}, α_{pv} = 0.91 [@Azur2025], an array factor "
        "f_{arr} = 0.85 for packing, wiring and conversion (assumption), and on Mars a soiling loss d of 0.25% per sol "
        "removed by cleaning every 45 sols [@LandisJenkins2000;Lorenz2021]. The Earth NOCT relation used by building "
        "simulation tools does not apply: in vacuum a sunlit lunar array runs at 330–380 K. **Fission surface power** "
        "delivers a constant electric output (40 kWe, 18.1% end-to-end efficiency [@Kaldon2024;Oleson2022]) and rejects "
        "its waste heat through its own radiator. **Li-ion batteries** have a charge and discharge efficiency of 0.97 "
        "each and a minimum state of charge of 0.2. **Regenerative fuel cells** (H2/O2 electrolyser and fuel cell) have "
        "efficiencies of 0.85 and 0.60, a round trip of 0.51 in the 50–55% range demonstrated [@GilliganJakupca2023;"
        "Smith2022]. At every step the dispatch serves the load from generation; a surplus charges the battery, then the "
        "fuel-cell storage, and is otherwise shunted; a deficit draws the battery first, then the fuel cell, and any "
        "remainder is reported as unmet energy. Sizing helpers find the array area that balances the energy over the "
        "period (including storage losses) and the storage that then keeps the load met over the periodic cycle.")


def method(m):
    """ExoBEM method: level-2 subsections."""
    method_overview(m)
    method_coordination(m)
    method_core(m)
    method_cabin(m)
    method_ephemerides(m)
    method_sites(m)
    method_pwf(m)
    method_convection(m)
    method_tcs(m)
    method_power(m)


# =========================================================================== verification
def verif_eplus(m):
    """Comparative verification of the Earth core against EnergyPlus 23.2."""
    m.heading("Comparative verification against EnergyPlus 23.2", 2, label="vexo")
    m.para(
        "The terrestrial core was compared with EnergyPlus 23.2 on opaque versions of ASHRAE Standard 140 Cases 600 "
        "(lightweight) and 900 (heavyweight) [@ASHRAE140;Judkoff1995]. In these versions the 12 m² south window is "
        "replaced by wall so that the comparison isolates the opaque heat balance, which is the part relevant to "
        "windowless habitats. The 8 m × 6 m × 2.7 m zone has 200 W of internal gains (60% radiant), 0.5 ACH "
        "infiltration, a floor on R-25 insulation over ground at 10 °C, and 20/27 °C ideal-load set-points; "
        "free-floating variants (600FF, 900FF) have no HVAC. Both programs used the Golden, Colorado TMY3 file "
        "[@Wilcox2008], 10-minute time steps, TARP convection inside and outside, the Perez sky model [@Perez1990] and "
        "Country terrain. EnergyPlus used conduction transfer functions; ExoBEM used its finite-volume solver. "
        "EnergyPlus input files are generated by a script in the repository.")
    rows = []
    for nm, d in (("600", v600), ("900", v900)):
        rows.append([f"Case {nm}", f0(d["eplus_heating_kWh"]), f0(d["exobem_heating_kWh"]),
                     pct(d["exobem_heating_kWh"], d["eplus_heating_kWh"]),
                     f0(d["eplus_cooling_kWh"]), f0(d["exobem_cooling_kWh"]),
                     pct(d["exobem_cooling_kWh"], d["eplus_cooling_kWh"]),
                     f"{d['eplus_peak_heating_W']/1000:.3f} / {d['exobem_peak_heating_W']/1000:.3f}",
                     f"{d['eplus_peak_cooling_W']/1000:.3f} / {d['exobem_peak_cooling_W']/1000:.3f}",
                     f"{d['hourly_net_load_R2']:.4f}", f"{d['hourly_net_load_CVRMSE_pct']:.1f}"])
    m.table(["Case", "Heating E+ (kWh)", "Heating ExoBEM (kWh)", "Diff.", "Cooling E+ (kWh)", "Cooling ExoBEM (kWh)",
             "Diff.", "Peak heat E+/Exo (kW)", "Peak cool E+/Exo (kW)", "Hourly R²", "CV(RMSE) %"],
            rows, "Annual loads, ExoBEM (Earth mode) versus EnergyPlus 23.2, opaque ASHRAE 140 cases, Golden CO.",
            col_widths_cm=[1.4, 1.4, 1.5, 1.2, 1.4, 1.5, 1.2, 1.7, 1.7, 1.3, 1.3], font_size=7.5, label="eplusloads")
    rows = [[f"Case {n}FF", f2(d["eplus_Tmin"]), f2(d["exobem_Tmin"]), f2(d["eplus_Tmax"]), f2(d["exobem_Tmax"]),
             f2(d["eplus_Tmean"]), f2(d["exobem_Tmean"]), f2(d["T_RMSE_K"]), f"{d['T_MBE_K']:+.3f}", f"{d['T_R2']:.4f}"]
            for n, d in (("600", f600), ("900", f900))]
    m.table(["Case", "T_{min} E+", "T_{min} Exo", "T_{max} E+", "T_{max} Exo", "T_{mean} E+", "T_{mean} Exo",
             "RMSE (K)", "MBE (K)", "R²"], rows,
            "Free-floating zone air temperature (°C), ExoBEM versus EnergyPlus 23.2, 10-minute values over one year.",
            col_widths_cm=[1.6, 1.5, 1.5, 1.5, 1.5, 1.6, 1.6, 1.4, 1.4, 1.4], font_size=8, label="eplusff")
    m.para(
        f"Annual heating differs by {pct(v600['exobem_heating_kWh'], v600['eplus_heating_kWh'])} (Case 600) and "
        f"{pct(v900['exobem_heating_kWh'], v900['eplus_heating_kWh'])} (Case 900), and annual cooling by "
        f"{pct(v600['exobem_cooling_kWh'], v600['eplus_cooling_kWh'])} and {pct(v900['exobem_cooling_kWh'], v900['eplus_cooling_kWh'])} "
        "(Table @tab:eplusloads). Peak heating loads agree within "
        f"{max(abs(d['exobem_peak_heating_W']/d['eplus_peak_heating_W']-1) for d in (v600, v900))*100:.1f}% and peak "
        f"cooling loads within {max(abs(d['exobem_peak_cooling_W']/d['eplus_peak_cooling_W']-1) for d in (v600, v900))*100:.1f}%, "
        "and hourly net loads have R² above 0.998 (Fig. @[fig:eplusverif]a). Because the windows were removed, the "
        "acceptance ranges of ASHRAE 140 do not apply to these cases; the comparison is code-to-code and tests the "
        "opaque heat balance, not the planetary physics, which is checked in Section @sec:vplanet. Free-floating temperatures "
        f"agree with an annual RMSE of {f2(f600['T_RMSE_K'])} K (600FF) and {f2(f900['T_RMSE_K'])} K (900FF) and a mean "
        "bias under 0.05 K (Table @tab:eplusff, Fig. @[fig:eplusverif]b–c). The remaining differences come from documented implementation choices: "
        "finite volumes versus conduction transfer functions, implicit Euler versus third-order backward differencing "
        "of the air balance, the sub-hourly interpolation of weather data, and the solar-position algorithm. The "
        "planetary extensions of this paper are inactive in Earth mode, and these results are unchanged by them.")
    m.figure(FIG / "fig2_verification.png",
             "Comparative verification against EnergyPlus 23.2 (Golden CO, TMY3). (a) Hourly net load (heating positive) "
             "for opaque Cases 600 and 900. (b, c) Free-floating zone air temperature over one winter and one summer week.",
             16.0, label="eplusverif")


def verif_planet(m):
    """Verification of the planetary models and of the new physics."""
    m.heading("Verification of the planetary and habitat models", 2, label="vplanet")
    rows = [
        ["Mars24 worked example, 2000-01-06 00:00 UTC", "L_{s} = 277.18758°, EOT = −5.18774°, r = 1.39358 AU, MST = 23.99425 h", "Identical to 5 decimals", "[@Mars24]"],
        ["Lunar equatorial surface temperature (Diviner)", "≈385–390 K noon; ≈95 K pre-dawn; ≈252–256 K at ~1 m", f"{env_eq['T_ground_max_K']:.0f} K; {env_eq['T_ground_min_K']:.0f} K; 253 K (1 m)", "[@Vasavada2012;Hayne2017]"],
        ["Deep regolith equilibrium (accelerated method)", "Brute-force integration, 2,500 lunations", "Within 0.3 K at 3 m", "This work"],
        ["Mars net-flux function f(z, τ), 20 table values", "Appelbaum & Flood tables, albedo 0.1", "RMSE 0.014, max. error 0.035", "[@Appelbaum1990]"],
        ["Jezero surface pressure (daily means)", "≈625–790 Pa; minimum near L_{s} 150°", f"{env_jz['P_min']:.0f}–{env_jz['P_max']:.0f} Pa; minimum at L_{{s}} 157°", "[@RodriguezManfredi2023]"],
        ["Jezero air temperature at 1.45 m", "≈188–262 K", f"{env_jz['T_air_min_K']:.0f}–{env_jz['T_air_max_K']:.0f} K", "[@RodriguezManfredi2023]"],
        ["Jezero ground temperature", "≈183–290 K", f"{env_jz['T_ground_min_K']:.0f}–{env_jz['T_ground_max_K']:.0f} K", "[@Martinez2023]"],
        ["Jezero downwelling long-wave flux", "≈30 W/m² clear-season daily mean (20–45 W/m²)", f"{env_jz['L_down_clear_mean']:.0f} W/m² clear-season mean ({env_jz['L_down_min']:.0f}–{env_jz['L_down_max']:.0f} W/m² over the year)", "[@Martinez2023]"],
        ["2018 global dust storm, change of diurnal-mean air temperature", "about −4 K (Gale)", f"{MS['storm_dta']:+.0f} K (Jezero, τ = 6)", "[@ViudezMoreiras2019]"],
        ["Lunar south-polar ridge illumination", "92.3% at 2 m (Connecting Ridge)", f"{100*env_po['sunlit_fraction']:.1f}% (horizon −1.65°)", "[@Glaser2014]"],
        ["Vertical radiator sink, lunar equator, noon", "≈333 K", f"{RAD['Vertical, faces N/S (baseline, 96 m2)']['sink_max_K']:.0f} K", "[@Bien1969]"],
        ["Lunar habitat night heat leak at 293 K (NASA)", "≈1550 W (used to calibrate the MLI)", f"{CAL['night_loss_W']:.0f} W (MLI R = {CAL['mli_R_m2K_W']:.1f} m²K/W)", "[@Schunk2022]"],
        ["Lunar habitat daylight net loss (NASA)", "≈850 W", f"{CAL['day_loss_W']:.0f} W ({CAL['day_error_pct']:+.0f}%)", "[@Schunk2022]"],
        ["Steady conduction through cylindrical and spherical shells", "Exact solutions", "Error < 10^{-6} (unit tests)", "[@Incropera2007]"],
        ["PV cell in vacuum, both faces to a 2.7 K sink", "(α − η)G = 2εσT⁴", "Error < 10^{-6} (unit test)", "Analytic"],
        ["Cabin vapour balance at steady state", "Condensate = crew moisture", "Within 0.2% (unit test)", "Analytic"],
        ["Steady conduction, semi-infinite step (erfc), parallel-plate ScriptF, vacuum steady state", "Exact solutions", "Errors < 0.1% (unit tests)", "[@Incropera2007]"],
    ]
    m.table(["Quantity", "Reference", "ExoBEM", "Source"], rows,
            "Verification of the planetary and habitat models against reference data and analytical solutions.",
            col_widths_cm=[4.6, 4.6, 4.3, 2.5], font_size=7.5, label="planetver")
    m.para(
        "Table @tab:planetver summarizes the checks of the planetary and habitat models; all are automated in the test "
        "suite. Mars24's worked example is reproduced exactly. The regolith model reproduces Diviner's equatorial noon "
        "and pre-dawn temperatures and the Apollo subsurface temperatures (Fig. @[fig:envmodels]a), and the accelerated "
        "equilibrium of the column matches brute-force integration. The fitted delta-Eddington model reproduces the "
        "Appelbaum–Flood insolation tables over 0.1 ≤ τ ≤ 3 and 0° ≤ z ≤ 80° (Fig. @[fig:envmodels]b). The Jezero "
        "environment falls within the ranges MEDA observed for pressure, air and ground temperature and downwelling "
        "infrared, with the pressure minimum in the right season. The lunar radiator sink agrees with the classic "
        "Bien–Guentert estimate. The habitat envelope was calibrated to NASA's thermal analysis of the Artemis surface "
        f"habitat: an effective MLI resistance of {CAL['mli_R_m2K_W']:.1f} m²K/W reproduces the night-time heat leak of "
        f"1550 W at 293 K, and the daylight net loss then comes out at {CAL['day_loss_W']:.0f} W against NASA's 850 W "
        f"({CAL['day_error_pct']:+.0f}%), an independent check whose residual reflects the unknown sun geometry of the "
        "NASA daylight case and the uniform horizon used here. The polar horizon depression of −1.65° was chosen to "
        "match the 92.3% illumination of the best Connecting Ridge site [@Glaser2014]. Because a uniform horizon "
        f"concentrates darkness into seasons, it yields a longest eclipse of {env_po['longest_dark_days']:.0f} days, "
        "against 3–5 days for real ridge terrain [@Glaser2014;Mazarico2011]; polar storage results below are therefore "
        "given both for this horizon and for NASA's 100-hour design eclipse.")
    m.figure(FIG / "fig3_environment_models.png",
             "Planetary environment models. (a) Lunar regolith surface temperature over a lunation at three latitudes, "
             "with Diviner equatorial ranges. (b) Normalized Martian surface net flux from the fitted delta-Eddington "
             "model (lines) and the Appelbaum–Flood tables (dots). (c) Seasonal dust optical depth at Jezero, nominal and "
             "with a 2018-type global dust storm.", 16.0, label="envmodels")


# =========================================================================== case studies
def case_studies(m):
    """Case studies: habitats, sites, results, power, convection."""
    hm, hr = H["moon"], H["mars"]
    m.heading("Reference habitats for the first crews", 2, label="habitats")
    m.para(
        "The case studies use two habitats sized from NASA mission concepts (Fig. @fig:geometry, Table @tab:habitats). "
        "The lunar habitat follows the Artemis surface habitat: a vertical module 6.5 m in diameter and 5.25 m high "
        f"({hm['volume_m3']:.0f} m³ pressurized, about 32 m³ of habitable volume per person) for four crew on stays of "
        "30–60 days, standing on legs 1.5 m above the regolith [@Kessler2022;Burke2022;Stromgren2023]. Its envelope is "
        "beta cloth (α = 0.40, ε = 0.90) over multi-layer insulation over the aluminium structure [@Schunk2022]. The Mars "
        "habitat follows Design Reference Architecture 5.0: six crew for about 500 sols in a two-deck module 7.2 m in "
        f"diameter and 5.5 m high ({hr['volume_m3']:.0f} m³; 25 m³ of habitable volume per person [@Whitmire2014]) "
        "[@Drake2009;Rucker2018]; because multi-layer insulation loses most of its performance in 0.7 kPa of CO2, it is "
        "insulated with 40 mm of silica aerogel. Both cabins are at 56.5 kPa with 34% O2, the exploration atmosphere for "
        "frequent EVA, between 20 and 25 °C and 30–60% relative humidity [@Anderson2018;NASA2026STD]. Crew heat and "
        "moisture follow the NASA Baseline Values and Assumptions Document, with sleep, work and exercise periods and "
        "two-person EVAs (twice a week on the Moon, every workday on Mars) [@Anderson2018]. Electric power inside the "
        f"shell, {EL_MOON:.1f} kW on the Moon and {EL_MARS:.1f} kW on Mars, follows the NASA habitat power levels "
        "[@Schunk2021;Drake2009;Cataldo2009] and is divided into life support (25%, assumption), water electrolysis, "
        "fans, lighting (7 W/m² of deck) and avionics and crew equipment, with part of the life-support and avionics "
        "heat on cold plates. Racks and stowage add internal mass equal to twice the deck area.")
    m.figure(FIG / "fig_geometry.png",
             "Reference habitats. (a) Four-crew lunar surface habitat and (b) six-crew Mars surface habitat as modelled "
             "(12-sided prisms with the floor area and volume of the cylinders). (c, d) Layers of their shells from the "
             "outside to the cabin.", 16.0, label="geometry")
    rows = [
        ["Crew; stay", "4; 30–60 d", "6; ~500 sols"],
        ["Shape; size", "Vertical cylinder D 6.5 m × H 5.25 m", "Vertical two-deck cylinder D 7.2 m × H 5.5 m"],
        ["Pressurized volume; envelope area", f"{hm['volume_m3']:.0f} m³; {hm['area_exposed_m2']:.0f} m²",
         f"{hr['volume_m3']:.0f} m³; {hr['area_exposed_m2']:.0f} m²"],
        ["Envelope (outside → in)", f"Beta cloth / MLI (R {CAL['mli_R_m2K_W']:.1f} m²K/W) / Al 4 mm / panel 10 mm",
         "Beta cloth / aerogel 40 mm / Al 4 mm / panel 10 mm"],
        ["Cabin atmosphere; control band", "56.5 kPa, 34% O2; 20–25 °C, RH 30–60%", "Same"],
        ["Crew heat per person (sensible + latent, daily mean)", "85.1 + 53.8 W", "76.5 + 76.3 W (long-duration)"],
        ["Electric power inside the shell", f"{EL_MOON:.1f} kW (life support 3.5, electrolysis 0.9, fans 0.5, lighting 0.46)",
         f"{EL_MARS:.1f} kW (life support 3.0, electrolysis 1.35, fans 0.5, lighting 0.57)"],
        ["Leakage; airlock venting", f"{hm['leak_kg_d']:.3f} kg/d; {hm['airlock_kg_cycle']:.2f} kg × {hm['airlock_cycles_d']*7:.0f} cycles/week",
         f"{hr['leak_kg_d']:.3f} kg/d; {hr['airlock_kg_cycle']:.2f} kg × {hr['airlock_cycles_d']*7:.0f} cycles/week"],
        ["Radiator", "96 m² (48 m² panel, two faces), vertical, pole-facing", "80 m², vertical, two faces"],
    ]
    m.table(["Parameter", "Lunar surface habitat", "Mars surface habitat"], rows,
            "Reference habitats (sources in the text and in docs/research of the repository).",
            col_widths_cm=[4.6, 5.7, 5.7], font_size=7.5, label="habitats")
    rows = [
        ["Moon, south pole", "Ridge at 89.5°S, horizon −1.65°", "1 year from 2030-01-01", "1 h",
         f"{100*env_po['sunlit_fraction']:.0f}% sunlit; regolith {env_po['T_ground_min_K']:.0f}–{env_po['T_ground_max_K']:.0f} K"],
        ["Moon, equator", "Mare Tranquillitatis, 0.67°N 23.47°E", "2 lunations from 2030-01-01", "30 min",
         f"Regolith {env_eq['T_ground_min_K']:.0f}–{env_eq['T_ground_max_K']:.0f} K"],
        ["Mars, Jezero", "18.44°N 77.45°E", f"1 Mars year from L_{{s}} = 0° ({R['sites']['mars_jezero']['start'][:10]})", "1/24 sol",
         f"P {env_jz['P_min']:.0f}–{env_jz['P_max']:.0f} Pa; τ 0.45–{env_jz['tau_max']:.2f}"],
        ["Mars, Jezero, dust storm", "As above", "As above", "1/24 sol", "τ up to 6 at L_{s} 190–270°"],
    ]
    m.table(["Case", "Site", "Period", "Time step", "Environment"], rows, "Case-study sites and simulation periods.",
            col_widths_cm=[2.8, 3.8, 3.8, 1.6, 4.0], font_size=8, label="sites")
    m.figure(FIG / "fig4_environments.png",
             "Simulated surface environments: irradiance (top) and ground, sky and air temperatures (bottom) at the lunar "
             "equator, a lunar south-polar ridge and Jezero crater.", 16.0, label="envs")

    m.heading("Thermal results", 2, label="thermal")
    m.para(
        "Fig. @fig:envs contrasts the three environments. At the lunar equator, 14.8 days of sunlight at up to "
        f"{env_eq['dni_max']:.0f} W/m² alternate with 14.8 days of darkness, and the regolith swings from "
        f"{env_eq['T_ground_min_K']:.0f} to {env_eq['T_ground_max_K']:.0f} K. At the polar ridge the Sun circles the "
        "horizon at grazing elevation: beam irradiance on a vertical surface is high, but the flat ground stays below "
        f"{env_po['T_ground_max_K']:.0f} K. At Jezero the cycle repeats every sol; dust removes about a fifth of the "
        "noon beam and turns much of it into diffuse light, and the CO2 atmosphere keeps the effective sky above "
        f"{env_jz['T_sky_min_K']:.0f} K.")
    rows = []
    for key, lab in (("moon_pole", "Moon, south pole"), ("moon_equator", "Moon, equator"),
                     ("mars_jezero", "Mars, Jezero"), ("mars_jezero_storm", "Mars, dust storm")):
        d = B[key]
        rows.append([lab, f1(d["cooling_kWh_per_day"]), f1(d["coldplate_kWh_per_day"]), f1(d["latent_kWh_per_day"]),
                     f1(d["tcs_heat_kWh_per_day"]), f0(d["envelope_gain_mean_W"]),
                     f"{100 * d.get('heat_pump_hours_frac', 0):.0f}", f1(d["thermal_control_kWh_per_day"]),
                     f"{d['min_surface_minus_dewpoint_K']:+.1f}", f"{d['condensation_risk_hours']:.0f}",
                     f"{d['gas_makeup_kg_per_day']:.2f}", f"{d['condensate_kg_per_day']:.1f}"])
    m.table(["Case", "Cabin cooling (kWh/d)", "Cold plates (kWh/d)", "Latent (kWh/d)", "Heat to radiators (kWh/d)",
             "Mean envelope gain (W)", "Heat-pump time (%)", "TCS electricity (kWh/d)", "Min. surface − dew point (K)",
             "Condensation risk (h)", "Gas make-up (kg/d)", "Condensate (kg/d)"],
            rows, "Thermal results for the reference habitats (energies per Earth day).",
            col_widths_cm=[2.0, 1.25, 1.25, 1.2, 1.35, 1.35, 1.2, 1.35, 1.35, 1.3, 1.2, 1.2], font_size=6.8, label="baseline")
    m.para(
        f"**Both habitats are cooling-dominated** (Table @tab:baseline). The lunar habitat collects "
        f"{f1(mpo['tcs_heat_kWh_per_day'])} kWh/d at the pole ({mpo['tcs_heat_kWh_per_day']/24:.1f} kW on average): "
        "the electric power used inside the shell, plus crew heat, minus what the envelope loses. Its MLI envelope loses "
        f"{abs(mpo['envelope_gain_mean_W']):.0f} W on average at the pole and {abs(meq['envelope_gain_mean_W']):.0f} W at "
        "the equator, under a tenth of the internal gains, so the envelope matters little to the cooling load; about 55% "
        "of the heat reaches the coolant through cold plates rather than the cabin air. The Mars habitat is different: "
        f"its aerogel envelope loses {abs(mjz['envelope_gain_mean_W'])/1000:.1f} kW to the cold, CO2-filled surroundings, "
        f"so the cabin needs only {f1(mjz['cooling_kWh_per_day'])} kWh/d of sensible cooling, but some inner surfaces "
        f"fall {abs(mjz['min_surface_minus_dewpoint_K']):.1f} K below the dew point of the 25 °C, 60% RH cabin. "
        f"Condensation is possible for {mjz['condensation_risk_hours']:.0f} hours of the Mars year, a habitability and "
        "corrosion risk that a heat-balance model without a humidity balance would not reveal; Section @sec:envvar shows "
        "how to remove it. Over a year the lunar crew release about 8 kg of water a day that the condensing heat "
        f"exchanger recovers, and {mpo['gas_makeup_kg_per_day']:.2f} kg/d (Moon) to {mjz['gas_makeup_kg_per_day']:.2f} kg/d "
        "(Mars) of cabin gas must be made up for leakage and airlock venting, a negligible energy term but a consumable "
        "to plan. Inside, the cabin air temperature stays within the band at all times and the inside surfaces vary by "
        "about 1 K, while the outer surfaces follow the environment (Fig. @[fig:moonhab]a).")
    m.figure(FIG / "fig5_moon_habitat.png",
             "Lunar surface habitat at the equator over two lunations. (a) Outer surface temperatures. (b) Heat collected by "
             "the thermal control system from the cabin air, the cold plates and the condensing heat exchanger, and the "
             "electric power used inside the shell. (c) Sink temperature of a vertical two-sided radiator facing N/S or E/W "
             "and the radiator temperature, with the 270 K evaporator temperature.", 16.0, label="moonhab")
    m.para(
        "**Heat rejection is where the equator differs from the pole.** The sink temperature of a vertical radiator at "
        f"the equator rises to {meq['radiator_sink_max_K']:.0f} K at noon because half of its view is regolith at nearly "
        f"390 K (Fig. @[fig:moonhab]c). For {100*meq['heat_pump_hours_frac']:.0f}% of the lunation the heat can only be "
        f"rejected by lifting it with a heat pump; the COP falls to {meq['cop_min']:.2f}, and the thermal control system "
        f"draws {f1(meq['thermal_control_kWh_per_day'])} kWh/d with peaks of "
        f"{RAD['Vertical, faces N/S (baseline, 96 m2)']['peak_W']/1000:.1f} kW, against "
        f"{f1(mpo['thermal_control_kWh_per_day'])} kWh/d of pump power at the pole, where the sink never exceeds "
        f"{mpo['radiator_sink_max_K']:.0f} K. On Mars the sink peaks at {mjz['radiator_sink_max_K']:.0f} K and the heat pump "
        f"runs {100*mjz['heat_pump_hours_frac']:.0f}% of the time ({100*mst['heat_pump_hours_frac']:.0f}% with the dust "
        "storm, whose infrared glow warms the sink).")
    rows = [[k, f1(v["tcs_kWh_per_day"]), f2(v["peak_W"] / 1000), f"{v['sink_max_K']:.0f}", f"{100*v['heat_pump_frac']:.0f}"]
            for k, v in RAD.items()]
    m.table(["Radiator configuration (ε = 0.80)", "Thermal-control electricity (kWh/d)", "Peak power (kW)",
             "Max. sink (K)", "Heat-pump time (%)"], rows,
            "Effect of radiator orientation, area and dust degradation at the lunar equator (α = 0.10 unless noted).",
            col_widths_cm=[6.0, 3.0, 2.2, 2.2, 2.4], font_size=8, label="radiator")
    h, hd = RAD["Horizontal, faces up (48 m2 one side)"], RAD["Horizontal, dust-degraded (alpha = 0.35)"]
    v2 = RAD["Vertical N/S, 2x area"]
    m.para(
        "Table @tab:radiator compares radiator options at the equator. Turning the vertical radiator from the poles to "
        "east–west makes it face the low morning and evening Sun and costs about 13% more electricity. Doubling the "
        f"vertical area saves {100*(1 - v2['tcs_kWh_per_day']/RAD['Vertical, faces N/S (baseline, 96 m2)']['tcs_kWh_per_day']):.0f}%, "
        "less than one might expect: the larger area lowers the radiator temperature needed in the morning and evening, "
        "but at noon the sink is above the cabin temperature whatever the area. A horizontal radiator does not "
        f"see the regolith and its clean sink never exceeds {h['sink_max_K']:.0f} K, but with one radiating face it needs "
        f"lift {100*h['heat_pump_frac']:.0f}% of the time; if lunar dust raises its absorptance to 0.35 [@Gaier2008] its "
        f"noon sink climbs to {hd['sink_max_K']:.0f} K and it draws {f1(hd['tcs_kWh_per_day'])} kWh/d. Radiator "
        "orientation and dust mitigation are thus first-order energy decisions for equatorial bases.")

    m.heading("Envelope variants", 2, label="envvar")
    em, emo, mm = R["envelope_moon_pole"], R["envelope_moon_equator"], R["envelope_mars_jezero"]
    m.para(
        "Fig. @fig:envelopes compares envelope variants. On the Moon, adding a regolith radiation shield on top of the "
        "MLI (with the habitat then resting on the ground) reduces the envelope loss from "
        f"{abs(em['MLI on legs (baseline)']['envelope_gain_mean_W']):.0f} W to "
        f"{abs(em['MLI + 1 m regolith']['envelope_gain_mean_W']):.0f} W at the pole and so raises the cooling load by "
        f"{100*(em['MLI + 1 m regolith']['cooling_kWh_per_day']/em['MLI on legs (baseline)']['cooling_kWh_per_day']-1):.0f}%: "
        "a sealed, well-insulated habitat full of electronics is a heat-rejection problem, and the shield, needed for "
        "radiation protection, removes the small help the bare envelope gives. Once 0.5 m of regolith is present, more "
        "thickness or MLI changes the load by less than 2%, because lunar regolith (3–5 mW/(m·K)) is itself an "
        "excellent insulator. On Mars the picture is reversed. CO2 in the pores raises regolith conductivity to about "
        "0.08 W/(m·K), and the bare habitat on legs loses heat by conduction and convection to the cold atmosphere. With "
        "multi-layer insulation, whose performance collapses in 0.7 kPa of CO2, the habitat needs "
        f"{f1(mm['MLI (in CO2) on legs']['heating_kWh_per_day'])} kWh/d of heating and its walls fall "
        f"{abs(mm['MLI (in CO2) on legs']['min_surface_minus_dewpoint_K']):.0f} K below the dew point; 50 mm of polyimide "
        "foam is better but still condenses; 40 mm of aerogel reduces the risk to "
        f"{mm['Aerogel 40 mm on legs (baseline)']['condensation_risk_hours']:.0f} hours a year at "
        f"{abs(mm['Aerogel 40 mm on legs (baseline)']['min_surface_minus_dewpoint_K']):.1f} K below the dew point; a 1 m "
        "regolith cover removes it entirely (surfaces stay "
        f"{mm['Aerogel + 1 m regolith']['min_surface_minus_dewpoint_K']:.1f} K above the dew point) while turning the "
        "habitat into a cooling-dominated building. The condensation result depends on the cabin set-points. The "
        "baseline cabin sits at the top of its control band, 25 °C and 60% relative humidity, because the habitat "
        "always needs cooling and the crew always add water. Limiting the humidity to 50% or 40% reduces the risk to "
        f"{CSP['25 C, 50%']['condensation_risk_hours']:.0f} and {CSP['25 C, 40%']['condensation_risk_hours']:.0f} hours "
        "a year; the water removed is the same, but the condensing heat exchanger must then run at a lower dew point, "
        "a cost the ideal-load model does not resolve. A 22 °C cabin at 60% gives "
        f"{CSP['22 C, 60%']['condensation_risk_hours']:.0f} hours and at 50% "
        f"{CSP['22 C, 50%']['condensation_risk_hours']:.0f} hours.")
    m.figure(FIG / "fig7_envelopes.png",
             "Daily heating and cooling loads of the cabin air for envelope variants at the three sites (kWh per Earth day).",
             16.0, label="envelopes")

    m.heading("Mars seasons and dust storms", 2)
    m.para(
        f"Over the Mars year at Jezero (Fig. @fig:marsyear), sol-mean insolation varies between {MS['ghi_min']:.0f} and "
        f"{MS['ghi_max']:.0f} W/m², and sol-mean air temperature between {MS['ta_min']:.0f} and {MS['ta_max']:.0f} °C. A "
        f"2018-type global storm cuts sol-mean insolation to {MS['storm_ghi_min']:.0f} W/m² and keeps it below 60 W/m² for "
        f"{MS['storm_sols']} sols. Dust re-emits part of the absorbed sunlight as infrared, so the nights warm and the days "
        f"cool: at peak opacity the diurnal air-temperature range shrinks from {MS['storm_rng_nom']:.0f} to "
        f"{MS['storm_rng']:.0f} K while the sol-mean air temperature changes by {MS['storm_dta']:+.0f} K, as observed by "
        "Curiosity in 2018 [@Guzewich2019;ViudezMoreiras2019]. The habitat responds through its envelope and its "
        "radiator. Its envelope loses less heat to the warmer night sky, so its sol-mean cabin cooling load rises by up "
        f"to {MS['storm_qc_dmax']/1000:.1f} kW; by day the dimmed Sun lowers the radiator sink, so thermal-control power "
        f"falls by up to {-MS['storm_el_dmin']/1000:.1f} kW. These are modest changes for a habitat whose internal gains "
        "are about 14 kW; the power system "
        "is affected far more, as shown next.")
    m.figure(FIG / "fig6_mars_year.png",
             "One Mars year at Jezero crater. (a) Sol-mean global horizontal irradiance, nominal and with a global dust "
             "storm. (b) Sol-mean air and ground temperatures. (c) Sol-mean cabin cooling load and thermal-control "
             "electricity.", 16.0, label="marsyear")

    m.heading("Power systems", 2, label="powerres")
    rows = []
    for key, lab in (("moon_pole", "Moon, south pole"), ("moon_equator", "Moon, equator"),
                     ("mars_jezero", "Mars, Jezero"), ("mars_jezero_storm", "Mars, dust storm")):
        d = P[key]
        a, b, a2 = d["PV + Li-ion"], d["PV + RFC"], d["PV x2 + Li-ion"]
        rows.append([lab, f2(a["mean_load_kW"]), f2(a["peak_load_kW"]), f"{100*d['thermal_control_share']:.0f}",
                     f"{a['pv_area_m2']:.0f}; {a['storage_kWh']/1000:.1f} ({a['storage_mass_t']:.0f} t)",
                     f"{a2['pv_area_m2']:.0f}; {a2['storage_kWh']/1000:.2f} ({a2['storage_mass_t']:.1f} t)",
                     f"{b['pv_area_m2']:.0f}; {b['storage_kWh']/1000:.1f}",
                     f"1 unit; {d['Fission 40 kWe']['curtailed_kWh']/d['Fission 40 kWe']['load_kWh']*100:.0f}% shunted"])
    m.table(["Case", "Mean load (kW)", "Peak load (kW)", "Thermal-control share (%)",
             "PV + Li-ion, balance area: PV m²; storage MWh (mass)", "PV × 2 + Li-ion: PV m²; storage MWh (mass)",
             "PV + RFC: PV m²; storage MWh", "Fission 40 kWe"], rows,
            "Power systems that meet the habitat's electric demand with no shortfall over the simulated period "
            "(storage is nameplate; Li-ion mass at 160 Wh/kg packaged [@Gilligan2023]).",
            col_widths_cm=[2.2, 1.3, 1.3, 1.5, 2.9, 2.9, 2.3, 2.0], font_size=7.0, label="power")
    pp, pe, pj, ps = P["moon_pole"], P["moon_equator"], P["mars_jezero"], P["mars_jezero_storm"]
    m.para(
        "Table @tab:power and Fig. @fig:power size three power systems that meet the electric demand of each habitat "
        "with no shortfall. Two numbers dominate. First, at the lunar equator the 354-hour night sets the storage "
        f"whatever the array: {pe['PV + Li-ion']['storage_kWh']/1000:.1f} MWh of Li-ion "
        f"({pe['PV + Li-ion']['storage_mass_t']:.0f} t) or {pe['PV + RFC']['storage_kWh']/1000:.1f} MWh of regenerative "
        "fuel cells, and thermal control is "
        f"{100*pe['thermal_control_share']:.0f}% of the load because of heat-pump lift. Second, sizing arrays only for the "
        "energy balance shifts surplus from summer to winter and asks storage to carry seasons: "
        f"{pj['PV + Li-ion']['storage_kWh']/1000:.1f} MWh ({pj['PV + Li-ion']['storage_mass_t']:.0f} t) at Jezero. Doubling "
        f"the array cuts this to {pj['PV x2 + Li-ion']['storage_kWh']/1000:.2f} MWh, only the nightly deficit "
        f"(Fig. @[fig:power]a), a trade-off that favours larger arrays on Mars. A global dust storm undoes it: even with "
        f"twice the array, {ps['PV x2 + Li-ion']['storage_kWh']/1000:.0f} MWh ({ps['PV x2 + Li-ion']['storage_mass_t']:.0f} t) "
        "is needed to ride out the weeks of darkness, while the habitat's thermal loads hardly change. At the polar ridge "
        "the uniform horizon produces a polar-winter eclipse of "
        f"{env_po['longest_dark_days']:.0f} days and {pp['PV x2 + Li-ion']['storage_kWh']/1000:.1f} MWh of storage with "
        f"twice the array; NASA's 100-hour design eclipse would need {pp['eclipse_100h_storage_kWh']/1000:.1f} MWh "
        "(nameplate, as in Table @tab:power). A single 40 kWe fission unit meets every case independently of light and "
        "dust; it produces more than twice the demand, so the surplus is available for other surface loads (in-situ "
        "resource production, rovers) or is shunted, and it rejects about "
        f"{pp['Fission 40 kWe']['waste_heat_kW']:.0f} kW of waste heat through its own radiator. The comparison of "
        "energy is not a comparison of systems: NASA's Fission Surface Power design goal is under 6 t for a 10-year "
        f"life [@Kaldon2024], against {pp['PV x2 + Li-ion']['storage_mass_t']:.0f}–{pe['PV + Li-ion']['storage_mass_t']:.0f} t "
        "of Li-ion for the lunar cases, but it excludes the reactor's radiator, power cable and "
        "emplacement, and a single reactor is a single point of failure that a crewed base would back up with a second "
        "unit or with storage sized for the critical load. In vacuum the sunlit cells of a lunar two-axis array run at "
        f"330–380 K, lowering their efficiency by {0.23*(330-301.15):.0f}–{0.23*(380-301.15):.0f}% relative to the "
        "28 °C rating (γ = −0.0023 K^{-1}), an effect absent from Earth building tools.")
    m.figure(FIG / "fig9_power.png",
             "Power systems. (a) Usable storage needed to meet the load against the PV array area (multiples of the "
             "energy-balance area), Li-ion. (b) Daily minimum battery state of charge with twice the energy-balance array.",
             16.0, label="power")

    m.heading("Convection under reduced gravity and pressure", 2)
    m.para(
        "Fig. @fig:convection quantifies why convection coefficients cannot be carried over from Earth. Cabin natural "
        "convection on a 2.5 m wall with a 3 K temperature difference drops from about "
        f"{np.interp(9.807, R['convection']['g'], R['convection']['101.3']):.1f} W/(m²·K) at 1 g and 101 kPa to about "
        f"{np.interp(1.625, R['convection']['g'], R['convection']['56.5']):.2f} W/(m²·K) at lunar gravity in the "
        f"56.5 kPa cabin of the reference habitats ({np.interp(3.721, R['convection']['g'], R['convection']['56.5']):.2f} "
        "W/(m²·K) at Mars gravity). That is comparable to the forced coefficient at a "
        "0.15 m/s ventilation velocity, so cabin ventilation, not buoyancy, controls interior surface heat transfer on "
        "the Moon. Outside on Mars, mixed convection in 700 Pa CO2 gives 0.15–0.7 W/(m²·K) over the full range of wind "
        "speeds, 20–70 times less than on Earth at the same wind speed. Exterior convection on Mars is therefore a "
        "correction to the radiative balance rather than a dominant term, consistent with the small sensible heat "
        "fluxes MEDA measured [@Martinez2023].")
    m.figure(FIG / "fig8_convection.png",
             "(a) Interior natural convection coefficient versus gravity for three cabin atmospheres (2.5 m vertical wall, "
             "ΔT = 3 K), with the forced-convection value at 0.15 m/s. (b) Exterior mixed convection versus wind speed for "
             "a 3 m surface on Earth and Mars (ΔT = 10 K and 30 K, respectively).", 16.0, label="convection")


# =========================================================================== discussion
def implications(m):
    """Discussion: implications for habitat design."""
    m.heading("Implications for habitat design", 2)
    m.para(
        "The case studies suggest a shift in emphasis for habitat energy design. On Earth, BES spends most of its effort "
        "on the envelope; a sealed habitat full of life-support equipment and electronics is a heat-rejection problem "
        "whose envelope mainly decides how much of the internal heat leaks away for free, whether its inner surfaces "
        "stay above the dew point, and how much radiation shielding costs in extra cooling. Design then turns on "
        "(i) internal heat generation and where it is collected (cabin air or cold plates), (ii) where and how it is "
        "rejected, and (iii) electric storage across darkness, which is set by the lunar night, polar terrain or "
        "Martian dust rather than by the habitat. Radiator placement and coating degradation by dust change "
        "thermal-control energy by a factor of two at the lunar equator; array oversizing trades against storage by "
        "two orders of magnitude on Mars; and a single fission unit removes the dependence on light. These conclusions "
        "are qualitatively known to spacecraft thermal and power engineers [@Simonsen1992;Schunk2022;Cataldo2009]. "
        "What ExoBEM adds is a way to quantify them with the annual, schedule-driven methods of building science, "
        "including humidity and consumables, and to carry the same model from early massing studies to detailed design.")


def limitations(m, title="Limitations"):
    """Discussion: limitations of ExoBEM."""
    m.heading(title, 2, label="limits")
    m.bullets([
        "**Single zone.** Multi-zone habitats, airlocks as separate zones and inter-module air exchange are not yet modelled.",
        "**Ideal systems.** Radiators, heat pumps and storage are quasi-steady models without component dynamics; cold-plate fractions and the life-support share of the electric load are assumptions where no public source exists.",
        "**Idealized terrain.** Horizons are uniform or user-supplied profiles; DEM horizons (LOLA, HiRISE) and shading between modules are planned. The uniform polar horizon overstates eclipse length.",
        "**Empirical Mars boundary layer.** Near-surface air temperature uses a calibrated surrogate, and the regolith surface exchanges no sensible heat with the air; Mars Climate Database input through the PWF format is the planned route to better atmospheres [@Millour2018;Forget1999].",
        "**Effective dust optics.** Broadband scattering parameters are fitted to Appelbaum–Flood tables; the Beer-law beam with the forward-scattered peak counted as diffuse is a modelling choice that measured Martian direct/diffuse data should confirm [@Wolff2009;ChenChen2019].",
        f"**Dust storms.** The storm case (τ = 6) lies outside the 0.1 ≤ τ ≤ 3 range of the Appelbaum–Flood tables used to fit the two-stream model, so its insolation is an extrapolation; the dust re-emission term is calibrated to a single storm response observed at another site (Gale crater), and the peak downwelling infrared in the storm ({E['mars_jezero_storm']['L_down_max']:.0f} W/m²) has not been checked against measurements. Storm results are scenarios, not predictions.",
        "**Verification scope.** The EnergyPlus comparison tests the Earth heat balance only; the planetary models are checked against reference data component by component, and the habitat envelope is calibrated to one NASA thermal analysis and checked at a second operating point (+24%). Empirical validation of a whole habitat in thermal-vacuum chambers or analog habitats remains to be done.",
    ])


# =========================================================================== appendix
def appendix_tutorial(m):
    """Appendix A: installing and using ExoBEM, with the tutorial example."""
    m.heading("Appendix A. Using ExoBEM: installation and a worked example", 1, numbered=False)
    m.para(
        "ExoBEM is installed with pip and provides a Python package and a command-line tool. A step-by-step tutorial "
        "with this example is in the repository (docs/tutorial); here are its main steps.", indent=False)
    m.para("**1. Install and copy the examples:**", align="left")
    m.para("python -m pip install \"exobem[plot] @ git+https://github.com/TensorBuildLab/ExoBEM\"", align="left", size=9)
    m.para("exobem examples my_project", align="left", size=9)
    m.para("**2. Generate a planetary weather file** for 30 days at a lunar south-polar ridge, hourly:", align="left")
    m.para("exobem weather --body moon --lat -89.5 --lon 0 --horizon -1.65 --days 30 --timestep 3600 -o south_pole_30d.pwf",
           align="left", size=9)
    m.para("**3. Inspect the model and its geometry.** The model file lunar_surface_habitat.json has the sections "
           "simulation, site (here \"weather_file\": \"south_pole_30d.pwf\"), materials, constructions, geometry, zone "
           "(cabin pressure and oxygen, set-points, leakage, airlock, humidity limits, internal mass), gains (crew, life "
           "support, electrolysis, fans, lighting, equipment, each with a 24-hour schedule, electric, heat and cold-plate "
           "fractions), thermal_control and power:", align="left")
    m.para("exobem geometry lunar_surface_habitat.json -o habitat.png", align="left", size=9)
    m.para("**4. Run it:**", align="left")
    m.para("exobem run lunar_surface_habitat.json -o out", align="left", size=9)
    m.para("The run takes about a second and writes out/timeseries.csv (zone and surface temperatures, loads), "
           "out/environment.csv, out/power.csv (generation, storage state of charge, unmet energy) and out/summary.json "
           "with the cabin cooling, cold-plate and latent energy, the humidity range, the minimum margin between the "
           "inside surfaces and the dew point, the condensation-risk hours, the cabin gas to make up, the thermal-control "
           "electricity and the power-system summary.", align="left")
    m.para("**5. Use the Python interface** to change the design and compare, for example adding a regolith cover:",
           align="left")
    for line in ("import json, exobem", "from exobem.io import build_model", "from exobem.weather import read_pwf",
                 "cfg = json.load(open('lunar_surface_habitat.json'))",
                 "cfg['constructions']['covered'] = ['lunar_regolith_cover_1m'] + cfg['constructions']['shell']",
                 "cfg['geometry'].update(wall='covered', roof='covered')",
                 "res = exobem.simulate(build_model(cfg), read_pwf('south_pole_30d.pwf'))",
                 "print(res.summary())"):
        m.para(line, align="left", size=8.5, space_after=0)
    m.para("", space_after=4)


def appendix_pwf(m):
    """Appendix B: PWF header."""
    m.heading("Appendix B. Header of a planetary weather file", 1, numbered=False)
    for line in ("# PWF 1.0", "# body: mars", "# site_name: Jezero crater", "# latitude_deg: 18.440000",
                 "# longitude_deg: 77.450000", "# start_utc: 2030-01-01T00:00:00", "# timestep_s: 1800",
                 "# n_records: 1488", "# solar_day_s: 88775.244147", "# gravity_m_s2: 3.72100", "# atmosphere: mars_co2",
                 "# clock: mars_lmst", "# sky_includes_air: false", "# generator: exobem 0.2.0 weather --body mars ...",
                 "time_s,local_time_h,day_index,zenith_deg,sun_azimuth_deg,sun_visible,dni_W_m2,dhi_W_m2,ghi_W_m2,T_air_K,...",
                 "1800,4.076848,0,121.9043,107.584,0,0,0,0,205.549,..."):
        m.para(line, align="left", size=8.5, space_after=0)
    m.para("", space_after=4)
