"""Sections of the Thermonaut manuscript (Journal of Building Performance Simulation version).

Numbers come from paper/Thermonaut/data/core_facts.json and core_summary.json, written by extract_thermonaut_data.py
from the Thermonaut repository and its verification runs.  ANON = True withholds identifying links for double-anonymous
review (the separate title page carries them).
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIG = HERE / "figures"
F = json.loads((HERE / "data" / "core_facts.json").read_text(encoding="utf-8-sig"))
S = json.loads((HERE / "data" / "core_summary.json").read_text(encoding="utf-8-sig"))
AF, DIFF, UT, RT = F["audit_facts"], F["diff"], F["unit_tests"], F["run_time_s"]
CM, CR = S["moon_equator"]["comparison"], S["mars_jezero"]["comparison"]                       # engine reads the PWF file
CMg, CRg = S["moon_equator"]["comparison_generator"], S["mars_jezero"]["comparison_generator"]  # engine's own generator
LH, LHF, PV = S["lunar_habitat"], F["lunar_habitat"], S["pv_vacuum"]
HZ, BC, MR = S["horizons"], S["boundary"], S["moon_regolith"]
RB, HU, MC = S["robustness"], S["humidity"], S["mars_convection"]
TS, ER, AU = S["planetary_tests"], S["earth_regression"], S["audit_inventory"]
N_FIND = sum(a["P0"] + a["P1"] + a["P2"] for a in F["audit"]["areas"])
N_P0 = sum(a["P0"] for a in F["audit"]["areas"])
N_P1 = sum(a["P1"] for a in F["audit"]["areas"])
N_P2 = sum(a["P2"] for a in F["audit"]["areas"])
N_EARTH = len(F["earth_regression"]["files"])
KLOC = F["source_lines_cc_hh"] / 1000
ENGINE_SHARE = 100 * DIFF["insertions"] / F["source_lines_cc_hh"]
N_VALUES = sum(v.get("n_values", 0) for v in ER["chicago"].values())
N_IDENT = {w: sum(v["status"] == "identical" for v in ER[w].values()) for w in ER}
N_RUN = {w: sum(v["status"] in ("identical", "differs") for v in ER[w].values()) for w in ER}
AU_NOTES = sum(AU["by_priority"].get("none", {}).values())
DISP = ["modified", "refused", "avoided", "deferred", "harmless"]


def dpct(c):
    e = c["energy"]
    return 100 * (e["ep_cooling_kWh"] / e["py_cooling_kWh"] - 1)


MOON_DIFF, MARS_DIFF = dpct(CM), dpct(CR)
MOON_DIFF_G, MARS_DIFF_G = dpct(CMg), dpct(CRg)
HAB_S, HAB_L = LH["energy"]["sensible_diff_pct"], LH["energy"]["latent_diff_pct"]
ANON = True


def sec(*labels):
    return "Section" + ("s " if len(labels) > 1 else " ") + " and ".join(f"@sec:{x}" for x in labels)


# =========================================================================== background
def background(m):
    m.heading("Where EnergyPlus meets its environment", 2, label="enginebg")
    m.para(
        "EnergyPlus advances a nested loop over run periods, days, hours and zone time steps [@EPlus262;Crawley2001]. "
        "Each day the weather manager reads the weather file, computes the Earth solar declination and equation of "
        "time from Fourier fits and interpolates hourly records to the time step; the solar routines advance the hour "
        "angle at 15° per hour. The surface heat balance applies convection correlations for air, splits long-wave "
        "exchange among sky, air and ground, conducts through walls with conduction transfer functions (CTF) "
        "[@Seem1987] or conduction finite differences (CondFD) [@TabaresVelasco2012], couples inside faces to the zone "
        "air and passes the load to HVAC, plant and electric models whose air properties come from the outdoor "
        "barometric pressure. The Earth thus enters in many places at once, often as literals (3600 s, 15°/h, 1 atm, "
        "9.81 m/s²) or as conventions (the ground is at air temperature; the zone is at outdoor pressure) that are not "
        "visible in the input. A lunar habitat therefore cannot be modelled correctly by editing the weather file alone.")

    m.heading("Routes to off-Earth thermal simulation", 2, label="routes")
    m.para(
        "Spacecraft and habitat thermal control is designed with lumped-parameter tools such as SINDA/FLUINT and "
        "Thermal Desktop, which solve radiation exchange, conduction and fluid loops for worst-case hot and cold "
        "cases, with component temperature limits as design drivers [@Gilmore2002]. They are the right tools for "
        "radiators, coolant loops and electronics, but they are not organized around what building simulation "
        "provides: mission-long, schedule-driven energy accounting of an occupied zone with internal gains, humidity, "
        "controls, HVAC and electric systems in one model. The two are complementary; building simulation supplies the "
        "loads and energy budgets that a thermal-control design then has to meet. Building-simulation work for Mars has "
        "so far kept an Earth engine and replaced its weather [@Lagarde2021;Aydemir2026;Millour2018], coupled climate "
        "output to design tools [@Jadeja2016], or built new models: a semi-empirical heat balance [@Ross2022] and "
        "ExoBEM, a Python re-implementation of the EnergyPlus heat-balance method with planetary physics "
        "[@ZhangExoBEM]. Table @tab:routes compares the routes. This paper takes a third: modifying the EnergyPlus "
        "engine itself, so that a sealed habitat can use the engine's zone, control and output machinery. The "
        "difficulty is less the planetary physics, whose models are established [@Hayne2017;Allison2000;Appelbaum1990], "
        "than finding every place where a large engine silently assumes the Earth and changing those places without "
        "disturbing terrestrial results.")
    rows = [
        ["Earth physics replaced", "No (Earth sun, air convection, sky and ground)", "Yes, in a new code", "Yes, inside EnergyPlus"],
        ["EnergyPlus features", "All, driven by wrong physics", "Heat-balance method only (one zone, ideal loads)",
         "Zones, schedules, EMS, ideal loads, PV, storage, outputs (Table @tab:coverage)"],
        ["Verification", "None reported", "Earth: against EnergyPlus; planets: references", f"{sec('earth', 'indep', 'cross', 'habver', 'sens')}"],
        ["Typical use", "Early climate studies", "Early design, parametric studies", "Detailed design in EnergyPlus workflows"],
    ]
    m.table(["Aspect", "Mars weather in stock EnergyPlus", "Re-implementation (ExoBEM)", "Engine modification (Thermonaut)"], rows,
            "Routes to building energy simulation of planetary habitats.", col_widths_cm=[2.6, 4.0, 4.4, 5.0], font_size=7.5,
            label="routes")
    m.para(
        "EnergyPlus is distributed under a BSD-3-Clause licence with a clause from the U.S. Department of Energy: a "
        "modified version may not be called EnergyPlus or imply endorsement. The fork is therefore named Thermonaut, "
        "keeps the licence and notices, and states that it is neither EnergyPlus nor endorsed by its developers.")


# =========================================================================== audit
def audit(m):
    m.heading("Audit protocol", 2, label="auditmethod")
    m.para(
        f"The audit covered EnergyPlus v{F['base_version']} (git tag v26.2.0), about {KLOC:,.0f} thousand lines of C++ in "
        "src/EnergyPlus, in six areas that together cover every path from input to output: (1) time, calendar, weather "
        "input and sizing; (2) solar geometry, sky and ground radiation; (3) psychrometrics, pressure, gravity and "
        "airflow; (4) surface heat balance, conduction, convection and ground contact; (5) windows; (6) HVAC, plant, "
        "heat rejection and electric power. For each area a written brief listed the symbols through which the Earth "
        "can enter: time constants (rSecsInHour, 3600, 86400), solar literals (15°/h, 1353 and 1367 W/m², Fourier "
        "coefficients), pressure and density (OutBaroPress, StdBaroPress, StdRhoAir), gravity (9.81, 9.807), gas "
        "constants and psychrometric ratios, outdoor-air temperature used as a sky or ground proxy, and empirical "
        "correlation coefficients and validity limits. One large-language-model code agent per area searched the "
        "source for these symbols, followed the call graph from each hit, separated bookkeeping (an hour used as an "
        "index) from physics (an hour converting a rate to energy), and recorded file and line, the Earth value, the "
        "consequence on the Moon and Mars, a proposed change and a priority: P0 if needed for a first single-zone "
        "opaque habitat with ideal loads, P1 for windows, HVAC, plant, PV or outputs, P2 for rarely used modules better "
        "refused than fixed.")
    m.para(
        "Every finding that led to a code change was checked against the source during implementation. Afterwards a "
        "separate agent pass traced every row of the six reports to the current code: it re-located the cited file and "
        "line in v26.2.0 and assigned a disposition from the actual Thermonaut changes (Table @tab:trace). "
        f"Of the {AU['total']} rows ({N_FIND} prioritized findings and {AU_NOTES} notes without a priority), "
        f"{AU['location']['ok']} citations were at the stated line, {AU['location']['moved']} nearby in the same file, "
        f"{AU['location']['not_found']} not found and {AU['location']['n/a']} cited no line. The tracing also exposed "
        "gaps between the documented and the implemented refusals (for example windows, SimpleCombined outside "
        "convection and several air-cooled and outdoor-air components), which were closed in the version reported here "
        "(M2e). The inventory with the disposition of each row is supplementary material S1. The audit is a search "
        "under a stated protocol: an assumption that passes through none of the searched symbols, such as a "
        "correlation calibrated to Earth conditions without a telltale constant, can be missed, so the count is a count "
        "of findings, not a proof of completeness.")

    m.heading("What the audit found", 2, label="auditfound")
    m.para(
        f"The audit recorded {N_FIND} findings: {N_P0} P0, {N_P1} P1 and {N_P2} P2 (Fig. @fig:audit, Table "
        "@tab:findings). The P0 findings cluster in time and weather, solar and sky radiation, pressure and air "
        "properties, and the exterior boundary; windows have none because no window code runs without fenestration.")
    m.figure(FIG / "core_fig2_audit.png",
             f"Earth-specific assumptions found in EnergyPlus v26.2.0 by area and priority ({N_FIND} findings).", 16.0,
             label="audit")
    rows = [
        ["Time base", f"1 h = 3600 s is constexpr; {AF['rSecsInHour_physical']} of {AF['rSecsInHour_uses']} uses of rSecsInHour are physical; CTFs in Earth hours",
         "A longer hour would rescale part of the physics only", "Earth clock kept; sun rate generalized"],
        ["Weather", "EPW checks treat ≥ 99.9 °C as missing and replace pressures ≤ 31 kPa", "Lunar 120 °C and Martian 700 Pa silently altered",
         "Planetary weather file, values set after the EPW read"],
        ["Sun", "Earth Fourier fits for declination and equation of time; 15°/h", "Wrong sun on any other body", "Daily fit to Mars24 or lunar ephemeris"],
        ["Sky, ground", f"Part of the sky view sees air; ground long-wave = outdoor air ({AF['ground_lw_equals_air_sites']} sites)",
         "No air on the Moon; regolith swings 290 K", "All sky view to the sky; regolith column"],
        ["Pressure", f"One OutBaroPress for zone, HVAC and outdoors ({AF['OutBaroPress_uses']} uses in {AF['OutBaroPress_files']} files)",
         "Moon: zero air capacity, NaN humidity", "OutBaroPress = cabin; new ambient pressure"],
        ["Convection", "Air at 1 atm and 1 g with a non-zero floor; TARP inside",
         f"Heat loss to absent air; cabin convection ~{AF['tarp_overestimate_moon']}× too high on the Moon", "Zero or CO2 mixed convection; cabin-gas correlation"],
        ["Conduction", "CondFD clamps at −100 °C; walls start at 23 °C", "Lunar nights near −180 °C; regolith time constants of years", "−270 °C; steady start with correction"],
        ["PV", "NOCT, Sandia and PVWatts cell temperatures assume Earth air", "Modules in vacuum cool only by radiation", "Radiative (and CO2) cell balance"],
    ]
    m.table(["Area", "Earth assumption in v26.2", "Effect off-Earth", "Thermonaut"], rows,
            "Representative audit findings and their treatment.", col_widths_cm=[1.8, 5.6, 4.4, 4.2], font_size=7.2,
            label="findings")
    rows = []
    for a in F["audit"]["areas"]:
        d = AU["by_area"].get(a["key"][:2], {})
        rows.append([a["label"]] + [str(d.get(k, 0)) for k in DISP] + [str(sum(d.values()))])
    tot = AU["by_disposition"]
    rows.append(["All areas"] + [str(tot.get(k, 0)) for k in DISP] + [str(AU["total"])])
    p0 = AU["by_priority"].get("P0", {})
    rows.append(["of which P0"] + [str(p0.get(k, 0)) for k in DISP] + [str(sum(p0.values()))])
    m.table(["Audit area", "Modified", "Refused", "Avoided", "Deferred", "Harmless", "Total"], rows,
            "Disposition of every audit row in Thermonaut M2e: changed by a hook, refused by the input validator, made "
            "correct by a design decision, deferred to a later milestone, or without effect off-Earth.",
            col_widths_cm=[5.4, 1.8, 1.7, 1.7, 1.8, 1.8, 1.4], font_size=7.5, label="trace")
    m.para(
        f"Three findings shaped the design. Time is the most pervasive assumption: {AF['rSecsInHour_units']} uses of the "
        "hour constant are genuine unit conversions that must stay 3600 s while the physical uses would follow a "
        "longer hour, and the CTF generator works in Earth hours. The engine has one air pressure: about "
        f"{AF['OutBaroPress_cabin']} of the {AF['OutBaroPress_uses']} uses of OutBaroPress describe air inside the "
        f"pressure shell and about {AF['OutBaroPress_outdoor']} outdoor air, which is absent on the Moon. And the "
        "exterior boundary hides air in the long-wave split, the ground temperature and the PV cell temperature, not "
        "only in convection. Most findings are therefore resolved not one by one but by a few decisions (Table "
        "@tab:trace): keeping the Earth clock avoids the time findings, letting OutBaroPress carry the cabin pressure "
        "makes the zone and HVAC uses correct without edits, and refusing outdoor-air objects removes whole modules "
        "from the planetary domain. The deferred rows are mostly windows and the Mars sol clock (Section @sec:roadmap).")


# =========================================================================== planetary mode
def design(m):
    m.heading("Design rules and supported domain", 2, label="rules")
    m.para("Three rules guided every change (Fig. @fig:hooks):")
    m.bullets([
        "**Earth stays identical.** Planetary mode is active only with a Site:PlanetaryBody object for the Moon or "
        "Mars; every change is behind that switch or replaces a literal by a variable with the same Earth value.",
        "**Reuse, do not rewrite.** Planetary values enter where EnergyPlus already reads its environment; the heat "
        "balance, conduction solvers, shading, view factors, ideal loads, electric load centre and reporting run unchanged.",
        "**Refuse what cannot be right.** Objects that need outdoor air or Earth weather stop the run with an error "
        "instead of producing plausible-looking wrong numbers.",
    ])
    m.para(
        f"Version M2e adds {DIFF['insertions']:,} lines of C++ and input definition and changes {DIFF['deletions']} in "
        f"{DIFF['files']} files: a PlanetaryBody module ({DIFF['new_module_lines']:,} lines), the input object "
        f"({DIFF['idd_lines']} lines) and {DIFF['hook_lines_existing_files']} lines of hooks in "
        f"{DIFF['existing_files_touched']} existing files ({ENGINE_SHARE:.1f}% of the engine). Table @tab:coverage "
        "states what the planetary mode supports: envelope, load and power studies of sealed, windowless habitats with "
        "prescribed set-points (version history in supplementary material S6).")
    m.figure(FIG / "core_fig1_hooks.png",
             "Where Thermonaut enters the EnergyPlus engine. Grey: unchanged stages and the files that carry the hooks; "
             "orange: what each hook does off-Earth. The PlanetaryBody module supplies ephemerides, the environment, "
             "regolith temperatures, gas properties and the PV cell temperature.", 16.0, label="hooks")
    rows = [
        ["Time loop, schedules, EMS, outputs", "Inherited unchanged (Earth clock)", "Sol clock for Mars planned"],
        ["Weather", "Planetary weather file or internal generator", "Generalized"],
        ["Sun position and shading", "Body's hour-angle rate, daily ephemeris fit, disk visibility", "Generalized"],
        ["Exterior surface balance", "Vacuum or thin-CO2 convection; sky and regolith long-wave; regolith ground", "Generalized"],
        ["Conduction (CTF, CondFD)", "Unchanged solvers; −270 °C limit; regolith start-up", "Generalized"],
        ["Interior convection, zone air", "Cabin gas at cabin pressure and body gravity", "Generalized; moist-air psychrometrics"],
        ["Ideal loads with humidistat", "Inherited unchanged", "Supported (Section @sec:habver)"],
        ["PV, batteries", "One-diode PV with planetary cell temperature; Li-ion in a zone", "Generalized"],
        ["Water-cooled chillers, plant loops", "Inherited unchanged; no heat sink available", "Space radiator planned"],
        ["Windows; infiltration, ventilation, outdoor-air and air-cooled equipment; design days and sizing; Kiva; "
         "AirflowNetwork", "Refused with a severe error", "Windows and planetary sizing planned"],
    ]
    m.table(["EnergyPlus element", "Thermonaut planetary mode", "Status"], rows,
            "Feature coverage of the planetary mode. On Earth every element is that of EnergyPlus v26.2.",
            col_widths_cm=[5.4, 6.6, 4.0], font_size=7.5, label="coverage")

    m.heading("How a planetary run is coordinated", 2, label="coord")
    m.para(
        "Thermonaut adds no second simulation loop. At input, Site:PlanetaryBody sets the body, gravity and cabin "
        "pressure, which is stored in OutBaroPress; a planetary weather file, if named, is read and checked, and a "
        "calendar-only EPW keeps the weather manager's day bookkeeping unchanged. A validator then refuses unsupported "
        "objects (Section @sec:refuse). Before the first day the environment of the whole run is interpolated from the "
        "file or generated, the regolith column is brought to periodic equilibrium and CondFD walls start from a "
        "steady profile (Section @sec:startup). Each day the planetary module overwrites every weather value and fits "
        "declination and equation of time to the ephemeris, and shading is recomputed. Each time step then runs the "
        "stock sequence of outside faces, conduction, inside faces, zone air, ideal loads and electric load centre "
        "with the planetary coefficients of Fig. @fig:hooks.")

    m.heading("Input and planetary weather files", 2, label="pwf")
    m.para(
        "Site:PlanetaryBody selects the body, a reference year and habitat parameters: gravity, cabin pressure and "
        "oxygen mole fraction, cabin air velocity and a convection length; optional fields set a uniform horizon "
        "elevation, regolith properties and, for Mars, mean pressure, dust model and wind. The last field names a file "
        "in the Planetary Weather Format (PWF 1.0) [@ZhangExoBEM], whose versioned specification defines every column, "
        "unit and convention (supplementary material S8): a key–value header (body, site, start time in UTC, record "
        "length, solar-day length, gravity, atmosphere) and one record per interval with solar zenith and azimuth, "
        "visible fraction of the solar disk, direct normal, diffuse and global irradiance, air temperature (nan in "
        "vacuum), effective sky, regolith surface and deep temperatures, albedo, ambient pressure and wind. Solar "
        "quantities refer to the middle of each interval, state quantities to its end. The engine rejects a file for "
        "another body, with a missing column, unequal spacing or incomplete coverage of the run period, or with any "
        "non-physical value (negative irradiance, temperatures below 2.7 K, albedo outside 0–1, negative pressure or "
        "wind; only the air temperature may be nan), reporting the record number; Earth range checks are not applied. "
        "Values are interpolated linearly to the time step. The engine does not use the zenith and azimuth columns: it "
        "computes the solar position itself, so that shading and incidence follow its own geometry, and takes only the "
        "irradiance magnitudes from the file.")

    m.heading("Time base and sun position", 2, label="sun")
    m.para(
        "A planetary hour would touch the physical uses of the hour constant and the CTF generator. Thermonaut therefore "
        "keeps the Earth clock (3600 s hours, days from 00:00 UTC), so crew schedules are written as on Earth, and changes "
        "the rate at which the Sun moves. The hour angle becomes")
    m.equation(r"H=r\left[12-\left(t+E\right)\right]+\left(\lambda_{TZ}-\lambda\right),\qquad r=\frac{360^{\circ}}{P_{d}/3600\,\mathrm{s}}",
               label="hourangle")
    m.para(
        "where t is the clock hour, E the equation of time in hours, λ_{TZ} and λ the time-zone meridian and longitude, "
        "and P_{d} the solar day: 86,400 s on Earth (r = 15°/h), the synodic month on the Moon (0.508°/h) and the sol on "
        "Mars (14.6°/h). Each day the declination is taken from Mars24 [@Allison2000] or the selenographic subsolar "
        "point [@Meeus1998] at 12:00 UTC, and E is chosen so that Eq. (@eq:hourangle) reproduces the ephemeris hour "
        "angle H_{⊙} at mid-day,")
    m.equation(r"E_{d}=\frac{H_{\odot}\left(12\,\mathrm{h}\right)+\lambda_{TZ}-\lambda}{r}", label="eotfit")
    m.para(
        "Because the hour angle is linear in time over a day on both bodies, the fit holds through the day. The hour "
        "angle is wrapped to ±180° before the sunrise test, and the visible fraction of the solar disk above the "
        "horizon is its area fraction.")

    m.heading("Planetary environment", 2, label="env")
    m.para(
        "Without a weather file the environment comes from an internal generator. On the Moon there is no diffuse "
        "light, the sky is at 2.725 K and the ground is a one-dimensional regolith column [@Hayne2017]. On Mars a "
        "delta-Eddington two-stream solution with a seasonal dust optical depth and an optional global storm gives the "
        "irradiance [@Joseph1976;Appelbaum1990]; pressure follows the seasonal CO2 cycle; the sky emits as a dusty-CO2 "
        "layer calibrated to MEDA infrared data and the 2018 dust storm [@Martinez2023;ViudezMoreiras2019]; and the "
        "near-surface air follows the ground with a lag. Regolith columns are brought to periodic equilibrium over a "
        "year of forcing. Lunar Earthshine (below 0.2 W/m²) and Earth's thermal emission seen from the Moon (about "
        "0.07 W/m²) are neglected; both are below 0.1% of the long-wave exchange of a sunlit surface. The verified "
        "domain is equatorial and mid-latitude sites with a uniform horizon: the ground view factor is (1 − cos β)/2, "
        "and terrain slopes, polar illumination, permanently shadowed regions and terrain eclipses are outside it.")

    m.heading("Cabin and ambient pressure", 2, label="pressure")
    m.para(
        "Of two ways to split the single pressure, adding a cabin pressure and editing the roughly 350 zone and HVAC "
        "uses, or letting OutBaroPress carry the cabin pressure and editing the outdoor uses, Thermonaut takes the "
        "second: zone balances, psychrometrics, ideal loads and HVAC components see the gas they contain without "
        "edits, and a new ambient pressure (zero on the Moon, 600–800 Pa on Mars) serves the exterior model and "
        "outputs. The cabin is a nitrogen–oxygen mixture defined by its oxygen mole fraction. Its convection properties "
        "are those of the mixture, but the zone moisture balance keeps EnergyPlus's moist-air psychrometrics at cabin "
        "pressure. At 26.5% O2 the mixture's gas constant is 0.4% below that of air and its specific heat 0.1% below; "
        "at 34% O2 they are 1.4% and 1.0% below, so the volumetric heat capacity of the zone gas is 0.4% too low and the "
        "humidity ratio at a given relative humidity 1.4% too high (molar-mass ratio 0.613 instead of 0.622). Both "
        "errors are small next to the input uncertainties of Section @sec:sens.")

    m.heading("Exterior and interior boundaries", 2, label="extbc")
    m.para(
        "Outside, the convection coefficient is zero in vacuum, bypassing EnergyPlus's lower limit. On Mars, natural "
        "convection (Churchill–Chu for vertical faces, McAdams/Lloyd–Moran for horizontal ones, blended by tilt) and "
        "laminar or turbulent flat-plate forced convection are computed for CO2 at the ambient pressure and the body's "
        "gravity and combined as [@Churchill1975;Incropera2007]")
    m.equation(r"h=\left(h_{n}^{3}+h_{f}^{3}\right)^{1/3},\qquad h_{n}=\frac{k}{L}Nu\left(Ra\right),\quad Ra=\frac{g\beta\Delta T L^{3}\rho^{2}c_{p}}{\mu k}",
               label="mixed")
    m.para(
        "with the vertical length from the input, A/P for horizontal faces and √A for forced flow. Over the Mars "
        f"verification run Ra on the top facet spans {MC['Ra_range'][0]:.0e} to {MC['Ra_range'][1]:.0e}, Re "
        f"{MC['Re_range'][0]:.1e} to {MC['Re_range'][1]:.1e} (laminar) and Pr {MC['Pr_range'][0]:.2f}–{MC['Pr_range'][1]:.2f}. "
        f"The mean free path of CO2 is {MC['mean_free_path_um'][0]:.0f}–{MC['mean_free_path_um'][1]:.0f} µm, a Knudsen "
        f"number below {MC['Knudsen_max']:.0e}, so continuum correlations apply without slip correction. The lower "
        "Rayleigh numbers fall below the fitted range of the horizontal-plate correlation, but there forced convection "
        "dominates the blend. All of the sky view goes to the sky, the ground view sees the regolith skin temperature, "
        "ground contact uses the deep-regolith temperature, an isotropic sky replaces the Perez model [@Perez1990] and "
        "outdoor moisture exchange is off. Inside, the TARP correlation for air at 1 atm and 1 g [@Walton1983] "
        f"overestimates natural convection about {AF['tarp_overestimate_moon']} times at lunar gravity; the same mixed "
        "model is applied to the cabin gas with the body's gravity and the cabin air velocity. Surfaces are grey, with "
        "one thermal emissivity and the solar absorptance of the input.")

    m.heading("Conduction and the start-up of regolith covers", 2, label="startup")
    m.para(
        "CTF and CondFD run unchanged on the Earth clock; the CondFD node limit of −100 °C becomes −270 °C. The start-up "
        "had to be reconsidered. EnergyPlus starts every wall at 23 °C and repeats the first day until the zone "
        "converges, which suits walls with time constants of hours, not a metre of regolith, whose time constant is "
        "months on Mars and years on the Moon. Off-Earth, each CondFD construction starts from its steady conduction "
        "profile between the period-mean outer-face temperature T̄_{o} and the initial inside temperature T_{in},")
    m.equation(r"T_{i}=\bar{T}_{o}+\left(T_{in}-\bar{T}_{o}\right)\frac{R_{i}}{R_{tot}},\qquad R_{i}=\sum_{j<i}\frac{\Delta x_{j}}{k_{j}\left(T_{j}\right)}",
               label="steady")
    m.para(
        "iterated six times for the temperature-dependent conductivity (the sixth iteration changes the profile by "
        f"{RB['kT']['max_change_per_iteration_K'][5]:.0e} K). T̄_{{o}} solves the mean radiative–convective balance of the "
        "outer face. After warm-up the inside faces sit at their real temperature, and the profile is recomputed with "
        "it. The difference Δ_{i} between the two profiles must not be added in full, because the nodes near the inside "
        "face have already moved during warm-up (Fig. @fig:startupfig). Node i receives Δ_{i}(1 − g_{i}), where g_{i} is "
        "the response of the construction's own node network to a unit step of the inside-face temperature over the "
        "warm-up period t_{w},")
    m.equation(r"C_{i}\frac{dg_{i}}{dt}=G_{i-1}\left(g_{i-1}-g_{i}\right)+G_{i}\left(g_{i+1}-g_{i}\right),\qquad g_{N}=1,\;g_{1}=0,\;g_{i}\left(0\right)=0",
               label="warmup")
    m.para(
        "with conductances G = k/Δx and capacities C = ρc_{p}Δx as CondFD discretizes the construction (no-mass layers "
        "enter as resistances), integrated implicitly in hourly steps with the outer node fixed. Because no-mass layers "
        "have no capacity, an MLI blanket blocks the step as it should: the panel inside it receives no correction and "
        "the regolith behind it nearly all. Like warm-up itself, the method assumes that the deep layers respond "
        "linearly over t_{w}; it has not been tested with phase-change or moisture-dependent materials. Thin, light "
        "envelopes need none of this and are best run with CTF.")
    m.figure(FIG / "core_fig6_startup.png",
             "Start-up of the lunar regolith-module shell (regolith 1 m, beta cloth, MLI, interior panel) from "
             "Eqs. (@eq:steady)–(@eq:warmup) for six warm-up days: (a) temperature profiles; (b) departure from the steady "
             "profile with the real inside temperature. The full correction overshoots the inner panel; the warm-up-aware "
             "correction does not.", 16.0, label="startupfig")

    m.heading("Photovoltaics and storage", 2, label="pvsec")
    m.para(
        "Every EnergyPlus PV cell-temperature model assumes Earth air. Off-Earth, Thermonaut computes the cell "
        "temperature of the equivalent one-diode model [@EPlus262] in Decoupled mode from the steady balance of a thin, "
        "free-standing module with both faces exposed,")
    m.equation(r"\left(\tau\alpha-\eta\right)G=\varepsilon_{f}\sigma\left(T^{4}-T_{f}^{4}\right)+\varepsilon_{b}\sigma\left(T^{4}-T_{b}^{4}\right)+2h\left(T-T_{a}\right)",
               label="pvcell")
    m.para(
        "where G is the plane-of-array irradiance, η the electrical efficiency, ε_{f} = ε_{b} = 0.85, T_{f}⁴ and T_{b}⁴ "
        "the view-weighted fourth powers of the sky and regolith temperatures seen by each face (front sky view "
        "(1 + cos β)/2), and h the coefficient of Eq. (@eq:mixed) on Mars (zero on the Moon). The balance is solved by "
        "Newton iteration inside the engine's efficiency loop, which restarts every time step and repeats until η "
        "changes by less than 0.1%. Mutual shading and radiative coupling within an array are not modelled. The steady "
        "balance neglects heat capacity: for a module of about 4 kJ/(m²K) and a radiative conductance of about "
        "14 W/(m²K) the time constant is about 5 min, close to the 3-min step. Because T ∝ ε^{−1/4} in sunlight, a 10% "
        "change in emissivity changes the sunlit cell temperature by about 2.5% (8 K). The Li-ion battery model runs "
        "unchanged but must sit in a zone, so that its losses become cabin heat.")

    m.heading("Refusing what cannot be right", 2, label="refuse")
    m.para(
        "After input processing a validator stops the run if any refused object type is present, whether or not it is "
        "used: windows; infiltration and ventilation; outdoor-air controllers, mixers, nodes and outdoor-air zone "
        "units; air- and evaporatively cooled condensers, chillers and coils; cooling towers and fluid coolers; "
        "heat-pump water heaters with outdoor-air inlets; combustion and wind generators; ground heat exchangers, "
        "EcoRoof and solar collectors; Sandia, PVWatts and dynamic PV models; batteries without a zone; Kiva and "
        "AirflowNetwork; design days and sizing; SimpleCombined outside convection; one time step per hour (at which "
        "EnergyPlus evaluates the sun at mid-hour); and water use without a scheduled mains temperature (full list with "
        "reasons in supplementary material S9). As a backstop, a planetary run stops at the start of the next day if "
        "any component has registered an outdoor-air node, whether or not its type is listed.")


# =========================================================================== verification
def verif_intro(m):
    m.para(
        "Each result below is reported at the level of evidence it supports (Table @tab:vv). No system-level validation "
        "exists: there is no measured habitat-scale dataset, and none of the checks should be read as validation of a "
        "complete habitat's thermal response.")
    rows = [
        ["1 Software regression", "Earth results unchanged", f"{N_EARTH} example files, two climates; {UT['tests']:,} upstream unit tests", sec("earth")],
        ["2 Planetary software tests", "Inputs accepted and refused as specified", f"{TS['total']} end-to-end tests", sec("earth")],
        ["3 Numerical verification", "Implemented equations satisfied", "Closed-form boundary balances; PV residual", sec("indep", "pvver")],
        ["4 Component checks", "Components agree with independent references", "JPL Horizons; Diviner and Apollo; NIST CO2", sec("indep")],
        ["5 Code-to-code", "Two implementations solve the same model alike", "ExoBEM, two habitats, two bodies", sec("cross", "habver")],
        ["6 Sensitivity", "Effect of uncertain inputs and numerics", "Start-up, spin-up, grid, step; regolith, envelope, dust", sec("startupres", "sens")],
        ["– System validation", "Prediction of a real habitat", "Not available", sec("limcore")],
    ]
    m.table(["Level", "What it shows", "Evidence", "Where"], rows,
            "Verification and validation evidence by level.", col_widths_cm=[3.4, 4.4, 5.2, 3.0], font_size=7.5, label="vv")


def verif_earth(m):
    m.heading("Earth regression and planetary software tests", 2, label="earth")
    m.para(
        f"{N_EARTH} example files from the EnergyPlus distribution, chosen to exercise every hook (CTF and CondFD with "
        "k(T), every convection path, ground contact and Kiva, windows and daylighting, sizing, VAV, DX, plant, PV and "
        "batteries, moisture models and solar collectors), were run with an unmodified v26.2.0 build and with "
        "Thermonaut, both release builds from the same compiler (MSVC 14.44, Windows 11), and every number of the "
        f"complete output time series was compared: about {N_VALUES/1e6:.1f} million values per climate. With Chicago "
        f"TMY3 weather {N_IDENT['chicago']} of {N_RUN['chicago']} runnable files and with Phoenix TMY3 weather "
        f"{N_IDENT['phoenix']} of {N_RUN['phoenix']} were bit-for-bit identical; one further file does not run with "
        f"either weather file in either build. The upstream unit tests ({UT['tests']:,} in {UT['suites']} suites) pass "
        "unchanged, but they do not exercise the planetary mode. The claim is therefore bit-for-bit identity for the "
        "tested files, climates and build, which every patch set from M1 to M2e was required to pass (per-file record "
        f"in supplementary material S3). The planetary mode is covered by {TS['total']} end-to-end tests "
        "(supplementary material S4): valid habitat inputs with and without a weather file; weather files for the "
        "wrong body, with a missing column, negative irradiance, missing ground temperature, albedo above 1, unequal "
        "spacing, short coverage or no PWF header; refusal of infiltration, Earth-fitted PV models, a battery without "
        "a zone, a negative horizon, SimpleCombined convection, one step per hour, unscheduled water mains, EcoRoof, "
        "windows and an air-cooled chiller; and a Site:PlanetaryBody object with Body = Earth, whose output is identical "
        f"to that of the same file without it. All {TS['passed']} pass.")


def verif_independent(m):
    hm, hr = HZ["moon_equator"], HZ["mars_jezero"]
    mv, mc = BC["moon_vacuum"], BC["mars_convection"]
    dz = RB["depth"]
    m.heading("Numerical and component checks against independent references", 2, label="indep")
    rows = [
        ["Solar altitude, lunar equator, 59 d (4)", "JPL Horizons [@Horizons]",
         f"RMSE {hm['rmse_all_deg']:.2f}°; sunlit hours {hm['sunrise_hours_engine']} vs {hm['sunrise_hours_horizons']}"],
        ["Solar altitude, Jezero, 31 d (4)", "JPL Horizons [@Horizons]", f"RMSE {hr['rmse_all_deg']:.2f}° (sunlit bias {hr['bias_sunlit_deg']:+.2f}°)"],
        ["Lunar equatorial surface, noon / pre-dawn (4)", "≈385–390 K / ≈95 K, Diviner [@Vasavada2012]", f"{MR['Tg_max_K']:.0f} K / {MR['Tg_min_K']:.0f} K"],
        ["Lunar regolith at 1 m (4)", "≈252–256 K, Diviner-constrained model, Apollo heat flow [@Vasavada2012;Hayne2017]",
         f"{dz['1.0']:.1f} K (0.5 m {dz['0.5']:.0f} K; 2 m {dz['2.0']:.0f} K; 3 m {dz['3.0']:.0f} K)"],
        ["Convection in vacuum, every outer face (3)", "Zero", f"Zero over {mv['steps']:,} face-steps"],
        ["Net long-wave on outer faces in vacuum (3)", "εσ[F_{sky}(T_{sky}⁴ − T⁴) + F_{g}(T_{g}⁴ − T⁴)]",
         f"RMSE {mv['lw_residual_rmse_W_m2']:.2f} W/m² (mean magnitude {mv['lw_mean_abs_W_m2']:.0f} W/m²)"],
        ["Martian exterior convection (4, properties)", "Same correlations with NIST CO2 at 700 Pa [@NISTWebBook]",
         f"{mc['rel_diff_mean_pct']:+.1f}% (RMSE {mc['rel_diff_rmse_pct']:.1f}%)"],
    ]
    m.table(["Quantity (level)", "Independent reference", "Thermonaut"], rows,
            "Numerical and component checks against references independent of this work.",
            col_widths_cm=[4.6, 5.6, 5.8], font_size=7.3, label="indep")
    m.para(
        f"The sun follows the Horizons ephemeris within {hm['rmse_all_deg']:.2f}° on the Moon and {hr['rmse_all_deg']:.2f}° on "
        "Mars; the Martian bias comes from the EnergyPlus convention of evaluating the sun at the end of each 3-min step, "
        "during which the Sun moves 0.7°. The regolith reproduces the Diviner noon and pre-dawn temperatures and, at the "
        f"depth of the reference, gives {dz['1.0']:.0f} K at 1 m against ≈252–256 K, itself uncertain by a few kelvin. "
        "In vacuum the exterior boundary satisfies its defining equations; the few larger long-wave residuals occur in "
        "the step in which sunlight reaches or leaves a wall and its temperature jumps by 30–37 K, because EnergyPlus "
        "linearizes long-wave exchange about the previous temperature, on Earth as here. The Martian convection check "
        "confirms the implemented calculation and the engine's gas-property fits, not the correlations themselves, whose "
        f"applicability is discussed in {sec('extbc')}.")


def verif_cross(m):
    hb = F["habitat"]
    m.heading("Code-to-code comparison: regolith-shielded module", 2, label="cross")
    m.para(
        "The complete response was compared with ExoBEM [@ZhangExoBEM], a Python implementation of the same planetary "
        "model by the same authors. The two codes share the physical model (the equations and parameters of sun, "
        "environment, boundaries and cabin) and the weather format, but no code; they differ in language, conduction "
        "solver (CondFD or CTF versus finite volumes on stretched grids), grids, surface–air coupling (iterative versus "
        "simultaneous) and start-up. Agreement therefore shows that both solve that model alike [@Oberkampf2010], not "
        "that the model is right, and it cannot reveal an error the two share. Two habitats were used "
        "(Fig. @fig:habitats).")
    m.figure(FIG / "core_fig5_habitats.png",
             "The two habitats, drawn from the input-file vertices: (a) the regolith-shielded module; (b) the "
             "NASA-informed four-crew lunar habitat. (c, d) Habitat (b) at the lunar equator over 30 days: sensible and "
             "latent cooling and outer-face temperatures, ExoBEM (solid) and Thermonaut (dashed).", 16.0, label="habitats")
    m.para(
        f"The module is a horizontal cylinder (radius {hb['radius_m']:.0f} m, length {hb['length_m']:.0f} m, {hb['facets']} "
        f"facets) under {hb['cover_m']:.0f} m of regolith over MLI (Moon) or 20 mm of aerogel (Mars), with a "
        f"{hb['cabin_kPa']} kPa, {100*hb['o2']:.1f}% O2 cabin, {hb['gains_W']:,.0f} W of gains and ideal loads at "
        f"{hb['setpoints_C'][0]}–{hb['setpoints_C'][1]} °C, at 3-min steps, for two lunations at the lunar equator and 31 "
        "days at Jezero from 1 January 2030. CondFD cannot resolve the 4 mm aluminium wall at this step, so its capacity "
        "was lumped into the panel. Thermonaut ran with its own generator and with the weather file ExoBEM wrote; the "
        "latter fixes the environment and isolates the heat balance (Table @tab:cross).")
    rows = [
        ["Sensible cooling, generator / PWF / ExoBEM (kWh)",
         f"{CMg['energy']['ep_cooling_kWh']:.0f} / {CM['energy']['ep_cooling_kWh']:.0f} / {CM['energy']['py_cooling_kWh']:.0f} ({MOON_DIFF_G:+.2f}% / {MOON_DIFF:+.2f}%)",
         f"{CRg['energy']['ep_cooling_kWh']:.0f} / {CR['energy']['ep_cooling_kWh']:.0f} / {CR['energy']['py_cooling_kWh']:.0f} ({MARS_DIFF_G:+.2f}% / {MARS_DIFF:+.2f}%)"],
        ["Hourly cooling RMSE, generator / PWF (W)", f"{CMg['Qc']['rmse']:.1f} / {CM['Qc']['rmse']:.1f}", f"{CRg['Qc']['rmse']:.0f} / {CR['Qc']['rmse']:.0f}"],
        ["Regolith surface RMSE, generator (K)", f"{CMg['Tg']['rmse']:.2f}", f"{CRg['Tg']['rmse']:.2f}"],
        ["Direct normal irradiance R² / RMSE, generator (W/m²)", f"{CMg['beam']['r2']:.4f} / {CMg['beam']['rmse']:.1f}",
         f"{CRg['beam']['r2']:.4f} / {CRg['beam']['rmse']:.1f}"],
        ["Top facet outer / inner face RMSE, PWF (K)", f"{CM['top']['rmse']:.2f} / {CM['tin_top']['rmse']:.3f}", f"{CR['top']['rmse']:.2f} / {CR['tin_top']['rmse']:.2f}"],
    ]
    m.table(["Quantity (hourly values)", "Moon, 2nd lunation (720 h)", "Mars, days 16–31 (384 h)"], rows,
            "Code-to-code comparison for the regolith-shielded module.", col_widths_cm=[6.0, 5.0, 5.0], font_size=7.5, label="cross")
    m.figure(FIG / "core_fig3_environment.png",
             "Environment generated by Thermonaut (dashed) and ExoBEM (solid) at the lunar equator (left) and Jezero "
             "(right): (a, b) solar altitude, (c, d) direct normal and diffuse irradiance, (e, f) regolith surface and sky "
             "temperatures.", 16.0, label="coreenv")
    m.para(
        f"The generated environments agree closely (Fig. @fig:coreenv), and the responses within {abs(MOON_DIFF):.2f}% "
        f"(Moon) and {abs(MARS_DIFF):.1f}% (Mars) in cooling energy (Fig. @fig:coreresp). Because the weather-file run "
        "removes every environment difference without reducing the residual, the residual lies in the heat balance: in "
        "the codes' initial regolith states, whose memory outlasts the comparison window (Section @sec:startupres), and "
        "in their grids.")
    m.figure(FIG / "core_fig4_response.png",
             "Response of the regolith-shielded module, Thermonaut reading the weather file (dashed) and ExoBEM (solid): "
             "(a, b) sensible cooling, (c, d) outer and (e, f) inner face of the top facet. Shading: comparison window.",
             16.0, label="coreresp")


def verif_startup(m):
    m.heading("Start-up of regolith-covered walls", 2, label="startupres")
    rows = [[r[0].replace(" C ", " °C "), r[1] if r[1] is not None else "not run",
             r[2], "—" if (r[3] is None or "�" in str(r[3])) else r[3]] for r in F["startup_ablation"]["rows"]]
    sp, st = RB["spinup"], RB["startup"]
    st_max = max(abs(v["vs_base_pct"]) for k, v in st.items() if k != "warmup_min20")
    m.para(
        "The start-up mattered more than any other choice (Table @tab:startup). With the EnergyPlus default the Mars "
        "cooling over the comparison window was 32% higher than in ExoBEM, because the regolith was still releasing the "
        "heat of its warm start. A steady profile reduced the difference to −2.5%; the k(T) profile with the full "
        "correction brought the windows within 0.01% (Moon) and 0.9% (Mars) but left a transient of 2.4 kW on the Moon "
        "at the start of the run, caused by the overshoot of Fig. @fig:startupfig; the warm-up-aware correction "
        "removes it.")
    m.table(["Start-up treatment of CondFD walls", "Moon vs ExoBEM (%)", "Mars vs ExoBEM (%)", "First-hour excess, Moon / Mars (W)"], rows,
            "Effect of the start-up treatment (generator mode; the first two rows predate the M2c Mars long-wave update).",
            col_widths_cm=[7.2, 2.6, 2.6, 3.6], font_size=7.5, label="startup")
    m.para(
        "Two further tests bound what remains. Against a long spin-up that needs no correction, a 25-month Mars run and "
        f"a 31-day run ending on the same date differ by {sp['mars_short_vs_long_pct']:+.2f}% in cooling over the final "
        f"16 days, whereas a 36-month and a two-lunation lunar run differ by {sp['moon_short_vs_long_pct']:+.1f}% over "
        "the final lunation: the corrected start is effectively at equilibrium on Mars, while the lunar regolith, whose "
        "time constant is years, keeps about 1% of start-up memory after two lunations. The 31-day Mars result changes "
        f"by at most {st_max:.2f}% when the minimum warm-up is shortened from 6 to 1 day, the CondFD space-discretization "
        "constant changed from 30 to 10 or 90, or the time step from 3 to 2 or 6 min, and by "
        f"{st['warmup_min20']['vs_base_pct']:+.2f}% when warm-up is extended to 20 days, which repeats the first day's "
        "forcing long enough to shift the deep state (supplementary material S5). For lunar design studies a one-year "
        "spin-up is therefore advisable. The lesson applies beyond planetary habitats: any construction whose time "
        "constant exceeds the warm-up period, such as an earth-sheltered wall or a thick slab, inherits its initial "
        "state for months.")


def verif_habitat(m):
    e = LH["energy"]
    hu_t, hu_p = HU["engine"], HU["exobem"]
    m.heading("Code-to-code comparison: NASA-informed lunar habitat", 2, label="habver")
    m.para(
        "The second case is a representative four-crew lunar habitat informed by NASA surface-habitat studies "
        f"[@Kessler2022;Burke2022;Schunk2022]: a vertical cylinder of 6.5 m diameter and 5.25 m height ({LHF['volume_m3']:.0f} m³) "
        "on legs, with beta cloth, MLI (R 19.2 m²K/W), 4 mm aluminium and a 10 mm panel; a 56.5 kPa, 34% O2 cabin at "
        "20–25 °C and 30–60% relative humidity; about 14 kW of electric power inside the shell, partly removed by cold "
        "plates and partly leaving as electrolysis products; BVAD crew heat and moisture [@Anderson2018]; and internal "
        "mass. It is a design benchmark, not an official NASA configuration: supplementary material S7 gives the source "
        "of each input, separating values from NASA documents, values derived from them (the MLI resistance, calibrated "
        "to NASA's night-time heat leak) and the authors' assumptions (life-support share of the load, cold-plate "
        "fractions, lighting density). Leakage of 0.05% of the cabin mass per day and two airlock cycles a week need "
        "about 0.3 kg/day of make-up gas; heating it from storage to cabin temperature takes less than 1 W, so the "
        "sealed cabin carries no outdoor-air load. Compression and oxygen generation are life-support electric loads "
        "inside the 14 kW.")
    m.para(
        "Both codes read the same weather file for 30 days at the lunar equator; the engine's input was written from "
        "ExoBEM's model by a script (CTF, crew latent heat as an OtherEquipment latent fraction, cold-plate and chemical "
        f"shares as its lost fraction, humidistat ideal loads). Over days 4–30 the codes agree within {HAB_S:+.2f}% in "
        f"sensible and {HAB_L:+.1f}% in latent cooling (Table @tab:habver, Fig. @fig:habitats).")
    rows = [
        ["Sensible / latent cooling (kWh)", f"{e['ep_sensible_kWh']:.0f} / {e['ep_latent_kWh']:.0f}", f"{e['py_sensible_kWh']:.0f} / {e['py_latent_kWh']:.0f}",
         f"{HAB_S:+.2f}% / {HAB_L:+.1f}%"],
        ["Outer-face RMSE, south wall / roof / floor (K)", "", "",
         f"{LH['wall_05']['outside_rmse']:.2f} / {LH['roof']['outside_rmse']:.2f} / {LH['floor']['outside_rmse']:.2f}"],
        ["Cabin relative humidity (%)", f"{hu_t['rh_min']:.0f}–{hu_t['rh_max']:.0f}", f"{hu_p['rh_min']:.0f}", "ideal-loads convention"],
        ["Cabin dew point (°C)", f"{hu_t['dew_min']:.1f}–{hu_t['dew_max']:.1f}", f"{hu_p['dew_min']:.1f}", ""],
        ["Coldest inside surface minus dew point (K)", f"{hu_t['margin_min_K']:.1f}", f"{hu_p['margin_min_K']:.1f}",
         f"{hu_t['margin_min_K'] - hu_p['margin_min_K']:+.1f} K"],
        ["Run time, 30 days at 3-min steps (s)", f"{RT['habitat_cpp']:.1f}", f"{RT['habitat_python']:.0f}", ""],
    ]
    m.table(["Quantity", "Thermonaut", "ExoBEM", "Difference"], rows,
            "Lunar habitat at the lunar equator, days 4–30, both codes on the same weather file.",
            col_widths_cm=[5.8, 2.8, 2.6, 4.8], font_size=7.5, label="habver")
    m.para(
        "The humidity results differ in kind. EnergyPlus's ideal-loads system dries the supply air while it cools, so the "
        f"cabin settles at {hu_t['rh_min']:.0f}–{hu_t['rh_max']:.0f}% instead of the 60% limit that ExoBEM's condensing "
        "heat exchanger holds. The latent energy agrees because over time both remove the crew's moisture, but the "
        "moisture state does not: the engine's lower dew point overstates the margin of the coldest inside surface by "
        f"{hu_t['margin_min_K'] - hu_p['margin_min_K']:.1f} K. Neither code predicts condensation for this well-insulated "
        "habitat, and neither models condensation, frost or moisture storage in the envelope, so condensation risk "
        "should not be judged from ideal-loads results.")

    m.heading("PV cell temperature in vacuum", 2, label="pvver")
    h, ea = PV["PV_H"], PV["PV_E"]
    m.para(
        "Two one-diode modules (horizontal and east-facing) on detached shading surfaces of the lunar module case were "
        "checked against Eq. (@eq:pvcell) at every step: a check of numerical closure, not a comparison with measured "
        f"module temperatures. The 99th-percentile residual is {h['residual_p99_W_m2']:.3f} W/m² (horizontal) and "
        f"{ea['residual_p99_W_m2']:.3f} W/m² (east); larger residuals occur only below the engine's 30 W/m² insolation "
        f"threshold or when its efficiency loop exits after one pass. Sunlit cells reach {h['Tcell_sunlit_max_K']:.0f}–"
        f"{ea['Tcell_sunlit_max_K']:.0f} K and fall to {h['Tcell_min_K']:.0f} K at night, when a horizontal module faces the "
        "2.7 K sky with its front and the 94 K regolith with its back, so that T⁴ ≈ T_{g}⁴/2.")


def sensitivity(m):
    m.heading("Sensitivity to uncertain planetary inputs", 2, label="sens")
    pm = RB["params"]
    lab = {"regolith_albedo_0.07": "Regolith albedo 0.07 / 0.17 (0.12)", "regolith_emissivity_0.90": "Regolith emissivity 0.90 / 0.99 (0.95)",
           "horizon_5deg": "Horizon elevation 5° (0°)", "shell_solar_abs_0.3": "Beta-cloth solar absorptance 0.3 / 0.5 (0.4)",
           "shell_emissivity_0.80": "Beta-cloth emissivity 0.80 (0.90)", "mli_R_-25pct": "MLI resistance −25% / +25%",
           "thermal_inertia_250": "Regolith thermal inertia 250 / 450 (350 SI)", "regolith_albedo_0.10": "Regolith albedo 0.10 / 0.18 (0.14)",
           "dust_tau_0.3": "Dust optical depth 0.3 / 1.5 (seasonal)", "wind_1": "Mean wind 1 / 6 m/s (3.2)"}
    pair = {"regolith_albedo_0.07": "regolith_albedo_0.17", "regolith_emissivity_0.90": "regolith_emissivity_0.99",
            "shell_solar_abs_0.3": "shell_solar_abs_0.5", "mli_R_-25pct": "mli_R_+25pct", "thermal_inertia_250": "thermal_inertia_450",
            "regolith_albedo_0.10": "regolith_albedo_0.18", "dust_tau_0.3": "dust_tau_1.5", "wind_1": "wind_6"}
    rows = []
    for body, title in (("moon", "Lunar habitat (MLI shell)"), ("mars", "Mars regolith module (1 m cover)")):
        for k, label in lab.items():
            if k not in pm[body]:
                continue
            v = f"{pm[body][k]['vs_base_pct']:+.1f}%"
            if k in pair and pair[k] in pm[body]:
                v += f" / {pm[body][pair[k]]['vs_base_pct']:+.1f}%"
            rows.append([title, label, v])
    m.table(["Case", "Input changed (base)", "Change in cooling energy"], rows,
            "One-at-a-time sensitivity of the cooling energy (internal generator; lunar habitat days 4–30, Mars module "
            "days 16–31).", col_widths_cm=[4.2, 7.0, 4.8], font_size=7.5, label="sens")
    w = MC["sensitivity"]["wind"]
    m.para(
        "Code-to-code differences of a fraction of a percent are not the uncertainty of a prediction. Table @tab:sens "
        "varies the least certain inputs. For the lunar habitat the MLI resistance dominates and the beta cloth's "
        "optical properties follow, while regolith properties and a modest horizon barely change the load, because "
        "internal gains dominate and the shell sees the regolith only through its floor and lower walls. For the Mars "
        "module the dust optical depth dominates; regolith thermal inertia and albedo matter at the half-percent level, "
        "and wind hardly at all, because the regolith cover isolates the module from surface convection. Exposed Martian "
        f"surfaces are more sensitive: on a horizontal facet h rises from {w[0][1]:.2f} to {w[-1][1]:.2f} W/(m²K) as wind "
        "goes from 0 to 10 m/s and changes by about ±7% for ±100 Pa of pressure, a correction to a radiation-dominated "
        "balance. Several of these sensitivities exceed the code-to-code differences, so design studies should treat "
        "such inputs as ranges.")


# =========================================================================== discussion
def discussion(m):
    m.heading("What the planetary mode can be used for", 2, label="domain")
    m.para(
        "The current version supports envelope, load and power studies of sealed, windowless habitats at equatorial and "
        "mid-latitude lunar sites and on Mars, with prescribed set-points, ideal loads, scheduled internal gains, PV and "
        "batteries, using any EnergyPlus zone, schedule, EMS and output feature that does not need outdoor air. A user "
        "can compare envelopes, regolith shields, set-points, gain schedules and PV and storage sizes, and obtain the "
        "loads that the thermal control system must handle. A user cannot yet design the heat-rejection loop or "
        "radiators, judge condensation risk, model windows, size equipment with design days or model polar terrain, and "
        "should treat results as verified computations of a model that has not been validated against a real habitat. "
        "That validation needs thermal-vacuum tests of a habitat-scale article.")

    m.heading("Limitations", 2, label="limcore")
    m.bullets([
        "**Earth clock on Mars.** Hours are 3600 s, so the Martian day drifts by about 40 min per Earth day against the clock; the physics is right, but schedules cannot follow local solar time.",
        "**Systems.** No space-radiator component, condensing heat exchanger, windows or planetary design days; heat rejection is represented by ideal loads.",
        "**Cabin gas and moisture.** Moist-air psychrometrics at cabin pressure (errors up to 1.4% at 34% O2); no envelope condensation or frost.",
        "**Terrain and radiation.** Uniform horizon, (1 − cos β)/2 ground view, no Earthshine; polar and shadowed terrain outside the verified domain.",
        "**Numerics and controls.** Exterior long-wave coefficients are linearized about the previous step's surface temperature, as on Earth, which matters most in the step when sunlight reaches a wall; controls that read outdoor conditions see the Martian air or, on the Moon, the regolith skin temperature.",
        "**PV.** Emissivity 0.85 on both faces, free-standing modules, no soiling, temperature dependence of optics or array self-shading.",
        "**Evidence.** Code-to-code results come from a second implementation of the same model by the same authors; independent checks are at component level; there is no system-level validation, and no independent group has yet reproduced the cases.",
    ])

    m.heading("Tracking EnergyPlus releases and upstreaming", 2, label="releases")
    m.para(
        "Every change is applied by an idempotent patch script that finds a short, unique anchor in a stock source file "
        "and inserts a hook; a script stops with an error, rather than patching the wrong place, if its anchor has moved. "
        "The scripts have so far been applied only to v26.2.0, so the procedure for a new release is proposed rather "
        "than demonstrated: check out the release tag, run the scripts in order, update moved anchors, review the "
        "refusal list against new object types, and rerun the Earth regression against an unmodified build of the same "
        f"release, the unit tests and the planetary tests. Because the {DIFF['hook_lines_existing_files']} lines of hooks "
        "sit at a few interfaces rather than inside the solvers, most releases should need only anchor updates, and "
        "upstream fixes arrive with each rebase. Releases are tagged by milestone (M2e for this paper). Because every "
        "change is gated on the planetary object and Earth results are unchanged in the tested files, the planetary "
        "mode could be offered upstream as an optional feature through the EnergyPlus new-feature-proposal process. The "
        "intention is to propose it once the sol clock and the space-radiator component of milestone M3 complete the "
        "changes to the time base and plant, so that the proposal covers a stable interface.")

    m.heading("Roadmap", 2, label="roadmap")
    m.para(
        "M3 introduces a sol clock by making the hour length a run-time variable (the audit identified the four lines "
        f"that set the time-step lengths, the {AF['rSecsInHour_physical']} physical uses of the hour constant that must "
        f"follow it and the {AF['rSecsInHour_units']} unit conversions that must not), a cabin gas-mixture block for "
        "psychrometrics, body gravity in every buoyancy model, planetary design days and sizing, a space-radiator plant "
        "component, a planetary condensing heat exchanger that holds the cabin at its humidity limit, terrain horizons, "
        "PV soiling, and windows with vacuum-compatible solvers.")
