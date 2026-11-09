"""Build the ExoBEM journal manuscript (Word) from results.

    python paper/build_paper.py   ->  paper/ExoBEM_manuscript.docx
All numbers quoted in the text are read from studies/results and verification/results.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "paper"))

from docxkit import Manuscript  # noqa: E402
from refs import REFS  # noqa: E402

FIG = ROOT / "paper" / "figures"
R = json.loads((ROOT / "studies" / "results" / "case_studies.json").read_text())
V = json.loads((ROOT / "verification" / "results" / "energyplus_comparison.json").read_text())
B = R["baseline"]
E = R["environment"]
P = R["power"]
RAD = R["radiator_moon_equator"]


def f0(x):
    return f"{x:,.0f}"


def f1(x):
    return f"{x:,.1f}"


def f2(x):
    return f"{x:.2f}"


def pct(a, b):
    return f"{100 * (a / b - 1):+.2f}%"


def mars_year_stats():
    import numpy as np
    SOL = 88775.244
    out = {}
    for nm in ("mars_jezero", "mars_jezero_storm"):
        d = np.load(ROOT / "studies" / "results" / f"{nm}.npz")
        si = np.floor(d["t_days"] * 86400 / SOL - 1e-9).astype(int)
        c = np.bincount(si)
        dm = lambda k: (np.bincount(si, weights=d[k]) / c)[1:-1]  # noqa: E731
        out[nm] = dict(ghi=dm("ghi"), ta=dm("T_air") - 273.15, qc=dm("Qc"))
    a, b = out["mars_jezero"], out["mars_jezero_storm"]
    return dict(ghi_min=a["ghi"].min(), ghi_max=a["ghi"].max(), ta_min=a["ta"].min(), ta_max=a["ta"].max(),
                storm_ghi_min=b["ghi"].min(), storm_sols=int((b["ghi"] < 60).sum()),
                storm_ta_drop=float((a["ta"] - b["ta"]).max()), storm_qc_dmax=float(abs(b["qc"] - a["qc"]).max()))


def build():
    MS = mars_year_stats()
    m = Manuscript()
    m.set_references(REFS)
    v600, v900, f600, f900 = V["Case600_opaque"], V["Case900_opaque"], V["Case600FF_opaque"], V["Case900FF_opaque"]
    meq, mpo, mjz, mst = B["moon_equator"], B["moon_pole"], B["mars_jezero"], B["mars_jezero_storm"]
    env_po = E["moon_pole"]
    env_jz = E["mars_jezero"]

    # ======================================================================= title page
    m.para("**ExoBEM: re-engineering the EnergyPlus heat-balance method for building energy simulation "
           "of lunar and Martian habitats**", align="center", size=15, space_after=12)
    m.para("Liang Zhang^{a,*}", align="center", size=11, space_after=2)
    m.para("^{a} University of Arizona, Tucson, AZ, USA", align="center", size=9.5, space_after=2)
    m.para("^{*} Corresponding author: liangzhang1@arizona.edu", align="center", size=9.5, space_after=2)
    m.para("[Draft for author review — confirm author list, affiliations, funding and target journal before submission.]",
           align="center", size=9, italic=True, space_after=14)

    m.heading("Highlights", numbered=False)
    m.bullets([
        "ExoBEM re-implements the EnergyPlus zone heat balance for the Moon and Mars.",
        f"Earth-mode verification against EnergyPlus 23.2: annual loads within {max(abs(v600['exobem_heating_kWh']/v600['eplus_heating_kWh']-1), abs(v900['exobem_heating_kWh']/v900['eplus_heating_kWh']-1), abs(v600['exobem_cooling_kWh']/v600['eplus_cooling_kWh']-1), abs(v900['exobem_cooling_kWh']/v900['eplus_cooling_kWh']-1))*100:.1f}%.",
        "Planetary physics: Mars24 time, dusty-sky transfer, regolith ground, vacuum and CO2 convection.",
        "Regolith-shielded habitats are nearly adiabatic; heat rejection, not insulation, drives energy.",
        "Lunar radiator orientation and dust storms on Mars dominate power-system sizing.",
    ])

    m.heading("Abstract", numbered=False)
    m.para(
        "Building energy simulation (BES) programs such as EnergyPlus encode Earth in their physics: a 24-hour day, "
        "terrestrial solar geometry, outdoor air as the convective and long-wave medium, and empirical sky and ground models. "
        "None of these hold on the Moon or Mars, where future crewed habitats must be designed for 354-hour lunar nights, "
        "a 600–800 Pa CO2 atmosphere, global dust storms and regolith radiation shields. This paper presents ExoBEM, an "
        "open-source BES engine that re-implements the EnergyPlus heat-balance method (surface heat balances, conduction "
        "finite differences, TARP convection, ScriptF interior radiation, zone air balance and ideal loads) and replaces "
        "each Earth-specific assumption with planetary physics: the Mars24 areocentric ephemeris and a selenographic solar "
        "model; a delta-Eddington treatment of dusty Martian skies fitted to the Appelbaum–Flood tables; the Hayne et al. "
        "lunar regolith thermophysical model; gas-, pressure- and gravity-aware convection; and radiator-based heat "
        "rejection with heat-pump lift. In Earth mode, ExoBEM reproduces EnergyPlus 23.2 for opaque ASHRAE 140 Cases 600 "
        f"and 900 within {abs(v600['exobem_heating_kWh']/v600['eplus_heating_kWh']-1)*100:.2f}% and "
        f"{abs(v900['exobem_heating_kWh']/v900['eplus_heating_kWh']-1)*100:.2f}% in annual heating, with hourly-load "
        f"R² of {v600['hourly_net_load_R2']:.3f} and free-floating temperature RMSE of {f2(f600['T_RMSE_K'])}–{f2(f900['T_RMSE_K'])} K. "
        "The planetary models reproduce Mars24 reference values, Diviner lunar surface temperatures, Appelbaum–Flood "
        "surface insolation and MEDA observations at Jezero crater. Case studies of a four-crew, regolith-shielded "
        "habitat show that a metre of regolith makes the envelope nearly adiabatic on both bodies, so the thermal design "
        f"problem becomes one of rejecting {f1(meq['cooling_kWh_per_day'])} kWh per day of internal heat. Equatorial lunar "
        f"radiators need heat-pump lift during {100*meq['heat_pump_hours_frac']:.0f}% of the lunation, while polar and Martian "
        "radiators reject heat passively almost all the time. Energy storage, set by the lunar night or by global dust storms, dominates the power "
        "system. ExoBEM provides a verified starting point for porting planetary physics into EnergyPlus itself.",
        space_after=6)
    m.para("**Keywords:** building energy simulation; EnergyPlus; lunar habitat; Mars habitat; heat balance; regolith; "
           "space architecture; thermal control", align="left")

    # ======================================================================= 1 introduction
    m.heading("Introduction")
    m.para(
        "Whole-building energy simulation has matured over five decades into a reliable design tool for terrestrial "
        "buildings [@Hong2000;Crawley2008]. EnergyPlus, developed by the U.S. Department of Energy, is the most widely "
        "used open-source engine; its heat-balance formulation solves coupled surface and zone-air energy balances at "
        "sub-hourly time steps and has been tested against analytical, comparative and empirical benchmarks "
        "[@Crawley2001;Strand2001;EPlusEngRef;ASHRAE140]. With the Artemis program planning sustained surface operations "
        "near the lunar south pole and with crewed Mars missions in long-term planning, the same questions that BES answers "
        "on Earth — how large must the heating, cooling and power systems be, and how do envelope choices trade against "
        "each other — must now be answered for habitats on other worlds [@Schunk2021;Schunk2022]."
    )
    m.para(
        "Existing habitat thermal analyses come from two traditions. Spacecraft thermal engineering uses lumped-network "
        "or finite-element tools and focuses on radiator sizing, worst-case hot and cold cases and component temperatures "
        "[@Gilmore2002;Simonsen1992;Gadkari1991;Schunk2022]. Structural and civil-engineering studies solve conduction "
        "through regolith-covered shells to obtain temperature fields for design [@Malla2015;Tripathi2023;Steiner2023;"
        "Kachalov2025;Li2025]. Neither tradition provides the annual, schedule-driven, whole-zone energy accounting that "
        "building scientists use to compare design alternatives. A small number of studies have tried to bring "
        "building-simulation tools to Mars, but they did so by constructing Mars-like weather files and running "
        "unmodified Earth engines or front-ends [@Lagarde2021;Aydemir2026], or by using design tools without a "
        "transient heat balance [@Jadeja2016]. This is not sufficient: changing a weather file changes neither the "
        "length of the day, the solar geometry, the convective medium nor the ground model."
    )
    m.para(
        "Table 1 lists the Earth assumptions embedded in a conventional BES engine and what replaces them on the Moon and "
        "Mars. The Moon has no atmosphere, so there is no exterior convection, the sky is a 3 K sink and the regolith "
        "swings between about 95 K and 390 K over a 29.5-day lunar day [@Vasavada2012;Hayne2017]. Mars has a 88,775-second "
        "sol, a 668.6-sol year with strong eccentricity-driven seasons, a 600–800 Pa CO2 atmosphere in which convection "
        "coefficients are one to two orders of magnitude lower than on Earth, and suspended dust whose optical depth "
        "ranges from about 0.3 to more than 8 during global storms [@Allison2000;Martinez2017;Guzewich2019]. Inside, "
        "habitats operate at reduced pressure (70.3 or 56.5 kPa) and reduced gravity, both of which weaken natural "
        "convection [@Anderson2018;EAWG2010]."
    )
    m.table(
        ["Element", "Earth BES (EnergyPlus)", "Moon (ExoBEM)", "Mars (ExoBEM)"],
        [["Time base", "24 h day, 8760 h year", "Synodic month 29.53 d; schedules on Earth clock", "Sol 88,775 s; year 668.6 sols; schedules on local mean solar time"],
         ["Solar position", "Earth declination and equation of time", "Selenographic subsolar point (Meeus; Cassini laws)", "Mars24 (Allison & McEwen 2000)"],
         ["Sky radiation", "Perez diffuse model; sky temperature from weather file", "No diffuse light; 2.7 K sky", "Delta-Eddington dust transfer; ε_{sky}(τ)σT_{a}^{4}"],
         ["Exterior convection", "Air at ~101 kPa (TARP, DOE-2, ...)", "None (vacuum)", "CO2 at 600–800 Pa, g = 3.72 m/s²"],
         ["Ground", "Monthly ground temperatures", "Hayne et al. (2017) regolith model", "Thermal-inertia regolith column"],
         ["Interior convection", "Correlations at 1 g, 101 kPa", "Scaled to 1.62 m/s², cabin pressure and O2", "Scaled to 3.72 m/s², cabin pressure and O2"],
         ["Heat rejection", "Outdoor air", "Radiators; heat-pump lift", "Radiators (CO2 convection secondary)"]],
        "Earth-specific assumptions of conventional BES and their planetary replacements in ExoBEM.",
        col_widths_cm=[2.8, 4.2, 4.5, 4.5])
    m.para(
        "This paper makes four contributions. (i) It presents ExoBEM, to the authors' knowledge the first open-source "
        "re-implementation of the EnergyPlus heat-balance method with physics modifications for planetary surface "
        "environments. (ii) It verifies the terrestrial core against EnergyPlus 23.2 and the planetary models against "
        "published reference data. (iii) It applies the tool to a regolith-shielded habitat at the lunar equator, at a "
        "lunar south-polar ridge and at Jezero crater on Mars, including a global dust storm. (iv) It documents a roadmap "
        "for porting the verified planetary physics back into EnergyPlus. Section 2 reviews related work, Section 3 "
        "describes the method, Section 4 the verification, Section 5 the case studies, Section 6 discusses implications "
        "and limitations, and Section 7 concludes."
    )

    # ======================================================================= 2 related work
    m.heading("Related work")
    m.heading("Thermal design of lunar and Martian habitats", 2)
    m.para(
        "Early lunar base studies established the thermal control architecture still in use: a single-phase water loop "
        "inside the pressure shell, an external ammonia loop and deployable radiators, with heat pumps to lift rejection "
        "temperature during the lunar day [@Simonsen1992;Gadkari1991]. Bien and Guentert showed that a vertical radiator "
        "at the lunar equator sees an equivalent sink of about 333 K at noon because half of its view is hot regolith "
        "[@Bien1969]. NASA's recent surface-habitat concept rejects about 15 kWt with 48 m² of double-sided panels and "
        "must survive eclipses of up to about 100 h near the south pole [@Schunk2021;Schunk2022]. Malla and co-workers "
        "computed lunar surface and subsurface temperatures and transient temperature fields in regolith-covered domes, "
        "showing that a metre of regolith damps the 300 K surface swing [@Malla2015;Tripathi2023;Steiner2023]. "
        "Other studies examined 3D-printed regolith walls with phase-change cores [@Kachalov2025], steel structures under "
        "Martian thermal cycling [@Li2025], cabin ventilation by CFD [@vonEinem2022] and habitat system-of-systems "
        "simulation [@Azimi2025]. Engler et al. forecast energy demand of the HI-SEAS analog habitat from data [@Engler2019], "
        "and Charoenboonvivat and de Weck modeled surface power demand for crewed missions [@Charoenboonvivat2026]."
    )
    m.heading("Building simulation tools applied off-Earth", 2)
    m.para(
        "Building-simulation tools have been applied to Mars only in a limited way. Jadeja et al. combined PlanetWRF "
        "climate output with Ecotect and CFD to study thermal comfort in a Mars module [@Jadeja2016]. Lagarde built a "
        "Gale-crater EPW weather file for Ladybug/Grasshopper solar and orientation studies and left heating and cooling "
        "loads to future work [@Lagarde2021]. Aydemir developed a Mars building-performance framework that converts Mars "
        "Climate Database output to EPW format for an EnergyPlus-based front-end [@Aydemir2026;Millour2018]. Ross "
        "developed an open-source semi-empirical heat balance for Mars habitats outside the BES tradition [@Ross2022]. "
        "None of these modify the heat-balance physics: an EPW file can carry Martian temperatures and irradiances, but "
        "the engine still computes Earth solar geometry over a 24-hour day, applies air-based convection at 101 kPa and "
        "assumes an Earth-like sky. To the authors' knowledge, no previous work has modified EnergyPlus-family physics "
        "for vacuum or thin-CO2 convection, regolith ground coupling, the Martian sol or the lunar day, and no lunar "
        "application of an EnergyPlus-family tool has been reported."
    )
    m.heading("Licensing and naming", 2)
    m.para(
        "EnergyPlus is distributed under a BSD-3-Clause-style license that permits modification and redistribution, "
        "including for derived tools, provided the copyright notice is retained, the developers' names are not used for "
        "endorsement, and (clause 4) a modified product is not named \"EnergyPlus\", \"E+\" or a confusingly similar "
        "name without U.S. DOE consent. ExoBEM contains no EnergyPlus source code; it re-implements algorithms documented "
        "in the Engineering Reference [@EPlusEngRef], credits EnergyPlus in a NOTICE file and uses a distinct name."
    )

    # ======================================================================= 3 method
    m.heading("Method")
    m.heading("Overview", 2)
    m.para(
        "ExoBEM (Fig. 1) is organized like EnergyPlus: a site-environment module plays the role of the weather manager, "
        "a heat-balance core computes surface and zone-air balances each time step, and post-processors compute "
        "thermal-control power and energy storage. The core is planet-agnostic: it receives time series of solar "
        "position, beam and diffuse irradiance, sky, ground and air temperatures, gas pressure and composition, wind and "
        "gravity, at an arbitrary time step and for an arbitrary day length. Models are defined in Python or in a JSON "
        "input file modeled on epJSON. The code is written in Python with NumPy and SciPy and released under the "
        "BSD-3-Clause license."
    )
    m.figure(FIG / "fig1_architecture.png",
             "ExoBEM architecture. The heat-balance core follows the EnergyPlus method; the ephemeris, site-environment, "
             "thermal-control and power modules carry the planetary physics.", 16.0)

    m.heading("Heat-balance core", 2)
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
        "regolith, the fixed-point radiation coefficient used in many BES codes oscillates and fails to converge.")
    m.para(
        "Conduction is solved with the node-centred, fully implicit finite-volume scheme of the EnergyPlus CondFD "
        "algorithm [@EPlusEngRef]:")
    m.equation(r"C_{i}\frac{T_{i}^{n+1}-T_{i}^{n}}{\Delta t}=K_{i-1/2}\left(T_{i-1}^{n+1}-T_{i}^{n+1}\right)+K_{i+1/2}\left(T_{i+1}^{n+1}-T_{i}^{n+1}\right)")
    m.para(
        "with node capacitances C_{i} (half of each adjacent cell) and conductances K = k/Δx or 1/R for massless layers. "
        "Two extensions matter off-Earth. First, metre-thick regolith covers have diffusivities near 2×10^{-9} m²/s, so "
        "each layer uses a grid stretched geometrically from both faces (first cell ½(αΔt)^{1/2}, growth 1.3). Second, "
        "conductivity and specific heat may depend on temperature; they are lagged by one step, as in CondFD.")
    m.para("At the inside face, conduction, convection to zone air, long-wave exchange and radiant internal gains balance:")
    m.equation(r"q_{ki}+h_{ci}\left(T_{z}-T_{si}\right)+\sum_{j}\sigma\mathcal{F}_{ij}\left(T_{sj}^{4}-T_{si}^{4}\right)+\frac{f_{i}Q_{rad}}{A_{i}}=0")
    m.para(
        "where ℱ_{ij} are Hottel gray-interchange (ScriptF) factors computed from EnergyPlus-style area-weighted view "
        "factors with enforced reciprocity [@Hottel1967;EPlusEngRef], and radiant gains are distributed in proportion to "
        "area times emissivity. The zone air balance is")
    m.equation(r"C_{z}\frac{dT_{z}}{dt}=\sum_{i}h_{ci}A_{i}\left(T_{si}-T_{z}\right)+Q_{conv}+\dot{m}c_{p}\left(T_{sup}-T_{z}\right)+Q_{sys}")
    m.para(
        "in which ṁ is outdoor-air infiltration on Earth and leakage make-up gas in a habitat. Q_{sys} is the ideal load "
        "that keeps T_{z} inside the heating and cooling set-points.")
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
        "coefficients and temperature-dependent properties) are updated by fixed-point iteration. The iteration "
        "typically converges to 0.005 K in two to three iterations per step.")
    m.para(
        "**Initialization.** EnergyPlus warms up by repeating the first day. A 1-m lunar regolith cover has a thermal "
        "time constant of years, so ExoBEM first solves a pseudo-transient steady state with period-mean boundary "
        "conditions (time steps growing geometrically to 10^{9} s, with T^{4}-mean sky and ground temperatures). It then "
        "repeats the first solar day (one sol or one lunation) once before recording results.")

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
        "Near the poles, the Sun is treated as a disk of finite angular radius above an azimuth-dependent horizon. "
        "Schedules run on local mean solar time on Mars and on Earth (UTC) time on the Moon, where the 29.5-day "
        "lunar day cannot set crew rhythms. The total solar irradiance is 1361 W/m² at 1 AU [@Kopp2011].")

    m.heading("Site environments", 2)
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
        "flux is 0.018 W/m². The column is spun up over six lunations.")
    m.para(
        "**Mars.** Top-of-atmosphere irradiance is 1361/r² W/m². Beam and diffuse components at the surface follow a "
        "delta-Eddington two-stream solution [@Joseph1976;Meador1980;Toon1989]:")
    m.equation(r"\frac{dF^{\pm}}{d\tau}=\pm\left(\gamma_{1}F^{\pm}-\gamma_{2}F^{\mp}\right)\mp\gamma_{3,4}\,\omega_{0}F_{s}e^{-\tau/\mu_{0}}")
    m.para(
        "with a Lambertian surface and a spherical-shell air mass. The broadband single-scattering albedo "
        "ω_{0} = 0.885 and asymmetry parameter g = 0.74 were fitted to the normalized net-flux tables of Appelbaum and "
        "Flood [@Appelbaum1990;Appelbaum1993]. These are effective solar-band values: they are lower than visible-band "
        "retrievals [@Wolff2009;ChenChen2019] because they absorb near-infrared absorption and two-stream error. Dust "
        "optical depth follows a seasonal climatology representative of Jezero crater (0.45 in the aphelion season, "
        "0.85 near L_{s} = 245°) [@Lemmon2015;Lemmon2022;Montabone2015]. A global-storm scenario raises τ to 6 between "
        "L_{s} = 190° and 270° [@Guzewich2019]. Surface pressure follows a two-harmonic CO2-cycle fit (mean 710 Pa). "
        "Ground temperature comes from a homogeneous regolith column with thermal inertia 350 J m^{-2} K^{-1} s^{-1/2} and "
        "albedo 0.14, as measured at Jezero by MEDA [@Martinez2023]. Near-surface air temperature is an empirical "
        "boundary-layer surrogate, T_{a} = T̄_{g} + κ(T_{g}(t−0.5 h) − T̄_{g}) with κ = 0.6, which reproduces the "
        "roughly 2:1 ratio of ground-to-air diurnal amplitude measured by MEDA and REMS "
        "[@RodriguezManfredi2021;GomezElvira2012;RodriguezManfredi2023]. Downwelling long-wave flux is")
    m.equation(r"L^{\downarrow}=\varepsilon_{sky}\left(\tau\right)\sigma T_{a}^{4}+f_{re}\left\langle G_{toa,h}-G_{h}\right\rangle_{sol},\quad \varepsilon_{sky}=\min\left(0.08+0.125\,\tau,\;0.6\right)")
    m.para(
        "The first term is emission by CO2 and dust; the second re-emits a fraction f_{re} = 0.45 of the sunlight that "
        "dust removes (sol-running mean), a one-layer-atmosphere energy term. The parameters were calibrated so that the "
        "clear-season daily mean is about 30 W/m², as measured by MEDA/TIRS [@Martinez2023], and so that in a global "
        "storm the sol-mean temperature drops by about 10 K while the diurnal range collapses, as observed in 2018 "
        "[@Guzewich2019].")

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
        "BVAD [@Anderson2018]). Gas properties come from Sutherland-type fits: the Mars mixture is 95% CO2, and cabin "
        "atmospheres are N2/O2 at 101.3 kPa/21%, 70.3 kPa/26.5% or 56.5 kPa/34% O2 [@Anderson2018;EAWG2010]. In Earth "
        "mode the TARP formulation is retained for comparability with EnergyPlus.")

    m.heading("Thermal control and power", 2)
    m.para(
        "Because a habitat cannot reject heat to outdoor air, the ideal cooling load (sensible plus crew latent heat "
        "removed by a condensing heat exchanger) is passed to a radiator model. The radiator's environmental sink "
        "temperature is")
    m.equation(r"\varepsilon_{r}\sigma T_{sink}^{4}=\alpha_{r}\left(G_{b}+G_{d}+G_{r}\right)+\varepsilon_{r}\sigma\left(F_{sky}T_{sky}^{4}+F_{g}T_{g}^{4}\right)")
    m.para(
        "The default radiator is two-sided, vertical and pole-facing, 40 m², with silver-Teflon optical properties "
        "α = 0.10 and ε = 0.80, midway between beginning and end of life [@Anderson2018]. If the radiator temperature "
        "needed to reject the load is below the cabin coolant temperature (2 °C less a 5 K approach), rejection is "
        "passive and only pump power (150 W) is drawn. Otherwise a vapor-compression heat pump lifts the heat, with COP "
        "equal to 40% of the Carnot value between the evaporator and the radiator temperature plus approach. The "
        "radiator temperature is found with a bracketed root search so that radiated power equals Q_{c}(1 + 1/COP). "
        "Photovoltaic generation (30% efficient arrays with two-axis or vertical single-axis tracking; a 0.85 dust factor "
        "on Mars) and storage capacity are sized so that the habitat's total electric demand (equipment, lighting and "
        "thermal control) is met over the period with an 85% storage round-trip efficiency.")

    # ======================================================================= 4 verification
    m.heading("Verification")
    m.heading("Comparative verification against EnergyPlus 23.2", 2)
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
                     f"{d['eplus_peak_heating_W']/1000:.2f} / {d['exobem_peak_heating_W']/1000:.2f}",
                     f"{d['eplus_peak_cooling_W']/1000:.2f} / {d['exobem_peak_cooling_W']/1000:.2f}",
                     f"{d['hourly_net_load_R2']:.4f}", f"{d['hourly_net_load_CVRMSE_pct']:.1f}"])
    m.table(["Case", "Heating E+ (kWh)", "Heating ExoBEM (kWh)", "Diff.", "Cooling E+ (kWh)", "Cooling ExoBEM (kWh)",
             "Diff.", "Peak heat E+/Exo (kW)", "Peak cool E+/Exo (kW)", "Hourly R²", "CV(RMSE) %"],
            rows, "Annual loads, ExoBEM (Earth mode) versus EnergyPlus 23.2, opaque ASHRAE 140 cases, Golden CO.",
            col_widths_cm=[1.4, 1.4, 1.5, 1.2, 1.4, 1.5, 1.2, 1.7, 1.7, 1.3, 1.3], font_size=7.5)
    rows = [[f"Case {n}FF", f2(d["eplus_Tmin"]), f2(d["exobem_Tmin"]), f2(d["eplus_Tmax"]), f2(d["exobem_Tmax"]),
             f2(d["eplus_Tmean"]), f2(d["exobem_Tmean"]), f2(d["T_RMSE_K"]), f"{d['T_MBE_K']:+.3f}", f"{d['T_R2']:.4f}"]
            for n, d in (("600", f600), ("900", f900))]
    m.table(["Case", "T_{min} E+", "T_{min} Exo", "T_{max} E+", "T_{max} Exo", "T_{mean} E+", "T_{mean} Exo",
             "RMSE (K)", "MBE (K)", "R²"], rows,
            "Free-floating zone air temperature (°C), ExoBEM versus EnergyPlus 23.2, 10-minute values over one year.",
            col_widths_cm=[1.6, 1.5, 1.5, 1.5, 1.5, 1.6, 1.6, 1.4, 1.4, 1.4], font_size=8)
    m.para(
        f"Annual heating differs by {pct(v600['exobem_heating_kWh'], v600['eplus_heating_kWh'])} (Case 600) and "
        f"{pct(v900['exobem_heating_kWh'], v900['eplus_heating_kWh'])} (Case 900), and annual cooling by "
        f"{pct(v600['exobem_cooling_kWh'], v600['eplus_cooling_kWh'])} and {pct(v900['exobem_cooling_kWh'], v900['eplus_cooling_kWh'])} "
        "(Table 2). Peak loads agree within 1%, and hourly net loads have R² above 0.998 (Fig. 2a). These differences are "
        "far smaller than the spread between programs in the ASHRAE 140 reference results. Free-floating temperatures "
        f"agree with an annual RMSE of {f2(f600['T_RMSE_K'])} K (600FF) and {f2(f900['T_RMSE_K'])} K (900FF) and a mean "
        "bias under 0.05 K (Table 3, Fig. 2b–c). The remaining differences come from documented implementation choices: "
        "finite volumes versus conduction transfer functions, implicit Euler versus third-order backward differencing "
        "of the air balance, the sub-hourly interpolation of weather data, and the solar-position algorithm.")
    m.figure(FIG / "fig2_verification.png",
             "Comparative verification against EnergyPlus 23.2 (Golden CO, TMY3). (a) Hourly net load (heating positive) "
             "for opaque Cases 600 and 900. (b, c) Free-floating zone air temperature over one winter and one summer week.",
             16.0)

    m.heading("Verification of the planetary models", 2)
    lt = E["moon_equator"]
    rows = [
        ["Mars24 worked example, 2000-01-06 00:00 UTC", "L_{s} = 277.18758°, EOT = −5.18774°, r = 1.39358 AU, MST = 23.99425 h", "Identical to 5 decimals", "[@Mars24]"],
        ["Lunar equatorial surface temperature (Diviner)", "≈385–390 K noon; ≈95 K pre-dawn; ≈252–256 K at ~1 m", f"{lt['T_ground_max_K']:.0f} K; {lt['T_ground_min_K']:.0f} K; {lt['T_deep_K']:.0f} K (3 m)", "[@Vasavada2012;Hayne2017]"],
        ["Mars net-flux function f(z, τ), 20 table values", "Appelbaum & Flood tables, albedo 0.1", "RMSE 0.014, max. error 0.035", "[@Appelbaum1990]"],
        ["Jezero surface pressure (daily means)", "≈625–790 Pa", f"{env_jz['P_min']:.0f}–{env_jz['P_max']:.0f} Pa", "[@RodriguezManfredi2023]"],
        ["Jezero air temperature at 1.45 m", "≈188–262 K", f"{env_jz['T_air_min_K']:.0f}–{env_jz['T_air_max_K']:.0f} K", "[@RodriguezManfredi2023]"],
        ["Jezero ground temperature", "≈183–290 K", f"{env_jz['T_ground_min_K']:.0f}–{env_jz['T_ground_max_K']:.0f} K", "[@Martinez2023]"],
        ["Jezero downwelling long-wave flux", "≈30 W/m² daily mean (20–45 W/m²)", f"{env_jz['L_down_mean']:.0f} W/m² mean ({env_jz['L_down_min']:.0f}–{env_jz['L_down_max']:.0f} W/m²)", "[@Martinez2023]"],
        ["Lunar south-polar ridge illumination", "92.3% at 2 m (Connecting Ridge)", f"{100*env_po['sunlit_fraction']:.1f}% (horizon −1.65°)", "[@Glaser2014]"],
        ["Vertical radiator sink, lunar equator, noon", "≈333 K", f"{RAD['Vertical, faces N/S (pole-facing)']['sink_max_K']:.0f} K", "[@Bien1969]"],
        ["Analytical: steady conduction, semi-infinite step (erfc), parallel-plate ScriptF, vacuum steady state", "Exact solutions", "Errors < 0.1% (unit tests)", "[@Incropera2007]"],
    ]
    m.table(["Quantity", "Reference", "ExoBEM", "Source"], rows,
            "Verification of the planetary models against reference data and analytical solutions.",
            col_widths_cm=[4.6, 4.6, 4.3, 2.5], font_size=8)
    m.para(
        "Table 4 summarizes the checks of the planetary models; all are automated in the test suite. Mars24's worked "
        "example is reproduced exactly. The regolith model reproduces Diviner's equatorial noon and pre-dawn temperatures "
        "and the Apollo heat-flow subsurface temperatures (Fig. 3a). The fitted delta-Eddington model reproduces the "
        "Appelbaum–Flood insolation tables over 0.1 ≤ τ ≤ 3 and 0° ≤ z ≤ 80° (Fig. 3b). The Jezero environment falls "
        "within the ranges MEDA observed for pressure, air and ground temperature and downwelling infrared. The lunar "
        "radiator sink agrees with the classic Bien–Guentert estimate. The polar horizon depression of −1.65° was "
        "chosen to match the 92.3% illumination of the best Connecting Ridge site [@Glaser2014]. Because a uniform "
        f"horizon concentrates darkness into seasons, it yields a longest eclipse of {env_po['longest_dark_days']:.0f} "
        "days, against 3–5 days for real ridge terrain [@Glaser2014;Mazarico2011]. Polar storage results below are "
        "therefore conservative.")
    m.figure(FIG / "fig3_environment_models.png",
             "Planetary environment models. (a) Lunar regolith surface temperature over a lunation at three latitudes, "
             "with Diviner equatorial ranges. (b) Normalized Martian surface net flux from the fitted delta-Eddington "
             "model (lines) and the Appelbaum–Flood tables (dots). (c) Seasonal dust optical depth at Jezero, nominal and "
             "with a 2018-type global dust storm.", 16.0)

    # ======================================================================= 5 case studies
    m.heading("Case studies")
    m.heading("Habitat model and sites", 2)
    m.para(
        "The reference habitat is a horizontal cylinder 6 m in diameter and 10 m long (about 280 m³), a size typical of "
        "rigid or inflatable surface modules. Sixteen shell facets resolve orientation; the two lowest rest on a regolith "
        "berm. The shell consists, from outside to inside, of a regolith radiation shield, beta cloth, insulation, "
        "a 4 mm aluminium-2219 pressure wall and a 10 mm interior panel. Insulation is 20-layer MLI on the Moon. On Mars, "
        "where MLI is ineffective at 600–800 Pa [@Trevino2000], it is a 20 mm silica-aerogel blanket "
        "(k = 0.012 W/(m·K) in CO2 [@Hickey1995]). Four crew contribute the BVAD nominal 85.1 W sensible and 53.8 W "
        "latent heat each [@Anderson2018], with sleep from 22:00 to 06:00. Equipment draws 2.5 kW (70% at night) and "
        "lighting 0.4 kW. The cabin is held at 70.3 kPa and 26.5% O2, between 18 and 27 °C [@Anderson2018;NASA3001], "
        "with 0.1 kg/day of leakage. Table 5 lists the sites.")
    rows = [
        ["Moon, equator", "Mare Tranquillitatis, 0.67°N 23.47°E", "2 lunations from 2030-01-01", "30 min", f"Vacuum; 2.7 K sky; regolith {E['moon_equator']['T_ground_min_K']:.0f}–{E['moon_equator']['T_ground_max_K']:.0f} K"],
        ["Moon, south pole", "Ridge at 89.5°S, horizon −1.65°", "12 lunations (354 d)", "60 min", f"{100*env_po['sunlit_fraction']:.0f}% sunlit; regolith {env_po['T_ground_min_K']:.0f}–{env_po['T_ground_max_K']:.0f} K"],
        ["Mars, Jezero", "18.44°N 77.45°E", f"1 Mars year from L_{{s}} = 0° ({R['sites']['mars_jezero']['start'][:10]})", "1/24 sol", f"P {env_jz['P_min']:.0f}–{env_jz['P_max']:.0f} Pa; τ 0.45–{env_jz['tau_max']:.2f}"],
        ["Mars, Jezero, dust storm", "As above", "As above", "1/24 sol", "τ up to 6 at L_{s} 190–270°"],
    ]
    m.table(["Case", "Site", "Period", "Time step", "Environment"], rows, "Case-study sites and simulation periods.",
            col_widths_cm=[2.8, 3.8, 3.8, 1.6, 4.0], font_size=8)
    m.figure(FIG / "fig4_environments.png",
             "Simulated surface environments: irradiance (top) and ground, sky and air temperatures (bottom) at the lunar "
             "equator, a lunar south-polar ridge and Jezero crater.", 16.0)

    m.heading("Results", 2)
    m.para(
        "Fig. 4 contrasts the three environments. At the lunar equator, 14.8 days of sunlight at up to 1406 W/m² alternate "
        f"with 14.8 days of darkness, and the regolith swings from {E['moon_equator']['T_ground_min_K']:.0f} to "
        f"{E['moon_equator']['T_ground_max_K']:.0f} K. At the polar ridge the Sun circles the horizon at grazing elevation: "
        "beam irradiance on a vertical surface is high, but the flat ground stays below "
        f"{env_po['T_ground_max_K']:.0f} K. At Jezero the cycle repeats every sol. In the clear season, dust removes "
        "about a fifth of the noon beam and turns much of it into diffuse light, and the CO2 atmosphere keeps the "
        f"effective sky above {env_jz['T_sky_min_K']:.0f} K.")
    rows = []
    for key, lab in (("moon_equator", "Moon, equator"), ("moon_pole", "Moon, south pole"),
                     ("mars_jezero", "Mars, Jezero"), ("mars_jezero_storm", "Mars, dust storm")):
        d = B[key]
        rows.append([lab, f1(d["heating_kWh_per_day"]), f1(d["cooling_kWh_per_day"]), f2(d["peak_cooling_W"] / 1000),
                     f0(d["envelope_gain_mean_W"]), f"{d['T_out_min_K']:.0f}–{d['T_out_max_K']:.0f}",
                     f"{100 * d.get('heat_pump_hours_frac', 0):.0f}", f1(d["thermal_control_kWh_per_day"]),
                     f"{d['radiator_sink_min_K']:.0f}–{d['radiator_sink_max_K']:.0f}"])
    m.table(["Case", "Heating (kWh/d)", "Cooling (kWh/d)", "Peak cooling (kW)", "Mean envelope gain (W)",
             "Outer surface (K)", "Heat-pump time (%)", "Thermal-control electricity (kWh/d)", "Radiator sink (K)"],
            rows, "Baseline results for the regolith-shielded habitat (1 m cover). Energies per Earth day.",
            col_widths_cm=[2.4, 1.5, 1.5, 1.5, 1.7, 1.8, 1.5, 2.1, 1.9], font_size=7.5)
    m.para(
        f"**The shielded habitat is cooling-dominated everywhere** (Table 6). With 1 m of regolith, the envelope "
        f"exchanges on average only {abs(meq['envelope_gain_mean_W']):.0f} W at the lunar equator and "
        f"{abs(mpo['envelope_gain_mean_W']):.0f} W at the pole, about 1–3% of the 2.9 kW of internal sensible gains. "
        "The cabin never needs heating, and the cooling load "
        f"({f1(meq['cooling_kWh_per_day'])} and {f1(mpo['cooling_kWh_per_day'])} kWh/d) is essentially the internal "
        "gain. The reason is the extraordinarily low conductivity of lunar regolith (3–5 mW/(m·K)): a 1-m cover has a "
        "thermal resistance of roughly 200 m²·K/W, an order of magnitude more than the MLI beneath it. On Mars, CO2 in "
        "the pores raises regolith conductivity to about 0.08 W/(m·K), and the envelope loses "
        f"{abs(mjz['envelope_gain_mean_W'])/1000:.2f} kW to the −60 °C environment. The cooling load "
        f"({f1(mjz['cooling_kWh_per_day'])} kWh/d) is therefore a little over half the lunar value. The outer regolith surface "
        f"follows the environment ({meq['T_out_min_K']:.0f}–{meq['T_out_max_K']:.0f} K at the lunar equator), but the "
        f"inside surfaces vary by about 1 K (Fig. 5a).")
    m.figure(FIG / "fig5_moon_habitat.png",
             "Regolith-shielded habitat at the lunar equator over two lunations. (a) Outer surface temperatures of selected "
             "facets. (b) Ideal sensible cooling, heating and crew latent loads. (c) Sink temperature of a vertical two-sided "
             "radiator facing north/south or east/west, compared with the 270 K evaporator temperature.", 16.0)
    m.para(
        "**Heat rejection is where the Moon's equator differs from the pole.** The sink temperature of a vertical "
        f"radiator at the equator rises to {meq['radiator_sink_max_K']:.0f} K at noon because half of its view is "
        f"regolith at nearly 390 K (Fig. 5c). For {100*meq['heat_pump_hours_frac']:.0f}% of the lunation, heat can only be "
        "rejected by lifting it with a heat pump; the COP falls to "
        f"{meq['cop_min']:.1f}, and the thermal-control system draws {f1(meq['thermal_control_kWh_per_day'])} kWh/d, "
        f"{meq['thermal_control_kWh_per_day']/mpo['thermal_control_kWh_per_day']:.1f} times the passive pump-only demand "
        f"at the pole, where the sink never exceeds {mpo['radiator_sink_max_K']:.0f} K. On Mars the sink peaks at "
        f"{mjz['radiator_sink_max_K']:.0f} K and rejection is passive for {100*(1-mjz['heat_pump_hours_frac']):.1f}% of the "
        f"year ({100*(1-mst['heat_pump_hours_frac']):.1f}% with the dust storm, whose infrared glow warms the sink).")
    rows = [[k, f1(v["tcs_kWh_per_day"]), f2(v["peak_W"] / 1000), f"{v['sink_max_K']:.0f}", f"{100*v['heat_pump_frac']:.0f}"]
            for k, v in RAD.items()]
    m.table(["Radiator configuration (40 m², ε = 0.80)", "Thermal-control electricity (kWh/d)", "Peak power (kW)",
             "Max. sink (K)", "Heat-pump time (%)"], rows,
            "Effect of radiator orientation and surface degradation at the lunar equator (α = 0.10 unless noted).",
            col_widths_cm=[6.0, 3.0, 2.2, 2.2, 2.4], font_size=8)
    h, hd = RAD["Horizontal, faces up"], RAD["Horizontal, dust-degraded (alpha = 0.35)"]
    m.para(
        "Table 7 compares radiator options at the equator. Turning a vertical radiator from the poles to east–west "
        "slightly worsens performance because it then faces the low morning and evening Sun. Doubling the vertical area "
        "saves only about 14%, because the noon sink is above the cabin temperature whatever the area. A horizontal "
        "radiator does not see the regolith: with a clean silver-Teflon surface its sink stays at "
        f"{h['sink_max_K']:.0f} K, and rejection is passive throughout ({f1(h['tcs_kWh_per_day'])} kWh/d). If lunar dust "
        f"raises its absorptance to 0.35 [@Gaier2008], the noon sink climbs to {hd['sink_max_K']:.0f} K and the heat pump "
        f"runs {100*hd['heat_pump_frac']:.0f}% of the time ({f1(hd['tcs_kWh_per_day'])} kWh/d). Radiator orientation and "
        "dust mitigation are thus first-order energy decisions for equatorial bases.")

    m.para(
        "**Envelope choices.** Fig. 6 compares envelope variants. On the Moon, removing the regolith (MLI alone) cuts the "
        f"cooling load by {100*(1-R['envelope_moon_equator']['MLI only']['cooling_kWh_per_day']/R['envelope_moon_equator']['MLI + 1 m regolith']['cooling_kWh_per_day']):.0f}% at the equator and "
        f"{100*(1-R['envelope_moon_pole']['MLI only']['cooling_kWh_per_day']/R['envelope_moon_pole']['MLI + 1 m regolith']['cooling_kWh_per_day']):.0f}% at the pole. This is not a benefit: the bare habitat "
        "simply leaks heat to space, and its internal surfaces follow the lunar day. Once 0.5 m of regolith is present, "
        "additional thickness or MLI changes the load by less than 3%. On Mars the picture is reversed. A habitat "
        "insulated only with 20 mm of aerogel or 50 mm of polyimide foam needs "
        f"{f1(R['envelope_mars_jezero']['Aerogel 20 mm']['heating_kWh_per_day'])} kWh/d of heating, about 4 kW on average. "
        "A 1 m regolith cover, with or without insulation, turns it into a cooling-dominated building. MLI in the CO2 "
        "atmosphere adds almost nothing to the regolith.")
    m.figure(FIG / "fig7_envelopes.png",
             "Daily heating and cooling loads for envelope variants at the three sites (kWh per Earth day).", 16.0)

    m.para(
        f"**Mars seasons and dust storms.** Over the Mars year at Jezero (Fig. 7), sol-mean insolation varies between "
        f"{MS['ghi_min']:.0f} and {MS['ghi_max']:.0f} W/m², and sol-mean air temperature between {MS['ta_min']:.0f} and "
        f"{MS['ta_max']:.0f} °C. A 2018-type global storm cuts sol-mean insolation to {MS['storm_ghi_min']:.0f} W/m² and "
        f"keeps it below 60 W/m² for {MS['storm_sols']} sols. Dust re-emits part of the absorbed sunlight as infrared, "
        f"so the nights warm, the days cool and the sol-mean air temperature falls by at most {MS['storm_ta_drop']:.0f} K, "
        "consistent with the 2018 observations [@Guzewich2019]. The habitat barely notices: its sol-mean cooling load "
        f"changes by at most {MS['storm_qc_dmax']:.0f} W. The power system notices a great deal, as shown next.")
    m.figure(FIG / "fig6_mars_year.png",
             "One Mars year at Jezero crater. (a) Sol-mean global horizontal irradiance, nominal and with a global dust "
             "storm. (b) Sol-mean air and ground temperatures. (c) Sol-mean habitat ideal loads.", 16.0)

    rows = []
    for key, lab in (("moon_equator", "Moon, equator (2-axis PV)"), ("moon_pole", "Moon, pole (vertical 1-axis PV)"),
                     ("mars_jezero", "Mars, Jezero (2-axis PV)"), ("mars_jezero_storm", "Mars, dust storm (2-axis PV)")):
        d = P[key]
        rows.append([lab, f2(d["mean_load_W"] / 1000), f2(d["peak_load_W"] / 1000), f"{100*d['thermal_control_share']:.0f}",
                     f0(d["pv_area_m2"]), f0(d["storage_kWh"])])
    m.table(["Case", "Mean electric load (kW)", "Peak load (kW)", "Thermal-control share (%)",
             "PV area for energy balance (m²)", "Storage needed (kWh)"], rows,
            "Power-system sizing for the habitat's total electric load (equipment, lighting and thermal control).",
            col_widths_cm=[4.6, 2.2, 1.8, 2.3, 2.6, 2.5], font_size=8)
    m.para(
        f"**Power-system implications** (Table 8). With arrays sized for energy balance, the equatorial lunar base "
        f"needs about {f0(P['moon_equator']['storage_kWh'])} kWh of storage to cross the 354-hour night, and its "
        f"thermal-control system accounts for {100*P['moon_equator']['thermal_control_share']:.0f}% of the electric load. "
        f"At the polar ridge the array shrinks to {f0(P['moon_pole']['pv_area_m2'])} m², but the idealized horizon's "
        f"{env_po['longest_dark_days']:.0f}-day eclipses still call for {f0(P['moon_pole']['storage_kWh'])} kWh. Real ridge "
        "terrain, whose eclipses last only 3–5 days [@Glaser2014], would need far less. At Jezero, nominal dust requires "
        f"{f0(P['mars_jezero']['pv_area_m2'])} m² of arrays and {f0(P['mars_jezero']['storage_kWh'])} kWh of storage, "
        "mostly to buffer the dusty, low-sun northern winter. A global dust storm multiplies the storage by "
        f"{P['mars_jezero_storm']['storage_kWh']/P['mars_jezero']['storage_kWh']:.1f}, to "
        f"{f0(P['mars_jezero_storm']['storage_kWh'])} kWh, although the thermal loads hardly change. Oversizing the "
        "arrays trades directly against these storage figures.")

    m.heading("Convection under reduced gravity and pressure", 2)
    m.para(
        "Fig. 8 quantifies why convection coefficients cannot be carried over from Earth. Cabin natural convection on a "
        "2.5 m wall with a 3 K temperature difference drops from about 2.1 W/(m²·K) at 1 g and 101 kPa to about "
        "0.9 W/(m²·K) at lunar gravity and 70.3 kPa. That is comparable to the forced coefficient at a 0.15 m/s "
        "ventilation velocity, so cabin ventilation, not buoyancy, controls interior surface heat transfer on the "
        "Moon. Outside on Mars, mixed convection in 700 Pa CO2 gives 0.15–0.7 W/(m²·K) over the full range of wind "
        "speeds, 20–70 times less than on Earth at the same wind speed. Exterior convection on Mars is therefore a correction to the radiative "
        "balance rather than a dominant term. This is consistent with the small sensible heat fluxes MEDA measured "
        "[@Martinez2023].")
    m.figure(FIG / "fig8_convection.png",
             "(a) Interior natural convection coefficient versus gravity for three cabin atmospheres (2.5 m vertical wall, "
             "ΔT = 3 K), with the forced-convection value at 0.15 m/s. (b) Exterior mixed convection versus wind speed for "
             "a 3 m surface on Earth and Mars (ΔT = 10 K and 30 K, respectively).", 16.0)

    # ======================================================================= 6 discussion
    m.heading("Discussion")
    m.heading("Implications for habitat design", 2)
    m.para(
        "The case studies suggest a shift in emphasis for habitat energy design. On Earth, BES spends most of its effort "
        "on the envelope; a regolith-shielded habitat on the Moon is so well insulated by its radiation shield that "
        "envelope optimization is nearly moot. Design then turns on (i) internal heat generation, (ii) where and how "
        "that heat is rejected, and (iii) storage across darkness. Radiator placement, coating degradation by dust, and "
        "site choice (equator versus pole) change thermal-control energy by a factor of five. On Mars, insulation "
        "matters again because CO2-filled regolith and the atmosphere conduct, but power-system sizing is dominated by "
        "dust. These conclusions are qualitatively known to spacecraft thermal engineers [@Simonsen1992;Schunk2022]. "
        "What ExoBEM adds is a way to quantify them with the annual, schedule-driven methods of building science, and to "
        "carry the same model from early massing studies to detailed design.")
    m.heading("Limitations", 2)
    m.bullets([
        "**Single zone.** Multi-zone habitats, airlocks and inter-module air exchange are not yet modelled.",
        "**Sensible-only air balance.** Crew latent heat is passed to the coolant loop, but cabin humidity is not tracked.",
        "**Idealized terrain.** Horizons are uniform or user-supplied profiles; DEM horizons (LOLA, HiRISE) and shading between modules are planned.",
        "**Empirical Mars boundary layer.** Near-surface air temperature uses a calibrated surrogate rather than a surface-layer model; Mars Climate Database input is planned [@Millour2018;Forget1999].",
        "**Effective dust optics.** Broadband scattering parameters are fitted to Appelbaum–Flood tables; spectral and site-specific optics would refine the beam/diffuse split [@Wolff2009;ChenChen2019].",
        f"**Storm infrared.** The dust re-emission term was calibrated to the observed temperature response; peak downwelling infrared in the τ = 6 storm ({E['mars_jezero_storm']['L_down_max']:.0f} W/m²) is probably overestimated and should be checked against MEDA and REMS storm data.",
        "**Ideal thermal control.** Radiators, heat pumps and storage are quasi-steady post-processors without component dynamics or capacity limits.",
        "**Verification scope.** The Earth core was compared with EnergyPlus on opaque cases; windows, empirical validation in thermal-vacuum chambers and analog habitats remain to be done.",
    ])
    m.heading("Roadmap: back into EnergyPlus", 2)
    m.para(
        "Re-implementing the method in a compact engine allowed the planetary physics to be developed and verified "
        "quickly. A full EnergyPlus fork must touch the weather manager (non-24-hour days), schedule manager, solar "
        "calculations, outdoor convection, psychrometrics and ground models. The verified ExoBEM modules define those "
        "changes and serve as regression references. Under clause 4 of the EnergyPlus license, such a fork must carry a "
        "different name. The planned steps are a Site:Planet object (gravity, day length, atmosphere, solar ephemeris), "
        "a generalized time base and weather format, a vacuum/CO2 outdoor-medium option, a regolith ground model and "
        "radiator plant components.")

    # ======================================================================= 7 conclusions
    m.heading("Conclusions")
    m.para(
        "ExoBEM brings whole-building energy simulation to the Moon and Mars by re-implementing the EnergyPlus "
        "heat-balance method and replacing its Earth-specific physics with planetary ephemerides, airless and thin-CO2 "
        "environments, regolith thermophysics, gravity- and pressure-aware convection and radiator heat rejection. Its "
        "terrestrial core matches EnergyPlus 23.2 within 0.7% in annual loads, and its planetary models reproduce "
        "Mars24, Diviner, Appelbaum–Flood and MEDA reference data. For a four-crew habitat under 1 m of regolith, the "
        "envelope is nearly adiabatic on the Moon; the energy problem becomes rejecting about 3 kW of internal heat. "
        "That costs several times more electricity at the lunar equator, where radiators see hot regolith, than at the "
        "pole or on Mars. On Mars, insulation matters again and dust storms dominate storage sizing. The code, "
        "verification scripts and inputs are open source to support community development toward a planetary version "
        "of EnergyPlus.")

    # ======================================================================= back matter
    m.heading("Software and data availability", numbered=False)
    m.para(
        "ExoBEM v0.1.0, the EnergyPlus verification inputs, case-study scripts and the data behind every figure and "
        "table are available at https://github.com/TensorBuildLab/ExoBEM (BSD-3-Clause). "
        "The repository will be renamed to avoid the EnergyPlus name in accordance with the EnergyPlus license. "
        "EnergyPlus 23.2 and the TMY3 weather file are available from the U.S. DOE.")
    m.heading("Declaration of generative AI use", numbered=False)
    m.para(
        "During the preparation of this work the author used Claude (Anthropic) to assist with literature search, "
        "software implementation, verification scripting and drafting of the manuscript. The author reviewed and edited "
        "all content and takes full responsibility for the publication. [Authors: confirm and adapt to the target "
        "journal's policy.]")
    m.heading("CRediT authorship contribution statement", numbered=False)
    m.para("[To be completed by the authors.]")
    m.heading("Declaration of competing interest", numbered=False)
    m.para("The authors declare that they have no known competing financial interests or personal relationships that "
           "could have appeared to influence the work reported in this paper.")
    m.heading("Acknowledgements", numbered=False)
    m.para("EnergyPlus is developed by the U.S. Department of Energy's Building Technologies Office and its national "
           "laboratory and university partners; ExoBEM is not endorsed by them. [Funding to be added.]")

    m.heading("References", numbered=False)
    m.reference_list()
    out = ROOT / "paper" / "ExoBEM_manuscript.docx"
    m.save(out)
    unused = sorted(set(REFS) - set(m.cite_order))
    print("saved", out, "| cited", len(m.cite_order), "| unused refs:", unused)


if __name__ == "__main__":
    build()
