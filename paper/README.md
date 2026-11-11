# Manuscripts

The work is published as two companion papers. Each has its own folder with its build script, section text,
figures, data and the Word manuscript. Paper 2 uses ExoBEM (Paper 1) as its verification reference, so Paper 1
should be submitted first or together with Paper 2.

```
paper/
├── common/                  shared by both papers
│   ├── docxkit.py           Word builder: headings, equations, figures, tables, citations, cross-references
│   └── refs.py              reference list
├── ExoBEM/                  Paper 1: the Python tool
│   ├── ExoBEM_manuscript.docx
│   ├── build_paper.py       assembles the paper
│   ├── sections_exobem.py   section text
│   ├── make_figures_v2.py   flow and geometry figures
│   └── figures/             fig1-fig9 (studies/make_figures.py), fig_flow, fig_geometry
├── Thermonaut/             Paper 2: the modified EnergyPlus engine
│   ├── Thermonaut_manuscript.docx
│   ├── build_paper_thermonaut.py  assembles the paper
│   ├── sections_thermonaut.py     section text
│   ├── build_figures_thermonaut.py
│   ├── extract_thermonaut_data.py collects results from the Thermonaut repository into data/
│   ├── data/                verification results the paper is built from
│   └── figures/             core_fig1-core_fig4
└── archive/
    └── combined/            single-paper version of both tools (not pursued; kept for reference)
```

| Paper | Content | Length |
|---|---|---|
| 1. ExoBEM | Factor analysis, method and coordination, comparison with EnergyPlus, sealed cabin, weather format, power systems, verification, NASA-class Moon/Mars case studies, tutorial appendix | ~33 pages, 11 figures, 11 tables |
| 2. Thermonaut | Audit of Earth assumptions in EnergyPlus v26.2, planetary mode, Earth bit-for-bit regression, cross-verification against ExoBEM | ~17 pages, 4 figures, 5 tables |

## Building

```
python studies/make_figures.py                       # Paper 1 figures (from studies/ and verification/ results)
python paper/ExoBEM/build_paper.py                   # Paper 1

python paper/Thermonaut/build_figures_thermonaut.py       # Paper 2 figures (from paper/Thermonaut/data)
python paper/Thermonaut/build_paper_thermonaut.py         # Paper 2

python paper/archive/combined/build_paper_combined.py   # archived combined version
```

`paper/Thermonaut/extract_thermonaut_data.py` refreshes `paper/Thermonaut/data/` from an Thermonaut checkout and its
verification runs (`THERMONAUT`, `THERMONAUT_RUNS`); the paper itself only needs the files in `data/`.

Cross-references in the section text are written as `@fig:name`, `@tab:name`, `@sec:name` or `@eq:name`
(`@[fig:name]a` when a letter follows) and are numbered in a second build pass by `docxkit.build_two_pass`.
The archived combined paper is frozen: its Word file and build script are kept as they were at commit 61efe28, before Paper 1 was revised, and the script no longer builds against the current section text.
