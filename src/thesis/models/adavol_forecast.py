"""AdaVol as a forecast-table model.

AdaVol updates its parameters after every observation, so there is no re-estimation at the fit
origins: one pass over the stock's whole return series gives the one-day-ahead variance for every day,
and each forecast uses only the returns up to its origin (tests/test_adavol.py). The windows only
label `fit_origin`.

Horizon h: the recursion is a GARCH(1,1) around the running variance gamma2 with theta = (alpha, beta)
frozen at the origin, so the j-day-ahead variance is gamma2 + (alpha + beta)^(j-1) (sigma2_{t+1} -
gamma2) and `var` is the sum over j = 1..h. Return quantiles are Gaussian, as in de Vilmarest & Werge
(2025) (config `dist`).

Leading zero returns are dropped (the recursion cannot start on one; same as the authors' notebook).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from thesis.models.adavol import adavol
from thesis.models.base import dist_df, forecast_rows, window_mask


def multi_step_sum(sigma2_next: np.ndarray, gamma2: np.ndarray, persistence: np.ndarray, h: int) -> np.ndarray:
    """Sum over j = 1..h of gamma2 + persistence^(j-1) (sigma2_next - gamma2)."""
    rho = np.clip(np.asarray(persistence, dtype=float), 0.0, 1.0)
    geometric = np.full_like(rho, float(h))                 # rho = 1: every day carries the full gap
    ok = rho < 1.0
    geometric[ok] = (1.0 - rho[ok] ** h) / (1.0 - rho[ok])
    return h * np.asarray(gamma2, dtype=float) + (np.asarray(sigma2_next, dtype=float) - gamma2) * geometric


def fit_predict(stock: pd.DataFrame, windows, horizons, cfg: dict) -> pd.DataFrame:
    spec = cfg["models"]["adavol"]
    levels = cfg["evaluation"]["quantiles"]
    g = stock.sort_values("date").dropna(subset=["ret"])
    g = g[g["ret"].ne(0).cummax()].reset_index(drop=True)
    x = g["ret"].to_numpy(dtype=float)
    fit = adavol(x, tuple(spec.get("theta0", (0.05, 0.90))), eta=float(spec.get("eta", 0.1)))
    sigma2_next = fit.sigma2[1:]                      # forecast for the day after x[k]
    persistence = fit.theta.sum(axis=1)
    sym = g["symbol"].iloc[0]
    out = []
    for fit_origin, until in windows:
        m = window_mask(g["date"], fit_origin, until)
        if not m.any():
            continue
        for h in horizons:
            var = multi_step_sum(sigma2_next[m], fit.gamma2[m], persistence[m], h)
            out.append(forecast_rows(sym, g["date"][m], h, "adavol", var, levels, df=dist_df(spec),
                                     fit_origin=fit_origin))
    return pd.concat(out, ignore_index=True)
