"""Build the combined manuscript (ExoBEM and ExoBEM-Core in one paper).

    python paper/archive/combined/build_paper_combined.py   ->  paper/archive/combined/ExoBEM_combined_manuscript.docx
Reuses the sections of the two separate manuscripts (sections_exobem.py, sections_core.py).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "paper" / d) for d in ("common", "ExoBEM", "ExoBEM-Core")]

import sections_core as C  # noqa: E402
import sections_exobem as X  # noqa: E402
from docxkit import build_two_pass  # noqa: E402
from refs import REFS  # noqa: E402
from sections_core import DIFF, KLOC, MARS_DIFF, MOON_DIFF, N_EARTH, N_FIND, N_P0, UT  # noqa: E402
from sections_exobem import EPLUS_MAX_DIFF, f1, meq, v600, v900  # noqa: E402

C.COMBINED = True


def front_matter(m):
    m.para("**Building energy simulation for lunar and Martian habitats: a planetary re-implementation of the "
           "EnergyPlus heat balance and a modified EnergyPlus engine**", align="center", size=15, space_after=12)
    m.para("Liang Zhang^{a,*}", align="center", size=11, space_after=2)
    m.para("^{a} University of Arizona, Tucson, AZ, USA", align="center", size=9.5, space_after=2)
    m.para("^{*} Corresponding author: liangzhang1@arizona.edu", align="center", size=9.5, space_after=2)
    m.para("[Draft for author review — confirm author list, affiliations, funding and target journal before submission.]",
           align="center", size=9, italic=True, space_after=14)

    m.heading("Highlights", numbered=False)
    m.bullets([
        "Two tools bring the EnergyPlus heat-balance method to the Moon and Mars: ExoBEM and ExoBEM-Core.",
        f"ExoBEM re-implements the method in Python and matches EnergyPlus 23.2 on Earth within {EPLUS_MAX_DIFF:.1f}%.",
        f"ExoBEM-Core modifies the EnergyPlus v26.2 engine after an audit of {N_FIND} Earth assumptions; Earth results are unchanged.",
        f"The independent tools agree within {abs(MOON_DIFF):.2f}% (Moon) and {abs(MARS_DIFF):.1f}% (Mars) in cooling energy.",
        "Regolith-shielded habitats are nearly adiabatic; heat rejection and storage drive their energy design.",
    ])

    m.heading("Abstract", numbered=False)
    m.para(
        "Building energy simulation (BES) engines such as EnergyPlus encode the Earth in their physics and in their code: "
        "a 24-hour day and a Sun moving 15° per hour, a single air pressure shared by the zone and the outdoors, "
        "convection correlations for air at one atmosphere and sky and ground models that assume an atmosphere. "
        "Future habitats on the Moon and Mars violate all of these. This paper brings the EnergyPlus heat-balance method "
        "to both bodies by two independent routes and uses each to verify the other. ExoBEM re-implements the method in "
        "Python with planetary physics throughout: the Mars24 and selenographic ephemerides, a delta-Eddington dusty "
        "Martian sky, the Hayne et al. lunar regolith model, gas-, pressure- and gravity-aware convection, and radiator "
        f"heat rejection. In Earth mode it reproduces EnergyPlus 23.2 for opaque ASHRAE 140 cases within "
        f"{EPLUS_MAX_DIFF:.1f}% in annual loads, and its planetary models reproduce Mars24, Diviner, Appelbaum–Flood and "
        f"MEDA reference data. ExoBEM-Core modifies the EnergyPlus v26.2 engine itself. An audit of its "
        f"{KLOC:,.0f}-thousand-line C++ code recorded {N_FIND} Earth-specific assumptions; a planetary mode of "
        f"{DIFF['insertions']:,} lines then moves the Sun at the body's rate, generates the planetary environment, "
        "stores the cabin pressure where zone and HVAC models already read it, and replaces the boundary models. Its "
        f"Earth results are bit-for-bit identical to EnergyPlus on {N_EARTH} example files, all {UT['tests']:,} unit tests "
        f"pass, and it agrees with ExoBEM within {abs(MOON_DIFF):.2f}% (Moon) and {abs(MARS_DIFF):.1f}% (Mars) in cooling "
        "energy. Case studies of a four-crew, regolith-shielded habitat show that the envelope is nearly adiabatic, so "
        f"design turns on rejecting {f1(meq['cooling_kWh_per_day'])} kWh per day of internal heat and on storage across "
        "the lunar night or Martian dust storms. Cross-verification also revealed that walls whose time constants exceed "
        "the warm-up period need a physically consistent start-up state.", space_after=6)
    m.para("**Keywords:** building energy simulation; EnergyPlus; lunar habitat; Mars habitat; heat balance; regolith; "
           "code audit; cross-verification", align="left")


def build(m):
    front_matter(m)

    # ======================================================================= 1 introduction
    m.heading("Introduction", label="intro")
    m.para(
        "Whole-building energy simulation has matured over five decades into a reliable design tool for terrestrial "
        "buildings [@Hong2000;Crawley2008]. EnergyPlus is the most widely used open-source engine; its heat-balance "
        "formulation solves coupled surface and zone-air energy balances at sub-hourly time steps and has been tested "
        "against analytical, comparative and empirical benchmarks [@Crawley2001;Strand2001;EPlusEngRef;ASHRAE140]. With "
        "the Artemis program planning sustained surface operations near the lunar south pole and crewed Mars missions "
        "in long-term planning, the questions that BES answers on Earth — how large must the heating, cooling and power "
        "systems be, and how do envelope choices trade against each other — must now be answered for habitats on other "
        "worlds [@Schunk2021;Schunk2022].")
    m.para(
        "The obstacle is that BES engines encode the Earth. The Moon has no atmosphere and a 29.5-day solar day; its "
        "regolith swings between about 95 K and 390 K [@Vasavada2012;Hayne2017]. Mars has an 88,775-second sol, a "
        "600–800 Pa CO2 atmosphere and dust storms that can raise the optical depth above 8 "
        "[@Allison2000;Martinez2017;Guzewich2019]. Inside, habitats operate at reduced pressure and gravity "
        "[@Anderson2018;EAWG2010]. Studies that brought BES tools to Mars did so by writing Martian weather into Earth "
        "weather files [@Lagarde2021;Aydemir2026], which changes neither the length of the day, the solar geometry, the "
        "convective medium nor the ground model.")
    m.para(
        "There are two ways to remove these assumptions. One re-implements the heat-balance method in a new code "
        "designed for planetary physics; it is quick to build and verify but leaves the rest of the engine behind. The "
        "other modifies the engine itself, keeping its HVAC, plant, control and reporting capabilities, but first has "
        "to find every place where the code assumes the Earth. This paper does both and compares them. Its "
        "contributions are: (i) ExoBEM, an open-source Python re-implementation of the EnergyPlus heat-balance method "
        "with planetary ephemerides, environments, regolith and convection, verified against EnergyPlus 23.2 and "
        "against planetary reference data; (ii) a line-level audit of Earth assumptions in the EnergyPlus v26.2 engine; "
        "(iii) ExoBEM-Core, a fork of that engine with a planetary mode that leaves Earth results bit-for-bit "
        "unchanged; (iv) cross-verification of the two independent tools; and (v) case studies of a regolith-shielded "
        "habitat at the lunar equator, a lunar south-polar ridge and Jezero crater.")
    m.para(
        "Section @sec:related reviews related work and how EnergyPlus meets its environment, Section @sec:earthsec the "
        "Earth assumptions and the audit, Section @sec:method ExoBEM, Section @sec:coresec ExoBEM-Core, Section "
        "@sec:verif the verification of both, Section @sec:cases the case studies, Section @sec:disc the discussion and "
        "Section @sec:concl the conclusions.")

    # ======================================================================= 2 related work
    m.heading("Related work", label="related")
    X.related_work(m)
    C.engine_background(m)
    m.heading("Licensing and naming", 2)
    m.para(
        "EnergyPlus is distributed under a BSD-3-Clause-style license that permits modification and redistribution, "
        "including for derived tools, provided the copyright notice is retained, the developers' names are not used for "
        "endorsement, and (clause 4) a modified product is not named \"EnergyPlus\", \"E+\" or a confusingly similar "
        "name without U.S. DOE consent. ExoBEM contains no EnergyPlus source code; it re-implements algorithms documented "
        "in the Engineering Reference [@EPlusEngRef] and credits EnergyPlus in a NOTICE file. ExoBEM-Core is a fork of "
        "the EnergyPlus source; it keeps the original license and notices, states that it is not EnergyPlus and is not "
        "endorsed by DOE or the National Laboratory of the Rockies (formerly NREL), and carries a different name "
        "[@ExoBEMRepo;ExoBEMCoreRepo].")

    # ======================================================================= 3 Earth assumptions
    m.heading("Earth assumptions in building simulation", label="earthsec")
    m.para(
        "Table @tab:earth summarizes, at the level of physics, what a conventional BES engine assumes and what replaces "
        "it on the Moon and Mars. The first route (ExoBEM, Section @sec:method) starts from this list. The second route "
        "(ExoBEM-Core, Section @sec:coresec) needs it at the level of code: where, in which file and line, does the "
        "engine make each assumption? The audit described next answers that question.")
    X.earth_table(m)
    C.audit(m)

    # ======================================================================= 4 ExoBEM
    m.heading("ExoBEM: a planetary re-implementation of the heat-balance method", label="method")
    X.method(m)

    # ======================================================================= 5 ExoBEM-Core
    m.heading("ExoBEM-Core: a planetary mode for the EnergyPlus engine", label="coresec")
    C.design(m)

    # ======================================================================= 6 verification
    m.heading("Verification", label="verif")
    m.para(
        "Verification proceeds in four steps: ExoBEM's terrestrial core against EnergyPlus (Section @sec:vexo), "
        "ExoBEM's planetary models against reference data (Section @sec:vplanet), ExoBEM-Core against unmodified "
        "EnergyPlus on Earth (Section @sec:earth), and the two tools against each other off-Earth (Section @sec:cross).")
    X.verif_eplus(m)
    X.verif_planet(m)
    C.verif_earth(m)
    C.verif_cross(m)
    C.verif_startup(m)

    # ======================================================================= 7 case studies
    m.heading("Case studies", label="cases")
    m.para(
        "The case studies below were computed with ExoBEM, which includes the radiator, heat-pump and power-system "
        "models that ExoBEM-Core does not yet have. Section @sec:cross showed that ExoBEM-Core reproduces ExoBEM's "
        "loads for the same habitat with constant internal gains.")
    X.case_studies(m)

    # ======================================================================= 8 discussion
    m.heading("Discussion", label="disc")
    C.tool_comparison(m)
    X.implications(m)
    X.limitations(m, title="Limitations of ExoBEM")
    C.limitations_core(m, title="Limitations of ExoBEM-Core")
    C.roadmap_core(m)

    # ======================================================================= 9 conclusions
    m.heading("Conclusions", label="concl")
    m.para(
        "This paper brought the EnergyPlus heat-balance method to the Moon and Mars by two independent routes. ExoBEM "
        "re-implements the method with planetary physics; its terrestrial core matches EnergyPlus 23.2 within "
        f"{EPLUS_MAX_DIFF:.1f}% in annual loads and its planetary models reproduce Mars24, Diviner, Appelbaum–Flood and "
        f"MEDA reference data. ExoBEM-Core modifies the EnergyPlus engine itself: an audit found {N_FIND} Earth "
        f"assumptions ({N_P0} blocking a first habitat run), and a planetary mode of {DIFF['insertions']:,} lines removes "
        "them for regolith-shielded habitats while leaving Earth results bit-for-bit unchanged. The two tools agree "
        f"within {abs(MOON_DIFF):.2f}% on the Moon and {abs(MARS_DIFF):.1f}% on Mars in cooling energy, and their "
        "comparison exposed the need to start long-time-constant walls from a consistent state. For a four-crew habitat "
        "under 1 m of regolith the envelope is nearly adiabatic on the Moon; the energy problem becomes rejecting about "
        "3 kW of internal heat, which costs several times more electricity at the lunar equator than at the pole or on "
        "Mars, while dust storms dominate storage on Mars. ExoBEM is suited to fast exploration and serves as the "
        "reference; ExoBEM-Core carries the physics into the full engine. Both are open source.")

    # ======================================================================= back matter
    m.heading("Software and data availability", numbered=False)
    m.para(
        "ExoBEM v0.1.0, its EnergyPlus verification inputs, case-study scripts and the data behind every figure and table "
        "are available at https://github.com/TensorBuildLab/ExoBEM (BSD-3-Clause). ExoBEM-Core, the audit reports and "
        "its verification cases are available at https://github.com/TensorBuildLab/ExoBEM-Core under the EnergyPlus "
        "license. EnergyPlus and the TMY3 weather files are available from the U.S. DOE.")
    m.heading("Declaration of generative AI use", numbered=False)
    m.para(
        "During the preparation of this work the author used Claude (Anthropic) to assist with literature search, the "
        "code audit, software implementation, verification scripting and drafting of the manuscript. The author "
        "reviewed and edited all content and takes full responsibility for the publication. [Authors: confirm and "
        "adapt to the target journal's policy.]")
    m.heading("CRediT authorship contribution statement", numbered=False)
    m.para("[To be completed by the authors.]")
    m.heading("Declaration of competing interest", numbered=False)
    m.para("The authors declare that they have no known competing financial interests or personal relationships that "
           "could have appeared to influence the work reported in this paper.")
    m.heading("Acknowledgements", numbered=False)
    m.para("EnergyPlus is developed by the U.S. Department of Energy's Building Technologies Office, the National "
           "Laboratory of the Rockies (formerly NREL) and their partners; neither ExoBEM nor ExoBEM-Core is endorsed by "
           "them. [Funding to be added.]")

    m.heading("References", numbered=False)
    m.reference_list()


def main():
    m = build_two_pass(build, REFS)
    out = HERE / "ExoBEM_combined_manuscript.docx"
    m.save(out)
    print("saved", out, "| cited", len(m.cite_order), "| figs", m.fig_no, "| tables", m.tab_no, "| eqs", m.eq_no)


if __name__ == "__main__":
    main()
