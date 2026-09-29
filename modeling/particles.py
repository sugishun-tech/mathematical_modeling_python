"""Memory-bounded particle tracking and bin-based concentration diagnostics."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .probability import wilson_interval

@dataclass(frozen=True)
class ParticleResult:
    times: np.ndarray
    counts: np.ndarray
    final_positions: np.ndarray
    snapshots: dict

def centered_pareto(rng, size, alpha=1.1, scale=0.0131):
    """One-sided power-law jump, analytically centered; 1<alpha<2, infinite variance."""
    if not 1 < alpha < 2 or not np.isfinite(scale) or scale <= 0:
        raise ValueError('1<alpha<2 and positive finite scale required')
    u = rng.random(size)
    return (scale / (1 - u)) ** (1 / alpha) - scale ** (1 / alpha) * alpha / (alpha - 1)

def track_particles(rng, number, final_time, steps, drift, noise, *, window=None, snapshot_steps=()):
    """Euler drift plus caller-provided random increments; O(number) working memory.

    noise(rng, number, dt) returns the complete stochastic increment, including
    the time scaling. Never silently clip drift, negative positions or outliers.
    """
    if not isinstance(number, (int, np.integer)) or number < 1 or (not isinstance(steps, (int, np.integer))) or (steps < 1) or (not np.isfinite(final_time)) or (final_time <= 0):
        raise ValueError('positive particle count, time and integer steps required')
    if window is not None and (len(window) != 2 or window[0] >= window[1]):
        raise ValueError('increasing observation window required')
    requested = set(snapshot_steps)
    if any((not isinstance(s, (int, np.integer)) or s < 0 or s > steps for s in requested)):
        raise ValueError('snapshot steps must belong to 0..steps')
    dt = final_time / steps
    x = np.zeros(number)
    times = np.arange(1, steps + 1) * dt
    counts = np.zeros(steps, dtype=int)
    snapshots = {0.0: x.copy()} if 0 in requested else {}
    for j, time in enumerate(times):
        velocity = np.asarray(drift(time - dt, x), float)
        increment = np.asarray(noise(rng, number, dt), float)
        if velocity.shape not in [(), x.shape] or increment.shape != x.shape:
            raise ValueError('drift/noise shape mismatch')
        x = x + velocity * dt + increment
        if not np.isfinite(x).all():
            raise FloatingPointError('nonfinite particle position')
        if window is not None:
            counts[j] = np.count_nonzero((x > window[0]) & (x <= window[1]))
        if j + 1 in requested:
            snapshots[time] = x.copy()
    return ParticleResult(times, counts, x, snapshots)

def concentration_interval(counts, number, total_mass, width, confidence=0.95):
    """Bin-average mass per length, not mass in the bin or density at a point."""
    if total_mass < 0 or width <= 0 or (not np.isfinite([total_mass, width]).all()):
        raise ValueError('nonnegative finite mass and positive width required')
    lo, hi = wilson_interval(counts, number, confidence)
    scale = total_mass / width
    return (scale * np.asarray(counts) / number, scale * lo, scale * hi)

def last_threshold_bracket(times, values, threshold):
    """Last sampled exceedance bracket, NOT a guarantee about future behavior.

    Return (left,right,status). Right=None denotes right-censoring at horizon.
    With no sampled exceedance there is no estimated crossing.
    """
    times, values = (np.asarray(times, float), np.asarray(values, float))
    if times.ndim != 1 or times.shape != values.shape or (not len(times)) or np.any(np.diff(times) <= 0) or (not np.isfinite([times, values]).all()):
        raise ValueError('finite matching series with increasing times required')
    hit = np.flatnonzero(values > threshold)
    if not len(hit):
        return (None, None, 'no sampled exceedance')
    i = int(hit[-1])
    if i == len(times) - 1:
        return (float(times[i]), None, 'right-censored')
    return (float(times[i]), float(times[i + 1]), 'last sampled downcrossing (not a safety guarantee)')
