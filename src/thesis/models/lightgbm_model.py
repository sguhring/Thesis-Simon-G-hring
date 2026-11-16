"""LightGBM on the log realised variance, one model pooled across all stocks (a "global" model),
one model per horizon, re-estimated at every fit origin on the expanding window.

Features (config `models.lightgbm.features`): the HAR averages of log rv, semivariances, quarticity,
the market's realised variance, the VIX, yesterday's return and its negative part, the jump share,
the weekday, the earnings flag, plus `log_rv_expanding`, the stock's own average log variance up to
the day (the per-stock scale a pooled model needs; Bergmeir's course, notes/ffds_course_assessment.md).
Every feature uses information up to and including the forecast origin (features.py).

Two targets, written as separate models:
  lgbm        y_h = log mean daily variance over t+1 .. t+h (decision 9), the level
  lgbm_ratio  y_h - log_rv_m22: the log ratio of the coming variance to the last 22 days. Trees cannot
              predict outside the range of their training targets, so a level model trained before a
              crisis cannot forecast crisis-level variance; the ratio target is stationary and lets the
              model extrapolate the level (course note, item 3). The prediction is added back.

Number of trees: chosen by early stopping on the last `validation_days` trading days before the fit
origin (train = everything before them minus an h-day gap, so no validation target overlaps a training
row), then the model is refitted on all training rows with that number of trees. Nothing after the fit
origin is used. The validation residuals also give s^2 for the mean correction: as for HAR, `*_median`
= h exp(mu) and the unsuffixed row = h exp(mu + s^2/2). Return quantiles: normal (config `dist`).
"""
from __future__ import annotations

import warnings

import lightgbm as lgb
import numpy as np
import pandas as pd

from thesis.models.base import dist_df, forecast_rows

DEFAULT_FEATURES = ["log_rv_m1", "log_rv_m5", "log_rv_m22", "log_rsn_m1", "log_rsp_m1", "log_rq_m1",
                    "log_mkt_rv_m1", "log_mkt_rv_m5", "log_mkt_rv_m22", "log_vix", "ret_m1", "neg_ret_m1",
                    "jump_share", "dow", "earnings_afterclose", "log_rv_expanding"]


def add_scale_feature(f: pd.DataFrame) -> pd.DataFrame:
    """The stock's expanding mean of log rv up to each day (needs log_rv_m1 = log rv of the day)."""
    f = f.sort_values(["symbol", "date"]).reset_index(drop=True)
    f["log_rv_expanding"] = f.groupby("symbol")["log_rv_m1"].transform(lambda s: s.expanding().mean())
    return f


def _params(spec: dict, seed: int) -> dict:
    return {"objective": "regression", "learning_rate": float(spec.get("learning_rate", 0.03)),
            "num_leaves": int(spec.get("num_leaves", 15)),
            "min_child_samples": int(spec.get("min_child_samples", 100)),
            "feature_fraction": float(spec.get("feature_fraction", 0.8)),
            "bagging_fraction": float(spec.get("bagging_fraction", 0.8)), "bagging_freq": 1,
            "lambda_l2": float(spec.get("lambda_l2", 1.0)),
            "seed": seed, "deterministic": True, "force_col_wise": True, "verbosity": -1,
            "num_threads": int(spec.get("num_threads", 0))}


def fit_one(X: np.ndarray, y: np.ndarray, is_val: np.ndarray, spec: dict, seed: int) -> tuple[lgb.Booster, int, float]:
    """Early-stop on the validation rows, refit on everything with that many trees.
    Returns the booster, the number of trees and the validation residual variance."""
    params = _params(spec, seed)
    n_max = int(spec.get("n_estimators", 500))
    dtrain = lgb.Dataset(X[~is_val], y[~is_val], free_raw_data=False)
    dval = lgb.Dataset(X[is_val], y[is_val], reference=dtrain, free_raw_data=False)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        first = lgb.train(params, dtrain, num_boost_round=n_max, valid_sets=[dval],
                          callbacks=[lgb.early_stopping(int(spec.get("early_stopping_rounds", 50)), verbose=False)])
        n_trees = max(int(first.best_iteration), 1)
        resid = y[is_val] - first.predict(X[is_val], num_iteration=n_trees)
        s2 = float(resid @ resid) / max(len(resid) - 1, 1)
        final = lgb.train(params, lgb.Dataset(X, y, free_raw_data=False), num_boost_round=n_trees)
    return final, n_trees, s2


