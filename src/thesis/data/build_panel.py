"""Build the clean stock-day panel: VOLARE realised measures + Yahoo returns + flags.

Output: data/processed/panel.parquet, one row per (symbol, date), 40 stocks x 2,932 days.
Run:    python -m thesis.data.build_panel
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from thesis.paths import FLAGS, PANEL, RAW_VOLARE, RAW_YAHOO, load_config

VOLARE_KEEP = [
    "date", "symbol", "open_price", "close_price", "high_price", "low_price", "volume", "trades",
    "rv1", "rv5", "rv5_ss", "bv5", "bv5_ss", "rsp5", "rsn5", "rsp5_ss", "rsn5_ss",
    "medrv5", "minrv5", "rk", "rq5", "rq5_ss", "pr", "gkr", "rr5",
]


def load_volare(cfg: dict) -> pd.DataFrame:
    v = pd.read_csv(RAW_VOLARE, parse_dates=["date"], usecols=VOLARE_KEEP)
    v = v[v.symbol.isin(cfg["sample"]["tickers"])]
    v = v[(v.date >= cfg["sample"]["start"]) & (v.date <= cfg["sample"]["end"])]
    return v.rename(columns={"open_price": "volare_open", "close_price": "volare_close",
                             "high_price": "volare_high", "low_price": "volare_low"})


def load_yahoo(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    y = pd.read_csv(RAW_YAHOO, parse_dates=["date"])
    y = y.sort_values(["symbol", "date"])
    g = y.groupby("symbol")
    # close-to-close log return from dividend- and split-adjusted close
    y["ret"] = g["adj_close"].transform(lambda s: np.log(s).diff())
    # overnight: previous close -> today's open, from split-adjusted (not dividend-adjusted) prices
    y["ret_overnight"] = np.log(y["open"]) - np.log(g["close"].shift(1))
    y["ret_intraday"] = np.log(y["close"]) - np.log(y["open"])
    stocks = y[y.symbol.isin(cfg["sample"]["tickers"])][
        ["date", "symbol", "open", "close", "adj_close", "volume", "dividend", "split",
         "ret", "ret_overnight", "ret_intraday"]
    ].rename(columns={"volume": "yahoo_volume"})

    vix = y[y.symbol == cfg["sample"]["vix"]][["date", "close"]].rename(columns={"close": "vix"})
    mkt = y[y.symbol == cfg["sample"]["market_proxy"]][["date", "ret"]].rename(columns={"ret": "mkt_ret"})
    market = vix.merge(mkt, on="date", how="outer")
    return stocks, market


def load_flags() -> pd.DataFrame:
    f = pd.read_csv(FLAGS, parse_dates=["date"], usecols=["date", "symbol"])
    f["earnings_afterclose"] = True
    return f


def build(cfg: dict) -> pd.DataFrame:
    v = load_volare(cfg)
    stocks, market = load_yahoo(cfg)
    p = v.merge(stocks, on=["date", "symbol"], how="left", validate="one_to_one")
    p = p.merge(market, on="date", how="left")
    p = p.merge(load_flags(), on=["date", "symbol"], how="left")
    p["earnings_afterclose"] = p["earnings_afterclose"].fillna(False).astype(bool)

    t = cfg["target"]
    base = p["bv5_ss"].where(p["earnings_afterclose"], p[t["intraday_measure"]]) \
        if t["earnings_days"] == "bv5" else p[t["intraday_measure"]]
    p["rv_target"] = base + (p["ret_overnight"] ** 2 if t["add_overnight"] else 0.0)
    p["log_rv_target"] = np.log(p["rv_target"])

    # market-wide realised variance: cross-sectional mean of log rv5_ss, back on the variance scale
    p["mkt_rv"] = np.exp(p.groupby("date")["rv5_ss"].transform(lambda s: np.log(s).mean()))

    p = p.sort_values(["symbol", "date"]).reset_index(drop=True)
    return p


def check(p: pd.DataFrame) -> None:
    n_sym, n_day = p.symbol.nunique(), p.date.nunique()
    print(f"panel: {len(p):,} rows, {n_sym} stocks, {n_day} days, {p.date.min().date()} -> {p.date.max().date()}")
    assert len(p) == n_sym * n_day, "panel is not balanced"
    miss = p[["ret", "ret_overnight", "rv5_ss", "rv_target", "vix", "mkt_ret"]].isna().sum()
    print("missing values:\n" + miss.to_string())
    # the first day per stock has no overnight return / return; everything else must be complete
    assert miss["ret"] <= n_sym and miss["ret_overnight"] <= n_sym, "unexpected missing returns"
    print("after-close earnings days flagged:", int(p.earnings_afterclose.sum()))
    print("share of target from overnight (median):",
          float(((p.ret_overnight ** 2) / p.rv_target).median()))


def main() -> None:
    cfg = load_config()
    p = build(cfg)
    check(p)
    p.to_parquet(PANEL, index=False)
    print("saved", PANEL)


if __name__ == "__main__":
    main()
