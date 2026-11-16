"""Rolling-origin driver (decision 4): monthly fit origins on an expanding window, a forecast for
every trading day with the latest parameters, all models, all stocks.

Writes  data/processed/forecasts.parquet   (the forecast table, thesis.models.base)
        data/processed/realised.parquet    (symbol, origin, horizon, ret_h, rv_h: the truth)
Run:    python -m thesis.evaluate.rolling [--models garch,har] [--symbols AAPL,MSFT] [--jobs 8]
"""
from __future__ import annotations

import argparse
import time

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from thesis.models import MODELS, is_pooled
from thesis.paths import FEATURES, FORECASTS, REALISED, load_config


def fit_windows(dates: pd.Series, cfg: dict) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """(fit_origin, until) pairs: the first trading day of every month from config
    evaluation.first_origin on; `until` is the next fit origin, or the day after the last date."""
    d = pd.DatetimeIndex(pd.Series(dates).drop_duplicates().sort_values())
    d = d[d >= pd.Timestamp(cfg["evaluation"]["first_origin"])]
    if cfg["evaluation"].get("origin_frequency", "monthly") != "monthly":
        raise NotImplementedError("only monthly fit origins are implemented")
    origins = pd.Series(d).groupby([d.year, d.month]).min().tolist()
    ends = origins[1:] + [d[-1] + pd.Timedelta(days=1)]
    return list(zip(origins, ends))


def realised(features: pd.DataFrame, horizons) -> pd.DataFrame:
    """The truth for each (symbol, origin, horizon): the h-day cumulative return and the sum of the
    daily realised variances over origin+1 .. origin+h."""
    out = []
    for sym, g in features.groupby("symbol", sort=False):
        g = g.sort_values("date")
        for h in horizons:
            fwd = lambda s: s.shift(-1).rolling(h).sum().shift(-(h - 1))
            out.append(pd.DataFrame({"symbol": sym, "origin": g["date"].to_numpy(), "horizon": h,
                                     "ret_h": fwd(g["ret"]).to_numpy(), "rv_h": fwd(g["rv_target"]).to_numpy()}))
    return pd.concat(out, ignore_index=True)


def _task(name, stock, windows, horizons, cfg):
    t0 = time.time()
    fc = MODELS[name](stock, windows, horizons, cfg)
    return fc, name, stock["symbol"].iloc[0], time.time() - t0


def run(features: pd.DataFrame, cfg: dict, models=None, symbols=None, n_jobs: int = -1,
        verbose: bool = True) -> pd.DataFrame:
    models = list(MODELS) if models is None else list(models)
    unknown = set(models) - set(MODELS)
    if unknown:
        raise KeyError(f"unknown models {sorted(unknown)}; known: {list(MODELS)}")
    f = features if symbols is None else features[features["symbol"].isin(symbols)]
    windows = fit_windows(f["date"], cfg)
    horizons = list(cfg["horizons"])
    stocks = {sym: g.sort_values("date").reset_index(drop=True) for sym, g in f.groupby("symbol", sort=False)}
    per_stock = [m for m in models if not is_pooled(m)]
    pooled = [m for m in models if is_pooled(m)]
    tasks = [(name, sym) for name in per_stock for sym in stocks]
    if verbose:
        print(f"{len(windows)} fit windows from {windows[0][0].date()} to {windows[-1][0].date()}, "
              f"{len(stocks)} stocks, per-stock models {per_stock}: {len(tasks)} tasks; pooled models {pooled}")
    frames = []
    if tasks:
        results = Parallel(n_jobs=n_jobs)(delayed(_task)(name, stocks[sym], windows, horizons, cfg) for name, sym in tasks)
        if verbose:
            timing = pd.DataFrame([(n, s, t) for _, n, s, t in results], columns=["model", "symbol", "seconds"])
            print(timing.groupby("model")["seconds"].agg(["mean", "max"]).round(1).to_string())
        frames += [r[0] for r in results]
    for name in pooled:                       # one task on all stocks; LightGBM parallelises internally
        t0 = time.time()
        frames.append(MODELS[name](f, windows, horizons, cfg, log=print if verbose else None))
        if verbose:
            print(f"{name}: {time.time() - t0:.0f} s")
    out = pd.concat(frames, ignore_index=True)
    out["origin"] = pd.to_datetime(out["origin"])
    return out.sort_values(["model", "symbol", "horizon", "origin"]).reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=None, help="comma-separated subset of " + ",".join(MODELS))
    ap.add_argument("--symbols", default=None)
    ap.add_argument("--jobs", type=int, default=-1)
    a = ap.parse_args()
    cfg = load_config()
    features = pd.read_parquet(FEATURES)
    models = a.models.split(",") if a.models else None
    symbols = a.symbols.split(",") if a.symbols else None
    t0 = time.time()
    fc = run(features, cfg, models=models, symbols=symbols, n_jobs=a.jobs)
    if models is not None and FORECASTS.exists():
        # partial run: replace only the models that were rerun
        old = pd.read_parquet(FORECASTS)
        fc = pd.concat([old[~old["model"].isin(fc["model"].unique())], fc], ignore_index=True)
    fc.to_parquet(FORECASTS, index=False)
    truth = realised(features, cfg["horizons"])
    truth.to_parquet(REALISED, index=False)
    print(f"forecasts: {len(fc):,} rows, models {sorted(fc['model'].unique())}, "
          f"{fc['origin'].min().date()} to {fc['origin'].max().date()}, {time.time() - t0:.0f} s")
    print("saved", FORECASTS, "and", REALISED)


if __name__ == "__main__":
    main()
