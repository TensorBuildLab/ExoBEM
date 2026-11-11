"""Build the ExoBEM journal manuscript (Word) from results.

    python paper/ExoBEM/build_paper.py   ->  paper/ExoBEM/ExoBEM_manuscript.docx
All numbers quoted in the text are read from studies/results and verification/results.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT / "paper" / "common")]

import sections_exobem as X  # noqa: E402
from docxkit import build_two_pass  # noqa: E402
from refs import REFS  # noqa: E402
from sections_exobem import (B, CAL, EPLUS_MAX_DIFF, P, f1, f600, f900, f2, mjz, mpo, meq, v600, v900)  # noqa: E402

# Applied Energy: 3-5 highlights, at most 85 characters each, also submitted as a separate file
HIGHLIGHTS = [
    "ExoBEM adapts the EnergyPlus heat balance to sealed habitats on the Moon and Mars.",
    f"Earth-mode verification against EnergyPlus 23.2: annual loads within {EPLUS_MAX_DIFF:.1f}%.",
    "Habitat loads are coupled with PV, battery, fuel-cell and fission power systems.",
    "Sealed-cabin model: no infiltration; leakage, humidity and condensation risk tracked.",
    "Night and dust-storm storage dominates solar power; a 40 kWe fission unit covers all.",
]
assert 3 <= len(HIGHLIGHTS) <= 5 and all(len(h) <= 85 for h in HIGHLIGHTS), [len(h) for h in HIGHLIGHTS]


def build(m):
    # ======================================================================= title page
    m.para("**ExoBEM: building energy simulation of sealed lunar and Martian habitats based on the EnergyPlus "
           "heat-balance method**", align="center", size=15, space_after=12)
    m.para("Liang Zhang^{a,*}", align="center", size=11, space_after=2)
    m.para("^{a} University of Arizona, Tucson, AZ, USA", align="center", size=9.5, space_after=2)
    m.para("^{*} Corresponding author: liangzhang1@arizona.edu", align="center", size=9.5, space_after=2)
    m.para("[Draft for author review — confirm author list, affiliations, funding and target journal before submission.]",
           align="center", size=9, italic=True, space_after=14)

    m.heading("Highlights", numbered=False)
    m.bullets(HIGHLIGHTS)

    m.heading("Abstract", numbered=False)
    m.para(
        "Building energy simulation (BES) programs such as EnergyPlus encode Earth in their physics: a 24-hour day, "
        "terrestrial solar geometry, outdoor air for convection, ventilation and humidity, and empirical sky and ground "
        "models. None of these hold for the sealed, pressurized habitats that crews will live in on the Moon and Mars. "
        "This paper presents ExoBEM, an open-source Python BES tool that re-implements the EnergyPlus heat-balance "
        "method and, starting from a factor-by-factor analysis of how the Moon and Mars differ from Earth, adds "
        "planetary ephemerides, airless and dusty-CO2 skies, regolith ground in periodic equilibrium, gas-, pressure- "
        "and gravity-aware convection, curved regolith shields, a sealed cabin with leakage, airlock losses and "
        "condensation checks, radiator heat rejection and a power system with photovoltaics, batteries, regenerative "
        "fuel cells and fission. Environments are exchanged through a new planetary weather-file format. In Earth mode "
        f"ExoBEM reproduces EnergyPlus 23.2 for opaque ASHRAE 140 cases within {EPLUS_MAX_DIFF:.1f}% in annual loads; its "
        "planetary models reproduce Mars24, Diviner, Appelbaum–Flood and MEDA reference data, and its envelope, "
        "calibrated to NASA's night-time heat leak of the Artemis surface habitat, predicts the daylight loss within "
        f"{abs(CAL['day_error_pct']):.0f}%. For four-crew lunar and six-crew Mars habitats sized from NASA concepts, heat "
        f"rejection dominates ({mpo['tcs_heat_kWh_per_day']/24:.1f} kW and {mjz['tcs_heat_kWh_per_day']/24:.1f} kW on average). "
        f"Equatorial lunar radiators need heat-pump lift {100*meq['heat_pump_hours_frac']:.0f}% of the time, an "
        f"aerogel-only Mars habitat risks condensation for {mjz['condensation_risk_hours']:.0f} hours a year, and storage "
        "across the lunar night or a dust storm dominates solar power, while a 40 kWe fission unit covers every case.",
        space_after=6)
    m.para("**Keywords:** building energy simulation; EnergyPlus; lunar habitat; Mars habitat; heat balance; regolith; "
           "humidity; power systems; space architecture", align="left")

    # ======================================================================= 1 introduction
    m.heading("Introduction", label="intro")
    m.para(
        "Whole-building energy simulation has matured over five decades into a reliable design tool for terrestrial "
        "buildings [@Hong2000;Crawley2008]. EnergyPlus, developed by the U.S. Department of Energy, is the most widely "
        "used open-source engine; its heat-balance formulation solves coupled surface and zone-air energy balances at "
        "sub-hourly time steps and has been tested against analytical, comparative and empirical benchmarks "
        "[@Crawley2001;Strand2001;EPlusEngRef;ASHRAE140]. With the Artemis program planning sustained surface operations "
        "near the lunar south pole and with crewed Mars missions in long-term planning, the same questions that BES answers "
        "on Earth — how large must the heating, cooling and power systems be, and how do envelope choices trade against "
        "each other — must now be answered for the first habitats on other worlds [@Schunk2021;Schunk2022;Drake2009].")
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
        "length of the day, the solar geometry, the convective medium nor the ground model, and an Earth engine still "
        "exchanges air and moisture with the outdoors.")
    m.para(
        "Getting this right matters because the result will size life-critical systems. This work therefore starts from "
        "a systematic analysis of every factor that distinguishes a sealed planetary habitat from an Earth building "
        "(Section @sec:factors, Table @tab:factors) and makes each one either a modelled physical process, a documented "
        "input, a check that stops an invalid run, or an explicitly justified omission. The paper makes five "
        "contributions. (i) It presents ExoBEM, to the authors' knowledge the first open-source re-implementation of the "
        "EnergyPlus heat-balance method for planetary surface habitats, distributed as an installable Python package with "
        "a tutorial. (ii) It explains how the tool coordinates its components and how it relates, element by element, to "
        "EnergyPlus. (iii) It adds the sealed-cabin physics (leakage, airlock losses, humidity, condensation risk), a "
        "planetary weather-file format and an electric power system to the building model. (iv) It verifies the "
        "terrestrial core against EnergyPlus 23.2, the planetary models against reference data and the envelope against "
        "NASA's thermal analysis of the Artemis surface habitat. (v) It applies the tool to NASA-class habitats for the "
        "first crews on the Moon and Mars. The companion engine ExoBEM-Core carries the same physics into the "
        "EnergyPlus code itself and uses ExoBEM as its reference [@ZhangCore]. Section @sec:related reviews related "
        "work, Section @sec:factors analyzes the planetary factors, Section @sec:method describes the method, Section "
        "@sec:verif the verification, Section @sec:cases the case studies and Section @sec:disc the implications and "
        "limitations; Appendix A shows how to use the tool.")

    # ======================================================================= 2 related work
    m.heading("Related work", label="related")
    X.related_work(m)
    X.licensing(m)

    # ======================================================================= 3 factors
    m.heading("What changes on the Moon and Mars", label="factors")
    m.para(
        "Table @tab:factors lists, category by category, the factors that set the energy balance of a building and how "
        "each changes on the Moon and Mars. Time and Sun: the lunar day lasts 29.5 Earth days and the Martian sol 24.66 h, "
        "Mars has strong orbital seasons, and polar terrain hides the Sun for days. Atmosphere and sky: the Moon has no "
        "atmosphere, so there is no convection, no diffuse light and a 2.7 K sky; Mars has a thin, dusty CO2 atmosphere "
        "whose dust can blot out the Sun for weeks. Ground: regolith is a superb insulator on the Moon and swings by "
        "about 290 K over a lunar day. Envelope: radiation shields of regolith add months to years of thermal time "
        "constant, multi-layer insulation works in vacuum but not in Martian CO2, and the cabin is a pressure vessel "
        "with no windows to speak of. Cabin: there is no outdoor air at all; the only exchanges are leakage and airlock "
        "venting, all moisture comes from the crew and must be condensed out, the gas is at reduced pressure and raised "
        "oxygen fraction, and natural convection is weakened by low gravity. Systems: heat can only be radiated, and "
        "electric power must be generated and stored on site through the night, polar eclipses or dust storms. The "
        "last column of Table @tab:factors states how ExoBEM treats each factor; the following section gives the "
        "equations.")
    X.factor_table(m)

    # ======================================================================= 4 method
    m.heading("Method", label="method")
    X.method(m)

    # ======================================================================= 5 verification
    m.heading("Verification", label="verif")
    X.verif_eplus(m)
    X.verif_planet(m)

    # ======================================================================= 6 case studies
    m.heading("Case studies", label="cases")
    X.case_studies(m)

    # ======================================================================= 7 discussion
    m.heading("Discussion", label="disc")
    X.implications(m)
    X.limitations(m)
    m.heading("Relation to the EnergyPlus engine", 2)
    m.para(
        "Re-implementing the method in a compact engine allowed the planetary physics to be developed and verified "
        "quickly, but it leaves out most of what EnergyPlus offers: multi-zone air and HVAC systems, plant loops, "
        "controls and an established input and output ecosystem. A companion paper [@ZhangCore] describes ExoBEM-Core, "
        "a fork of the EnergyPlus v26.2 C++ engine that adds a planetary mode with the same physics, reads the same "
        "planetary weather files, keeps Earth results bit-for-bit identical, and agrees with ExoBEM within 1% in cooling "
        "energy for a lunar and a Martian habitat. ExoBEM remains the faster tool for exploring design options, sizing "
        "power systems and studying humidity, and the independent reference for regression testing of the engine.")

    # ======================================================================= 8 conclusions
    m.heading("Conclusions", label="concl")
    m.para(
        "ExoBEM brings whole-building energy simulation to sealed habitats on the Moon and Mars. It re-implements the "
        "EnergyPlus heat-balance method and, guided by a systematic analysis of how the Moon and Mars differ from Earth, "
        "replaces its Earth-specific physics with planetary ephemerides, airless and dusty skies, equilibrated regolith "
        "ground, gravity- and pressure-aware convection, curved shields, a sealed cabin with leakage, airlock losses and "
        "humidity, radiator heat rejection and an on-site power system, all driven by a documented planetary weather "
        f"format. Its terrestrial core matches EnergyPlus 23.2 within {EPLUS_MAX_DIFF:.1f}% in annual loads, its "
        "planetary models reproduce Mars24, Diviner, Appelbaum–Flood and MEDA reference data, and its envelope model "
        "reproduces NASA's thermal analysis of the Artemis surface habitat. For NASA-class habitats for the first crews "
        f"the design problem is to reject {mpo['tcs_heat_kWh_per_day']/24:.0f}–{meq['tcs_heat_kWh_per_day']/24:.0f} kW of "
        "internal heat, which costs heat-pump power at the lunar equator but almost none at the pole or on Mars; to keep "
        "the inner surfaces of a Mars habitat above the dew point, which aerogel alone does not achieve; and to store "
        "energy through the lunar night, polar eclipses or dust storms, which favours large arrays on Mars and fission "
        "where darkness lasts. The package, tutorial, weather files and every script behind this paper are open source.")

    # ======================================================================= back matter
    m.heading("Software and data availability", numbered=False)
    m.para(
        "ExoBEM v0.2.0 is available at https://github.com/TensorBuildLab/ExoBEM (BSD-3-Clause) and is installed with "
        "python -m pip install \"exobem[plot] @ git+https://github.com/TensorBuildLab/ExoBEM\". The repository contains "
        "the tutorial (docs/tutorial), the planetary weather-format specification (docs/weather_format.md), the example "
        "models and weather files, the EnergyPlus verification inputs, the case-study scripts and the data behind every "
        "figure and table. The companion engine ExoBEM-Core is at https://github.com/TensorBuildLab/ExoBEM-Core. "
        "EnergyPlus 23.2 and the TMY3 weather file are available from the U.S. DOE.")
    m.heading("Declaration of generative AI use", numbered=False)
    m.para(
        "During the preparation of this work the author used Claude (Anthropic) to assist with literature search, "
        "software implementation, an independent review of the equations, verification scripting and drafting of the "
        "manuscript. The author reviewed and edited all content and takes full responsibility for the publication. "
        "[Authors: confirm and adapt to the target journal's policy.]")
    m.heading("CRediT authorship contribution statement", numbered=False)
    m.para("[To be completed by the authors.]")
    m.heading("Declaration of competing interest", numbered=False)
    m.para("The authors declare that they have no known competing financial interests or personal relationships that "
           "could have appeared to influence the work reported in this paper.")
    m.heading("Acknowledgements", numbered=False)
    m.para("EnergyPlus is developed by the U.S. Department of Energy's Building Technologies Office and its national "
           "laboratory and university partners; ExoBEM is not endorsed by them. [Funding to be added.]")

    X.appendix_tutorial(m)
    X.appendix_pwf(m)

    m.heading("References", numbered=False)
    m.reference_list()


def main():
    m = build_two_pass(build, REFS)
    out = HERE / "ExoBEM_manuscript.docx"
    m.save(out)
    print("saved", out, "| cited", len(m.cite_order), "| figs", m.fig_no, "| tables", m.tab_no, "| eqs", m.eq_no)
    from docx import Document
    d = Document()
    d.add_heading("Highlights", level=1)
    for h in HIGHLIGHTS:
        d.add_paragraph(h, style="List Bullet")
    d.save(HERE / "ExoBEM_highlights.docx")
    print("saved", HERE / "ExoBEM_highlights.docx")


if __name__ == "__main__":
    main()
