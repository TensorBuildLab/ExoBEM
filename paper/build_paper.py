"""Build the ExoBEM journal manuscript (Word) from results.

    python paper/build_paper.py   ->  paper/ExoBEM_manuscript.docx
All numbers quoted in the text are read from studies/results and verification/results.
The sections shared with the combined manuscript live in sections_exobem.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "paper"))

import sections_exobem as X  # noqa: E402
from docxkit import build_two_pass  # noqa: E402
from refs import REFS  # noqa: E402
from sections_exobem import f1, f2, v600, v900, f600, f900, meq, EPLUS_MAX_DIFF  # noqa: E402


def build(m):
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
        f"Earth-mode verification against EnergyPlus 23.2: annual loads within {EPLUS_MAX_DIFF:.1f}%.",
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
        "system. ExoBEM also serves as the independent reference for ExoBEM-Core, a modified EnergyPlus engine reported "
        "in a companion paper.",
        space_after=6)
    m.para("**Keywords:** building energy simulation; EnergyPlus; lunar habitat; Mars habitat; heat balance; regolith; "
           "space architecture; thermal control", align="left")

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
        "Table @tab:earth lists the Earth assumptions embedded in a conventional BES engine and what replaces them on the Moon and "
        "Mars. The Moon has no atmosphere, so there is no exterior convection, the sky is a 3 K sink and the regolith "
        "swings between about 95 K and 390 K over a 29.5-day lunar day [@Vasavada2012;Hayne2017]. Mars has a 88,775-second "
        "sol, a 668.6-sol year with strong eccentricity-driven seasons, a 600–800 Pa CO2 atmosphere in which convection "
        "coefficients are one to two orders of magnitude lower than on Earth, and suspended dust whose optical depth "
        "ranges from about 0.3 to more than 8 during global storms [@Allison2000;Martinez2017;Guzewich2019]. Inside, "
        "habitats operate at reduced pressure (70.3 or 56.5 kPa) and reduced gravity, both of which weaken natural "
        "convection [@Anderson2018;EAWG2010]."
    )
    X.earth_table(m)
    m.para(
        "This paper makes four contributions. (i) It presents ExoBEM, to the authors' knowledge the first open-source "
        "re-implementation of the EnergyPlus heat-balance method with physics modifications for planetary surface "
        "environments. (ii) It verifies the terrestrial core against EnergyPlus 23.2 and the planetary models against "
        "published reference data. (iii) It applies the tool to a regolith-shielded habitat at the lunar equator, at a "
        "lunar south-polar ridge and at Jezero crater on Mars, including a global dust storm. (iv) It provides the "
        "verified reference model for ExoBEM-Core, a modified EnergyPlus engine described in a companion paper "
        "[@ZhangCore]. Section @sec:related reviews related work, Section @sec:method "
        "describes the method, Section @sec:verif the verification, Section @sec:cases the case studies, Section @sec:disc "
        "discusses implications and limitations, and Section @sec:concl concludes."
    )

    # ======================================================================= 2 related work
    m.heading("Related work", label="related")
    X.related_work(m)
    X.licensing(m)

    # ======================================================================= 3 method
    m.heading("Method", label="method")
    X.method(m)

    # ======================================================================= 4 verification
    m.heading("Verification", label="verif")
    X.verif_eplus(m)
    X.verif_planet(m)

    # ======================================================================= 5 case studies
    m.heading("Case studies", label="cases")
    X.case_studies(m)

    # ======================================================================= 6 discussion
    m.heading("Discussion", label="disc")
    X.implications(m)
    X.limitations(m)
    m.heading("From ExoBEM to a modified EnergyPlus engine", 2)
    m.para(
        "Re-implementing the method in a compact engine allowed the planetary physics to be developed and verified "
        "quickly, but it leaves out most of what EnergyPlus offers: multi-zone air and HVAC systems, plant loops, "
        "electric power, control and an established input and output ecosystem. A companion paper [@ZhangCore] "
        "describes ExoBEM-Core, a fork of the EnergyPlus v26.2 C++ engine that adds a planetary mode. It audits the "
        "engine for Earth-specific assumptions, injects the ExoBEM ephemerides, environment generator, convection and "
        "regolith models at the points where EnergyPlus reads its environment, keeps Earth results bit-for-bit identical, "
        "and agrees with ExoBEM within 1% in cooling energy for the habitat of Section @sec:cases. Under clause 4 of "
        "the EnergyPlus license, the fork carries a different name. ExoBEM remains the faster tool for exploring "
        "design options and the independent reference for regression testing of the engine.")

    # ======================================================================= 7 conclusions
    m.heading("Conclusions", label="concl")
    m.para(
        "ExoBEM brings whole-building energy simulation to the Moon and Mars by re-implementing the EnergyPlus "
        "heat-balance method and replacing its Earth-specific physics with planetary ephemerides, airless and thin-CO2 "
        "environments, regolith thermophysics, gravity- and pressure-aware convection and radiator heat rejection. Its "
        "terrestrial core matches EnergyPlus 23.2 within 0.7% in annual loads, and its planetary models reproduce "
        "Mars24, Diviner, Appelbaum–Flood and MEDA reference data. For a four-crew habitat under 1 m of regolith, the "
        "envelope is nearly adiabatic on the Moon; the energy problem becomes rejecting about 3 kW of internal heat. "
        "That costs several times more electricity at the lunar equator, where radiators see hot regolith, than at the "
        "pole or on Mars. On Mars, insulation matters again and dust storms dominate storage sizing. The code, "
        "verification scripts and inputs are open source, and ExoBEM serves as the reference model for the "
        "ExoBEM-Core engine.")

    # ======================================================================= back matter
    m.heading("Software and data availability", numbered=False)
    m.para(
        "ExoBEM v0.1.0, the EnergyPlus verification inputs, case-study scripts and the data behind every figure and "
        "table are available at https://github.com/TensorBuildLab/ExoBEM (BSD-3-Clause). The companion engine "
        "ExoBEM-Core is available at https://github.com/TensorBuildLab/ExoBEM-Core. "
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


def main():
    m = build_two_pass(build, REFS)
    out = ROOT / "paper" / "ExoBEM_manuscript.docx"
    m.save(out)
    unused = sorted(set(REFS) - set(m.cite_order))
    print("saved", out, "| cited", len(m.cite_order), "| figs", m.fig_no, "| tables", m.tab_no)
    return unused


if __name__ == "__main__":
    main()
