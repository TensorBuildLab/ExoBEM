# Manuscript

The ExoBEM paper has its own folder with its build script, section text, figures and the Word manuscript.

```
paper/
├── common/                  shared building blocks
│   ├── docxkit.py           Word builder: headings, equations, figures, tables, citations, cross-references
│   ├── factors.py           Earth / Moon / Mars factor list (also docs/planetary_factors.md)
│   └── refs.py              reference list
└── ExoBEM/                  the paper (Applied Energy)
    ├── ExoBEM_manuscript.docx
    ├── build_paper.py       assembles the paper
    ├── sections_exobem.py   section text
    ├── make_figures_v2.py   flow and geometry figures
    └── figures/             fig1-fig9 (studies/make_figures.py), fig_flow, fig_geometry
```

| Paper | Content | Length |
|---|---|---|
| ExoBEM | Factor analysis, method and coordination, comparison with EnergyPlus, sealed cabin, weather format, power systems, verification, NASA-class Moon/Mars case studies, tutorial appendix | ~33 pages, 11 figures, 11 tables |

## Building

```
python studies/make_figures.py                       # figures (from studies/ and verification/ results)
python paper/ExoBEM/build_paper.py                   # manuscript and highlights
```

Cross-references in the section text are written as `@fig:name`, `@tab:name`, `@sec:name` or `@eq:name`
(`@[fig:name]a` when a letter follows) and are numbered in a second build pass by `docxkit.build_two_pass`.
