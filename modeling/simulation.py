"""Bounded stateful simulations with explicit random generators and censoring."""
import numpy as np

def docking_trial(rng, k=0.02, max_steps=2000, *, initial_velocity=50.0, velocity_tolerance=0.1, acceleration_sd=0.05, adjustment_mean=5.0, adjustment_sd=1.0, cycle_mean=15.0, cycle_error_sd=0.1):
    """Example 9.2, returning (elapsed, observations, rejected_times, completed).

    Positive time draws are obtained by rejection, explicitly replacing the
    unbounded Gaussian time model by its physically feasible truncation.
    Acceleration noise remains Gaussian. A horizon exhaustion is right-censored.
    """
    values = [k, initial_velocity, velocity_tolerance, acceleration_sd, adjustment_mean, adjustment_sd, cycle_mean, cycle_error_sd]
    if not np.isfinite(values).all() or k < 0 or min(velocity_tolerance, adjustment_mean, cycle_mean) <= 0 or (min(acceleration_sd, adjustment_sd, cycle_error_sd) < 0) or (max_steps < 1) or (int(max_steps) != max_steps):
        raise ValueError('invalid control, noise or horizon parameters')
    if adjustment_mean >= cycle_mean and adjustment_sd == 0 and (cycle_error_sd == 0):
        raise ValueError('deterministic waiting time must be positive')
    time = 0.0
    velocity = float(initial_velocity)
    previous_acceleration = 0.0
    rejections = 0
    for step in range(max_steps + 1):
        if abs(velocity) <= velocity_tolerance:
            return (time, step, rejections, True)
        if step == max_steps:
            break
        for _ in range(10000):
            c = rng.normal(adjustment_mean, adjustment_sd)
            w = cycle_mean - c + rng.normal(0, cycle_error_sd)
            if c > 0 and w > 0:
                break
            rejections += 1
        else:
            raise RuntimeError('failed to sample positive control times')
        acceleration = rng.normal(-k * velocity, acceleration_sd)
        velocity = velocity + c * previous_acceleration + w * acceleration
        previous_acceleration = acceleration
        time += c + w
        if not np.isfinite(velocity):
            raise FloatingPointError('nonfinite docking state')
    return (time, max_steps, rejections, False)

def triangular_wind(time, x):
    """Example 9.5: 3 km/h outside [0,20], rising to 8 at x=10, then falling."""
    distance = np.abs(np.asarray(x) - 10)
    return np.where(distance <= 10, 8 - 0.5 * distance, 3.0)
