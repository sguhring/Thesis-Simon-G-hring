"""Pull adjusted daily prices for the 40 VOLARE stocks, ^VIX and IVV from Yahoo Finance.

Run: python -m thesis.data.pull_yahoo   (writes data/raw/yahoo_prices.csv)
"""
import pandas as pd, numpy as np, yfinance as yf, time

from thesis.paths import RAW_VOLARE, RAW_YAHOO, load_config

_cfg = load_config()
TICKERS = _cfg["sample"]["tickers"]
EXTRA = [_cfg["sample"]["vix"], _cfg["sample"]["market_proxy"]]
START, END = "2014-12-01", "2026-09-16"
OUT = RAW_YAHOO

frames = []
for t in TICKERS + EXTRA:
    for attempt in range(3):
        try:
            h = yf.Ticker(t).history(start=START, end=END, auto_adjust=False, actions=True)
            break
        except Exception as e:
            print("retry", t, e); time.sleep(3)
    if h is None or h.empty:
        print("EMPTY", t); continue
    h = h.reset_index()
    h["Date"] = pd.to_datetime(h["Date"]).dt.tz_localize(None).dt.normalize()
    h["symbol"] = t
    h = h.rename(columns={"Date":"date","Open":"open","High":"high","Low":"low","Close":"close",
                          "Adj Close":"adj_close","Volume":"volume","Dividends":"dividend","Stock Splits":"split"})
    keep = ["date","symbol","open","high","low","close","adj_close","volume","dividend","split"]
    h = h[[c for c in keep if c in h.columns]]
    frames.append(h)
    print(f"{t:6s} {h.date.min().date()} -> {h.date.max().date()}  {len(h)} rows  splits={int((h.get('split',0)>0).sum())}")

df = pd.concat(frames, ignore_index=True).sort_values(["symbol","date"])
df["ret"] = df.groupby("symbol")["adj_close"].transform(lambda s: np.log(s).diff())
df.to_csv(OUT, index=False)
print("\nsaved", OUT, df.shape)

# ---- cross-check unadjusted closes against VOLARE ----
vol = pd.read_csv(RAW_VOLARE, parse_dates=["date"], usecols=["date","symbol","close_price","open_price"])
m = vol.merge(df[df.symbol.isin(TICKERS)][["date","symbol","close","split"]], on=["date","symbol"], how="left")
print("\nVOLARE rows without a Yahoo match:", m.close.isna().sum())
m = m.dropna(subset=["close"])
m["rel_diff"] = (m.close - m.close_price).abs() / m.close_price
print("relative |Yahoo close - VOLARE close|: median %.5f, 99th pct %.5f, max %.4f" % (m.rel_diff.median(), m.rel_diff.quantile(.99), m.rel_diff.max()))
print("rows with diff > 1%:", (m.rel_diff > 0.01).sum())
print(m[m.rel_diff > 0.01].sort_values("rel_diff", ascending=False).head(10).to_string())
print("\nsplit events found:")
print(df[df.split > 0][["date","symbol","split"]].to_string(index=False))
# Yahoo dates not in VOLARE (stock trading days)
ydates = set(df[df.symbol=="AAPL"].date); vdates = set(vol[vol.symbol=="AAPL"].date)
print("\nYahoo AAPL days missing in VOLARE:", sorted(d.date() for d in ydates - vdates if d >= pd.Timestamp("2015-01-02") and d <= pd.Timestamp("2026-08-31")))
print("VOLARE AAPL days missing in Yahoo:", sorted(d.date() for d in vdates - ydates))
