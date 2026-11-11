"""Build the Thermonaut journal manuscript (Word).

    python paper/Thermonaut/extract_thermonaut_data.py      (once, needs the Thermonaut checkout and runs)
    python paper/Thermonaut/build_figures_thermonaut.py
    python paper/Thermonaut/build_paper_thermonaut.py   ->  paper/Thermonaut/Thermonaut_manuscript.docx
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT / "paper" / "common")]

import sections_thermonaut as C  # noqa: E402
from docxkit import build_two_pass  # noqa: E402
from refs import REFS  # noqa: E402
from sections_thermonaut import (DIFF, HAB_L, HAB_S, KLOC, MARS_DIFF, MOON_DIFF, N_EARTH, N_FIND, N_P0, UT)  # noqa: E402


def front_matter(m):
    m.para("**Thermonaut: auditing and adapting the EnergyPlus engine for building energy simulation on the Moon "
           "and Mars**", align="center", size=15, space_after=12)
    m.para("Liang Zhang^{a,*}", align="center", size=11, space_after=2)
    m.para("^{a} University of Arizona, Tucson, AZ, USA", align="center", size=9.5, space_after=2)
    m.para("^{*} Corresponding author: liangzhang1@arizona.edu", align="center", size=9.5, space_after=2)
    m.para("[Draft for author review — confirm author list, affiliations, funding and target journal before submission.]",
           align="center", size=9, italic=True, space_after=14)

    m.heading("Highlights", numbered=False)
    hz = C.HZ
    highlights = [
        f"An audit of EnergyPlus v26.2 found {N_FIND} Earth-specific assumptions in six subsystems.",
        f"A planetary mode adds {DIFF['insertions']:,} lines; Earth results stay bit-for-bit identical.",
        f"Sun within {hz['mars_jezero']['rmse_all_deg']:.1f}° of JPL Horizons; vacuum boundary matches closed-form balances.",
        f"Code-to-code: a NASA-class lunar habitat within {abs(HAB_S):.2f}% of an independent tool.",
        "Regolith walls need a warm-up-aware start; the default start gave a 32% load error.",
    ]
    assert all(len(h) <= 85 for h in highlights), [len(h) for h in highlights]
    m.bullets(highlights)

    m.heading("Abstract", numbered=False)
    m.para(
        "Building energy simulation engines such as EnergyPlus encode the Earth in many places at once: in the hour "
        "and the motion of the Sun, in one air pressure shared by the zone and the outdoors, and in convection, sky and "
        "ground models that assume an atmosphere. A habitat on the Moon or Mars therefore needs more than a new weather "
        "file. This paper reports Thermonaut, a research fork of the EnergyPlus v26.2 engine with a planetary mode. An "
        f"audit of the {KLOC:,.0f}-thousand-line code base recorded {N_FIND} Earth-specific assumptions, {N_P0} of them "
        f"blocking a first habitat simulation. The planetary mode adds {DIFF['insertions']:,} lines: it moves the Sun "
        "at the body's rate, reads a planetary weather file or generates the environment, puts the cabin pressure "
        "where zone and HVAC models read it, replaces the boundaries with vacuum, thin-CO2 and cabin-gas physics, "
        "computes PV cell temperatures radiatively, and refuses every object that needs outdoor air. On Earth, "
        f"{N_EARTH} example files give bit-for-bit identical results and all "
        f"{UT['tests']:,} unit tests pass. Off-Earth, the Sun agrees with JPL Horizons within "
        f"{hz['moon_equator']['rmse_all_deg']:.2f}° (Moon) and {hz['mars_jezero']['rmse_all_deg']:.2f}° (Mars), the "
        "regolith with Diviner, and the exterior boundary with its closed-form balances. A code-to-code check against "
        f"the separately written tool ExoBEM agrees within {abs(HAB_S):.2f}% in sensible cooling for a four-crew lunar "
        f"habitat and within {abs(MOON_DIFF):.2f}% (Moon) and {abs(MARS_DIFF):.1f}% (Mars) for a regolith-shielded "
        "module. Walls whose time constant exceeds the warm-up period inherit their initial state; the default start "
        "gave a 32% load error, which a warm-up-aware correction removes.", space_after=6)
    m.para("**Keywords:** EnergyPlus; building energy simulation; software verification; lunar habitat; Mars habitat; "
           "regolith; code audit; planetary weather file; verification", align="left")


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
        "One route is to re-implement the EnergyPlus heat-balance method with planetary physics in a compact code, as "
        "the separately developed Python tool ExoBEM does [@ZhangExoBEM]. A re-implementation is quick to build and "
        "easy to verify, but it gives up most of what the full engine offers. This paper takes the other route and "
        "modifies the EnergyPlus engine itself. The main difficulty is not the planetary physics, whose models are "
        "established [@Hayne2017;Allison2000;Appelbaum1990], but finding every place where a large engine silently "
        "assumes the Earth, and changing them without disturbing terrestrial results.")
    m.para(
        "The paper makes four contributions. (i) A systematic, line-level audit of Earth-specific assumptions in "
        "EnergyPlus v26.2, organized by subsystem and by what must change for a first planetary simulation. (ii) The "
        "design and implementation of a planetary mode in a fork named Thermonaut, built on three rules that keep "
        "Earth results bit-for-bit identical. (iii) Verification on Earth by full-output regression and the unit-test "
        "suite; off-Earth against independent references (JPL Horizons, Diviner, closed-form boundary balances and "
        "NIST gas properties) and, code-to-code, against the separately written ExoBEM on a regolith-shielded module "
        "and a NASA-class lunar habitat run on the same planetary weather files. (iv) Lessons for adapting engines, "
        "notably a warm-up-aware start-up for walls whose time constants exceed the warm-up period and the conventions "
        "of ideal loads for a sealed cabin. Section @sec:bg "
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
    C.verif_independent(m)
    C.verif_cross(m)
    C.verif_startup(m)
    C.verif_habitat(m)

    # ======================================================================= 6 discussion
    m.heading("Discussion", label="discsec")
    C.tool_comparison(m)
    C.limitations_core(m)
    C.roadmap_core(m)

    # ======================================================================= 7 conclusions
    m.heading("Conclusions", label="concl")
    m.para(
        f"Thermonaut shows that a mature building energy simulation engine can be adapted to the Moon and Mars with "
        f"a small, well-placed change. The hard part is finding the Earth: the audit of EnergyPlus v26.2 recorded "
        f"{N_FIND} Earth-specific assumptions, hidden in time constants, a single shared air pressure, exterior "
        "boundary conventions, PV cell-temperature fits and empirical correlations. Once they are known, a planetary "
        f"mode of {DIFF['insertions']:,} lines suffices for sealed habitats with internal gains, humidity control, ideal "
        "loads, PV and batteries: the Sun moves at the body's rate, the weather comes from a planetary weather file or "
        "a generated environment, the cabin pressure takes the place of the outdoor pressure, the boundary models "
        "follow vacuum, thin CO2 and cabin gas, and outdoor air is refused. Earth results are bit-for-bit unchanged. "
        "Off-Earth, the parts the port changed agree with independent references: the Sun with JPL Horizons, the "
        "regolith with Diviner, the exterior boundary with its closed-form balances and Martian convection with NIST "
        "gas properties. As a code-to-code check, the engine agrees with the separately written Python tool ExoBEM "
        f"within {abs(HAB_S):.2f}% in sensible cooling for a NASA-class lunar habitat and within {abs(MARS_DIFF):.1f}% for "
        "a regolith-shielded module on the Moon and Mars. Having a second implementation was what revealed the most "
        "consequential issues: walls with time constants longer than the warm-up period must be initialized from a "
        "physically consistent state and corrected only where warm-up could not reach, and ideal loads dry a sealed "
        "cabin more than a condensing heat exchanger would. What remains is validation of a whole habitat against "
        "measurements. The audit, code, tutorial and verification cases are open, and the next milestone adds a sol "
        "clock, a cabin gas mixture, planetary sizing, a condensing heat exchanger, windows and a space radiator.")

    # ======================================================================= back matter
    m.heading("Software and data availability", numbered=False)
    m.para(
        "Thermonaut (branch thermonaut), the six audit reports, the design notes, the tutorial, the verification cases and the "
        "scripts that compare it with EnergyPlus v26.2.0 and with ExoBEM are available at "
        "https://github.com/TensorBuildLab/Thermonaut under the EnergyPlus license. ExoBEM and the data behind every "
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
           "Laboratory of the Rockies (formerly NREL) and their partners; Thermonaut is not EnergyPlus and is not "
           "endorsed by them. [Funding to be added.]")

    C.appendix_tutorial(m)

    m.heading("References", numbered=False)
    m.reference_list()


def main():
    m = build_two_pass(build, REFS)
    out = HERE / "Thermonaut_manuscript.docx"
    m.save(out)
    print("saved", out, "| cited", len(m.cite_order), "| figs", m.fig_no, "| tables", m.tab_no, "| eqs", m.eq_no)


if __name__ == "__main__":
    main()
