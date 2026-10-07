"""Feature table for HAR-type and ML models. All features use information up to and including day t.

Output: data/processed/features.parquet. Targets for horizon h are added as log mean realised
variance over days t+1 .. t+h (so a 20-day target is the average daily variance over the window).
Run:    python -m thesis.features
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from thesis.paths import FEATURES, PANEL, load_config


def har_lags(s: pd.Series, lags: list[int]) -> pd.DataFrame:
    out = {}
    for L in lags:
        out[f"{s.name}_m{L}"] = s.rolling(L).mean()
    return pd.DataFrame(out)


def build(cfg: dict) -> pd.DataFrame:
    p = pd.read_parquet(PANEL)
    lags = cfg["models"]["har"]["lags"]
    frames = []
    for sym, g in p.groupby("symbol", sort=False):
        g = g.sort_values("date").copy()
        log_rv = np.log(g["rv_target"]).rename("log_rv")
        f = pd.concat([
            g[["symbol", "date", "rv_target", "log_rv_target", "ret", "vix", "mkt_rv", "earnings_afterclose"]],
            har_lags(log_rv, lags),
            har_lags(np.log(g["rsn5_ss"]).rename("log_rsn"), lags[:1]),
            har_lags(np.log(g["rsp5_ss"]).rename("log_rsp"), lags[:1]),
            har_lags(np.log(g["rq5_ss"]).rename("log_rq"), lags[:1]),
            har_lags(np.log(g["mkt_rv"]).rename("log_mkt_rv"), lags),
        ], axis=1)
        f["log_vix"] = np.log(g["vix"])
        f["ret_m1"] = g["ret"]
        f["neg_ret_m1"] = g["ret"].clip(upper=0)
        # jump share: (rv - bv)/rv, floored at 0
        f["jump_share"] = ((g["rv5_ss"] - g["bv5_ss"]) / g["rv5_ss"]).clip(lower=0)
        f["dow"] = g["date"].dt.dayofweek
        for h in cfg["horizons"]:
            fwd = g["rv_target"].shift(-1).rolling(h).mean().shift(-(h - 1))
            f[f"y_h{h}"] = np.log(fwd)
        frames.append(f)
    out = pd.concat(frames, ignore_index=True)
    return out


def main() -> None:
    cfg = load_config()
    f = build(cfg)
    print(f"features: {f.shape}, columns: {list(f.columns)}")
    f.to_parquet(FEATURES, index=False)
    print("saved", FEATURES)


if __name__ == "__main__":
    main()
