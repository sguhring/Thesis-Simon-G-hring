"""HAR (Corsi 2009) on the log realised variance, one regression per stock and horizon.

    y_h(t) = b0 + b1 * log_rv_m1(t) + b5 * log_rv_m5(t) + b22 * log_rv_m22(t) + e,

where y_h is the log of the average daily variance over t+1 .. t+h (decision 9) and the regressors are
the averages of log rv over the last 1, 5 and 22 days (features.py). Estimated by OLS at each fit
origin on the rows whose target is fully observed by then (t + h <= fit_origin), expanding window.

Retransformation (decision 9): the plain exponential of the fitted log is the conditional median of
the variance; with normal residuals the conditional mean is exp(mu + s^2/2), s^2 the residual
variance. Both are written, as `har` (mean) and `har_median`, so the gap between them is visible in
every table. `var` is h times the daily forecast.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from thesis.models.base import dist_df, forecast_rows, window_mask


def fit_predict(stock: pd.DataFrame, windows, horizons, cfg: dict) -> pd.DataFrame:
    spec = cfg["models"]["har"]
    levels = cfg["evaluation"]["quantiles"]
    cols = [f"log_rv_m{L}" for L in spec["lags"]]
    g = stock.sort_values("date").reset_index(drop=True)
    dates = g["date"]
    X = np.column_stack([np.ones(len(g)), g[cols].to_numpy(dtype=float)])
    sym = g["symbol"].iloc[0]
    out = []
    for fit_origin, until in windows:
        k = int(dates.searchsorted(pd.Timestamp(fit_origin)))          # position of the fit origin
        m = window_mask(dates, fit_origin, until)
        if not m.any():
            continue
        for h in horizons:
            y = g[f"y_h{h}"].to_numpy(dtype=float)
            train = np.arange(0, max(k - h + 1, 0))                      # rows with t + h <= fit origin
            train = train[np.isfinite(y[train]) & np.isfinite(X[train]).all(axis=1)]
            if len(train) < 10 * X.shape[1]:
                raise ValueError(f"{sym}: only {len(train)} rows to fit HAR at {pd.Timestamp(fit_origin).date()}")
            beta, rss, *_ = np.linalg.lstsq(X[train], y[train], rcond=None)
            resid = y[train] - X[train] @ beta
            s2 = float(resid @ resid) / (len(train) - X.shape[1])
            mu = X[m] @ beta
            for name, var in (("har", h * np.exp(mu + s2 / 2)), ("har_median", h * np.exp(mu))):
                out.append(forecast_rows(sym, dates[m], h, name, var, levels, df=dist_df(spec),
                                         fit_origin=fit_origin))
    return pd.concat(out, ignore_index=True)
