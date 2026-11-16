"""The forecast-table contract every model must satisfy.

A model is a function  fit_predict(stock, windows, horizons, cfg) -> DataFrame  (see `thesis.models`)
with one row per forecast origin and horizon for one stock, and the columns below. Scoring never
looks inside a model; it only reads this table, so GARCH, HAR, LightGBM and a reimplemented M6 method
are all evaluated identically.

Columns
-------
symbol        asset
origin        the day the forecast is made (last day of information used)
fit_origin    the day the parameters were last estimated (decision 4: monthly, expanding window);
              forecasts between two fit origins use the latest parameters and the data up to `origin`
horizon       trading days ahead (1 or 20)
model         model name; a model that forecasts on the log scale records its retransformation here
              (e.g. `har` = exp(mu + s^2/2), the conditional mean; `har_median` = exp(mu))
var           forecast variance of the h-day cumulative return (not annualised): the sum of the daily
              variances over origin+1 .. origin+h (decision 9)
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


def qcol(level: float) -> str:
    """Column name of a quantile level, stable against floating-point noise (0.04999.. -> q_0.05)."""
    return f"q_{round(float(level), 6):g}"


def location_scale_quantiles(mean: np.ndarray, var: np.ndarray, levels: list[float],
                             df: float | None = None) -> np.ndarray:
    """(n, len(levels)) quantiles of a normal (df None) or Student-t (df) distribution with the given
    mean and variance. The t is scaled so that its variance equals `var`."""
    sd = np.sqrt(np.asarray(var, dtype=float))
    mean = np.asarray(mean, dtype=float)
    if df is None:
        z = stats.norm.ppf(levels)
        return mean[:, None] + sd[:, None] * z[None, :]
    scale = sd * np.sqrt((df - 2) / df)
    z = stats.t.ppf(levels, df)
    return mean[:, None] + scale[:, None] * z[None, :]


def forecast_rows(symbol: str, origins, horizon: int, model: str, var: np.ndarray,
                  quantile_levels: list[float], quantiles: np.ndarray | None = None,
                  mean: np.ndarray | None = None, df: float | None = None,
                  fit_origin=None) -> pd.DataFrame:
    """Forecast table for one stock and one horizon over many origins. If `quantiles` (n, levels)
    is not given, they are read off a normal (df None) or Student-t (df) with the given mean and
    variance."""
    var = np.asarray(var, dtype=float)
    mean = np.zeros_like(var) if mean is None else np.broadcast_to(np.asarray(mean, dtype=float), var.shape)
    out = pd.DataFrame({"symbol": symbol, "origin": pd.DatetimeIndex(origins),
                        "fit_origin": pd.Timestamp(fit_origin) if fit_origin is not None else pd.NaT,
                        "horizon": horizon, "model": model, "var": var})
    if quantiles is None:
        quantiles = location_scale_quantiles(mean, var, quantile_levels, df)
    for j, lv in enumerate(quantile_levels):
        out[qcol(lv)] = quantiles[:, j]
    return out


def forecast_frame(symbols, origin, horizon: int, model: str, var: np.ndarray,
                   quantile_levels: list[float], quantiles: np.ndarray | None = None,
                   mean: np.ndarray | None = None, df: float | None = None) -> pd.DataFrame:
    """Forecast table for many assets at one origin (the M6 setting)."""
    var = np.asarray(var, dtype=float)
    mean = np.zeros_like(var) if mean is None else np.asarray(mean, dtype=float)
    out = pd.DataFrame({"symbol": list(symbols), "origin": pd.Timestamp(origin),
                        "horizon": horizon, "model": model, "var": var})
    if quantiles is None:
        quantiles = location_scale_quantiles(mean, var, quantile_levels, df)
    for j, lv in enumerate(quantile_levels):
        out[qcol(lv)] = quantiles[:, j]
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


def window_mask(dates: pd.Series, fit_origin, until) -> np.ndarray:
    """Rows whose forecast origin lies in [fit_origin, until)."""
    return ((dates >= pd.Timestamp(fit_origin)) & (dates < pd.Timestamp(until))).to_numpy()


def dist_df(spec: dict) -> float | None:
    """Degrees of freedom for the return shape of a variance-only model: None for the normal."""
    dist = spec.get("dist", "normal")
    if dist == "normal":
        return None
    if dist == "t":
        return float(spec.get("df", 5))
    raise ValueError(f"unknown dist {dist!r}; use 'normal' or 't'")
