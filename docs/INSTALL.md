# Installing ExoBEM

ExoBEM is a pure-Python package (Python 3.10 or newer). Its only run-time dependencies are NumPy and SciPy;
Matplotlib is needed for plots.

## 1. Install from GitHub (recommended)

```bash
python -m pip install "exobem[plot] @ git+https://github.com/TensorBuildLab/ExoBEM"
```

This installs the `exobem` Python package and the `exobem` command-line tool. Check it:

```bash
exobem --version
```

## 2. Install a working copy (to change the code or run the tests and paper scripts)

```bash
git clone https://github.com/TensorBuildLab/ExoBEM.git
cd ExoBEM
python -m venv .venv
```

Activate the environment (`.venv\Scripts\activate` on Windows, `source .venv/bin/activate` on Linux and
macOS), then:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

All tests should pass in about two minutes. They include the comparison with EnergyPlus results, analytic
solutions, the weather-file format and the power-system model.

## 3. From PyPI

ExoBEM is not yet on PyPI. When it is, the command will be `python -m pip install exobem[plot]`.
(Maintainers: `python -m build` creates the wheel and source archive in `dist/`; upload them with
`python -m twine upload dist/*`.)

## Optional extras

| Extra | Installs | Needed for |
|---|---|---|
| `plot` | matplotlib | `exobem geometry`, `exobem.plot`, the tutorial figures |
| `dev` | pytest, matplotlib, python-docx | tests, the paper build scripts |

## Next step

Work through the [tutorial](tutorial/README.md): it generates a weather file, simulates a lunar habitat and
sizes its power system in about ten minutes.
