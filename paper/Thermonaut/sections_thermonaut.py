"""Sections of the Thermonaut (C++ engine) manuscript.

Numbers are read from paper/Thermonaut/data/core_facts.json and paper/Thermonaut/data/core_summary.json
(written by paper/Thermonaut/extract_thermonaut_data.py from the Thermonaut repository and its verification runs).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIG = HERE / "figures"
sys.path.insert(0, str(ROOT / "paper" / "common"))
F = json.loads((HERE / "data" / "core_facts.json").read_text(encoding="utf-8-sig"))
S = json.loads((HERE / "data" / "core_summary.json").read_text(encoding="utf-8-sig"))
AF = F["audit_facts"]
DIFF = F["diff"]
UT = F["unit_tests"]
RT = F["run_time_s"]
CM = S["moon_equator"]["comparison"]              # engine reads the planetary weather file
CR = S["mars_jezero"]["comparison"]
CMg = S["moon_equator"]["comparison_generator"]   # engine generates its own environment
CRg = S["mars_jezero"]["comparison_generator"]
LH = S["lunar_habitat"]
LHF = F["lunar_habitat"]
PV = S["pv_vacuum"]
HZ, BC, MR = S["horizons"], S["boundary"], S["moon_regolith"]
N_FIND = sum(a["P0"] + a["P1"] + a["P2"] for a in F["audit"]["areas"])
N_P0 = sum(a["P0"] for a in F["audit"]["areas"])
N_P1 = sum(a["P1"] for a in F["audit"]["areas"])
N_P2 = sum(a["P2"] for a in F["audit"]["areas"])
N_EARTH = len(F["earth_regression"]["files"])
KLOC = F["source_lines_cc_hh"] / 1000
ENGINE_SHARE = 100 * DIFF["insertions"] / F["source_lines_cc_hh"]


def dpct(c):
    e = c["energy"]
    return 100 * (e["ep_cooling_kWh"] / e["py_cooling_kWh"] - 1)


MOON_DIFF, MARS_DIFF = dpct(CM), dpct(CR)          # PWF mode (headline)
MOON_DIFF_G, MARS_DIFF_G = dpct(CMg), dpct(CRg)    # generator mode
HAB_S = LH["energy"]["sensible_diff_pct"]
HAB_L = LH["energy"]["latent_diff_pct"]

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
        "pressure for convection and psychrometrics, and Earth sky and ground models, and the EPW range checks alter "
        "values outside Earth's range. The second route builds a new model. Ross developed a semi-empirical habitat "
        "heat balance [@Ross2022], and the separately developed ExoBEM tool re-implements the EnergyPlus heat-balance method in "
        f"about {F['exobem_python_lines']:,} lines of Python with planetary physics throughout [@ZhangExoBEM]. A "
        "re-implementation can be verified quickly, but it leaves out most of what makes EnergyPlus useful for design: "
        "multi-zone HVAC and plant, controls, electric systems, a large and tested input and output ecosystem "
        "(OpenStudio and its measures [@Guglielmetti2011]), and decades of comparative testing [@ASHRAE140].")
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
        "is therefore named Thermonaut, keeps the original license and copyright notices, states in its README that "
        "it is not EnergyPlus and is not endorsed by DOE or the National Laboratory of the Rockies (formerly NREL), "
        "and is published as a separate repository with the upstream history intact [@ThermonautRepo].")


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
        "implementation. The six reports are published with the code [@ThermonautRepo].")

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
         "Lunar-day 120 °C and Martian 700 Pa silently altered", "Planetary weather file read directly; values set after the EPW read"],
        ["Sun", "Declination and equation of time from Earth Fourier fits (two copies); hour angle 15°/h",
         "Wrong sun on any other body", "Daily fit to Mars24 / lunar ephemeris; body hour-angle rate"],
        ["Sky", "Perez diffuse model (1353 W/m², Earth air mass); part of the sky long-wave view sees air",
         "No basis in vacuum or dusty CO2", "Isotropic diffuse; all sky long-wave to the sky"],
        ["Ground", f"Ground long-wave temperature = outdoor air at {AF['ground_lw_equals_air_sites']} sites; monthly ground temperatures",
         "No air on the Moon; regolith swings 290 K", "Regolith skin and deep temperatures from a 1-D column in periodic equilibrium"],
        ["Pressure", f"One pressure, OutBaroPress, for zone, HVAC and outdoor air ({AF['OutBaroPress_uses']} uses in "
         f"{AF['OutBaroPress_files']} files)", "Moon (0 Pa): zero air capacity, NaN humidity, one psychrometric routine never "
         "returns; Mars: 0.7% of the cabin's thermal mass", "OutBaroPress carries the cabin pressure; new AmbientBaroPress"],
        ["Convection", "Every exterior correlation assumes air at 1 atm and 1 g, with a non-zero floor; TARP inside",
         f"Heat loss to air that does not exist; cabin convection overestimated about {AF['tarp_overestimate_moon']}× on the Moon",
         "Zero (Moon) or CO2 mixed convection (Mars) outside; physical correlation inside"],
        ["Conduction", "CondFD clamps nodes at −100 °C; walls start at 23 °C and warm up by repeating day 1",
         "Lunar-night surfaces near −180 °C; regolith time constants of months to years", "−270 °C limit; steady start-up profile"],
        ["PV and storage", "Cell temperature from NOCT or Sandia fits for Earth air and wind; storage heat to outdoor air",
         "Modules in vacuum cool only by radiation", "One-diode PV with a vacuum or CO2 cell energy balance; batteries must sit in a zone"],
        ["HVAC and plant", f"Heat rejection to outdoor air; {AF['OutBaroPress_hvac_uses']} OutBaroPress and "
         f"{AF['StdRhoAir_uses']} StdRhoAir uses in HVAC and plant", "Cooling towers, air-cooled condensers and outdoor-air "
         "systems meaningless in vacuum", "Refused with an error; space radiator planned"],
        ["Windows", f"{AF['window_solvers']} thermal solvers, each with its own Earth gas and pressure constants",
         "Interior film at outdoor pressure gives the floor value or NaN", "Not yet supported"],
    ]
    m.table(["Area", "Earth assumption in the v26.2 code", "Effect off-Earth", "Thermonaut M2"], rows,
            "Representative Earth assumptions found by the audit and their treatment in Thermonaut.",
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
        "ground temperature, in the PV cell temperature and in the moisture balance.")


# =========================================================================== design
def factor_table_core(m):
    """The Earth / Moon / Mars factors and how Thermonaut treats each one (shared list with ExoBEM)."""
    from factors import FACTORS
    rows, cat = [], None
    for c, fac, earth, moon, mars, _exo, core in FACTORS:
        if c != cat:
            rows.append([f"**{c}**", "", "", "", ""])
            cat = c
        rows.append([fac, earth, moon, mars, core])
    m.table(["Factor", "Earth", "Moon", "Mars", "Treatment in Thermonaut"], rows,
            "Factors that distinguish a lunar or Martian habitat from an Earth building, and how Thermonaut treats each "
            "one. modelled: physics implemented and verified; input: a parameter with a documented default; enforced or "
            "refused: contradicting input stops the run; neglected: left out, with the reason. The same list, with the "
            "ExoBEM column, is in the ExoBEM paper and in the documentation.",
            col_widths_cm=[2.9, 2.6, 3.4, 3.2, 3.9], font_size=7.0, label="factors")


def design(m):
    """Planetary mode: rules, factors, coordination, input, PWF, time and sun, environment, pressure, boundaries,
    start-up, PV, validator (level-2)."""
    m.heading("Design rules", 2, label="rules")
    m.para("Three rules guided every change (Fig. @fig:hooks):")
    m.bullets([
        "**Earth stays bit-for-bit.** Planetary mode is active only when the input contains a Site:PlanetaryBody object "
        "with Body = Moon or Mars. Every change is either behind that switch or replaces a literal by a variable whose "
        "Earth value is the same literal, so that IEEE floating-point results on Earth do not change.",
        "**Reuse, do not rewrite.** Planetary values are injected where EnergyPlus already reads its environment "
        "(weather arrays, sun direction, ground temperature, exterior and interior coefficients, PV cell temperature). "
        "The heat balance, conduction solvers, shading, view factors, ideal loads, electric load centre and reporting "
        "run unchanged.",
        "**Refuse what cannot be right.** Objects that need outdoor air or Earth weather stop the run with an error off-Earth "
        "instead of producing a plausible-looking wrong answer.",
    ])
    m.para(
        f"The result is small. The current version (M2d) adds {DIFF['insertions']:,} lines and changes {DIFF['deletions']} in "
        f"{DIFF['files']} files: a new PlanetaryBody module ({DIFF['new_module_lines']:,} lines), the input-object "
        f"definition ({DIFF['idd_lines']} lines) and about {DIFF['hook_lines_existing_files']} lines of hooks in "
        f"{DIFF['existing_files_touched']} existing files, which is {ENGINE_SHARE:.1f}% of the engine. M1 introduced the "
        "planetary environment and boundaries; M2 added planetary weather files with no EPW, PV in vacuum, batteries, "
        "the regolith periodic equilibrium and corrections from an independent review of the equations; M2c "
        "recalibrated the Martian sky long-wave to the 2018 dust storm; and M2d replaced the start-up correction of "
        "regolith-covered walls (Section @sec:startup).")
    m.figure(FIG / "core_fig1_hooks.png",
             "Where Thermonaut enters the EnergyPlus engine. Grey: unchanged EnergyPlus stages and the source files that "
             "carry the hooks; orange: what the hook does off-Earth. The new PlanetaryBody module supplies ephemerides, "
             "the environment (from a planetary weather file or its own generator), regolith temperatures, gas "
             "properties and the PV cell temperature.", 16.0, label="hooks")

    m.heading("What differs off-Earth", 2, label="factorsec")
    m.para(
        "Before changing code, the physical differences between an Earth building and a sealed habitat on the Moon or "
        "Mars were listed in one place (Table @tab:factors). The list is shared with ExoBEM and its documentation so the "
        "tools cannot drift apart. Most items are handled in the engine; a few are inputs, some are enforced by refusing "
        "objects, and a few are neglected with a stated reason. The most important enforced item is outdoor air: a "
        "habitat is a sealed pressure vessel, so infiltration, ventilation, economizers and outdoor-air systems are "
        "zero by construction and any such object stops the run (Section @sec:refuse). Gas lost through leakage and "
        "airlock cycles is real, but its make-up energy is below 1 W for the cases here; ExoBEM reports it.")
    factor_table_core(m)

    m.heading("How a planetary run is coordinated", 2, label="coord")
    m.para(
        "Thermonaut does not add a second simulation loop. The planetary module is called from the same places where "
        "EnergyPlus reads its environment, in this order:")
    m.bullets([
        "**Input.** When the input is read, Site:PlanetaryBody sets the body, the gravity and the cabin pressure, which "
        "from then on is stored in OutBaroPress together with the standard air density at that pressure. If a planetary "
        "weather file is named, it is read and checked, and a calendar-only EPW file is written to the output folder so "
        "that the run-period and day bookkeeping of the weather manager works unchanged.",
        "**Validation.** After all objects are read, a validator stops the run if any object needs outdoor air or Earth "
        "weather (Section @sec:refuse).",
        "**Environment.** Before the first day, the environment for the whole run period is either interpolated from the "
        "planetary weather file to the zone time step or produced by the internal generator. The regolith column is brought "
        "to periodic equilibrium and the deep-regolith temperature is stored for ground-contact surfaces.",
        "**Warm-up.** CondFD walls start from their steady conduction profile (Section @sec:startup); EnergyPlus then "
        "repeats the first day as usual, and the profile is corrected with the inside-face temperature reached.",
        "**Each day.** The weather manager reads the calendar day; the planetary module overwrites every weather value of "
        "that day and fits the declination and equation of time to the ephemeris. Shading is recomputed daily.",
        "**Each zone time step.** The engine computes the sun direction with the body's hour-angle rate, solves the "
        "outside-face balance with the planetary convection, sky and ground terms, conducts through the walls with CTF or "
        "CondFD, solves the inside faces with the cabin convection correlation, and updates the zone air and humidity "
        "balance at cabin pressure. The ideal-loads system meets the thermostat and humidistat; the electric load centre "
        "runs PV with the planetary cell temperature and the batteries; and seven planetary output variables are reported.",
    ])
    m.para(
        "Table @tab:eplus summarizes what is the same and what differs from EnergyPlus. The structure of the engine is "
        "untouched; what changes are the values that enter it at each of these points.")
    rows = [
        ["Simulation loop", "Run period, day, hour, zone and HVAC time steps", "Same; Earth clock (3600 s hours)", "same"],
        ["Weather input", "EPW, 8,760 hourly records, Earth range checks", "Planetary weather file (no EPW needed) or internal generator; values set after the read", "different"],
        ["Sun position", "Earth Fourier fits; 15°/h", "Daily fit to Mars24 or the lunar subsolar point; body's hour-angle rate", "adapted"],
        ["Sky and ground", "Perez diffuse; sky/air long-wave split; ground at air temperature", "Isotropic diffuse; all sky view to the sky; ground from the regolith column", "adapted"],
        ["Exterior convection", "TARP, DOE-2 and others with a non-zero floor", "Zero in vacuum; mixed convection in thin CO2 at body gravity", "different"],
        ["Conduction", "CTF or CondFD; walls start at 23 °C", "Same solvers; CondFD to −270 °C; steady k(T) start-up profile", "adapted"],
        ["Interior convection", "TARP (air, 1 atm, 1 g)", "Same physical correlation for the cabin gas at cabin pressure and body gravity", "adapted"],
        ["Zone air and moisture", "Air at outdoor pressure", "Same balances with OutBaroPress = cabin pressure", "same"],
        ["Outdoor air", "Infiltration, ventilation, OA systems", "Refused: sealed cabin", "different"],
        ["Loads and HVAC", "Ideal loads, HVAC and plant", "Ideal loads with humidistat; air- and water-cooled heat rejection refused", "adapted"],
        ["Electric power", "PV (simple, Sandia, one-diode, PVWatts), storage, generators", "Simple and one-diode PV with planetary cell temperature; storage (Li-ion in a zone)", "adapted"],
        ["Outputs", "ESO, SQLite, tabular reports", "Same, plus seven planetary output variables", "same"],
    ]
    m.table(["Element", "EnergyPlus v26.2", "Thermonaut planetary mode", "Relation"], rows,
            "Thermonaut compared with EnergyPlus, element by element. On Earth every element is identical to v26.2.",
            col_widths_cm=[2.8, 5.0, 6.4, 1.8], font_size=7.5, label="eplus")

    m.heading("Input", 2, label="input")
    m.para(
        "A single new object, Site:PlanetaryBody, selects the body (Earth, Moon or Mars), the clock, a reference year "
        "and the habitat parameters: gravity (by default the body's surface value: 1.625 m/s² on the Moon, 3.721 m/s² "
        "on Mars), cabin pressure and oxygen fraction (for example 70.3 kPa and 26.5%, or the 56.5 kPa and 34% "
        "exploration atmosphere [@EAWG2010]), cabin air velocity (0.15 m/s) and a convection length scale. Optional "
        "fields set the horizon elevation, the regolith thermal inertia, albedo, emissivity and spin-up cycles, the "
        "deep-regolith depth, and for Mars the mean surface pressure, the dust optical-depth model (seasonal climatology "
        "or constant, with an optional global storm defined by start and end solar longitude and peak optical depth) "
        "and the wind. The last field names a planetary weather file. Everything else in the input file is standard "
        "EnergyPlus input (Appendix A).")

    m.heading("Planetary weather files", 2, label="pwf")
    m.para(
        "EnergyPlus weather files cannot carry a planetary environment: they hold 8,760 Earth hours, their range checks "
        "alter lunar and Martian values, and they have no fields for a regolith temperature, a sky with no air, or a "
        "dust optical depth. Thermonaut therefore reads the Planetary Weather Format (PWF) defined with ExoBEM "
        f"{exo_ref()}: a CSV file with a header of key–value lines (body, site, start time, time step, solar-day length, "
        "gravity, atmosphere type, clock) and one record per time step. Each record gives the solar zenith and azimuth, "
        "the fraction of the solar disk above the horizon, direct normal, diffuse and global irradiance, the near-surface "
        "air temperature (empty in vacuum), the effective sky temperature, the regolith surface and deep temperatures, "
        "the ground albedo, the ambient pressure and the wind, with optional downwelling long-wave radiation, solar "
        "longitude and dust optical depth. Solar quantities refer to the middle of each interval and state quantities "
        "to its end.")
    m.para(
        "The engine checks that the file's body matches the input, that it covers the run period, and that every value "
        "is physical (no negative irradiance, no temperature below 0 K); it does not apply Earth ranges. Values are "
        "interpolated linearly to the zone time step. The solar position is still computed by the engine, so that "
        "shading and incidence angles use the same geometry as on Earth, and the file's irradiance is used for the "
        "magnitudes. Files are written by ExoBEM from its environment models and can be converted from other sources, "
        "such as the Mars Climate Database [@Millour2018] or rover data. With a PWF file the two tools see an identical "
        "environment, which separates environment differences from heat-balance differences in the verification "
        "(Section @sec:cross).")

    m.heading("Time base and sun position", 2, label="sun")
    m.para(
        "The audit showed that a planetary hour would touch about a hundred physical uses of the hour length and the "
        "CTF generator. Thermonaut therefore keeps the Earth clock: an hour is 3600 s and a day starts at 00:00 UTC, so "
        "that crew schedules, which follow Earth or mission time, are written as on Earth. What changes is the rate at which "
        "the Sun moves. EnergyPlus computes the hour angle in several places, all with the same expression; Thermonaut "
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
        "lunation. Near the horizon the visible fraction of the solar disk is the area fraction of a disk cut by a "
        "line, f = [acos(−x) + x√(1−x²)]/π with x the disk centre's height above the horizon in solar radii; on the "
        "Moon the Sun takes about an hour to rise.")

    m.heading("Planetary environment", 2, label="env")
    m.para(
        "Without a weather file, the environment comes from a generator that implements in C++ the same environment "
        f"models {exo_ref()} and is run for the whole run period before the simulation starts. On the Moon there is no "
        "diffuse light, the sky is at 2.725 K and the ground is a 1-D regolith column following Hayne et al. "
        "[@Hayne2017]. On Mars the total irradiance comes from a delta-Eddington two-stream solution with a seasonal dust "
        "optical depth and an optional global storm [@Joseph1976;Appelbaum1990]; the beam is the Beer-law attenuation "
        "of the solar disk, exp(−τm), and the rest of the total, including the forward-scattered peak, is diffuse. The "
        "pressure follows the seasonal CO2 cycle with its minimum near Ls 157° and its maximum near Ls 269°, the sky "
        "emits as an effective dusty-CO2 layer, and the near-surface air follows the ground with a lag. Seven new output "
        "variables report the planetary environment (ground surface and deep temperature, ambient pressure, downwelling "
        "long-wave radiation, Sun distance, solar longitude and dust optical depth). Values are set after the weather "
        "manager has read its day, so none of the EPW range checks found by the audit can alter them.")
    m.para(
        "The regolith column needs a starting state. A metre of regolith has a thermal time constant of years on the "
        "Moon, so spinning it up over a few lunations from a guess leaves the deep temperature wherever the guess put "
        "it. Both tools therefore bring the column to periodic equilibrium: they run a full year of forcing, take the "
        "period-mean temperature at the depth below which the daily wave has died out (0.15 m on the Moon, 0.25 m on "
        "Mars), rebuild the deeper profile so that it carries the geothermal flux with the local conductivity, and "
        "repeat until the deep temperature changes by less than 0.02 K. The result does not depend on the start date "
        "or the initial guess; at the lunar equator it gives −14.9 °C at 3 m.")

    m.heading("Cabin and ambient pressure", 2, label="pressure")
    m.para(
        "The single-pressure finding admits two fixes: add a cabin pressure and change the roughly 350 zone and HVAC "
        "uses of OutBaroPress, or let OutBaroPress carry the cabin pressure and change the outdoor uses. Thermonaut "
        "takes the second option. Off-Earth, OutBaroPress holds the cabin pressure, so the zone air balance, "
        "psychrometrics, ideal loads and every HVAC component see the air they actually contain, without edits; the "
        "standard pressure and density used for volume-to-mass conversions follow the cabin as well. A new variable, "
        "AmbientBaroPress, holds the real outdoor pressure (zero on the Moon, 600–800 Pa on Mars) and is used by the "
        "exterior convection model and the outputs. Almost all outdoor users of the old variable are outdoor-air "
        "systems, infiltration and heat rejection to air, and these are refused off-Earth (Section @sec:refuse), so the "
        "option leaves no silent outdoor use of the cabin pressure in a valid input. The zone moisture balance runs with "
        "moist-air psychrometrics at cabin pressure; at 26.5–34% oxygen the specific heat and gas constant differ from "
        f"air by less than {AF['cabin_psychrometric_error_pct']}%. The cabin-gas properties used for convection are "
        "mixed from nitrogen and oxygen by mass fraction.")

    m.heading("Exterior boundary", 2, label="extbc")
    m.para(
        "Off-Earth, the exterior convection coefficient is replaced. It is zero in vacuum, and the EnergyPlus lower "
        "limit on the coefficient is bypassed. On Mars, a physical mixed-convection correlation is used for CO2 at the "
        "ambient pressure and the body's gravity, combining Churchill–Chu or horizontal-plate natural convection with "
        "flat-plate forced convection [@Churchill1975;Incropera2007]:")
    m.equation(r"h=\left(h_{n}^{3}+h_{f}^{3}\right)^{1/3},\qquad h_{n}=\frac{k}{L}Nu\left(Ra\right),\quad Ra=\frac{g\beta\Delta T L^{3}\rho^{2}c_{p}}{\mu k}",
               label="mixed")
    m.para(
        "with Sutherland-type gas properties. The sky/air split of the long-wave view, which on Earth sends part of the "
        "sky view to the air temperature, is set to send all of it to the sky; the ground view, which on Earth sees "
        "the outdoor air temperature, sees the regolith skin temperature; and surfaces in contact with the ground use "
        "the deep-regolith temperature. The Perez anisotropic sky model is replaced by an isotropic sky, since its "
        "coefficients were fitted to Earth air masses [@Perez1990]. Outdoor moisture exchange is switched off, and the "
        "sanity checks that stop a run when an outdoor or surface temperature falls below −100 °C are skipped.")

    m.heading("Interior convection", 2, label="intconv")
    m.para(
        "Inside, the default TARP correlation describes air at one atmosphere and 1 g [@Walton1983]. Natural "
        "convection scales roughly as (gρ²)^{1/3}, so at lunar gravity and 70.3 kPa TARP overestimates it by about "
        f"{AF['tarp_overestimate_moon']} times. Off-Earth, Thermonaut applies the same mixed-convection correlation to the cabin gas "
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
        "still far from its periodic state. Off-Earth, Thermonaut starts each CondFD construction from its steady "
        "conduction profile between the period-mean outer-face temperature T̄_{o} and the initial inside temperature "
        "T_{in},")
    m.equation(r"T_{i}=\bar{T}_{o}+\left(T_{in}-\bar{T}_{o}\right)\frac{R_{i}}{R_{tot}},\qquad R_{i}=\sum_{j<i}\frac{\Delta x_{j}}{k_{j}\left(T_{j}\right)}",
               label="steady")
    m.para(
        "where the resistances follow each layer's temperature-dependent conductivity and are iterated six times. "
        "T̄_{o} solves the mean radiative–convective balance of the outer face under the planetary environment "
        "(absorbed solar radiation, sky and ground long-wave exchange with T⁴-mean temperatures, and convection on "
        "Mars). At the end of warm-up the inside faces have reached their real temperature, so the profile is "
        "recomputed with that temperature. The difference Δ_{i} between the two profiles is not added in full: the "
        "nodes near the inside face have already moved toward the real inside temperature during warm-up, and adding "
        "Δ_{i} to them as well overshoots (Section @sec:startupres). Node i therefore receives Δ_{i}(1 − g_{i}), where "
        "g_{i} is the fraction of a unit step of the inside-face temperature that has reached node i after the warm-up "
        "period t_{w}. It is obtained by integrating the construction's own node network implicitly over t_{w},")
    m.equation(r"C_{i}\frac{dg_{i}}{dt}=G_{i-1}\left(g_{i-1}-g_{i}\right)+G_{i}\left(g_{i+1}-g_{i}\right),\qquad g_{N}=1,\;g_{1}=0,\;g_{i}\left(0\right)=0",
               label="warmup")
    m.para(
        "with the conductances G = k/Δx and capacities C = ρc_{p}Δx exactly as CondFD discretizes the construction, "
        "the outer node held fixed and hourly steps. Because CondFD gives no-mass layers a near-zero capacity, an MLI "
        "blanket blocks the step as it should: the regolith behind it receives the full correction and the panel inside "
        "it none. A simpler weighting by diffusion depth, erf(ξ/2√t_{w}), was tried first and rejected because it "
        "treats a no-mass MLI layer as transparent. The correction is zero at the outer face and does not disturb the "
        "daily cycle that warm-up has established there. Thin, light envelopes such as an MLI shell need none of this "
        "and are best run with CTF.")

    m.heading("Photovoltaics and storage", 2, label="pvsec")
    m.para(
        "Power is part of the habitat's energy balance, and the audit found that every EnergyPlus PV cell-temperature "
        "model assumes Earth air: the NOCT form of the one-diode model, the Sandia fits and PVWatts all cool the module "
        "by convection to air and wind. In vacuum a module cools only by radiation from both faces. Off-Earth, Thermonaut "
        "computes the cell temperature of the equivalent one-diode model [@EPlus262] in its Decoupled mode from the "
        "steady energy balance of a thin module,")
    m.equation(r"\left(\tau\alpha-\eta\right)G=\varepsilon_{f}\sigma\left(T^{4}-T_{f}^{4}\right)+\varepsilon_{b}\sigma\left(T^{4}-T_{b}^{4}\right)+2h\left(T-T_{a}\right)",
               label="pvcell")
    m.para(
        "where G is the plane-of-array irradiance, η the electrical efficiency, ε_{f} = ε_{b} = 0.85 (constant), "
        "T_{f}⁴ and T_{b}⁴ the view-weighted fourth powers of the sky and regolith temperatures seen by the front and back "
        "faces, and h the mixed-convection coefficient of Eq. (@eq:mixed) on Mars (zero on the Moon). The balance is "
        "solved by Newton iteration inside the engine's existing efficiency loop, which restarts every time step and is "
        "repeated until η changes by less than 0.1%. No value is carried over from the previous step, so rapid changes "
        "of insolation, such as sunrise over a Martian horizon, cannot destabilize it; the price is that the steady "
        "balance ignores the module's heat capacity, which matters only for minutes. The simple PV model, which has no cell "
        "temperature, and the integrated mode, which takes the cell temperature from the planetary surface heat "
        "balance, run unchanged. Storage objects run unchanged as well, except that the Li-ion battery model, whose "
        "thermal model otherwise uses the outdoor air temperature, must be placed in a zone, so that its losses become "
        "cabin heat. Regenerative fuel cells and fission power have no planetary counterpart in the engine yet.")

    m.heading("Refusing what cannot be right", 2, label="refuse")
    m.para(
        "After input processing, a validator stops the run with a severe error if the input contains an object that "
        "needs outdoor air or Earth weather. The list covers infiltration and ventilation objects, outdoor-air "
        "controllers, mixers and nodes, air-cooled and evaporatively cooled equipment (DX coils, packaged terminal "
        "units, VRF, the electric EIR chiller), cooling towers, fluid coolers and evaporative coolers, combustion and "
        "wind generators, PVWatts, the Sandia PV model in Decoupled mode and the dynamic (Ulleberg) cell model, Li-ion "
        "batteries without a zone, the Kiva foundation model, AirflowNetwork, DElight, design days and sizing. Each of these "
        "would otherwise run and return numbers. The list is deliberately conservative; items leave it as their physics "
        "is generalized.")


# =========================================================================== verification
def verif_earth(m):
    """Earth regression and unit tests (level-2)."""
    m.heading("Earth: identical results and unit tests", 2, label="earth")
    rows = [[f, c, r] for f, c, r in F["earth_regression"]["files"]]
    m.para(
        f"The first rule was tested directly. {N_EARTH} example files from the EnergyPlus distribution were run with an "
        "unmodified v26.2.0 build and with Thermonaut, built with the same compiler (MSVC 14.44, release mode) and "
        f"the same weather file ({F['earth_regression']['weather']}), and every number of the complete output time "
        f"series was compared. The files were chosen to exercise every hook (Table @tab:earthreg): CTF and CondFD "
        "conduction with temperature-dependent conductivity, every convection path, ground contact, windows and "
        "daylighting, sizing and design days, VAV and DX systems, plant and chillers, PV and batteries, moisture "
        f"models, Kiva and solar collectors. All {N_EARTH} gave bit-for-bit identical results after every patch set, "
        "including the weather-file and PV hooks of M2 and the changes of M2c–M2d. A fifteenth file (HAMT_HourlyProfileReport) fails with this "
        "weather file in both builds and was excluded. The full EnergyPlus unit-test suite "
        f"({UT['tests']:,} tests in {UT['suites']} suites) also passes on the fork with {UT['failed']} failures.")
    m.table(["Example file", "Exercises", "Result"], rows,
            f"Earth regression: Thermonaut versus unmodified EnergyPlus v26.2.0, full output time series "
            f"({F['earth_regression']['weather']}).", col_widths_cm=[6.5, 6.5, 2.5], font_size=8, label="earthreg")


def verif_independent(m):
    """Checks against independent references and closed-form balances (level-2)."""
    hm, hr = HZ["moon_equator"], HZ["mars_jezero"]
    mv, mc = BC["moon_vacuum"], BC["mars_convection"]
    m.heading("Off-Earth checks against independent references", 2, label="indep")
    m.para(
        "Off-Earth there is no measured building to compare with. The engine's planetary parts were therefore checked "
        "against references that share nothing with this work (Table @tab:indep): an independent ephemeris for the "
        "Sun, orbital measurements of the lunar regolith, closed-form solutions of the exterior boundary and tabulated "
        "gas properties.")
    rows = [
        ["Solar altitude, Moon equator (59 days)", "JPL Horizons [@Horizons]",
         f"RMSE {hm['rmse_all_deg']:.2f}°; sunlit hours {hm['sunrise_hours_engine']} vs {hm['sunrise_hours_horizons']}"],
        ["Solar altitude, Mars Jezero (31 days)", "JPL Horizons [@Horizons]",
         f"RMSE {hr['rmse_all_deg']:.2f}° (sunlit {hr['rmse_sunlit_deg']:.2f}°, bias {hr['bias_sunlit_deg']:+.2f}°); sunlit hours {hr['sunrise_hours_engine']} vs {hr['sunrise_hours_horizons']}"],
        ["Lunar equatorial regolith surface, noon / pre-dawn", "≈385–390 K / ≈95 K (Diviner) [@Vasavada2012;Hayne2017]",
         f"{MR['Tg_max_K']:.0f} K / {MR['Tg_min_K']:.0f} K"],
        ["Lunar regolith at depth", "≈252–256 K near 1 m (Apollo, Diviner) [@Vasavada2012]",
         f"{MR['T_deep_3m_K']:.0f} K at 3 m (geothermal gradient ≈ 2 K/m)"],
        ["Convection in vacuum (every outer face, 3-min steps)", "Exactly zero", f"Maximum |q| {mv['max_abs_convection_W_m2']:.0f} W/m² over {mv['steps']:,} face-steps"],
        ["Net long-wave on outer faces in vacuum", "εσ[F_{sky}(T_{sky}⁴ − T⁴) + F_{g}(T_{g}⁴ − T⁴)]",
         f"RMSE {mv['lw_residual_rmse_W_m2']:.2f} W/m² (mean magnitude {mv['lw_mean_abs_W_m2']:.0f} W/m²); 99% of steps within {mv['lw_residual_p99_W_m2']:.2f} W/m²"],
        ["Outer-face energy balance in vacuum", "Solar + long-wave + convection + conduction = 0", f"Closes to rounding (RMSE {mv['balance_residual_rmse_W_m2']:.1g} W/m²)"],
        ["Exterior convection on Mars (top facet)", "Same correlations with NIST CO2 properties at 700 Pa [@NISTWebBook]",
         f"{mc['rel_diff_mean_pct']:+.1f}% (RMSE {mc['rel_diff_rmse_pct']:.1f}%) over {mc['steps_used']:,} steps"],
    ]
    m.table(["Quantity", "Independent reference", "Thermonaut"], rows,
            "Off-Earth checks of Thermonaut against independent references and closed-form balances.",
            col_widths_cm=[4.6, 5.4, 6.0], font_size=7.5, label="indep")
    m.para(
        f"The sun follows the Horizons ephemeris within {hm['rmse_all_deg']:.2f}° on the Moon and {hr['rmse_all_deg']:.2f}° on "
        "Mars, which confirms the generalized hour angle and the daily fit independently of any code written for this "
        "work; the Martian bias is the EnergyPlus convention of evaluating the sun at the end of each 3-minute step, "
        "during which the Sun moves by 0.7°. The engine's own regolith column reproduces the Diviner noon and pre-dawn "
        "temperatures. In vacuum the exterior boundary satisfies its defining equations: there is no convection, the "
        "long-wave exchange is the closed-form expression with all of the sky view at the sky temperature and the "
        "ground view at the regolith temperature, and the face balance closes. The few larger long-wave residuals, "
        "13–22 of 14,400 steps per wall, occur in the single step in which sunlight reaches or leaves a wall and its "
        "temperature jumps by 30–37 K; EnergyPlus linearizes the long-wave term about the previous step's temperature, "
        "on Earth as here. On Mars the exterior convection coefficient agrees within 2% with a calculation that uses "
        "measured CO2 properties instead of the engine's property fits. With the PV cell balance of Section @sec:pvver, "
        "these checks cover the parts of the engine that the port changed; what they cannot cover is the behaviour of a "
        "whole habitat, for which no measurements exist.")


def verif_cross(m):
    """Cross-verification against the Python ExoBEM: regolith-shielded module (level-2)."""
    hb = F["habitat"]
    m.heading("Code-to-code check against ExoBEM: regolith-shielded module", 2, label="cross")
    m.para(
        "The whole habitat response was then compared with a second, separately written implementation of the same "
        "physics: the Python ExoBEM, whose terrestrial core agrees with EnergyPlus within "
        "0.7% and whose planetary models reproduce Mars24, Diviner, Appelbaum–Flood and MEDA reference data "
        f"{exo_ref()}. This is a comparative verification in the sense of Oberkampf and Roy [@Oberkampf2010]: "
        "it is a code-to-code check. Agreement shows that the two codes solve the same equations, with different "
        "conduction solvers, grids and start-up procedures, not that the equations are right, which is the job of "
        "Section @sec:indep and of ExoBEM's reference-data checks. The two programs share no code. Two habitats were used: a "
        "regolith-shielded module that exercises the regolith, the start-up and the Martian atmosphere, and a "
        "NASA-class surface habitat that exercises a light envelope, crew moisture and humidity control (Section "
        "@sec:habver). Fig. @fig:habitats shows both.")
    m.figure(FIG / "core_fig5_habitats.png",
             "The two verification habitats, drawn from the vertices written to the input files: (a) the regolith-shielded "
             "module of Section @sec:cross and (b) the NASA-class four-crew lunar habitat of Section @sec:habver. (c, d) "
             "Habitat (b) at the lunar equator over 30 Earth days: sensible and latent cooling and outer-face temperatures "
             "of the south wall and the floor, ExoBEM (solid) and Thermonaut (dashed).", 16.0, label="habitats")
    m.para(
        f"The module is a horizontal cylinder of radius {hb['radius_m']:.0f} m and length {hb['length_m']:.0f} m with "
        f"{hb['facets']} shell facets, under {hb['cover_m']:.0f} m of regolith over MLI (Moon) or 20 mm of aerogel "
        f"(Mars), with a cabin at {hb['cabin_kPa']} kPa and {100*hb['o2']:.1f}% oxygen, constant internal gains of "
        f"{hb['gains_W']:,.0f} W and ideal loads holding {hb['setpoints_C'][0]}–{hb['setpoints_C'][1]} °C, at "
        f"{hb['timestep_min']}-minute time steps. The Moon case is at the equator of Mare Tranquillitatis for two "
        "lunations from 1 January 2030; the Mars case is at Jezero crater for 31 Earth days from the same date. "
        "Thermonaut solves conduction with CondFD, the regolith's k(T) and c_{p}(T) entered as standard "
        "temperature-dependent material tables; ExoBEM uses its own finite-volume solver with a stretched grid, planar "
        "layers as in the engine, and solves surfaces and air simultaneously. One simplification was needed: CondFD "
        "cannot resolve the 4 mm aluminium pressure wall at this time step, so its heat capacity was lumped into the "
        "interior panel and its negligible resistance (3×10^{-5} m²K/W) dropped.")
    m.para(
        "Thermonaut was run twice: with its own environment generator, which tests the C++ port of the environment "
        "models, and reading the PWF file that ExoBEM wrote for its own run, which gives both codes the same "
        "environment and isolates the heat balance. Results are compared over the second lunation on the Moon and "
        "days 16–31 on Mars, after both start-up procedures have settled (Table @tab:cross).")
    rows = [
        ["Sensible cooling, C++ / Python (kWh)",
         f"{CMg['energy']['ep_cooling_kWh']:.1f} / {CM['energy']['ep_cooling_kWh']:.1f} / {CM['energy']['py_cooling_kWh']:.1f}",
         f"{CRg['energy']['ep_cooling_kWh']:.1f} / {CR['energy']['ep_cooling_kWh']:.1f} / {CR['energy']['py_cooling_kWh']:.1f}"],
        ["Cooling difference vs ExoBEM (%)", f"{MOON_DIFF_G:+.2f} / {MOON_DIFF:+.2f}", f"{MARS_DIFF_G:+.2f} / {MARS_DIFF:+.2f}"],
        ["Hourly cooling RMSE (W)", f"{CMg['Qc']['rmse']:.1f} / {CM['Qc']['rmse']:.1f}", f"{CRg['Qc']['rmse']:.0f} / {CR['Qc']['rmse']:.0f}"],
        ["Regolith surface temperature RMSE (K)", f"{CMg['Tg']['rmse']:.2f} / {CM['Tg']['rmse']:.3f}",
         f"{CRg['Tg']['rmse']:.2f} / {CR['Tg']['rmse']:.3f}"],
        ["Sky temperature RMSE (K)", "0 (2.725 K)", f"{CRg['Tsky']['rmse']:.2f} / {CR['Tsky']['rmse']:.3f}"],
        ["Deep regolith temperature, C++ / Python (°C)", f"{CMg['Tdeep']['ep_mean']:.2f} / {CMg['Tdeep']['py_mean']:.2f}",
         f"{CRg['Tdeep']['ep_mean']:.2f} / {CRg['Tdeep']['py_mean']:.2f}"],
        ["Direct normal irradiance R²", f"{CMg['beam']['r2']:.4f}", f"{CRg['beam']['r2']:.4f}"],
        ["Diffuse horizontal irradiance R²", "— (none)", f"{CRg['dif']['r2']:.4f}"],
        ["Top facet outer-face temperature RMSE (K)", f"{CMg['top']['rmse']:.2f} / {CM['top']['rmse']:.2f}",
         f"{CRg['top']['rmse']:.2f} / {CR['top']['rmse']:.2f}"],
        ["Top facet inner-face temperature RMSE (K)", f"{CMg['tin_top']['rmse']:.3f} / {CM['tin_top']['rmse']:.3f}",
         f"{CRg['tin_top']['rmse']:.2f} / {CR['tin_top']['rmse']:.2f}"],
        ["Interior convection coefficient, C++ / Python (W/m²K)", f"{CM['hin_top']['ep_mean']:.2f} / {CM['hin_top']['py_mean']:.2f}",
         f"{CR['hin_top']['ep_mean']:.2f} / {CR['hin_top']['py_mean']:.2f}"],
        ["Exterior convection coefficient, C++ / Python (W/m²K)", "0 / 0",
         f"{CR['hout_top']['ep_mean']:.3f} / {CR['hout_top']['py_mean']:.3f}"],
    ]
    m.table(["Quantity (hourly values)", f"Moon, equator, 2nd lunation ({CM['energy']['hours']} h)",
             f"Mars, Jezero, days 16–31 ({CR['energy']['hours']} h)"], rows,
            "Agreement between Thermonaut (C++) and ExoBEM (Python) for the regolith-shielded module. Pairs a / b give "
            "Thermonaut with its own generator / reading the PWF file; the first row gives generator / PWF / ExoBEM.",
            col_widths_cm=[5.6, 5.2, 5.2], font_size=8, label="cross")
    m.para(
        "The generated environments agree closely (Fig. @fig:coreenv). The solar altitude follows the ephemeris over the "
        "whole lunation and over each sol, which confirms that the generalized hour angle with a daily fit is sufficient "
        f"for both bodies; direct irradiance has R² of {CMg['beam']['r2']:.4f} on the Moon and {CRg['beam']['r2']:.4f} on "
        f"Mars. The regolith surface temperature, from {CMg['Tg']['ep_min']:.0f} to +{CMg['Tg']['ep_max']:.0f} °C on the "
        f"Moon, agrees within {CMg['Tg']['rmse']:.2f} K RMSE and within {CRg['Tg']['rmse']:.2f} K on Mars, and the deep "
        "regolith temperatures from the periodic equilibrium are the same to 0.01 K. The residual differences come from "
        "evaluating the sun at the end of each time step (the EnergyPlus convention) rather than at its middle, and from "
        "the hourly averaging of sub-hourly values.")
    m.figure(FIG / "core_fig3_environment.png",
             "Environment generated by Thermonaut (C++, dashed) and by ExoBEM (Python, solid) at the lunar equator over "
             "two lunations (left) and at Jezero crater over three Earth days (right): (a, b) solar altitude, (c, d) "
             "direct normal and diffuse horizontal irradiance, (e, f) regolith surface and sky temperatures.",
             16.0, label="coreenv")
    m.para(
        f"The habitat responses agree as well (Fig. @fig:coreresp). On the Moon the cooling energy over the second "
        f"lunation differs by {MOON_DIFF:+.2f}% and the hourly cooling load by {CM['Qc']['rmse']:.1f} W RMSE; the top "
        f"facet's outer face, which follows the 290 K swing of the lunar day, agrees within {CM['top']['rmse']:.2f} K "
        f"and its inner face within {CM['tin_top']['rmse']:.3f} K. On Mars the cooling energy differs by "
        f"{MARS_DIFF_G:+.2f}% with the generator and {MARS_DIFF:+.2f}% with the PWF file, and the interior convection "
        "coefficients by 1%. Because the PWF run removes every environment difference and does not reduce the residual, "
        "the residual lies in the heat-balance solution, not in the environment. It is a slowly decaying offset: the "
        "CO2-filled regolith cover conducts about twenty times better than lunar regolith, so the envelope exchanges "
        "about 1.3 kW with the environment and its deep layers are still drifting after a month in both codes, from "
        "different starting states (a pseudo-transient steady state in ExoBEM, the profile of Eq. (@eq:steady) in "
        "Thermonaut). Differences in grid (CondFD's uniform nodes per layer versus a stretched grid) contribute as well.")
    m.figure(FIG / "core_fig4_response.png",
             "Response of the regolith-shielded module in Thermonaut reading the PWF file (C++, dashed) and ExoBEM "
             "(Python, solid) at the lunar equator (left) and Jezero crater (right): (a, b) sensible cooling load, "
             "(c, d) outer-face and (e, f) inner-face temperature of the top shell facet. The shaded band is the "
             "comparison window. With the start-up correction of M2d no first-day transient remains (Section @sec:startupres).",
             16.0, label="coreresp")


def verif_startup(m):
    """Start-up ablation and the removed transient (level-2)."""
    rows = [[r[0].replace(" C ", " °C "), r[1] if r[1] is not None else "not run", r[2], r[3]] for r in F["startup_ablation"]["rows"]]
    m.heading("Start-up of regolith-covered walls", 2, label="startupres")
    m.para(
        "The start-up procedure turned out to matter more than any other choice in the port (Table @tab:startup). With "
        "the EnergyPlus default, walls at 23 °C and warm-up by repeating the first day, the Mars cooling load over the "
        "comparison period was 32% higher than in ExoBEM, because the inner part of the regolith cover was still "
        "releasing the heat of its unrealistically warm start. A steady linear profile with constant conductivities "
        "reduced the error to −2.5%. The k(T)-aware profile of Eq. (@eq:steady) with the full post-warm-up correction "
        "brought the comparison windows within 0.01% (Moon) and 0.9% (Mars), but left a transient: in the first hour "
        "after warm-up the cooling load was 2.4 kW (Moon) and 0.43 kW (Mars) too high and the inner face of the shell "
        "7 K and 2 K too warm, decaying within about a day. The cause was the correction itself, which was also added to "
        "the inner layers that warm-up had already brought to the real inside temperature.")
    m.table(["Start-up treatment of CondFD walls", "Moon cooling vs ExoBEM (%)", "Mars cooling vs ExoBEM (%)",
             "First-hour cooling excess, Moon / Mars (W)"], rows,
            "Effect of the wall start-up treatment (Thermonaut with its own environment generator). The first two rows are "
            "from M1, before the Martian long-wave recalibration of M2c.",
            col_widths_cm=[7.2, 2.8, 2.8, 3.2], font_size=8, label="startup")
    m.para(
        f"The correction of Eq. (@eq:warmup) (M2d) removes the transient: the first-hour cooling now differs from "
        "ExoBEM by 68 W on the Moon and 111 W on Mars, and the inner face by less than 0.4 K. The window agreement moves "
        f"to {MOON_DIFF_G:+.2f}% (Moon) and {MARS_DIFF_G:+.1f}% (Mars). The near-perfect lunar agreement before the fix had "
        "therefore been helped by the overshoot, which offset a small difference in how the two codes start the regolith "
        "cover: ExoBEM solves a pseudo-transient steady state with period-mean boundary conditions, Thermonaut builds the "
        "steady profile of Eq. (@eq:steady) from a T⁴-mean outer-face temperature. With a 1 m cover whose time constant "
        "is months to years, that difference does not decay within the comparison window. The lesson applies beyond "
        "planetary habitats: any construction whose time constant exceeds the warm-up period, such as earth-sheltered "
        "walls or thick ground slabs, inherits its initial state for months.")


def verif_habitat(m):
    """Cross-verification on the NASA-class lunar habitat and the PV check (level-2)."""
    e = LH["energy"]
    m.heading("Code-to-code check against ExoBEM: NASA-class lunar habitat", 2, label="habver")
    m.para(
        f"The second case is the lunar surface habitat of the ExoBEM paper, sized after NASA's Artemis surface-habitat "
        f"studies [@Kessler2022;Burke2022]: {LHF['crew']} crew in a vertical cylinder of 6.5 m diameter and 5.25 m height "
        f"({LHF['volume_m3']:.0f} m³) standing on legs, with an envelope of beta cloth, MLI (R 19.2 m²K/W), 4 mm of aluminium "
        "and a 10 mm interior panel. "
        "The cabin is at 56.5 kPa with 34% oxygen, held at 20–25 °C and 30–60% relative humidity. "
        f"About {LHF['electric_kW']:.0f} kW of electric power is used inside the "
        "shell by life support, electrolysis, fans, lighting and avionics; part of it is carried away by cold plates "
        "directly to the coolant loop, and part of the electrolysis power leaves as chemical energy. Crew sensible and "
        "latent heat follow BVAD values and schedules [@Anderson2018], and racks and stowage are internal mass. The "
        "habitat sits at the lunar equator for 30 days from 1 January 2030 with 3-minute steps, and both codes read the "
        "same PWF file.")
    m.para(
        "The input file was written from ExoBEM's model by a script, so that both codes describe the same habitat: the "
        "geometry from the model's surface vertices, the MLI as a no-mass resistance, CTF conduction, the crew latent "
        "heat as the latent fraction of OtherEquipment objects, the cold-plate and chemical shares as their \"lost\" "
        "fraction, and an ideal-loads system with a humidistat (30–60%). Over days 4–30, after the start-up "
        f"({e['hours']} h), the codes agree within {HAB_S:+.2f}% in sensible cooling and {HAB_L:+.1f}% in latent cooling "
        f"(Table @tab:habver, Fig. @fig:habitats c, d). Outer-face temperatures, which swing from −150 to +120 °C, agree "
        "within 0.03–0.32 K RMSE and inner faces within 0.1 K.")
    rows = [
        ["Sensible cooling (kWh)", f"{e['ep_sensible_kWh']:.1f}", f"{e['py_sensible_kWh']:.1f}",
         f"{HAB_S:+.2f}% (hourly RMSE {LH['Qc']['rmse']:.0f} W, R² {LH['Qc']['r2']:.4f})"],
        ["Latent cooling (kWh)", f"{e['ep_latent_kWh']:.1f}", f"{e['py_latent_kWh']:.1f}", f"{HAB_L:+.1f}%"],
        ["Outer-face RMSE, south wall / roof / floor (K)", "", "",
         f"{LH['wall_05']['outside_rmse']:.2f} / {LH['roof']['outside_rmse']:.2f} / {LH['floor']['outside_rmse']:.2f}"],
        ["Inner-face RMSE, south wall / roof / floor (K)", "", "",
         f"{LH['wall_05']['inside_rmse']:.2f} / {LH['roof']['inside_rmse']:.2f} / {LH['floor']['inside_rmse']:.2f}"],
        ["Mean cabin relative humidity", f"{100*LH['rh']['ep_mean']:.0f}%", f"{100*LH['rh']['py_mean']:.0f}%",
         "supply-air convention (see text)"],
        ["Run time, 30 days at 3-min steps (s)", f"{RT['habitat_cpp']:.1f}", f"{RT['habitat_python']:.0f}", ""],
    ]
    m.table(["Quantity", "Thermonaut", "ExoBEM", "Difference"], rows,
            "NASA-class lunar habitat at the lunar equator, days 4–30: Thermonaut and ExoBEM on the same PWF file.",
            col_widths_cm=[5.4, 2.4, 2.4, 5.8], font_size=8, label="habver")
    m.para(
        "The one visible difference is the cabin humidity. EnergyPlus's ideal-loads system dries the supply air while it "
        "cools, so the cabin settles near 48% instead of at the 60% humidistat limit, whereas ExoBEM models a condensing "
        "heat exchanger that removes only the excess. Over time the water removed must equal the crew's moisture "
        "production in both codes, which is why the latent energy agrees within 1%. The difference matters for the "
        "dew-point margin of cold surfaces: in the engine it should be read from a real cooling coil, not from ideal "
        "loads. A planetary condensing-heat-exchanger component that removes only the moisture above the humidistat "
        "limit, as ExoBEM's model does, is planned (Section @sec:roadmap).")

    m.heading("PV cell temperature in vacuum", 2, label="pvver")
    h, ea = PV["PV_H"], PV["PV_E"]
    m.para(
        "The PV hook was checked against its own definition. Two equivalent one-diode modules in Decoupled mode, one "
        "horizontal and one facing east, were placed on detached shading surfaces of the lunar module case, and the "
        "residual of Eq. (@eq:pvcell) was evaluated at every time step from the engine's outputs (cell temperature, "
        "plane-of-array irradiance, efficiency) and the sky and regolith temperatures (Table @tab:pvver). An input with "
        "the dynamic cell model and a battery outside a zone stops with the two expected severe errors.")
    rows = [
        ["Horizontal", f"{h['residual_p99_W_m2']:.3f}", f"{h['steps_over_1W']} of {h['steps']} ({h['of_which_below_30W']} below the 30 W/m² insolation threshold)",
         f"{h['Tcell_sunlit_max_K']:.0f}", f"{h['Tcell_min_K']:.0f}"],
        ["East-facing", f"{ea['residual_p99_W_m2']:.3f}", f"{ea['steps_over_1W']} of {ea['steps']} (efficiency loop exits after one pass)",
         f"{ea['Tcell_sunlit_max_K']:.0f}", f"{ea['Tcell_min_K']:.0f}"],
    ]
    m.table(["Module", "Residual, 99th percentile (W/m²)", "Steps with residual > 1 W/m²", "Max cell T (K)", "Min cell T (K)"], rows,
            "Energy-balance residual of the planetary PV cell temperature (lunar equator, two lunations).",
            col_widths_cm=[2.4, 3.0, 6.2, 2.2, 2.2], font_size=8, label="pvver")
    m.para(
        "Sunlit cells reach 336–359 K, as expected for a module that can only radiate, and fall to 79 K at night. The few "
        "larger residuals are at the edges of daylight, where the engine skips the efficiency iteration below 30 W/m² "
        "or exits it after one pass; they carry no energy of consequence.")


# =========================================================================== discussion
def tool_comparison(m):
    """Table comparing the two tools (level-2)."""
    m.heading("Re-implementation or engine modification?", 2, label="compare")
    rows = [
        ["Basis", "Re-implementation of the EnergyPlus heat-balance method", f"Fork of the EnergyPlus v{F['base_version']} engine"],
        ["Code", f"About {F['exobem_python_lines']:,} lines of Python (NumPy, SciPy); pip package",
         f"{KLOC:,.0f} thousand lines of C++ reused; {DIFF['insertions']:,} added"],
        ["Conduction and solution", "Finite volumes on stretched grids, optional curved shells; surfaces and air solved simultaneously",
         "EnergyPlus CTF or CondFD (planar layers); iterative surface and air balances"],
        ["Scope", "Single zone, ideal loads, cabin vapour balance and condensation check; radiator, heat pump, PV, "
         "batteries, regenerative fuel cells and fission as post-processors",
         "All engine features that do not need outdoor air: multi-zone, HVAC and plant, controls, EMS, PV, batteries, "
         "outputs; radiator component planned"],
        ["Weather", "Writes and reads PWF files; internal environment models", "Reads PWF files (no EPW needed) or runs a C++ port of the models"],
        ["Time base", "Sol clock on Mars; Earth clock on the Moon", "Earth clock on both (sol clock planned)"],
        ["Input", "Python objects or JSON", "Standard IDF or epJSON plus Site:PlanetaryBody"],
        ["Earth verification", "ASHRAE 140 opaque cases vs EnergyPlus 23.2: annual loads within 0.7%",
         f"Bit-for-bit identical to v{F['base_version']} on {N_EARTH} files; {UT['tests']:,} unit tests pass"],
        ["Planetary verification", "Mars24, Diviner, Appelbaum–Flood, MEDA reference data; NASA envelope analysis",
         f"JPL Horizons, Diviner, closed-form boundary balances, NIST CO2 properties; code-to-code against ExoBEM within {abs(MARS_DIFF):.1f}%"],
        ["Run time", f"Regolith module: {RT['python_moon']} s (Moon, {RT['moon_days']} d); NASA-class habitat: {RT['habitat_python']:.0f} s (30 d)",
         f"Regolith module (CondFD): {RT['moon']} s; NASA-class habitat (CTF): {RT['habitat_cpp']:.1f} s"],
        ["Best use", "Early design, parametric studies, power sizing, teaching, independent reference",
         "Detailed design with EnergyPlus workflows, multi-zone habitats and systems"],
    ]
    m.table(["Aspect", "ExoBEM (Python)", "Thermonaut (C++)"], rows,
            "The two tools compared. Run times are for 3-minute time steps on the same computer, single thread; the "
            "regolith-module Python time is for ExoBEM v0.1.",
            col_widths_cm=[3.0, 6.4, 6.6], font_size=7.5, label="compare")
    m.para(
        "Table @tab:compare compares the two routes. The re-implementation was the faster way to get the physics "
        "right: the planetary models of both tools share their equations, which ExoBEM had checked against reference "
        "data, but no code, and having a second implementation made it possible to find the start-up problem and the "
        "humidity convention, which a single code would have hidden. The engine fork is the way to use that physics in "
        "practice. It inherits multi-zone air balances, HVAC and plant loops, controls, electric systems and reporting, "
        "and it runs the habitat cases faster than the Python code. The shared weather format lets both tools run the "
        "same site, so a design can move from ExoBEM to Thermonaut without re-deriving its environment. The two are "
        "therefore complementary rather than competing, and neither needs the other: ExoBEM is a fast stand-alone tool "
        "for early design, Thermonaut the engine for detailed design with EnergyPlus workflows.")


def limitations_core(m, title="Limitations"):
    """Limitations of Thermonaut M2d (level-2)."""
    m.heading(title, 2, label="limcore")
    m.bullets([
        "**Earth clock on Mars.** Hours are 3600 s, so the Martian day drifts by about 40 minutes per Earth day against the clock. Physics is right, but schedules cannot follow local solar time.",
        "**Windows and radiators.** Fenestration and a space-radiator plant component are not yet available; heat rejection is represented by ideal loads, and planetary design days and sizing are refused.",
        "**Humidity control.** The ideal-loads system dries the cabin below the humidistat limit (Section @sec:habver); until a planetary condensing-heat-exchanger component is available, condensation risk on cold surfaces should be assessed with a real coil model.",
        "**Power.** PV and batteries are planetary; dust soiling of arrays, regenerative fuel cells and fission power are not. Module emissivity is a constant 0.85 on both faces: its dependence on temperature and its change as dust accumulates on Martian arrays are not modelled.",
        "**Cabin gas.** The zone moisture balance uses moist-air psychrometrics at cabin pressure; a gas-mixture block for other cabin atmospheres is planned.",
        "**Gravity.** Body gravity is used in the new convection correlations only; window gaps, airflow networks and stack effects are refused or still use 9.81 m/s².",
        "**Thin metal layers.** CondFD cannot resolve millimetre aluminium shells at minute time steps, so they must be lumped or modelled with CTF.",
        "**Verification scope.** Off-Earth, the engine is checked against an independent ephemeris, orbital temperature data, closed-form boundary balances and tabulated gas properties, and code-to-code against ExoBEM; no measurement of a whole habitat exists. Thermal-vacuum test data for a habitat-scale article, of the kind used to correlate spacecraft thermal models, would be the next benchmark; none is public today.",
    ])


def roadmap_core(m):
    """Roadmap and upstreaming (level-2)."""
    m.heading("Roadmap", 2, label="roadmap")
    m.para(
        "The audit provides the work list for the next milestone. M3 introduces a sol clock for Mars by making the "
        f"hour length a run-time variable: the audit identified the four lines that set the time-step lengths, the "
        f"{AF['rSecsInHour_physical']} physical uses of the hour constant that must follow it and the "
        f"{AF['rSecsInHour_units']} unit conversions that must not, and the change to the CTF generator's hour-based "
        "units. M3 also adds a cabin gas-mixture block for psychrometrics, body gravity in every buoyancy model, "
        "planetary design days and sizing, a space-radiator plant component modelled on the fluid cooler with a surface "
        "link like the flat-plate solar collector, a planetary condensing heat exchanger that holds the cabin at its "
        "humidity limit, dust soiling of PV, and windows with vacuum-compatible solvers.")
    m.heading("Tracking EnergyPlus releases", 2, label="releases")
    m.para(
        "A fork is only useful if it can follow the engine it forks. Every change in Thermonaut is applied by an "
        "idempotent patch script that finds a short, unique anchor in a stock source file and inserts a hook, plus the "
        "new PlanetaryBody module and the input object. Moving to a new EnergyPlus release means checking out the "
        "release tag, running the scripts in order (each stops with an error if its anchor has moved, instead of "
        "patching the wrong place), updating the anchors that moved, and rerunning the Earth regression against an "
        "unmodified build of the same release, the unit-test suite and the planetary checks of Section @sec:verifsec. "
        f"Because the {DIFF['hook_lines_existing_files']} lines of hooks sit at a few interfaces (weather arrays, sun "
        "direction, exterior and interior coefficients, CondFD start-up, PV cell temperature, input validation) rather "
        "than inside the solvers, most releases should need only anchor updates; a release that restructures one of "
        "those interfaces needs that hook rewritten. Because every change is gated on the planetary object and Earth "
        "results are unchanged, the planetary mode could also be offered upstream as an optional feature, which would "
        "end the need for a fork.")


# =========================================================================== appendix
def appendix_tutorial(m):
    """Appendix A: building Thermonaut and running the NASA-class habitat."""
    m.heading("Appendix A. Using Thermonaut: a worked example", 1, numbered=False)
    m.para(
        "The repository contains a step-by-step tutorial (planetary/TUTORIAL.md) that builds the engine and runs the "
        "NASA-class lunar habitat of Section @sec:habver. Its main steps are:", indent=False)
    m.para("**1. Build** (Windows, Visual Studio 2022 Build Tools; on Linux and macOS the standard EnergyPlus CMake build):",
           align="left")
    for line in ("git clone https://github.com/TensorBuildLab/Thermonaut.git", "cd Thermonaut",
                 "planetary\\tools\\build.bat configure 8"):
        m.para(line, align="left", size=8.5, space_after=0)
    m.para("", space_after=4)
    m.para("**2. Write a planetary weather file** with ExoBEM (lunar equator, 31 days, 3-minute records):", align="left")
    for line in ("python -m pip install \"exobem[plot] @ git+https://github.com/TensorBuildLab/ExoBEM\"",
                 "exobem weather --body moon --lat 0.674 --lon 23.473 --start 2030-01-01T00:00:00 --days 31 "
                 "--timestep 180 -o lunar_habitat.pwf"):
        m.para(line, align="left", size=8.5, space_after=0)
    m.para("", space_after=4)
    m.para("**3. Add the planetary object** to an ordinary input file (the habitat file is written by "
           "planetary/cases/make_habitat_case.py from ExoBEM's model):", align="left")
    for line in ("Site:PlanetaryBody,",
                 "  lunar_habitat,         !- Name",
                 "  Moon,                  !- Body",
                 "  EarthClock,            !- Clock",
                 "  2030,                  !- Reference Year",
                 "  autocalculate,         !- Gravity {m/s2}",
                 "  56500,                 !- Cabin Pressure {Pa}",
                 "  0.34,                  !- Cabin Oxygen Mole Fraction",
                 "  0.15,                  !- Cabin Air Velocity {m/s}",
                 "  5.25,                  !- Convection Vertical Length Scale {m}",
                 "  0.0,                   !- Horizon Elevation Angle {deg}",
                 "  autocalculate, autocalculate, autocalculate, autocalculate, 3.0,  !- regolith; deep depth {m}",
                 "  710, Climatology, 0.5, 0, 0, 0, 3.2, 2.0,   !- Mars-only fields",
                 "  lunar_habitat.pwf;     !- Planetary Weather File Name"):
        m.para(line, align="left", size=8.0, space_after=0)
    m.para("", space_after=4)
    m.para(
        "The rest is standard input: Material, Material:NoMass (MLI) and Construction for the envelope; "
        "BuildingSurface:Detailed with an Outdoors floor for a habitat on legs; InternalMass for racks; OtherEquipment "
        "with latent and lost fractions for crew and equipment; ZoneControl:Thermostat, ZoneControl:Humidistat and "
        "ZoneHVAC:IdealLoadsAirSystem; and, if wanted, Generator:Photovoltaic with the one-diode model in Decoupled "
        "mode and a battery placed in the zone. Infiltration, ventilation or outdoor-air objects stop the run.",
        align="left")
    m.para("**4. Run** (no EPW file is given):", align="left")
    m.para("build\\Products\\energyplus.exe -d out lunar_habitat.idf", align="left", size=8.5)
    m.para(
        "The error file reports the planetary mode, for example \"planetary weather file lunar_habitat.pwf (14880 "
        "records of 180 s); calendar EPW written to out\\planetary_calendar.epw\" and \"deep regolith −14.9 C\". All "
        "standard outputs are available, plus Site Planetary Ground Surface Temperature, Deep Ground Temperature, Ambient "
        "Pressure, Downwelling Longwave Radiation, Sun Distance, Solar Longitude and Dust Optical Depth.", align="left")
    m.para("**5. Compare with ExoBEM:** make_habitat_case.py also runs ExoBEM on the same weather file and writes "
           "comparison.json with the numbers of Table @tab:habver.", align="left")