def fit_predict(features: pd.DataFrame, windows, horizons, cfg: dict, log=None) -> pd.DataFrame:
    """Pooled model: `features` holds all stocks. Rows for every stock and day in each window."""
    spec = cfg["models"]["lightgbm"]
    levels = cfg["evaluation"]["quantiles"]
    cols = list(spec.get("features", DEFAULT_FEATURES))
    variants = list(spec.get("variants", ["level", "ratio"]))
    val_days = int(spec.get("validation_days", 250))
    seed = int(cfg.get("seed", 0))
    f = add_scale_feature(features.copy())
    f["earnings_afterclose"] = f["earnings_afterclose"].astype(int) if "earnings_afterclose" in f else 0
    missing = [c for c in cols if c not in f.columns]
    if missing:
        raise KeyError(f"features missing for LightGBM: {missing}")
    days = pd.DatetimeIndex(f["date"].drop_duplicates().sort_values())
    pos = pd.Series(np.arange(len(days)), index=days)
    f["pos"] = pos.reindex(f["date"]).to_numpy()
    X_all = f[cols].to_numpy(dtype=float)
    out, diag = [], []
    for w, (fit_origin, until) in enumerate(windows):
        fit_origin, until = pd.Timestamp(fit_origin), pd.Timestamp(until)
        k = int(pos[fit_origin])
        predict = ((f["date"] >= fit_origin) & (f["date"] < until)).to_numpy()
        if not predict.any():
            continue
        for h in horizons:
            y_level = f[f"y_h{h}"].to_numpy(dtype=float)
            train = (f["pos"].to_numpy() + h <= k)                     # target observed by the fit origin
            is_val_all = f["pos"].to_numpy() + h > k - val_days          # the last val_days targets
            gap = (f["pos"].to_numpy() + h > k - val_days - h) & ~is_val_all   # h-day gap before them
            for variant in variants:
                y = y_level if variant == "level" else y_level - f["log_rv_m22"].to_numpy(dtype=float)
                ok = train & np.isfinite(y) & np.isfinite(X_all).all(axis=1) & ~gap
                booster, n_trees, s2 = fit_one(X_all[ok], y[ok], is_val_all[ok], spec, seed + w)
                mu = booster.predict(X_all[predict])
                if variant == "ratio":
                    mu = mu + f.loc[predict, "log_rv_m22"].to_numpy(dtype=float)
                name = "lgbm" if variant == "level" else "lgbm_ratio"
                diag.append({"fit_origin": fit_origin, "horizon": h, "variant": variant, "n_train": int(ok.sum()),
                             "n_trees": n_trees, "s2_val": s2})
                sub = f.loc[predict, ["symbol", "date"]].reset_index(drop=True)   # aligned with mu
                for sym in sub["symbol"].unique():
                    sel = (sub["symbol"] == sym).to_numpy()
                    for suffix, var in (("", h * np.exp(mu[sel] + s2 / 2)), ("_median", h * np.exp(mu[sel]))):
                        out.append(forecast_rows(sym, sub.loc[sel, "date"], h, name + suffix, var, levels,
                                                 df=dist_df(spec), fit_origin=fit_origin))
        if log is not None:
            log(f"lightgbm window {w + 1}/{len(windows)} {fit_origin.date()}: " +
                ", ".join(f"{d['variant']} h{d['horizon']} {d['n_trees']} trees" for d in diag[-2 * len(variants):]))
    res = pd.concat(out, ignore_index=True)
    res.attrs["diagnostics"] = pd.DataFrame(diag)
    return res


fit_predict.pooled = True
