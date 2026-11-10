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
│   └── figures/             fig1-fig8 (made by studies/make_figures.py)
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
| 1. ExoBEM | Planetary physics, verification against EnergyPlus 23.2 and planetary reference data, Moon/Mars case studies | ~21 pages, 8 figures, 8 tables |
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
The archived combined paper reuses the section text of both papers, so it still builds from the current text.
