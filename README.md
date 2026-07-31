# Mathematical Modeling in Scientific Python

A reproducible, chapter-by-chapter Jupyter companion to:

> Mark M. Meerschaert, *Mathematical Modeling*, Fourth Edition, Academic Press, 2013. ISBN 978-0-12-386912-8.

The repository contains nine **pre-executed** notebooks. They reconstruct representative models with modern scientific Python rather than copying the textbook. The notebooks emphasize the book's five-step workflow, sensitivity analysis, robustness, and verification.

## 日本語クイックスタート

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run_all.py
jupyter lab
```

`python run_all.py` executes every notebook in place and exits nonzero on the first failure. The committed notebooks already contain outputs, so GitHub renders the calculations and figures without requiring a kernel.

## Notebook map

| Chapter | Notebook | Main Python methods |
|---|---|---|
| 1. One-Variable Optimization | `notebooks/01_one_variable_optimization.ipynb` | SymPy differentiation, scalar optimization, sensitivity coefficients |
| 2. Multivariable Optimization | `notebooks/02_multivariable_optimization.ipynb` | gradients, Hessians, Lagrange multipliers, SLSQP, shadow prices |
| 3. Computational Methods for Optimization | `notebooks/03_computational_optimization.ipynb` | Newton methods, random search, `linprog`, `milp` |
| 4. Introduction to Dynamic Models | `notebooks/04_introduction_dynamic_models.ipynb` | equilibria, vector fields, `solve_ivp`, difference equations |
| 5. Analysis of Dynamic Models | `notebooks/05_analysis_dynamic_models.ipynb` | Jacobians, eigenvalues, spectral radius, phase portraits |
| 6. Simulation of Dynamic Models | `notebooks/06_simulation_dynamic_models.ipynb` | discrete simulation, Euler convergence, bifurcation, Lorenz system |
| 7. Introduction to Probability Models | `notebooks/07_introduction_probability_models.ipynb` | expectations, LLN/CLT, exponential models, diffusion PDE |
| 8. Stochastic Models | `notebooks/08_stochastic_models.ipynb` | Markov chains/processes, OLS, AR(1), autocorrelation |
| 9. Simulation of Probability Models | `notebooks/09_simulation_probability_models.ipynb` | Monte Carlo, inverse transforms, analytic simulation, particle tracking, fractional diffusion |

## Repository layout

```text
.
├── README.md
├── LICENSE
├── SOURCE_NOTES.md
├── requirements.txt
├── environment.yml
├── Makefile
├── run_all.py
├── data/
│   ├── README.md
│   └── cm1.csv
└── notebooks/
    ├── 01_one_variable_optimization.ipynb
    ├── ...
    └── 09_simulation_probability_models.ipynb
```

## Local execution

Python 3.10 or newer is recommended.

```bash
python -m pip install -r requirements.txt
python run_all.py
```

Useful variants:

```bash
python run_all.py --pattern '0[1-3]_*.ipynb'
python run_all.py --timeout 1200
python run_all.py --validate-only
```

The notebooks use fixed random seeds. Small numerical differences can still occur across BLAS implementations, SciPy versions, and platforms, especially in iterative optimization and heavy-tailed Monte Carlo models.

## Kaggle

The notebooks use only common scientific Python packages and do not require internet access. Upload the repository as a Kaggle Dataset, attach it to a notebook, and open or copy the desired `.ipynb`. Chapter 8 reads `data/cm1.csv`; keep the data directory alongside the notebooks. Kaggle already includes most dependencies, but `requirements.txt` documents the tested stack.

## GitHub

All notebooks are stored with outputs. GitHub can render them directly. For a clean review workflow, execute the full suite before committing:

```bash
make execute
make validate
```

Notebook output contains binary PNG payloads, because apparently source-control systems needed one more way to make diffs unpleasant. Keep code changes small and review the rendered notebook as well as the JSON diff.

## Continuous integration

`.github/workflows/notebooks.yml` installs the declared environment, executes all nine notebooks, and scans their stored outputs for errors on every push and pull request. This is intentionally boring. Reproducibility usually is, right up until somebody skips it.

## Scope and publication note

- The code and explanatory text in this repository are original.
- The project does **not** include the source PDF, textbook prose, original figures, or a solutions manual.
- It implements selected representative examples and computational extensions; it is not a substitute for the textbook.
- Numerical assumptions and example structure are attributed to the cited book.
- `LICENSE` applies only to this repository's original code and prose. The textbook remains under its publisher's copyright.

## Verification

Each notebook contains assertions for central numerical results. `run_all.py` executes notebooks from the repository root so relative data paths are stable, then scans outputs for execution errors.

## Citation

When using the notebooks, cite both this repository and the source textbook. A suitable textbook citation is:

```bibtex
@book{meerschaert2013mathematical,
  title     = {Mathematical Modeling},
  author    = {Meerschaert, Mark M.},
  edition   = {4},
  year      = {2013},
  publisher = {Academic Press},
  isbn      = {978-0-12-386912-8}
}
```
