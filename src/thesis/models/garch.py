"""GARCH(1,1) and GJR-GARCH(1,1,1) with Student-t innovations (arch), one model per stock.

Parameters are estimated by maximum likelihood at each fit origin on all returns up to and including
it (expanding window). Between fit origins the parameters are held and the conditional variance is
filtered through the new returns, so every day gets a forecast made with the data up to that day.

Horizon 1: variance and quantiles are analytic (location-scale t with the fitted degrees of freedom).
Horizon h > 1: `var` is the analytic sum of the daily variance forecasts over the h days; the return
quantiles come from `n_sims` simulated paths of the fitted model (the sum of h t-distributed shocks
with time-varying variance is not t), seeded from config so runs are reproducible.

Returns are scaled by 100 for the optimiser (arch's recommendation); outputs are scaled back.
"""
from __future__ import annotations

import warnings
import zlib

import numpy as np
import pandas as pd
from arch import arch_model
from arch.univariate import Normal, StudentsT

from thesis.models.base import forecast_rows, qcol, window_mask

SCALE = 100.0


def fit_predict(stock: pd.DataFrame, windows, horizons, cfg: dict, spec: str = "garch") -> pd.DataFrame:
    m = cfg["models"][spec]
    p, o, q = int(m.get("p", 1)), int(m.get("o", 0)), int(m.get("q", 1))
    dist = m.get("dist", "t")
    levels = cfg["evaluation"]["quantiles"]
    n_sims = int(cfg["evaluation"].get("n_sims", 2000))
    seed = int(cfg.get("seed", 0))
    g = stock.sort_values("date").dropna(subset=["ret"])
    r = pd.Series(SCALE * g["ret"].to_numpy(dtype=float), index=pd.DatetimeIndex(g["date"]))
    sym = g["symbol"].iloc[0]
    max_h = max(horizons)
    out = []
    for i, (fit_origin, until) in enumerate(windows):
        fit_origin, until = pd.Timestamp(fit_origin), pd.Timestamp(until)
        y = r[r.index < until]
        pos = int(y.index.searchsorted(fit_origin))
        if pos >= len(y) or y.index[pos] != fit_origin:
            raise ValueError(f"{sym}: fit origin {fit_origin.date()} is not a trading day of the series")
        last_obs = y.index[pos + 1] if pos + 1 < len(y) else None     # arch's last_obs is exclusive
        am = arch_model(y, mean="Constant", vol="GARCH", p=p, o=o, q=q, dist=dist)
        am.distribution = (StudentsT if dist == "t" else Normal)(seed=seed + 1000 * i + zlib.crc32(sym.encode()) % 1000)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = am.fit(last_obs=last_obs, disp="off", show_warning=False)
            fc = res.forecast(start=fit_origin, horizon=max_h, method="simulation",
                              simulations=n_sims, reindex=False)
        mu = float(res.params["mu"])
        nu = float(res.params["nu"]) if dist == "t" else None
        origins = fc.variance.index
        sims = fc.simulations.values                                   # (n_days, n_sims, max_h), returns
        for h in horizons:
            var = fc.variance.iloc[:, :h].sum(axis=1).to_numpy() / SCALE ** 2
            if h == 1:
                rows = forecast_rows(sym, origins, h, spec, var, levels, mean=mu / SCALE, df=nu,
                                     fit_origin=fit_origin)
            else:
                cum = sims[:, :, :h].sum(axis=2) / SCALE
                qs = np.quantile(cum, levels, axis=1).T
                rows = forecast_rows(sym, origins, h, spec, var, levels, quantiles=qs, fit_origin=fit_origin)
            out.append(rows)
    res_df = pd.concat(out, ignore_index=True)
    assert res_df[qcol(levels[0])].notna().all()
    return res_df
