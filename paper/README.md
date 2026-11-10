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
├── ExoBEM-Core/             Paper 2: the modified EnergyPlus engine
│   ├── ExoBEM-Core_manuscript.docx
│   ├── build_paper_core.py  assembles the paper
│   ├── sections_core.py     section text
│   ├── build_figures_core.py
│   ├── extract_core_data.py collects results from the ExoBEM-Core repository into data/
│   ├── data/                verification results the paper is built from
│   └── figures/             core_fig1-core_fig4
└── archive/
    └── combined/            single-paper version of both tools (not pursued; kept for reference)
```

| Paper | Content | Length |
|---|---|---|
| 1. ExoBEM | Factor analysis, method and coordination, comparison with EnergyPlus, sealed cabin, weather format, power systems, verification, NASA-class Moon/Mars case studies, tutorial appendix | ~33 pages, 11 figures, 11 tables |
| 2. ExoBEM-Core | Audit of Earth assumptions in EnergyPlus v26.2, planetary mode, Earth bit-for-bit regression, cross-verification against ExoBEM | ~17 pages, 4 figures, 5 tables |

## Building

```
python studies/make_figures.py                       # Paper 1 figures (from studies/ and verification/ results)
python paper/ExoBEM/build_paper.py                   # Paper 1

python paper/ExoBEM-Core/build_figures_core.py       # Paper 2 figures (from paper/ExoBEM-Core/data)
python paper/ExoBEM-Core/build_paper_core.py         # Paper 2

python paper/archive/combined/build_paper_combined.py   # archived combined version
```

`paper/ExoBEM-Core/extract_core_data.py` refreshes `paper/ExoBEM-Core/data/` from an ExoBEM-Core checkout and its
verification runs (`EXOBEM_CORE`, `EXOBEM_CORE_RUNS`); the paper itself only needs the files in `data/`.

Cross-references in the section text are written as `@fig:name`, `@tab:name`, `@sec:name` or `@eq:name`
(`@[fig:name]a` when a letter follows) and are numbered in a second build pass by `docxkit.build_two_pass`.
The archived combined paper is frozen: its Word file and build script are kept as they were at commit 61efe28, before Paper 1 was revised, and the script no longer builds against the current section text.
