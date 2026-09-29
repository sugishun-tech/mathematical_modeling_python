"""Time grids, simultaneous updates, stopping rules and stability diagnostics."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.integrate import solve_ivp as _solve_ivp

@dataclass(frozen=True)
class Trajectory:
    times: np.ndarray
    states: np.ndarray
    stop_reason: str

def iterate_map(update, initial, steps, *, stop=None, max_norm=np.inf):
    """x[n+1]=update(n,x[n]); include the initial and first stopping state.

    A stop callback returns a reason string or None. Negative values are never
    silently clipped. 'horizon reached' is not an equilibrium or a draw.
    """
    if isinstance(steps, bool) or not isinstance(steps, (int, np.integer)) or steps < 0:
        raise ValueError('steps must be a nonnegative integer')
    x = np.atleast_1d(np.asarray(initial, float)).copy()
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ValueError('finite vector initial state required')
    states = [x.copy()]
    reason = stop(0, x.copy()) if stop else None
    for n in range(steps):
        if reason:
            break
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            y = np.atleast_1d(np.asarray(update(n, x.copy()), float))
        if y.shape != x.shape or not np.isfinite(y).all():
            raise FloatingPointError(f'invalid state at step {n + 1}')
        x = y
        states.append(x.copy())
        reason = stop(n + 1, x.copy()) if stop else None
        if not reason and np.linalg.norm(x, np.inf) > max_norm:
            reason = 'norm limit'
    return Trajectory(np.arange(len(states)), np.vstack(states), str(reason or 'horizon reached'))

def euler(rhs, t0, initial, final_time, steps):
    """Forward Euler with exactly steps equal intervals and both endpoints."""
    if not np.isfinite([t0, final_time]).all() or final_time <= t0:
        raise ValueError('finite increasing times required')
    if isinstance(steps, bool) or not isinstance(steps, (int, np.integer)) or steps < 1:
        raise ValueError('positive integer steps required')
    times = np.linspace(t0, final_time, steps + 1)
    h = (final_time - t0) / steps
    result = iterate_map(lambda n, x: x + h * np.asarray(rhs(times[n], x)), initial, steps)
    return (times, result.states)

def solve_ivp(*args, **kwargs):
    """SciPy integration with mandatory success and finite-output checks."""
    result = _solve_ivp(*args, **kwargs)
    if not result.success:
        raise RuntimeError(result.message)
    if not np.isfinite(result.y).all():
        raise FloatingPointError('nonfinite ODE result')
    return result

def stability(matrix, *, discrete=False, tolerance=1e-09):
    """Sufficient local tests; boundary eigenvalues are explicitly inconclusive."""
    a = np.asarray(matrix, float)
    if a.ndim != 2 or a.shape[0] != a.shape[1] or (not np.isfinite(a).all()):
        raise ValueError('finite square matrix required')
    eigenvalues = np.linalg.eigvals(a)
    score = np.abs(eigenvalues) - 1 if discrete else eigenvalues.real
    status = 'asymptotically stable' if max(score) < -tolerance else 'unstable' if max(score) > tolerance else 'inconclusive (boundary eigenvalue)'
    return (status, eigenvalues)

def docking_matrix(k, c=5.0, w=10.0):
    if not np.isfinite([k, c, w]).all() or min(k, c, w) < 0:
        raise ValueError('finite nonnegative gain and delays required')
    return np.array([[1 - k * w, -k * c], [1.0, 0.0]])

def iterate_linear(matrix, initial, steps=40):
    a = np.asarray(matrix, float)
    return iterate_map(lambda n, x: a @ x, initial, steps).states

def competition_rhs(rates, capacities, interactions):
    """Two logistic species, retaining a separate interaction coefficient each."""
    r, K, b = [np.asarray(v, float) for v in (rates, capacities, interactions)]
    if any((v.shape != (2,) for v in (r, K, b))) or not np.isfinite([r, K, b]).all() or np.any(r <= 0) or np.any(K <= 0) or np.any(b < 0):
        raise ValueError('positive rates/capacities and nonnegative interactions required')
    return lambda time, x: r * np.asarray(x) * (1 - np.asarray(x) / K) - b * np.prod(x)

def rlc_rhs(time, state, L=1.0, C=1.0):
    if L <= 0 or C <= 0:
        raise ValueError('positive L and C required')
    i, v = state
    return np.array([(i - i ** 3 - v) / L, i / C])

def lorenz(time, state, sigma=10.0, r=28.0, b=8 / 3):
    x, y, z = state
    return np.array([sigma * (y - x), r * x - y - x * z, x * y - b * z])

def simulate_battle(lam, red0=5.0, blue0=2.0, a=0.05, b=0.005, max_hours=10000):
    """Textbook discrete attrition model; terminal negative values mark overshoot."""
    import pandas as pd
    if not np.isfinite([lam, red0, blue0, a, b]).all() or min(lam, red0, blue0, a, b) < 0:
        raise ValueError('finite nonnegative parameters required')

    def stop(n, x):
        if x[0] <= 0 and x[1] <= 0:
            return 'simultaneous'
        if x[0] <= 0:
            return 'blue'
        if x[1] <= 0:
            return 'red'
        return None

    def update(n, x):
        red, blue = x
        return [red - lam * a * blue - lam * b * red * blue, blue - a * red - b * red * blue]
    result = iterate_map(update, [red0, blue0], max_hours, stop=stop)
    return (pd.DataFrame({'hour': result.times, 'red': result.states[:, 0], 'blue': result.states[:, 1]}), result.stop_reason)
