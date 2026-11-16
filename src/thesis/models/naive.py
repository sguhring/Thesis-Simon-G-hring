"""Naive benchmark: tomorrow's variance is the average realised variance of the last `window` days.

The h-day variance is h times that average (no mean reversion, no dynamics). Return quantiles come
from a normal (or t, config `dist`) with that variance. Nothing is estimated, so the windows only
label `fit_origin`.
"""
from __future__ import annotations

import pandas as pd

from thesis.models.base import dist_df, forecast_rows, window_mask


def fit_predict(stock: pd.DataFrame, windows, horizons, cfg: dict) -> pd.DataFrame:
    spec = cfg["models"]["naive"]
    levels = cfg["evaluation"]["quantiles"]
    g = stock.sort_values("date").reset_index(drop=True)
    avg = g["rv_target"].rolling(spec["window"]).mean()
    sym = g["symbol"].iloc[0]
    out = []
    for fit_origin, until in windows:
        m = window_mask(g["date"], fit_origin, until)
        if not m.any():
            continue
        for h in horizons:
            out.append(forecast_rows(sym, g["date"][m], h, "naive", h * avg[m].to_numpy(), levels,
                                     df=dist_df(spec), fit_origin=fit_origin))
    return pd.concat(out, ignore_index=True)
