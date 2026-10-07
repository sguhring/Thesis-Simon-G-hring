"""The forecast-table contract every model must satisfy.

A model is a function  forecast(train_panel, origin, horizon, cfg) -> DataFrame  with one row per
asset and the columns below. Scoring never looks inside a model; it only reads this table, so GARCH,
HAR, LightGBM and a reimplemented M6 method are all evaluated identically.

Columns
-------
symbol        asset
origin        forecast origin date (last day of information used)
horizon       trading days ahead (1 or 20)
model         model name
var           forecast variance of the h-day cumulative return (not annualised)
q_<level>     forecast quantiles of the h-day cumulative return, one column per level in
              config.evaluation.quantiles, e.g. q_0.025, q_0.5, q_0.975
p_q1 .. p_q5  (M6 setting only) probability the asset's h-day return falls in cross-sectional
              quintile 1 (lowest) .. 5 (highest).  Derived from the predictive distribution by
              simulation unless the method produces them directly.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

QUINTILE_COLS = [f"p_q{k}" for k in range(1, 6)]


def forecast_frame(symbols, origin, horizon: int, model: str, var: np.ndarray,
                   quantile_levels: list[float], quantiles: np.ndarray | None = None,
                   mean: np.ndarray | None = None, df: float | None = None) -> pd.DataFrame:
    """Assemble a forecast table. If quantiles are not given, they are read off a Student-t (df) or
    normal location-scale distribution with the given mean and variance."""
    var = np.asarray(var, dtype=float)
    mean = np.zeros_like(var) if mean is None else np.asarray(mean, dtype=float)
    out = pd.DataFrame({"symbol": list(symbols), "origin": pd.Timestamp(origin),
                        "horizon": horizon, "model": model, "var": var})
    if quantiles is None:
        sd = np.sqrt(var)
        if df is None:
            z = stats.norm.ppf(quantile_levels)
            quantiles = mean[:, None] + sd[:, None] * z[None, :]
        else:
            # scale so that the t distribution has the forecast variance
            scale = sd * np.sqrt((df - 2) / df)
            z = stats.t.ppf(quantile_levels, df)
            quantiles = mean[:, None] + scale[:, None] * z[None, :]
    for j, lv in enumerate(quantile_levels):
        out[f"q_{lv}"] = quantiles[:, j]
    return out


def quintile_probs_from_samples(samples: np.ndarray) -> np.ndarray:
    """samples: (n_sims, n_assets) simulated h-day returns. Returns (n_assets, 5) quintile
    probabilities by ranking assets within each simulation, as the M6 scoring does."""
    n_sims, n_assets = samples.shape
    ranks = samples.argsort(axis=1).argsort(axis=1)            # 0 = lowest
    quint = np.floor(ranks * 5 / n_assets).astype(int)          # 0..4
    probs = np.zeros((n_assets, 5))
    for k in range(5):
        probs[:, k] = (quint == k).mean(axis=0)
    return probs
