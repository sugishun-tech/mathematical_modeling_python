"""Shared iteration, sensitivity and optimization verification tools."""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from typing import Callable
import numpy as np
from scipy.optimize import linprog

@dataclass(frozen=True)
class NewtonResult:
    root: np.ndarray
    history: np.ndarray
    residuals: np.ndarray

def newton_system(function: Callable, jacobian: Callable, initial, *, tolerance=1e-10, max_iterations=100, domain=None) -> NewtonResult:
    """Solve F(x)=0 by damped Newton; retain the initial and accepted iterates.

    For optimization use F=gradient and DF=Hessian. Residual convergence does
    not establish a maximum, much less a global maximum: check those separately.
    """
    if not np.isfinite(tolerance) or tolerance <= 0 or max_iterations < 1:
        raise ValueError('positive tolerance and iteration limit required')
    x = np.atleast_1d(np.asarray(initial, dtype=float)).copy()
    if x.ndim != 1 or not np.all(np.isfinite(x)) or (domain and (not domain(x))):
        raise ValueError('invalid initial point')
    history, residuals = ([x.copy()], [])
    for iteration in range(max_iterations + 1):
        f = np.asarray(function(x), float).reshape(-1)
        if f.shape != x.shape or not np.isfinite(f).all():
            raise ValueError('F must return a finite vector matching the state')
        norm = float(np.linalg.norm(f, ord=np.inf))
        residuals.append(norm)
        if norm <= tolerance:
            return NewtonResult(x, np.vstack(history), np.asarray(residuals))
        if iteration == max_iterations:
            break
        J = np.asarray(jacobian(x), float)
        if J.shape != (x.size, x.size) or not np.isfinite(J).all():
            raise ValueError('Jacobian must be a finite square matrix')
        try:
            step = np.linalg.solve(J, f)
        except np.linalg.LinAlgError as error:
            raise RuntimeError('singular Newton Jacobian') from error
        for attempt in range(54):
            candidate = x - 2.0 ** (-attempt) * step
            if not np.isfinite(candidate).all() or (domain and (not domain(candidate))):
                continue
            fc = np.asarray(function(candidate), float).reshape(-1)
            if fc.shape == x.shape and np.isfinite(fc).all() and (np.linalg.norm(fc, np.inf) < norm):
                x = candidate
                history.append(x.copy())
                break
        else:
            raise RuntimeError('Newton stalled without residual reduction')
    raise RuntimeError(f'Newton failed to converge; residual={norm:g}')

def newton_scalar(function, derivative, initial, **kwargs):
    """Scalar adapter. The returned history has shape (iterations + 1, 1)."""
    return newton_system(lambda x: [function(x[0])], lambda x: [[derivative(x[0])]], [initial], **kwargs)

def sensitivity(function, parameter, relative_step=0.0001):
    """Centered finite-difference elasticity a f'(a)/f(a), for nonzero a,f(a)."""
    if not np.isfinite(parameter) or parameter == 0 or (not 0 < relative_step < 1):
        raise ValueError('nonzero finite parameter and 0 < relative_step < 1 required')
    y = float(function(parameter))
    if not np.isfinite(y) or y == 0:
        raise ValueError('relative sensitivity undefined for zero/nonfinite output')
    h = abs(parameter) * relative_step
    return parameter * (function(parameter + h) - function(parameter - h)) / (2 * h * y)

def check_solution(result, *, A_ub=None, b_ub=None, A_eq=None, b_eq=None, lower=None, upper=None, integral=False, tolerance=1e-06):
    """Check status before accessing x, then finite values and primal feasibility."""
    if not result.success or result.x is None:
        raise RuntimeError(f"optimization failed: {getattr(result, 'message', '')}")
    x = np.asarray(result.x, float)
    if not np.isfinite(x).all() or not np.isfinite(result.fun):
        raise FloatingPointError('nonfinite optimizer result')
    if A_ub is not None and np.any(np.asarray(A_ub) @ x > np.asarray(b_ub) + tolerance):
        raise AssertionError('inequality violation')
    if A_eq is not None and (not np.allclose(np.asarray(A_eq) @ x, b_eq, atol=tolerance, rtol=0)):
        raise AssertionError('equality violation')
    if lower is not None and np.any(x < np.asarray(lower) - tolerance):
        raise AssertionError('lower-bound violation')
    if upper is not None and np.any(x > np.asarray(upper) + tolerance):
        raise AssertionError('upper-bound violation')
    if integral and (not np.allclose(x, np.rint(x), atol=tolerance, rtol=0)):
        raise AssertionError('integrality violation')
    return result

def binary_knapsack(values, weights, capacity):
    """Exhaustive small binary knapsack, returning every tied optimum."""
    values, weights = (np.asarray(values, float), np.asarray(weights, float))
    if values.ndim != 1 or weights.shape != values.shape or len(values) > 22:
        raise ValueError('matching vectors of at most 22 items required')
    if capacity < 0 or not np.isfinite(capacity) or (not np.isfinite([values, weights]).all()) or np.any(weights < 0):
        raise ValueError('finite values and nonnegative weights/capacity required')
    best, solutions = (-np.inf, [])
    for bits in product([0, 1], repeat=len(values)):
        x = np.asarray(bits)
        if weights @ x <= capacity + 1e-12:
            value = float(values @ x)
            if value > best + 1e-10:
                best, solutions = (value, [x])
            elif abs(value - best) <= 1e-10:
                solutions.append(x)
    return (best, np.vstack(solutions))

def branch_and_bound(c, A, b, upper, *, max_nodes=10000):
    """Educational bounded all-integer maximization using LP relaxation bounds.

    Each node records its bound and why it was branched or pruned. This is a
    teaching implementation; production-sized problems should use HiGHS/MILP.
    """
    c, A, b, upper = [np.asarray(v, float) for v in (c, A, b, upper)]
    if c.ndim != 1 or A.shape != (len(b), len(c)) or upper.shape != c.shape:
        raise ValueError('incompatible dimensions')
    if not all((np.isfinite(v).all() for v in (c, A, b, upper))) or np.any(upper < 0):
        raise ValueError('finite inputs and nonnegative upper bounds required')
    stack = [(np.zeros_like(c), np.floor(upper))]
    best, point, log = (-np.inf, None, [])
    while stack:
        if len(log) >= max_nodes:
            raise RuntimeError('node budget exhausted: optimum not certified')
        lo, hi = stack.pop()
        if np.any(lo > hi):
            log.append({'status': 'empty bounds'})
            continue
        res = linprog(-c, A_ub=A, b_ub=b, bounds=list(zip(lo, hi)), method='highs')
        if res.status == 2:
            log.append({'status': 'infeasible'})
            continue
        check_solution(res, A_ub=A, b_ub=b, lower=lo, upper=hi)
        bound = -float(res.fun)
        if bound <= best + 1e-08:
            log.append({'status': 'bound pruned', 'bound': bound})
            continue
        fractional = np.abs(res.x - np.rint(res.x))
        j = int(fractional.argmax())
        if fractional[j] <= 1e-08:
            point = np.rint(res.x).astype(int)
            best = float(c @ point)
            log.append({'status': 'incumbent', 'bound': bound})
            continue
        floor = np.floor(res.x[j])
        hi_left = hi.copy()
        lo_right = lo.copy()
        hi_left[j] = floor
        lo_right[j] = floor + 1
        log.append({'status': 'branch', 'bound': bound, 'variable': j})
        stack.extend([(lo_right, hi.copy()), (lo.copy(), hi_left)])
    if point is None:
        raise ValueError('integer model is infeasible')
    return (best, point, log)
