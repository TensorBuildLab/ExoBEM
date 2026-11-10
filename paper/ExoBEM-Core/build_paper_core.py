"""Build the ExoBEM-Core journal manuscript (Word).

    python paper/ExoBEM-Core/extract_core_data.py      (once, needs the ExoBEM-Core checkout and runs)
    python paper/ExoBEM-Core/build_figures_core.py
    python paper/ExoBEM-Core/build_paper_core.py   ->  paper/ExoBEM-Core/ExoBEM-Core_manuscript.docx
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT / "paper" / "common")]

import sections_core as C  # noqa: E402
from docxkit import build_two_pass  # noqa: E402
from refs import REFS  # noqa: E402
from sections_core import (DIFF, KLOC, MARS_DIFF, MOON_DIFF, N_EARTH, N_FIND, N_P0, UT)  # noqa: E402


def front_matter(m):
    m.para("**ExoBEM-Core: auditing and adapting the EnergyPlus engine for building energy simulation on the Moon "
           "and Mars**", align="center", size=15, space_after=12)
    m.para("Liang Zhang^{a,*}", align="center", size=11, space_after=2)
    m.para("^{a} University of Arizona, Tucson, AZ, USA", align="center", size=9.5, space_after=2)
    m.para("^{*} Corresponding author: liangzhang1@arizona.edu", align="center", size=9.5, space_after=2)
    m.para("[Draft for author review — confirm author list, affiliations, funding and target journal before submission.]",
           align="center", size=9, italic=True, space_after=14)

    m.heading("Highlights", numbered=False)
    m.bullets([
        f"An audit of the EnergyPlus v26.2 engine found {N_FIND} Earth-specific assumptions in six subsystems.",
        f"A planetary mode adds {DIFF['insertions']:,} lines to the engine; Earth results stay bit-for-bit identical.",
        "A body-specific hour-angle rate and a cabin-pressure convention let the existing heat balance run off-Earth.",
        f"Cross-verified against an independent model: cooling within {abs(MOON_DIFF):.2f}% (Moon) and {abs(MARS_DIFF):.1f}% (Mars).",
        "Regolith-covered walls need a steady start-up profile; the default start gave a 32% load error.",
    ])

    m.heading("Abstract", numbered=False)
    m.para(
        "Building energy simulation engines such as EnergyPlus encode the Earth in many places at once: in the length of "
        "the hour and the motion of the Sun, in a single air pressure shared by the zone and the outdoors, in convection "
        "correlations for air at one atmosphere and in sky and ground models that assume an atmosphere. Simulating a "
        "habitat on the Moon or Mars with such an engine requires more than a new weather file. This paper reports "
        f"ExoBEM-Core, a research fork of the EnergyPlus v26.2 engine with a planetary mode. A systematic audit of the "
        f"{KLOC:,.0f}-thousand-line C++ code base recorded {N_FIND} Earth-specific assumptions with file and line, "
        f"{N_P0} of them blocking a first habitat simulation. Guided by three rules (Earth results must stay bit-for-bit "
        "identical, existing physics is reused rather than rewritten, and inputs that cannot be right off-Earth are "
        f"refused), the planetary mode adds {DIFF['insertions']:,} lines. It keeps the Earth clock but moves the Sun at "
        "the body's rate with a daily fit to the Mars24 or lunar ephemeris; replaces the weather with a generated "
        "planetary environment including a spun-up regolith column; stores the cabin pressure in the variable that zone "
        "and HVAC models already read; and replaces the exterior and interior boundary models with vacuum, thin-CO2 and "
        f"cabin-gas physics. On Earth, {N_EARTH} EnergyPlus example files give bit-for-bit identical results and all "
        f"{UT['tests']:,} unit tests pass. For a regolith-shielded habitat, ExoBEM-Core agrees with the independent "
        f"Python model ExoBEM within {abs(MOON_DIFF):.2f}% in cooling energy at the lunar equator and {abs(MARS_DIFF):.1f}% "
        "at Jezero crater, with regolith surface temperatures within 0.05–0.21 K RMSE. The comparison exposed a "
        "general problem: walls whose time constant exceeds the warm-up period inherit their initial state, which "
        "caused a 32% load error until a steady start-up profile was introduced.", space_after=6)
    m.para("**Keywords:** EnergyPlus; building energy simulation; software verification; lunar habitat; Mars habitat; "
           "regolith; code audit", align="left")


def build(m):
    front_matter(m)

    # ======================================================================= 1 introduction
    m.heading("Introduction", label="intro")
    m.para(
        "Crewed surface habitats on the Moon and Mars will be buildings in the most literal sense: enclosed, occupied "
        "volumes whose heating, cooling and power systems must be sized for a climate, a schedule and an envelope "
        "[@Schunk2021;Schunk2022]. Building energy simulation (BES) answers these questions on Earth, and EnergyPlus is "
        "its most widely used open-source engine, with a heat-balance formulation that has been tested against "
        "analytical, comparative and empirical benchmarks for two decades [@Crawley2001;Strand2001;EPlus262;ASHRAE140]. "
        "A planetary habitat, however, violates assumptions that are built into such engines: the Moon's day lasts 29.5 "
        "Earth days and it has no atmosphere; Mars has an 88,775-second sol and a 600–800 Pa CO2 atmosphere; and the cabin "
        "air is at a pressure unrelated to the outdoors [@Hayne2017;Allison2000;Anderson2018].")
    m.para(
        "A companion paper presents ExoBEM, a compact Python re-implementation of the EnergyPlus heat-balance method "
        "with planetary physics, verified against EnergyPlus on Earth and against planetary reference data "
        "[@ZhangExoBEM]. A re-implementation is quick to build and easy to verify, but it gives up most of what the "
        "full engine offers. This paper takes the other route and modifies the EnergyPlus engine itself. The main "
        "difficulty is not the planetary physics, which ExoBEM already provides, but finding every place where a "
        "large engine silently assumes the Earth, and changing them without disturbing terrestrial results.")
    m.para(
        "The paper makes four contributions. (i) A systematic, line-level audit of Earth-specific assumptions in "
        "EnergyPlus v26.2, organized by subsystem and by what must change for a first planetary simulation. (ii) The "
        "design and implementation of a planetary mode in a fork named ExoBEM-Core, built on three rules that keep "
        "Earth results bit-for-bit identical. (iii) Verification on Earth by full-output regression and the unit-test "
        "suite, and off-Earth by cross-verification against the independent ExoBEM code. (iv) Lessons for adapting "
        "engines, notably the start-up of walls whose time constants exceed the warm-up period. Section @sec:bg "
        "reviews how EnergyPlus meets its environment and the routes to off-Earth simulation, Section @sec:auditsec "
        "the audit, Section @sec:designsec the planetary mode, Section @sec:verifsec the verification, Section "
        "@sec:discsec discusses the approach and its limits, and Section @sec:concl concludes.")

    # ======================================================================= 2 background
    m.heading("Background", label="bg")
    C.engine_background(m)
    C.approaches(m)
    C.licensing_core(m)

    # ======================================================================= 3 audit
    m.heading("Auditing the engine for Earth assumptions", label="auditsec")
    C.audit(m)

    # ======================================================================= 4 design
    m.heading("Planetary mode", label="designsec")
    C.design(m)

    # ======================================================================= 5 verification
    m.heading("Verification", label="verifsec")
    C.verif_earth(m)
    C.verif_cross(m)
    C.verif_startup(m)

    # ======================================================================= 6 discussion
    m.heading("Discussion", label="discsec")
    C.tool_comparison(m)
    C.limitations_core(m)
    C.roadmap_core(m)

    # ======================================================================= 7 conclusions
    m.heading("Conclusions", label="concl")
    m.para(
        f"ExoBEM-Core shows that a mature building energy simulation engine can be adapted to the Moon and Mars with "
        f"a small, well-placed change. The hard part is finding the Earth: the audit of EnergyPlus v26.2 recorded "
        f"{N_FIND} Earth-specific assumptions, hidden in time constants, a single shared air pressure, exterior "
        "boundary conventions and empirical correlations. Once they are known, a planetary mode of "
        f"{DIFF['insertions']:,} lines suffices for regolith-shielded habitats with internal gains and ideal loads: the "
        "Sun moves at the body's rate, the weather is replaced by a generated planetary environment, the cabin "
        "pressure takes the place of the outdoor pressure, and the boundary models follow vacuum, thin CO2 and cabin "
        "gas. Earth results are bit-for-bit unchanged, and the engine agrees with an independent Python implementation "
        f"within {abs(MOON_DIFF):.2f}% on the Moon and {abs(MARS_DIFF):.1f}% on Mars in cooling energy. Building two "
        "independent tools was what revealed the most consequential issue: walls with time constants longer than the "
        "warm-up period must be initialized from a physically consistent state. The audit, code and verification "
        "cases are open, and the next milestones add a sol clock, a cabin gas mixture, windows and a space radiator.")

    # ======================================================================= back matter
    m.heading("Software and data availability", numbered=False)
    m.para(
        "ExoBEM-Core (branch exobem-core), the six audit reports, the design notes, the verification cases and the "
        "scripts that compare it with EnergyPlus v26.2.0 and with ExoBEM are available at "
        "https://github.com/TensorBuildLab/ExoBEM-Core under the EnergyPlus license. ExoBEM and the data behind every "
        "figure and table of this paper are available at https://github.com/TensorBuildLab/ExoBEM (BSD-3-Clause).")
    m.heading("Declaration of generative AI use", numbered=False)
    m.para(
        "During the preparation of this work the author used Claude (Anthropic) to assist with the code audit, "
        "software implementation, verification scripting and drafting of the manuscript. The author reviewed and edited "
        "all content and takes full responsibility for the publication. [Authors: confirm and adapt to the target "
        "journal's policy.]")
    m.heading("CRediT authorship contribution statement", numbered=False)
    m.para("[To be completed by the authors.]")
    m.heading("Declaration of competing interest", numbered=False)
    m.para("The authors declare that they have no known competing financial interests or personal relationships that "
           "could have appeared to influence the work reported in this paper.")
    m.heading("Acknowledgements", numbered=False)
    m.para("EnergyPlus is developed by the U.S. Department of Energy's Building Technologies Office, the National "
           "Laboratory of the Rockies (formerly NREL) and their partners; ExoBEM-Core is not EnergyPlus and is not "
           "endorsed by them. [Funding to be added.]")

    m.heading("References", numbered=False)
    m.reference_list()


def main():
    m = build_two_pass(build, REFS)
    out = HERE / "ExoBEM-Core_manuscript.docx"
    m.save(out)
    print("saved", out, "| cited", len(m.cite_order), "| figs", m.fig_no, "| tables", m.tab_no, "| eqs", m.eq_no)


if __name__ == "__main__":
    main()
