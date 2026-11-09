# Manuscripts

Three Word manuscripts are built from the same results, so the publication options can be compared side by side.

| File | Option | Content | Length |
|---|---|---|---|
| `ExoBEM_manuscript.docx` | Paper 1 of two | ExoBEM: the Python re-implementation, its verification (EnergyPlus 23.2, planetary reference data) and the Moon/Mars case studies | ~21 pages, 8 figures, 8 tables |
| `ExoBEM-Core_manuscript.docx` | Paper 2 of two | ExoBEM-Core: the audit of Earth assumptions in EnergyPlus v26.2, the planetary mode, Earth bit-for-bit regression and cross-verification against ExoBEM | ~17 pages, 4 figures, 5 tables |
| `ExoBEM_combined_manuscript.docx` | One paper | Both tools, verified against each other, plus the case studies | ~33 pages, 12 figures, 13 tables |

## Building

```
python paper/build_paper.py             # Paper 1
python paper/build_figures_core.py      # figures core_*.png (from paper/data)
python paper/build_paper_core.py        # Paper 2
python paper/build_paper_combined.py    # combined paper
```

`paper/extract_core_data.py` refreshes `paper/data/` from an ExoBEM-Core checkout and its verification runs
(`EXOBEM_CORE`, `EXOBEM_CORE_RUNS`); the papers themselves only need the files in `paper/data/`.

The text is shared: `sections_exobem.py` holds the ExoBEM sections and `sections_core.py` the ExoBEM-Core sections.
Each builder assembles them with its own title, abstract, introduction and conclusions. Cross-references are
written as `@fig:name`, `@tab:name`, `@sec:name` or `@eq:name` (`@[fig:name]a` when a letter follows) and are
numbered in a second build pass by `docxkit.build_two_pass`.
