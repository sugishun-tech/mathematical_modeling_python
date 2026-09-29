"""Small regression helpers with an explicit forecast-uncertainty convention."""
import numpy as np
import pandas as pd
from scipy.stats import norm

def ar1_forecast(intercept, trend, phi, last_value, first_time, horizon, sigma, confidence=0.95):
    """X_t=a+b*t+phi*X_(t-1)+epsilon_t, conditional on fitted coefficients.

    Innovation variance grows as sigma^2*sum(phi^(2*j),j=0..h-1).
    This interval omits parameter uncertainty and model misspecification.
    """
    if not np.isfinite([intercept, trend, phi, last_value, sigma]).all() or sigma < 0 or (not 0 < confidence < 1) or (horizon < 1) or (int(horizon) != horizon):
        raise ValueError('finite parameters, positive integer horizon, sigma>=0 required')
    value = float(last_value)
    variance = 0.0
    rows = []
    z = norm.ppf((1 + confidence) / 2)
    for h in range(1, horizon + 1):
        time = first_time + h - 1
        value = intercept + trend * time + phi * value
        variance = phi * phi * variance + sigma * sigma
        sd = np.sqrt(variance)
        rows.append({'horizon': h, 't': time, 'forecast': value, 'innovation_variance': variance, 'lower': value - z * sd, 'upper': value + z * sd})
    return pd.DataFrame(rows)

def corrected_deadtime_rate(count, elapsed, dead_time):
    """Type-I/nonparalyzable counter estimate n/(T-n*a), not a type-II model."""
    if count <= 0 or int(count) != count or dead_time < 0 or (not np.isfinite([elapsed, dead_time]).all()) or (elapsed <= count * dead_time):
        raise ValueError('require positive count and T > n * dead_time >= 0')
    return count / (elapsed - count * dead_time)
