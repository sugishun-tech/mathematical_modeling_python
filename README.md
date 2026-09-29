# Mathematical Modeling in Python

An executable study companion to Mark M. Meerschaert, **Mathematical Modeling, fourth edition (2013)**.

The nine chapter notebooks contain original **English problem statements**, explicit assumptions and units, calculations, verification checks, and explanations of what the results do—and do not—establish. The source PDF is not needed to read or execute the main worked examples.

## Start here

To read without installing Python, open **`docs/index.html`** in a browser. Each chapter page contains its own plots and static SVG mathematics. Reading does not require an internet connection, a MathJax CDN, or a running notebook kernel.

To run or change the models:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python run_all.py
jupyter lab
```

Open a notebook in `notebooks/`, restart its kernel, and run all cells in order. Launching Jupyter from the repository root or from its `notebooks` directory is supported. Keep `modeling/` and `data/` with the notebooks; copying an individual notebook elsewhere is not a self-contained installation.

The recorded execution environment uses Python 3.13.5. Declared dependencies allow Python 3.10 and later, but the lower-version combinations have not all been tested here. Exact versions used for this delivery are in `reports/tested_environment.json` and `requirements-tested.txt`.

## What is covered

| Chapter | Main notebook | Numbered examples |
|---|---|---:|
| 1. One-variable optimization | [Chapter 1](notebooks/01_one_variable_optimization.ipynb) | 1 |
| 2. Multivariable optimization | [Chapter 2](notebooks/02_multivariable_optimization.ipynb) | 5 |
| 3. Computational optimization | [Chapter 3](notebooks/03_computational_optimization.ipynb) | 7 |
| 4. Introduction to dynamic models | [Chapter 4](notebooks/04_introduction_dynamic_models.ipynb) | 4 |
| 5. Analysis of dynamic models | [Chapter 5](notebooks/05_analysis_dynamic_models.ipynb) | 4 |
| 6. Simulation of dynamic models | [Chapter 6](notebooks/06_simulation_dynamic_models.ipynb) | 6 |
| 7. Introduction to probability models | [Chapter 7](notebooks/07_introduction_probability_models.ipynb) | 5 |
| 8. Stochastic models | [Chapter 8](notebooks/08_stochastic_models.ipynb) | 6 |
| 9. Simulation of probability models | [Chapter 9](notebooks/09_simulation_probability_models.ipynb) | 6 |

**Scope is not the same as full verification.** All 44 numbered examples have central computational reconstructions, and all 33 instructional sections have a topic mapping. This is **not** a complete solutions manual: the 164 end-of-chapter exercises are inventoried, but their solutions have not been implemented or verified. Not every printed equation, figure, sensitivity analysis, or robustness experiment has been reproduced. See [COVERAGE.md](COVERAGE.md) for exact distinctions and `reports/coverage.csv` for individual records.

A **separate exercise study bundle** contains nine image-backed notebooks with the original English exercise statements, including their mathematics and tables, plus selected supporting source pages. Those are source excerpts, not newly authored solutions or searchable mathematical transcriptions. Extract that bundle alongside this project to add `notebooks/exercises/`. It contains textbook material not covered by this repository's MIT license; publication permission has not been established. It is deliberately excluded from the main code archive.

## How to study

Read an example's problem statement and predict the qualitative answer before executing it. Check which quantities are decisions, states, observations, or parameters. Follow the derivation and inspect the independent checks. Finally, change **one assumption or parameter at a time**, explain the result in the original units, and separate numerical error from uncertainty about the model.

Some useful lessons are errors or limitations rather than a single recommended answer: the chair model has no global maximum on its stated domain; a large Euler step can create artificial oscillations; a Markov chain can have a stationary distribution without ordinary convergence; and a finite Monte Carlo run cannot establish permanent safety after a threshold crossing.

## Shared numerical tools

| Module | Reused processes |
|---|---|
| `modeling/optimization.py` | residual-based damped Newton iteration, elasticity, feasibility/integrality checks, binary enumeration, educational branch-and-bound |
| `modeling/dynamics.py` | simultaneous state updates, stopping rules, Euler integration, checked adaptive ODE solves, stability tests, repeated population/circuit/control models |
| `modeling/probability.py` | stationary distributions, finite queues, inventory policies, exact run probabilities, Wilson intervals, inverse transforms, first passage |
| `modeling/particles.py` | streaming particle updates, centered heavy-tailed jumps, bin concentrations and uncertainty, censored threshold summaries |
| `modeling/regression.py` | multi-step autoregressive forecasting and innovation variance, dead-time correction |
| `modeling/simulation.py` | stochastic docking state transitions and the specified piecewise wind field |
| `modeling/notebook.py` | consistent display setup and environment reporting without suppressing numerical warnings |

The model equations remain visible in the notebooks. The modules centralize repeated algorithms rather than hiding the modeling choices behind a large framework.

## Re-execution and provenance

```bash
python run_all.py --pattern '0[1-3]*.ipynb'
python run_all.py --timeout 600
python run_all.py --validate-only
python scripts/audit_project.py
```

Each notebook executes in a **new kernel**. A failed run does not overwrite the last successful notebook. Validation rejects unexecuted code, stored error outputs, numerical/glyph warnings, and outputs that do not match the recorded notebook-source and model/data hashes. Validation does not prove that every mathematical statement is true.

Random experiments use explicitly seeded generators. Monte Carlo intervals are conditional on the model; unless stated otherwise, they are pointwise and do not include parameter uncertainty, discretization error, or the selection effect from choosing the largest sampled value.

## Render and inspect

The included HTML is already built. Rebuilding is optional:

```bash
python -m pip install -r requirements-render.txt
npm install --no-save mathjax-full@3.2.2
python scripts/export_html.py
python scripts/verify_rendering.py
```

For browser checks, Chromium must be available, or install the Playwright browser with `python -m playwright install chromium`. The export uses embedded SVG paths and PNGs, not external font files. The visual checker renders the complete HTML string in Chromium and checks image decoding, MathJax errors, unexpected network requests, and page overflow at desktop and narrow widths. Raster plot labels also require manual review.

To rebuild the optional source exercise workbooks from your own matching PDF:

```bash
python scripts/build_source_workbooks.py --pdf '/path/to/book.pdf' --output notebooks/exercises
```

The source inventory can then be regenerated with:

```bash
python scripts/build_source_inventory.py --pdf '/path/to/book.pdf' --workbooks notebooks/exercises
```

That extraction map targets the supplied 368-page fourth-edition PDF; it is not a general PDF-to-notebook converter.

## Verification records

`reports/execution.json` records chapter runs and hashes. `reports/unit-tests.xml` records unit tests. `reports/visual_checks.json` records browser checks. `reports/project_audit.json` reconciles notebook structure with the coverage inventory. Screenshots and plot contact sheets are in `reports/visual/`.

The GitHub Actions workflow repeats local tests and notebook execution on pushes and pull requests. The workflow file is provided, but no remote GitHub Actions run was performed as part of this delivery.

## Source and corrections

See [SOURCE_NOTES.md](SOURCE_NOTES.md) and [ERRATA.md](ERRATA.md). In particular, the corrected 120-acre integer-farm model yields **USD 162,250**, not the former USD 156,250, and its gap from the acreage LP is **USD 250**. Mathematical or source-model limitations are identified instead of being hidden by a successful solver status.

`LICENSE` covers original repository code and original explanations, not the source textbook, optional textbook excerpts, or third-party software. The main code archive contains no source PDF, original page images, Git history, dependency installations, or font files.
