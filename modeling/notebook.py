"""Notebook setup shared across chapters; no global warning suppression."""
from pathlib import Path
import platform
from importlib.metadata import version
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def setup(seed=20260930):
    plt.close('all')
    plt.rcdefaults()
    plt.rcParams.update({'figure.figsize': (8, 4.8), 'figure.dpi': 110, 'savefig.bbox': 'tight', 'axes.formatter.useoffset': False, 'figure.autolayout': True})
    np.set_printoptions(precision=6, suppress=True)
    pd.set_option('display.precision', 6)
    versions = {'Python': platform.python_version()}
    for name in ['numpy', 'scipy', 'sympy', 'pandas', 'matplotlib', 'statsmodels']:
        versions[name] = version(name)
    return (np.random.default_rng(seed), pd.Series(versions, name='version').to_frame())
