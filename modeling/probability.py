"""Probability calculations with explicit conventions and uncertainty."""
from __future__ import annotations
import numpy as np
from scipy.special import logsumexp
from scipy.stats import norm, poisson

def stationary_distribution(matrix, *, continuous=False, tolerance=1e-10):
    """Unique stationary row vector for P or generator Q; reject non-uniqueness."""
    a = np.asarray(matrix, float)
    if a.ndim != 2 or a.shape[0] != a.shape[1] or (not np.isfinite(a).all()):
        raise ValueError('finite square matrix required')
    n = len(a)
    if continuous:
        off = a.copy()
        np.fill_diagonal(off, 0)
        if np.any(off < -tolerance) or not np.allclose(a.sum(1), 0, atol=tolerance, rtol=0):
            raise ValueError('invalid generator')
        operator = a.T
    else:
        if np.any(a < -tolerance) or not np.allclose(a.sum(1), 1, atol=tolerance, rtol=0):
            raise ValueError('invalid transition matrix')
        operator = a.T - np.eye(n)
    A = np.vstack([operator, np.ones(n)])
    b = np.r_[np.zeros(n), 1.0]
    if np.linalg.matrix_rank(A) < n:
        raise ValueError('stationary distribution is not unique')
    p = np.linalg.lstsq(A, b, rcond=None)[0]
    if np.any(p < -tolerance) or not np.allclose(operator @ p, 0, atol=tolerance, rtol=0):
        raise RuntimeError('stationary residual is too large')
    p = np.maximum(p, 0)
    return p / p.sum()

def birth_death_stationary(arrival, service, capacity):
    """Finite M/M/1/K probabilities, including rho=1 and large rho safely."""
    if isinstance(capacity, bool) or not isinstance(capacity, (int, np.integer)) or capacity < 0:
        raise ValueError('capacity must be a nonnegative integer')
    if not np.isfinite([arrival, service]).all() or arrival < 0 or service <= 0:
        raise ValueError('arrival>=0 and service>0 required')
    if arrival == 0:
        return np.r_[1.0, np.zeros(capacity)]
    log_weights = np.arange(capacity + 1) * (np.log(arrival) - np.log(service))
    return np.exp(log_weights - logsumexp(log_weights))

def wilson_interval(successes, trials, confidence=0.95):
    """Binomial Wilson interval; works at 0 and n successes (unlike Wald)."""
    if not 0 < confidence < 1 or int(trials) != trials or trials <= 0 or np.any(np.asarray(successes) < 0) or np.any(np.asarray(successes) > trials):
        raise ValueError('valid counts and confidence required')
    successes = np.asarray(successes)
    if np.any(successes != np.floor(successes)):
        raise ValueError('success counts must be integers')
    z = norm.ppf((1 + confidence) / 2)
    p = successes / trials
    den = 1 + z * z / trials
    center = (p + z * z / (2 * trials)) / den
    half = z * np.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / den
    return (np.where(successes == 0, 0.0, np.maximum(0, center - half)), np.where(successes == trials, 1.0, np.minimum(1, center + half)))

def has_run(sequence, run_length=3):
    if run_length < 1:
        raise ValueError('run_length must be positive')
    streak = 0
    for value in sequence:
        streak = streak + 1 if value else 0
        if streak >= run_length:
            return True
    return False

def run_probability(days=7, run_length=3, p=0.5):
    """Exact dynamic programming probability, no 2**days enumeration required."""
    if not isinstance(days, (int, np.integer)) or days < 0 or run_length < 1 or (not 0 <= p <= 1):
        raise ValueError('invalid run-probability parameters')
    state = np.zeros(run_length)
    state[0] = 1.0
    for _ in range(days):
        nxt = np.zeros_like(state)
        nxt[0] = state.sum() * (1 - p)
        nxt[1:] = state[:-1] * p
        state = nxt
    return float(np.clip(1 - state.sum(), 0, 1))

def rainy_simulation(rng, trials, days=7, run_length=3, p=0.5):
    if trials < 1 or days < 0 or run_length < 1 or (not 0 <= p <= 1):
        raise ValueError('invalid simulation parameters')
    weather = rng.random((trials, days)) < p
    result = np.zeros(trials, dtype=bool)
    for start in range(days - run_length + 1):
        result |= weather[:, start:start + run_length].all(1)
    return result

def inventory_transition(rate=1.0, capacity=3, restock_below=1):
    """Beginning-of-week stock 1..capacity; replace stock below threshold by capacity.

    Restocking follows demand. Demand beyond stock is lost, not backlogged.
    """
    if rate < 0 or not np.isfinite(rate) or capacity < 1 or (not 1 <= restock_below <= capacity):
        raise ValueError('invalid inventory parameters')
    P = np.zeros((capacity, capacity))
    for stock in range(1, capacity + 1):
        for demand in range(stock):
            remaining = stock - demand
            target = capacity if remaining < restock_below else remaining
            P[stock - 1, target - 1] += poisson.pmf(demand, rate)
        P[stock - 1, capacity - 1] += poisson.sf(stock - 1, rate)
    return P

def inverse_exponential(u, rate=1.0):
    """Inverse CDF using log1p; u=0 allowed, u=1 excluded to keep finite samples."""
    u = np.asarray(u, float)
    if not np.isfinite(rate) or rate <= 0 or (not np.isfinite(u).all()) or np.any((u < 0) | (u >= 1)):
        raise ValueError('rate>0 and 0<=u<1 required')
    return -np.log1p(-u) / rate

def first_passage(rng, threshold=100.0, initial=1.0, max_steps=100000):
    """Example 9.3: sum X_1+...+X_n; X_0 supplies the first rate, not the sum."""
    if min(threshold, initial) <= 0 or not np.isfinite([threshold, initial]).all():
        raise ValueError('positive finite threshold and initial rate required')
    state = float(initial)
    total = 0.0
    for n in range(1, max_steps + 1):
        state = float(rng.exponential(1 / state))
        total += state
        if not np.isfinite(state) or state <= 0:
            raise FloatingPointError('degenerate exponential state')
        if total >= threshold:
            return n
    raise RuntimeError('first-passage horizon exhausted')
