"""Sections of the ExoBEM-Core (C++ engine) manuscript, shared by the ExoBEM-Core paper and the combined paper.

Numbers are read from paper/data/core_facts.json and paper/data/core_summary.json
(written by paper/extract_core_data.py from the ExoBEM-Core repository and its verification runs).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "paper" / "figures"
F = json.loads((ROOT / "paper" / "data" / "core_facts.json").read_text())
S = json.loads((ROOT / "paper" / "data" / "core_summary.json").read_text())
AF = F["audit_facts"]
DIFF = F["diff"]
UT = F["unit_tests"]
RT = F["run_time_s"]
CM = S["moon_equator"]["comparison"]
CR = S["mars_jezero"]["comparison"]
N_FIND = sum(a["P0"] + a["P1"] + a["P2"] for a in F["audit"]["areas"])
N_P0 = sum(a["P0"] for a in F["audit"]["areas"])
N_P1 = sum(a["P1"] for a in F["audit"]["areas"])
N_P2 = sum(a["P2"] for a in F["audit"]["areas"])
N_EARTH = len(F["earth_regression"]["files"])
KLOC = F["source_lines_cc_hh"] / 1000


def dpct(c):
    e = c["energy"]
    return 100 * (e["ep_cooling_kWh"] / e["py_cooling_kWh"] - 1)


MOON_DIFF, MARS_DIFF = dpct(CM), dpct(CR)

# Set by the combined manuscript: ExoBEM is then a section of the same paper, not a companion paper.
COMBINED = False


def exo_ref():
    return "(Section @sec:method)" if COMBINED else "[@ZhangExoBEM]"


# =========================================================================== background
def engine_background(m):
    """How the EnergyPlus engine meets its environment (level-2 subsection)."""
    m.heading("Where EnergyPlus meets its environment", 2, label="enginebg")
    m.para(
        "EnergyPlus advances a nested loop over run periods, days, hours and zone time steps [@EPlus262;Crawley2001]. "
        "At the start of each day the weather manager reads the next day of the weather file, computes the Earth "
        "solar declination and equation of time from Fourier fits keyed on the day of year, and interpolates the "
        "hourly records to the zone time step. Within the day the solar routines turn clock time, longitude and "
        "time-zone meridian into a sun direction with an hour angle that advances 15° per hour. The surface heat "
        "balance then applies exterior convection correlations for air, splits long-wave exchange among sky, air and "
        "ground, solves conduction with conduction transfer functions (CTF) [@Seem1987] or the conduction finite "
        "difference (CondFD) algorithm [@TabaresVelasco2012], couples inside faces to the zone air, and passes the "
        "zone load to HVAC, plant and electric-power models, all of which take their air properties from the outdoor "
        "barometric pressure.")
    m.para(
        "None of this is wrong on Earth; it is the reason EnergyPlus is fast and robust. But the Earth enters in many "
        "places at once, often as literals (3600 s, 15°/h, 1 atm, 9.81 m/s²) or as conventions (the ground is at air "
        "temperature; the zone is at outdoor pressure) that are not visible in the input. A model of a lunar habitat "
        "therefore cannot be made correct by editing the weather file alone, and an engine fork must first find "
        "where the planet is hidden.")


def approaches(m):
    """Three ways to simulate off-Earth buildings (level-2 subsection)."""
    m.heading("Three routes to off-Earth building simulation", 2, label="routes")
    m.para(
        "Previous work has taken one of two routes. The first keeps an Earth engine and replaces its weather: Mars "
        "Climate Database or rover data are written into EPW files and run through EnergyPlus front-ends "
        "[@Lagarde2021;Aydemir2026;Millour2018], or climate-model output is coupled with design tools [@Jadeja2016]. "
        "This keeps the tools but not the physics: the engine still uses a 24-hour Earth sun, air at outdoor "
        "pressure for convection and psychrometrics, and Earth sky and ground models. The second route builds a new "
        "model. Ross developed a semi-empirical habitat heat balance [@Ross2022], and the companion ExoBEM tool "
        "re-implements the EnergyPlus heat-balance method in about 2,500 lines of Python with planetary physics "
        "throughout [@ZhangExoBEM]. A re-implementation can be verified quickly, but it leaves out most of what "
        "makes EnergyPlus useful for design: multi-zone HVAC and plant, controls, electric systems, a large and "
        "tested input and output ecosystem (OpenStudio and its measures [@Guglielmetti2011]), and decades of "
        "comparative testing [@ASHRAE140].")
    m.para(
        "The third route, taken here, modifies the engine itself. This is the hardest of the three because the "
        "Earth assumptions must be located in a large code base before any physics can be changed, and every change "
        "must leave terrestrial results untouched for the fork to remain trustworthy. It is also the route that "
        "lets planetary habitats inherit everything else the engine can do.")


def licensing_core(m):
    """Licensing and naming of an EnergyPlus fork."""
    m.heading("Licensing and naming", 2, label="licensecore")
    m.para(
        "EnergyPlus is distributed under a BSD-3-Clause license with an additional clause from the U.S. Department of "
        "Energy: a modified version may be redistributed, but it may not be called \"EnergyPlus\", \"E+\" or a "
        "confusingly similar name without DOE consent, and the developers may not be used to endorse it. The fork "
        "is therefore named ExoBEM-Core, keeps the original license and copyright notices, states in its README that "
        "it is not EnergyPlus and is not endorsed by DOE or the National Laboratory of the Rockies (formerly NREL), "
        "and is published as a separate repository with the upstream history intact [@ExoBEMCoreRepo].")


# =========================================================================== audit
def audit(m):
    """Audit method and findings (level-2 subsections)."""
    m.heading("Audit method", 2, label="auditmethod")
    m.para(
        f"The audit covered EnergyPlus v26.2.0, whose src/EnergyPlus directory holds about {KLOC:,.0f} thousand lines of "
        "C++ in .cc and .hh files, plus the third-party libraries it compiles (window calculation engine, Kiva). It was "
        "split into six areas that together cover every path from input to output: (1) time base, calendar, weather "
        "input and sizing; (2) solar geometry, sky and ground radiation; (3) psychrometrics, pressure, gravity and "
        "airflow; (4) the surface heat balance, conduction, convection and ground contact; (5) windows; and (6) HVAC, "
        "plant, heat rejection and electric power. Each area was searched for the symbols through which Earth enters "
        "the code (time constants, hour-angle and solar-constant literals, OutBaroPress, StdRhoAir, gravity "
        "constants, outdoor-air temperature used as a ground or sky proxy, empirical correlation coefficients and "
        "validity limits), and each hit was classified as bookkeeping (for example, an hour used as an array index) "
        "or physics (an hour used to convert a rate to energy).")
    m.para(
        "Every finding records the file and line, the Earth value assumed, the consequence on the Moon and on Mars, "
        "a proposed change and a priority: **P0** if it must change for a first single-zone, opaque habitat with "
        "constructions, internal gains and ideal loads; **P1** if it is needed for windows, HVAC, plant, PV or "
        "realistic outputs; and **P2** for rarely used modules that are better refused off-Earth than fixed. The "
        "search was carried out with the help of large-language-model code agents working from a common written "
        "brief, one agent per area; the findings acted on in this work were checked against the source during "
        "implementation. The six reports are published with the code [@ExoBEMCoreRepo].")

    m.heading("What the audit found", 2, label="auditfound")
    m.para(
        f"The audit recorded {N_FIND} findings: {N_P0} P0, {N_P1} P1 and {N_P2} P2 (Fig. @fig:audit). They are spread "
        "over all six areas, but the P0 findings cluster in four: time and weather, solar and sky radiation, pressure "
        "and air properties, and the exterior surface boundary. Windows have no P0 finding because no window code runs "
        "in a model without fenestration, and HVAC has only four because the ideal-loads system already turns outdoor "
        "air off when no outdoor-air specification is given. Table @tab:findings lists representative findings.")
    m.figure(FIG / "core_fig2_audit.png",
             f"Earth-specific assumptions found in EnergyPlus v26.2.0 by area and priority ({N_FIND} findings). P0: "
             "needed for a first single-zone habitat with ideal loads; P1: needed for windows, HVAC, plant and PV; P2: "
             "rarely used modules that are refused off-Earth.", 16.0, label="audit")
    rows = [
        ["Time base", f"1 h = 3600 s is a compile-time constant; {AF['rSecsInHour_uses']} uses of rSecsInHour, "
         f"{AF['rSecsInHour_physical']} of them physical; CTFs computed in Earth hours",
         "A longer 'planetary hour' would rescale physics in some places but not others, and CTFs by up to ×29.5 on the Moon",
         "Earth clock kept (hour = 3600 s); sun rate generalized"],
        ["Weather input", "EPW range checks: dry-bulb ≥ 99.9 °C treated as missing; pressure ≤ 31 kPa replaced by the standard value",
         "Lunar-day 120 °C and Martian 700 Pa silently altered", "Generator overwrites each day after the read"],
        ["Sun", "Declination and equation of time from Earth Fourier fits (two copies); hour angle 15°/h",
         "Wrong sun on any other body", "Daily fit to Mars24 / lunar ephemeris; body hour-angle rate"],
        ["Sky", "Perez diffuse model (1353 W/m², Earth air mass); part of the sky long-wave view sees air",
         "No basis in vacuum or dusty CO2", "Isotropic diffuse; all sky long-wave to the sky"],
        ["Ground", f"Ground long-wave temperature = outdoor air at {AF['ground_lw_equals_air_sites']} sites; monthly ground temperatures",
         "No air on the Moon; regolith swings 290 K", "Regolith skin and deep temperatures from a 1-D column"],
        ["Pressure", f"One pressure, OutBaroPress, for zone, HVAC and outdoor air ({AF['OutBaroPress_uses']} uses in "
         f"{AF['OutBaroPress_files']} files)", "Moon (0 Pa): zero air capacity, NaN humidity, one psychrometric routine never "
         "returns; Mars: 0.7% of the cabin's thermal mass", "OutBaroPress carries the cabin pressure; new AmbientBaroPress"],
        ["Convection", "Every exterior correlation assumes air at 1 atm and 1 g, with a non-zero floor; TARP inside",
         f"Heat loss to air that does not exist; cabin convection overestimated about {AF['tarp_overestimate_moon']}× on the Moon",
         "Zero (Moon) or CO2 mixed convection (Mars) outside; physical correlation inside"],
        ["Conduction", "CondFD clamps nodes at −100 °C; walls start at 23 °C and warm up by repeating day 1",
         "Lunar-night surfaces near −180 °C; regolith time constants of months to years", "−270 °C limit; steady start-up profile"],
        ["HVAC and plant", f"Heat rejection to outdoor air; {AF['OutBaroPress_hvac_uses']} OutBaroPress and "
         f"{AF['StdRhoAir_uses']} StdRhoAir uses in HVAC and plant", "Cooling towers, air-cooled condensers and outdoor-air "
         "systems meaningless in vacuum", "Refused with an error; space radiator planned"],
        ["Windows", f"{AF['window_solvers']} thermal solvers, each with its own Earth gas and pressure constants",
         "Interior film at outdoor pressure gives the floor value or NaN", "Not yet supported"],
    ]
    m.table(["Area", "Earth assumption in the v26.2 code", "Effect off-Earth", "ExoBEM-Core M1"], rows,
            "Representative Earth assumptions found by the audit and their treatment in ExoBEM-Core.",
            col_widths_cm=[2.0, 5.4, 4.6, 4.0], font_size=7.5, label="findings")
    m.para(
        "Three findings shaped the design. First, time is the most pervasive assumption but also the least visible. "
        f"About 1,110 rate-times-time-step products go through two variables that are set in only "
        f"{AF['timestep_setters']} lines, which makes a variable hour length feasible, but {AF['rSecsInHour_units']} uses "
        "of the same constant are genuine unit conversions (kWh, air changes per hour, flow per hour) that must stay "
        "3600 s, and the CTF generator works internally in Earth hours. A longer hour is therefore a deep change. "
        "Second, the engine has a single air pressure. About "
        f"{AF['OutBaroPress_cabin']} of the {AF['OutBaroPress_uses']} uses of OutBaroPress describe air inside the "
        f"pressure shell and about {AF['OutBaroPress_outdoor']} describe outdoor air; on the Moon the outdoor value is "
        "zero. Third, the exterior boundary hides air in places other than convection: in the long-wave split, in the "
        "ground temperature and in the moisture balance.")


# =========================================================================== design
def design(m):
    """Planetary mode: rules, time and sun, environment, pressure, boundaries, start-up, validator (level-2)."""
    m.heading("Design rules", 2, label="rules")
    m.para("Three rules guided every change (Fig. @fig:hooks):")
    m.bullets([
        "**Earth stays bit-for-bit.** Planetary mode is active only when the input contains a Site:PlanetaryBody object "
        "with Body = Moon or Mars. Every change is either behind that switch or replaces a literal by a variable whose "
        "Earth value is the same literal, so that IEEE floating-point results on Earth do not change.",
        "**Reuse, do not rewrite.** Planetary values are injected where EnergyPlus already reads its environment "
        "(weather arrays, sun direction, ground temperature, exterior and interior coefficients). The heat balance, "
        "conduction solvers, shading, view factors, ideal loads and reporting run unchanged.",
        "**Refuse what cannot be right.** Objects that need outdoor air or Earth weather stop the run with an error off-Earth "
        "instead of producing a plausible-looking wrong answer.",
    ])
    m.para(
        f"The result is small. The first milestone (M1) adds {DIFF['insertions']:,} lines and changes {DIFF['deletions']} in "
        f"{DIFF['files']} files: a new PlanetaryBody module ({DIFF['new_module_lines']:,} lines), the input-object "
        f"definition ({DIFF['idd_lines']} lines) and about {DIFF['hook_lines_existing_files']} lines of hooks in "
        f"{DIFF['existing_files_touched']} existing files, which is 0.2% of the engine.")
    m.figure(FIG / "core_fig1_hooks.png",
             "Where ExoBEM-Core enters the EnergyPlus engine. Grey: unchanged EnergyPlus stages and the source files that "
             "carry the hooks; orange: what the hook does off-Earth. The new PlanetaryBody module supplies ephemerides, "
             "the environment, regolith temperatures and gas properties.", 16.0, label="hooks")

    m.heading("Input", 2, label="input")
    m.para(
        "A single new object, Site:PlanetaryBody, selects the body (Earth, Moon or Mars), the clock, a reference year "
        "and the habitat parameters: gravity (by default the body's surface value: 1.625 m/s² on the Moon, 3.721 m/s² "
        "on Mars), cabin pressure (70.3 kPa) and oxygen fraction (0.265), cabin air velocity (0.15 m/s) and a "
        "convection length scale. Optional fields set the horizon elevation, the regolith thermal inertia, albedo, "
        "emissivity and spin-up cycles, the deep-regolith depth, and for Mars the mean surface pressure, the dust "
        "optical-depth model (seasonal climatology or constant, with an optional global storm defined by start and end "
        "solar longitude and peak optical depth) and the wind. Everything else in the input file is standard. In M1 "
        "a weather file is still required, but it supplies only the calendar and the site; every weather value is "
        "replaced (Section @sec:env).")

    m.heading("Time base and sun position", 2, label="sun")
    m.para(
        "The audit showed that a planetary hour would touch about a hundred physical uses of the hour length and the "
        "CTF generator. M1 therefore keeps the Earth clock: an hour is 3600 s and a day starts at 00:00 UTC, so that "
        "crew schedules, which follow Earth or mission time, are written as on Earth. What changes is the rate at which "
        "the Sun moves. EnergyPlus computes the hour angle in several places, all with the same expression; ExoBEM-Core "
        "replaces the literal 15 by a variable:")
    m.equation(r"H=r\left[12-\left(t+E\right)\right]+\left(\lambda_{TZ}-\lambda\right),\qquad r=\frac{360^{\circ}}{P_{d}/3600\,\mathrm{s}}",
               label="hourangle")
    m.para(
        "where t is the clock hour, E the equation of time in hours, λ_{TZ} and λ the time-zone meridian and the "
        "longitude, and P_{d} the length of the solar day: 86,400 s on Earth (r = 15°/h, the original literal), the "
        "synodic month of 29.53 days on the Moon (r = 0.508°/h) and the sol of 88,775 s on Mars (r = 14.6°/h). For each "
        "simulated day the declination and E are fitted to the planetary ephemeris at 12:00 UTC: the declination is "
        "taken from Mars24 [@Allison2000] or from the selenographic subsolar point [@Meeus1998], and E is chosen so that "
        "Eq. (@eq:hourangle) reproduces the ephemeris hour angle H_{⊙} at mid-day,")
    m.equation(r"E_{d}=\frac{H_{\odot}\left(12\,\mathrm{h}\right)+\lambda_{TZ}-\lambda}{r}", label="eotfit")
    m.para(
        "Because the hour angle is linear in time over a day on both bodies, Eq. (@eq:hourangle) then follows the "
        "ephemeris through the day (Section @sec:cross). All downstream sun and shading routines, including the "
        "polygon-clipping shadow calculation, are reused. Two settings change off-Earth: the shading calculation is "
        "updated every day, because the declination fitted for one day does not hold for the next, and the hour "
        "angle is wrapped to ±180° before the sunrise test, because on the Moon it spans more than one revolution in a "
        "lunation.")

    m.heading("Planetary environment", 2, label="env")
    m.para(
        "The weather manager reads the next day from the weather file and then calls the PlanetaryBody module, which "
        "overwrites every per-time-step value (dry-bulb temperature, beam and diffuse irradiance, sky temperature, "
        "pressure, wind) for that day. The values come from an environment generator that is a C++ port of the ExoBEM "
        f"environment models {exo_ref()} and is run for the whole run period before the simulation starts. On the "
        "Moon there is no diffuse light, the sky is at 2.725 K and the ground is a 1-D regolith column following "
        "Hayne et al. [@Hayne2017], spun up over six lunations. On Mars the beam and diffuse irradiance come from a "
        "delta-Eddington two-stream solution with a seasonal dust optical depth and an optional global storm "
        "[@Joseph1976;Appelbaum1990], the pressure follows the seasonal CO2 cycle, the sky emits as an effective "
        "dusty-CO2 layer, the near-surface air follows the ground with a lag, and a thermal-inertia regolith column is "
        "spun up over thirty sols. The regolith skin temperature and the deep-regolith temperature are kept for the "
        "surface boundary, and seven new output variables report the planetary environment (ground surface and deep "
        "temperature, ambient pressure, downwelling long-wave radiation, Sun distance, solar longitude and dust optical "
        "depth). Because values are overwritten after the weather file is read, none of the EPW range checks found by "
        "the audit can alter them.")

    m.heading("Cabin and ambient pressure", 2, label="pressure")
    m.para(
        "The single-pressure finding admits two fixes: add a cabin pressure and change the roughly 350 zone and HVAC "
        "uses of OutBaroPress, or let OutBaroPress carry the cabin pressure and change the outdoor uses. ExoBEM-Core "
        "takes the second option. Off-Earth, OutBaroPress holds the cabin pressure, so the zone air balance, "
        "psychrometrics, ideal loads and every HVAC component see the air they actually contain, without edits; the "
        "standard pressure and density used for volume-to-mass conversions follow the cabin as well. A new variable, "
        "AmbientBaroPress, holds the real outdoor pressure (zero on the Moon, 600–800 Pa on Mars) and is used by the "
        "exterior convection model and the outputs. Almost all outdoor users of the old variable are outdoor-air "
        "systems, infiltration and heat rejection to air, and these are refused off-Earth (Section @sec:refuse), so the "
        "option leaves no silent outdoor use of the cabin pressure in a valid input. The cabin gas is treated with "
        "moist-air psychrometrics at cabin pressure; at 26.5% oxygen the specific heat and gas constant differ from "
        f"air by less than {AF['cabin_psychrometric_error_pct']}%.")

    m.heading("Exterior boundary", 2, label="extbc")
    m.para(
        "Off-Earth, the exterior convection coefficient is replaced. It is zero in vacuum, and the EnergyPlus lower "
        "limit on the coefficient is bypassed. On Mars, a physical mixed-convection correlation is used for CO2 at the "
        "ambient pressure and the body's gravity, combining Churchill–Chu or horizontal-plate natural convection with "
        "flat-plate forced convection [@Churchill1975;Incropera2007]" + (", as in ExoBEM (Section @sec:method). " if COMBINED else ":"))
    if not COMBINED:
        m.equation(r"h=\left(h_{n}^{3}+h_{f}^{3}\right)^{1/3},\qquad h_{n}=\frac{k}{L}Nu\left(Ra\right),\quad Ra=\frac{g\beta\Delta T L^{3}\rho^{2}c_{p}}{\mu k}",
                   label="mixed")
    m.para(
        ("Gas properties follow Sutherland-type fits. " if COMBINED else "with Sutherland-type gas properties. ") + "The sky/air split of the long-wave view, which on Earth sends part of the "
        "sky view to the air temperature, is set to send all of it to the sky; the ground view, which on Earth sees "
        "the outdoor air temperature, sees the regolith skin temperature; and surfaces in contact with the ground use "
        "the deep-regolith temperature. The Perez anisotropic sky model is replaced by an isotropic sky, since its "
        "coefficients were fitted to Earth air masses [@Perez1990]. Outdoor moisture exchange is switched off, and the "
        "sanity checks that stop a run when an outdoor or surface temperature falls below −100 °C are skipped.")

    m.heading("Interior convection", 2, label="intconv")
    m.para(
        "Inside, the default TARP correlation describes air at one atmosphere and 1 g [@Walton1983]. Natural "
        "convection scales roughly as (gρ²)^{1/3}, so at lunar gravity and 70.3 kPa TARP overestimates it by about "
        f"{AF['tarp_overestimate_moon']} times. Off-Earth, ExoBEM-Core applies the same mixed-convection correlation to the cabin gas "
        "(nitrogen and oxygen at the cabin pressure and oxygen fraction) with the body's gravity and the cabin air "
        "velocity as the forced component. The override is placed before the EnergyPlus Energy Management System "
        "override, so users can still set coefficients from EMS.")

    m.heading("Conduction and the start-up of regolith covers", 2, label="startup")
    m.para(
        "CTF and CondFD run unchanged on the Earth clock. Two things change. The CondFD lower node-temperature limit "
        "of −100 °C becomes −270 °C off-Earth. More importantly, the start-up procedure had to be reconsidered. "
        "EnergyPlus starts every wall at 23 °C and repeats the first day until zone temperatures and loads converge. "
        "That works for walls with time constants of hours to days but not for a metre of regolith, whose time "
        "constant is months on Mars and years on the Moon: the warm-up converges on the zone while the regolith is "
        "still far from its periodic state. Off-Earth, ExoBEM-Core starts each CondFD construction from its steady "
        "conduction profile between the period-mean outer-face temperature T̄_{o} and the initial inside temperature "
        "T_{in},")
    m.equation(r"T_{i}=\bar{T}_{o}+\left(T_{in}-\bar{T}_{o}\right)\frac{R_{i}}{R_{tot}},\qquad R_{i}=\sum_{j<i}\frac{\Delta x_{j}}{k_{j}\left(T_{j}\right)}",
               label="steady")
    m.para(
        "where the resistances follow each layer's temperature-dependent conductivity and are iterated six times. "
        "T̄_{o} solves the mean radiative–convective balance of the outer face under the generated environment "
        "(absorbed solar radiation, sky and ground long-wave exchange with T⁴-mean temperatures, and convection on "
        "Mars). At the end of warm-up the inside faces have reached their real temperature, so the profile is "
        "recomputed with that temperature and the difference is added to every node. The correction is zero at the "
        "outer face and does not disturb the daily cycle that warm-up has established there.")

    m.heading("Refusing what cannot be right", 2, label="refuse")
    m.para(
        "After input processing, a validator stops the run with a severe error if the input contains an object that "
        "needs outdoor air or Earth weather. In M1 the list covers infiltration and ventilation objects, outdoor-air "
        "controllers, mixers and nodes, air-cooled and evaporatively cooled equipment (DX coils, packaged terminal "
        "units, VRF, the electric EIR chiller), cooling towers, fluid coolers and evaporative coolers, "
        "combustion and wind generators, PVWatts, the Kiva foundation model, AirflowNetwork, DElight, design days and "
        "sizing. Each of these would otherwise run and return numbers. The list is deliberately conservative; items "
        "leave it as their physics is generalized.")


# =========================================================================== verification
def verif_earth(m):
    """Earth regression and unit tests (level-2)."""
    m.heading("Earth: identical results and unit tests", 2, label="earth")
    rows = [[f, c, r] for f, c, r in F["earth_regression"]["files"]]
    m.para(
        f"The first rule was tested directly. {N_EARTH} example files from the EnergyPlus distribution were run with an "
        "unmodified v26.2.0 build and with ExoBEM-Core, built with the same compiler (MSVC 14.44, release mode) and "
        f"the same weather file ({F['earth_regression']['weather']}), and every number of the complete output time "
        f"series was compared. The files were chosen to exercise every hook (Table @tab:earthreg): CTF and CondFD "
        "conduction with temperature-dependent conductivity, every convection path, ground contact, windows and "
        "daylighting, sizing and design days, VAV and DX systems, plant and chillers, PV and batteries, moisture "
        f"models, Kiva and solar collectors. All {N_EARTH} gave bit-for-bit identical results. A fifteenth file "
        "(HAMT_HourlyProfileReport) fails with this weather file in both builds and was excluded. The full EnergyPlus "
        f"unit-test suite ({UT['tests']:,} tests in {UT['suites']} suites) also passes on the fork with "
        f"{UT['failed']} failures.")
    m.table(["Example file", "Exercises", "Result"], rows,
            f"Earth regression: ExoBEM-Core versus unmodified EnergyPlus v26.2.0, full output time series "
            f"({F['earth_regression']['weather']}).", col_widths_cm=[6.5, 6.5, 2.5], font_size=8, label="earthreg")


def verif_cross(m):
    """Cross-verification against the Python ExoBEM (level-2 subsections)."""
    hb = F["habitat"]
    m.heading("Cross-verification against ExoBEM", 2, label="cross")
    m.para(
        "Off-Earth there is no measured building to compare with, so the engine was compared with an independent "
        "implementation of the same physics: the Python ExoBEM, whose terrestrial core agrees with EnergyPlus within "
        "0.7% and whose planetary models reproduce Mars24, Diviner, Appelbaum–Flood and MEDA reference data "
        f"{exo_ref()}. This is a comparative verification in the sense of Oberkampf and Roy [@Oberkampf2010]: "
        "agreement shows that the two codes solve the same equations correctly, not that the equations are right, "
        "which is the job of the reference-data checks.")
    m.para(
        f"Both programs simulated the ExoBEM case-study habitat: a horizontal cylinder of radius {hb['radius_m']:.0f} m "
        f"and length {hb['length_m']:.0f} m with {hb['facets']} shell facets, under {hb['cover_m']:.0f} m of regolith over "
        "MLI (Moon) or 20 mm of aerogel (Mars), with a cabin at "
        f"{hb['cabin_kPa']} kPa and {100*hb['o2']:.1f}% oxygen, constant internal gains of {hb['gains_W']:,.0f} W and ideal "
        f"loads holding {hb['setpoints_C'][0]}–{hb['setpoints_C'][1]} °C, at {hb['timestep_min']}-minute time steps. "
        "The Moon case is at the equator of Mare Tranquillitatis for two lunations from 1 January 2030; the Mars case "
        "is at Jezero crater for 31 Earth days from the same date. The two programs share no code. ExoBEM-Core generates its environment "
        "with the C++ port and solves conduction with CondFD, the regolith's k(T) and c_{p}(T) entered as standard "
        "temperature-dependent material tables; ExoBEM uses its own finite-volume solver with a stretched grid and "
        "solves surfaces and air simultaneously. One simplification was needed: CondFD cannot resolve the 4 mm "
        "aluminium pressure wall at this time step, so its heat capacity was lumped into the interior panel and its "
        "negligible resistance (3×10^{-5} m²K/W) dropped. Results are compared over the second lunation on the Moon "
        "and days 16–31 on Mars, after both start-up procedures have settled.")
    rows = [
        ["Sensible cooling, C++ / Python (kWh)", f"{CM['energy']['ep_cooling_kWh']:.1f} / {CM['energy']['py_cooling_kWh']:.1f} ({MOON_DIFF:+.2f}%)",
         f"{CR['energy']['ep_cooling_kWh']:.1f} / {CR['energy']['py_cooling_kWh']:.1f} ({MARS_DIFF:+.2f}%)"],
        ["Hourly cooling RMSE (W)", f"{CM['Qc']['rmse']:.1f}", f"{CR['Qc']['rmse']:.0f}"],
        ["Regolith surface temperature RMSE (K)", f"{CM['Tg']['rmse']:.2f} (range {CM['Tg']['ep_min']:.1f} to {CM['Tg']['ep_max']:.1f} °C)",
         f"{CR['Tg']['rmse']:.2f} (range {CR['Tg']['ep_min']:.1f} to {CR['Tg']['ep_max']:.1f} °C)"],
        ["Sky temperature RMSE (K)", f"{CM['Tsky']['rmse']:.2f}", f"{CR['Tsky']['rmse']:.2f}"],
        ["Direct normal irradiance R²", f"{CM['beam']['r2']:.4f}", f"{CR['beam']['r2']:.4f}"],
        ["Diffuse horizontal irradiance R²", "— (none)", f"{CR['dif']['r2']:.4f}"],
        ["Top facet outer-face temperature RMSE (K)", f"{CM['top']['rmse']:.2f}", f"{CR['top']['rmse']:.2f}"],
        ["Top facet inner-face temperature RMSE (K)", f"{CM['tin_top']['rmse']:.3f}", f"{CR['tin_top']['rmse']:.2f}"],
        ["Interior convection coefficient, C++ / Python (W/m²K)", f"{CM['hin_top']['ep_mean']:.2f} / {CM['hin_top']['py_mean']:.2f}",
         f"{CR['hin_top']['ep_mean']:.2f} / {CR['hin_top']['py_mean']:.2f}"],
        ["Exterior convection coefficient, C++ / Python (W/m²K)", "0 / 0",
         f"{CR['hout_top']['ep_mean']:.3f} / {CR['hout_top']['py_mean']:.3f}"],
    ]
    m.table(["Quantity (hourly values)", f"Moon, equator, 2nd lunation ({CM['energy']['hours']} h)",
             f"Mars, Jezero, days 16–31 ({CR['energy']['hours']} h)"], rows,
            "Agreement between ExoBEM-Core (C++) and ExoBEM (Python) for the regolith-shielded habitat.",
            col_widths_cm=[5.6, 5.2, 5.2], font_size=8, label="cross")
    m.para(
        "The environments agree closely (Fig. @fig:coreenv). The solar altitude follows the ephemeris over the whole "
        "lunation and over each sol, which confirms that the generalized hour angle with a daily fit is sufficient for "
        f"both bodies; direct irradiance has R² of {CM['beam']['r2']:.4f} on the Moon and {CR['beam']['r2']:.4f} on Mars. "
        f"The regolith surface temperature, from −179 to +114 °C on the Moon, agrees within {CM['Tg']['rmse']:.2f} K RMSE "
        f"and within {CR['Tg']['rmse']:.2f} K on Mars; the Martian sky temperature within {CR['Tsky']['rmse']:.2f} K. The "
        "residual differences come from evaluating the sun at the end of each time step (the EnergyPlus convention) "
        "rather than at its middle, and from the hourly averaging of sub-hourly values.")
    m.figure(FIG / "core_fig3_environment.png",
             "Environment generated by ExoBEM-Core (C++, dashed) and by ExoBEM (Python, solid) at the lunar equator over "
             "two lunations (left) and at Jezero crater over three Earth days (right): (a, b) solar altitude, (c, d) "
             "direct normal and diffuse horizontal irradiance, (e, f) regolith surface and sky temperatures.",
             16.0, label="coreenv")
    m.para(
        f"The habitat responses agree as well (Fig. @fig:coreresp, Table @tab:cross). On the Moon the cooling energy over the "
        f"second lunation differs by {MOON_DIFF:+.2f}% and the hourly cooling load by {CM['Qc']['rmse']:.1f} W RMSE; the "
        f"top facet's outer face, which follows the 290 K swing of the lunar day, agrees within {CM['top']['rmse']:.2f} K "
        f"and its inner face within {CM['tin_top']['rmse']:.3f} K. On Mars the cooling energy differs by {MARS_DIFF:+.2f}% "
        f"(hourly R² {CR['Qc']['r2']:.3f}) and the interior convection coefficients by 1%. Most of the Martian "
        "difference is a slowly decaying offset: the CO2-filled regolith cover conducts about twenty times better than "
        "lunar regolith, so the envelope exchanges about 1.3 kW with the environment and its deep layers are still "
        "drifting after a month in both codes, from different starting states (a pseudo-transient steady state in "
        "ExoBEM, the profile of Eq. (@eq:steady) in ExoBEM-Core). Differences in grid (CondFD's uniform nodes per layer "
        "versus a stretched grid) contribute as well.")
    m.figure(FIG / "core_fig4_response.png",
             "Habitat response in ExoBEM-Core (C++, dashed) and ExoBEM (Python, solid) at the lunar equator (left) and "
             "Jezero crater (right): (a, b) sensible cooling load, (c, d) outer-face and (e, f) inner-face temperature of "
             "the top shell facet. The shaded band is the comparison window; the C++ transient in the first day is "
             "discussed in Section @sec:startupres.", 16.0, label="coreresp")


def verif_startup(m):
    """Start-up ablation and the residual transient (level-2)."""
    rows = [[r[0].replace(" C ", " °C "), r[1] if r[1] is not None else "not run", r[2]] for r in F["startup_ablation"]["rows"]]
    m.heading("Start-up of regolith-covered walls", 2, label="startupres")
    m.para(
        "The start-up procedure turned out to matter more than any other choice in the port (Table @tab:startup). With "
        "the EnergyPlus default, walls at 23 °C and warm-up by repeating the first day, the Mars cooling load over the "
        "comparison period was 32% higher than in ExoBEM, because the inner part of the regolith cover was still "
        "releasing the heat of its unrealistically warm start. A steady linear profile with constant conductivities "
        "reduced the error to −2.5%, and the k(T)-aware profile of Eq. (@eq:steady) with the post-warm-up correction "
        f"to {MARS_DIFF:+.1f}% on Mars and {MOON_DIFF:+.2f}% on the Moon. The lesson applies beyond planetary habitats: "
        "any construction whose time constant exceeds the warm-up period, such as earth-sheltered walls or thick "
        "ground slabs, inherits its initial state for months.")
    m.table(["Start-up treatment of CondFD walls", "Moon cooling vs ExoBEM (%)", "Mars cooling vs ExoBEM (%)"], rows,
            "Effect of the wall start-up treatment on cooling energy over the comparison window.",
            col_widths_cm=[8.6, 3.6, 3.6], font_size=8, label="startup")
    m.para(
        "A short transient remains (Fig. @fig:coreresp): in the first day after warm-up, the ExoBEM-Core cooling load "
        "starts 0.4 kW (Mars) to 2.4 kW (Moon) high and decays within about a day, and the inner face of the shell "
        "starts 2 K (Mars) to 7 K (Moon) warm. The likely cause is that the post-warm-up correction is also added to the thin "
        "inner layers, which have already reached their real temperature during warm-up. Restricting the correction to "
        "layers deeper than the warm-up diffusion length is planned; the comparison windows exclude the transient.")


# =========================================================================== discussion
def tool_comparison(m):
    """Table comparing the two tools (level-2)."""
    m.heading("Re-implementation or engine modification?", 2, label="compare")
    rows = [
        ["Basis", "Re-implementation of the EnergyPlus heat-balance method", f"Fork of the EnergyPlus v{F['base_version']} engine"],
        ["Code", f"About {F['exobem_python_lines']:,} lines of Python (NumPy, SciPy)",
         f"{KLOC:,.0f} thousand lines of C++ reused; {DIFF['insertions']:,} added"],
        ["Conduction and solution", "Finite volumes on stretched grids; surfaces and air solved simultaneously",
         "EnergyPlus CTF or CondFD; iterative surface and air balances"],
        ["Scope", "Single zone, ideal loads; radiator, heat pump, PV and storage as post-processors",
         "All engine features that do not need outdoor air: multi-zone, HVAC and plant, controls, EMS, outputs; "
         "radiator component planned"],
        ["Time base", "Sol clock on Mars; Earth clock on the Moon", "Earth clock on both (sol clock planned)"],
        ["Input", "Python objects or JSON", "Standard IDF or epJSON plus Site:PlanetaryBody"],
        ["Earth verification", "ASHRAE 140 opaque cases vs EnergyPlus 23.2: annual loads within 0.7%",
         f"Bit-for-bit identical to v{F['base_version']} on {N_EARTH} files; {UT['tests']:,} unit tests pass"],
        ["Planetary verification", "Mars24, Diviner, Appelbaum–Flood, MEDA reference data",
         f"Against ExoBEM: cooling within {abs(MOON_DIFF):.2f}% (Moon) and {abs(MARS_DIFF):.1f}% (Mars)"],
        ["Run time, habitat case", f"{RT['python_moon']} s (Moon, {RT['moon_days']} d); {RT['python_mars']} s (Mars, {RT['mars_days']} d)",
         f"{RT['moon']} s (Moon); {RT['mars']} s (Mars)"],
        ["Best use", "Early design, parametric studies, teaching, independent reference",
         "Detailed design with EnergyPlus workflows, multi-zone habitats and systems"],
    ]
    m.table(["Aspect", "ExoBEM (Python)", "ExoBEM-Core (C++)"], rows,
            "The two tools compared. Run times are for 3-minute time steps on the same computer, single thread.",
            col_widths_cm=[3.0, 6.4, 6.6], font_size=7.5, label="compare")
    m.para(
        "Table @tab:compare compares the two routes. The re-implementation was the faster way to get the physics "
        "right: every planetary model in ExoBEM-Core is a port of an ExoBEM model that had already been checked against "
        "reference data, and having an independent code made it possible to find the start-up problem, which a "
        "single code would have hidden. The engine fork is the way to use that physics in practice. It inherits "
        "multi-zone air balances, HVAC and plant loops, controls, electric systems and reporting, and it runs the "
        "habitat cases faster than the Python code. The two are therefore complementary rather than competing: ExoBEM "
        "is the reference and the sandbox, ExoBEM-Core the engine.")


def limitations_core(m, title="Limitations"):
    """Limitations of ExoBEM-Core M1 (level-2)."""
    m.heading(title, 2, label="limcore")
    m.bullets([
        "**Earth clock on Mars.** Hours are 3600 s, so the Martian day drifts by about 40 minutes per Earth day against the clock. Physics is right, but schedules cannot follow local solar time.",
        "**Placeholder weather file.** A weather file is still read for the calendar and the site; runs without one, and planetary design days and sizing, are planned.",
        "**Windows, radiators and PV.** Fenestration, a space-radiator plant component and PV in vacuum are not yet available; heat rejection is represented by ideal loads.",
        "**Cabin gas.** Psychrometrics use moist air at cabin pressure; a gas-mixture block for other cabin atmospheres is planned.",
        "**Gravity.** Body gravity is used in the new convection correlations only; window gaps, airflow networks and stack effects are refused or still use 9.81 m/s².",
        "**Thin metal layers.** CondFD cannot resolve millimetre aluminium shells at minute time steps, so they must be lumped or modelled with CTF.",
        "**Start-up transient.** About a day of residual transient follows warm-up (Section @sec:startupres).",
        "**Verification scope.** Off-Earth verification is comparative (two codes, one habitat type); empirical data from thermal-vacuum tests or analog habitats are still needed.",
    ])


def roadmap_core(m):
    """Roadmap M2/M3 and upstreaming (level-2)."""
    m.heading("Roadmap", 2, label="roadmap")
    m.para(
        "The audit provides the work list for the next milestones. M2 introduces a sol clock for Mars by making the "
        f"hour length a run-time variable: the audit identified the four lines that set the time-step lengths, the "
        f"{AF['rSecsInHour_physical']} physical uses of the hour constant that must follow it and the "
        f"{AF['rSecsInHour_units']} unit conversions that must not, and the change to the CTF generator's hour-based "
        "units. M2 also adds a cabin gas-mixture block for psychrometrics, body gravity in every buoyancy model, runs "
        "without a weather file and planetary design days. M3 adds a space-radiator plant component, modelled on the "
        "fluid cooler with a surface link like the flat-plate solar collector, a PV cell-temperature model for vacuum "
        "and windows with vacuum-compatible solvers. Because every change is gated on the planetary object and Earth "
        "results are unchanged, the planetary mode could in principle be offered upstream as an optional feature; "
        "until then it is maintained as a fork that tracks EnergyPlus releases.")
