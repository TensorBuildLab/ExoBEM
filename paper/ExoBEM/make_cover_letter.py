"""Cover letter for submitting the ExoBEM paper to Applied Energy.

    python paper/ExoBEM/make_cover_letter.py  ->  paper/ExoBEM/ExoBEM_cover_letter.docx

Numbers come from the same result files as the manuscript. Text in [brackets] is for the authors to complete.
"""
from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT / "paper" / "common")]

from sections_exobem import CAL, EPLUS_MAX_DIFF, P, meq, mjz, mpo  # noqa: E402

TITLE = ("ExoBEM: building energy simulation of sealed lunar and Martian habitats based on the EnergyPlus "
         "heat-balance method")


def main():
    pe, ps = P["moon_equator"], P["mars_jezero_storm"]
    d = Document()
    st = d.styles["Normal"]
    st.font.name = "Calibri"
    st.font.size = Pt(11)
    for s in d.sections:
        s.left_margin = s.right_margin = Cm(2.5)
        s.top_margin = s.bottom_margin = Cm(2.2)

    def para(text="", bold=False, italic=False, align=None, after=8):
        p = d.add_paragraph()
        r = p.add_run(text)
        r.bold, r.italic = bold, italic
        p.paragraph_format.space_after = Pt(after)
        if align:
            p.alignment = align
        return p

    def bullet(lead, text):
        p = d.add_paragraph(style="List Bullet")
        p.add_run(lead).bold = True
        p.add_run(text)
        p.paragraph_format.space_after = Pt(4)

    para("Liang Zhang\nUniversity of Arizona, Tucson, AZ, USA\nliangzhang1@arizona.edu", after=12)
    para("[Date]", after=12)
    para("The Editor-in-Chief\nApplied Energy", after=12)
    para("Dear Editor,", after=10)

    para("Please consider the enclosed manuscript, “" + TITLE + ",” for publication in Applied Energy as a "
         "research article.")

    para("Crewed surface habitats are planned on the Moon within the next decade and on Mars after that, and their "
         "energy systems must be sized before launch: every kilowatt-hour of storage and every square metre of radiator or "
         "photovoltaic array is mass that has to be landed. Building energy simulation is the standard way to size "
         "such systems on Earth, but its tools assume the Earth throughout: a 24-hour day, outdoor air for "
         "convection and ventilation, Earth sky and ground models, and a grid. None of this holds for a sealed "
         "habitat in vacuum or in Mars's thin CO2 atmosphere. Our paper closes this gap with an open, verified tool "
         "that couples a habitat's envelope, thermal control and power system in one simulation.")

    para("The main contributions are:", after=4)
    bullet("A planetary building energy model. ",
           "ExoBEM re-implements the EnergyPlus heat-balance method and adds planetary sun, sky and regolith models, "
           "convection for any gas, pressure and gravity, and a sealed cabin with no infiltration, gas leakage, "
           "humidity control and a condensation check. Each Earth–Moon–Mars difference is listed and treated "
           "explicitly.")
    bullet("Verification. ",
           f"On Earth the tool reproduces EnergyPlus within {EPLUS_MAX_DIFF:.1f}% in annual loads for the ASHRAE 140 "
           "opaque cases; its planetary models reproduce Mars24, Diviner, Appelbaum–Flood and MEDA reference data; "
           "and its envelope, calibrated to NASA's night-time heat leak for the Artemis surface habitat, predicts the "
           f"daytime value within {abs(CAL['day_error_pct']):.0f}%.")
    bullet("Integrated power systems. ",
           "Habitat loads are coupled with photovoltaics (with a vacuum cell energy balance and Martian dust), "
           "lithium-ion batteries, regenerative fuel cells and fission power, with hourly dispatch.")
    bullet("Design results for NASA-class habitats. ",
           f"Heat rejection dominates ({mpo['tcs_heat_kWh_per_day']/24:.1f} kW at the lunar pole and "
           f"{mjz['tcs_heat_kWh_per_day']/24:.1f} kW on Mars on average). At the lunar equator, radiators need "
           f"heat-pump lift {100*meq['heat_pump_hours_frac']:.0f}% of the time, and the 354-hour night requires "
           f"{pe['PV + Li-ion']['storage_kWh']/1000:.1f} MWh ({pe['PV + Li-ion']['storage_mass_t']:.0f} t) of Li-ion "
           "storage for solar power. A Martian global dust storm requires "
           f"{ps['PV x2 + Li-ion']['storage_kWh']/1000:.0f} MWh ({ps['PV x2 + Li-ion']['storage_mass_t']:.0f} t) even "
           "with twice the minimum array, while one 40 kWe fission unit covers every case.")
    bullet("Open and reproducible. ",
           "The tool is an installable Python package with a tutorial, and it introduces a planetary weather-file "
           "format so that environments can be shared between tools. All code and the data behind every figure "
           "and table are public.")

    para("We believe the work fits the scope of Applied Energy. It is a modelling and design method for energy "
         "systems, combining building loads, thermal control, renewable generation and storage, applied where "
         "energy is most constrained. The central trade-off it quantifies, between generation, storage and "
         "dispatchable power over long periods of darkness, is the same one faced by off-grid and polar facilities "
         "on Earth.", after=8)

    para("This manuscript is original, has not been published, and is not under consideration elsewhere. A "
         "companion manuscript on adapting the EnergyPlus engine itself (ExoBEM-Core) is in preparation and will be "
         "submitted separately; it is cited as such. The use of generative AI in preparing this work is declared in "
         "the manuscript. The authors declare no competing interests. [Funding statement.]")

    para("[Optional: suggested reviewers, with name, affiliation, email and expertise.]", italic=True)

    para("Thank you for your consideration.", after=14)
    para("Sincerely,", after=24)
    para("Liang Zhang\n[Title], University of Arizona\nCorresponding author")

    out = HERE / "ExoBEM_cover_letter.docx"
    d.save(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
