"""Pooled HAR: the regression of `har.py`, fitted once on all stocks instead of once per stock.

Decision 12. This is the bridge row between `har` (per stock, linear) and `lgbm` (pooled, nonlinear):
the pooling effect is the step `har` -> `har_pooled`, the nonlinearity effect is the step
`har_pooled` -> `lgbm`, both measured on the same data, the same forecast schedule and the same loss.
Without it the LightGBM-vs-HAR gap changes two things at once and cannot be attributed to either.

    y_h(t) = b0 + b1 log_rv_m1(t) + b5 log_rv_m5(t) + b22 log_rv_m22(t) + bs log_rv_expanding(t) + e

Per stock the intercept absorbs each stock's volatility level; one shared intercept cannot, so the
stock's expanding mean of log rv enters as a regressor -- the same feature the pooled LightGBM gets
(decision 12). `scale_feature: false` in the config drops it.

Everything else is `har.py` unchanged, so the two rows differ in exactly one thing: OLS at every
monthly fit origin on the rows whose target is fully observed by then (t + h <= fit origin, applied on
the panel's global trading-day index), expanding window, no hyperparameters to tune, and the in-sample
residual variance for the retransformation. Two rows per fit, as for HAR: `har_pooled` =
h exp(mu + s^2/2), the conditional mean under normal residuals, and `har_pooled_median` = h exp(mu).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from thesis.models.base import add_scale_feature, day_index, dist_df, forecast_rows


def fit_predict(features: pd.DataFrame, windows, horizons, cfg: dict, log=None) -> pd.DataFrame:
    """Pooled model: `features` holds all stocks. Rows for every stock and day in each window."""
    spec = cfg["models"]["har_pooled"]
    levels = cfg["evaluation"]["quantiles"]
    cols = [f"log_rv_m{L}" for L in spec["lags"]]
    if spec.get("scale_feature", True):
        cols = cols + ["log_rv_expanding"]
    f = add_scale_feature(features.copy())
    missing = [c for c in cols if c not in f.columns]
    if missing:
        raise KeyError(f"features missing for the pooled HAR: {missing}")
    f, _ = day_index(f)
    X_all = np.column_stack([np.ones(len(f)), f[cols].to_numpy(dtype=float)])
    names = ["const"] + cols
    out, diag = [], []
    for w, (fit_origin, until) in enumerate(windows):
        fit_origin, until = pd.Timestamp(fit_origin), pd.Timestamp(until)
        k = int(f.loc[f["date"] == fit_origin, "pos"].iloc[0])
        predict = ((f["date"] >= fit_origin) & (f["date"] < until)).to_numpy()
        if not predict.any():
            continue
        sub = f.loc[predict, ["symbol", "date"]].reset_index(drop=True)      # aligned with mu below
        for h in horizons:
            y = f[f"y_h{h}"].to_numpy(dtype=float)
            train = ((f["pos"].to_numpy() + h <= k)                          # target observed by then
                     & np.isfinite(y) & np.isfinite(X_all).all(axis=1))
            if train.sum() < 10 * X_all.shape[1]:
                raise ValueError(f"only {int(train.sum())} rows to fit the pooled HAR at "
                                 f"{fit_origin.date()}")
            beta, *_ = np.linalg.lstsq(X_all[train], y[train], rcond=None)
            resid = y[train] - X_all[train] @ beta
            s2 = float(resid @ resid) / (int(train.sum()) - X_all.shape[1])
            mu = X_all[predict] @ beta
            diag.append({"fit_origin": fit_origin, "horizon": h, "n_train": int(train.sum()),
                         "s2": s2, **dict(zip(names, beta)),
                         "lag_sum": float(beta[1:1 + len(spec["lags"])].sum())})
            for sym in sub["symbol"].unique():
                sel = (sub["symbol"] == sym).to_numpy()
                for suffix, var in (("", h * np.exp(mu[sel] + s2 / 2)), ("_median", h * np.exp(mu[sel]))):
                    out.append(forecast_rows(sym, sub.loc[sel, "date"], h, "har_pooled" + suffix, var,
                                             levels, df=dist_df(spec), fit_origin=fit_origin))
        if log is not None:
            log(f"har_pooled window {w + 1}/{len(windows)} {fit_origin.date()}: " +
                ", ".join(f"h{d['horizon']} lag sum {d['lag_sum']:.3f} s2 {d['s2']:.3f}"
                          for d in diag[-len(horizons):]))
    res = pd.concat(out, ignore_index=True)
    res.attrs["diagnostics"] = pd.DataFrame(diag)
    return res


fit_predict.pooled = True
