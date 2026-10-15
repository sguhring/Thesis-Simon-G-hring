"""Every number on the 'Defining the Truth' slides, computed from the panel, in slide order.

Run:  python notes/deck_numbers.py
Long-form version with charts and explanations: notebooks/data_preparation_tutorial.ipynb
"""
import numpy as np
import pandas as pd

from thesis.paths import PANEL

p = pd.read_parquet(PANEL).sort_values(["symbol", "date"]).reset_index(drop=True)
r2 = p.ret ** 2                    # squared close-to-close return, one reading of each day's variance
on2 = p.ret_overnight ** 2         # squared overnight return
flag = p.earnings_afterclose       # the 459 after-close earnings days
ann_vol = lambda v: 100 * np.sqrt(252 * v)      # daily variance -> yearly volatility in percent

print("SLIDE 3  why realised variance")
local = p.rv_target.groupby(p.symbol).transform(lambda s: s.rolling(22, center=True).median())   # the month's level of risk
ok = local.notna() & (r2 > 0)
print(f"  typical deviation from the local level: squared return x{np.exp(np.log(r2[ok]/local[ok]).std()):.0f}, realised variance x{np.exp(np.log(p.rv_target[ok]/local[ok]).std()):.0f}")
yesterday = np.log(p.rv_target).groupby(p.symbol).shift(1)                                       # a naive forecast
for name, y in [("squared return", np.log(r2.where(r2 > 0))), ("realised variance", np.log(p.rv_target))]:
    m = pd.concat([y, yesterday], axis=1).dropna()
    print(f"  R^2 of yesterday's variance explaining the {name}: {np.corrcoef(m.iloc[:, 0], m.iloc[:, 1])[0, 1] ** 2:.2f}")
print(f"  mean realised variance / mean squared return: {p.rv_target.mean() / r2.mean():.2f}")

print("\nSLIDE 4  worked example, Apple 2 Jan 2015")
rv = p.loc[(p.symbol == "AAPL") & (p.date == "2015-01-02"), "rv5_ss"].iloc[0]
print(f"  rv5_ss {rv:.6f} -> daily vol {100*np.sqrt(rv):.2f}% -> yearly vol {ann_vol(rv):.1f}%")

print("\nSLIDE 6  decision 2, the size test")
truth_b, truth_a = p.rv5_ss, p.rv5_ss + on2                       # (b) trading hours only, (a) with the night
print(f"  all stocks: (b) {r2.mean()/truth_b.mean():.2f}   (a) {r2.mean()/truth_a.mean():.2f}")
by = p.assign(r2=r2, a=truth_a, b=truth_b).groupby("symbol")[["r2", "a", "b"]].mean()
print(f"  by stock:   (b) {(by.r2/by.b).min():.2f} to {(by.r2/by.b).max():.2f}   (a) {(by.r2/by.a).min():.2f} to {(by.r2/by.a).max():.2f}")

print("\nSLIDE 8  what option (a) costs")
print(f"  night's share of the truth: typical day {(on2/truth_a).median():.0%}, whole sample {on2.sum()/truth_a.sum():.0%}")
print(f"  share of overnight variance in the largest 1% of nights: {on2.nlargest(len(p)//100).sum()/on2.sum():.0%}")
z2 = np.random.default_rng(0).standard_normal(len(p)) ** 2        # what a normal distribution would give
print(f"  same share if nights were normal: {np.sort(z2)[-len(p)//100:].sum()/z2.sum():.0%}")
exdiv = p.dividend.fillna(0) > 0
raw_on2 = (np.log(p.open) - np.log(p.groupby("symbol")["close"].shift(1))) ** 2              # overnight without the dividend fix
print(f"  ex-dividend nights {exdiv.sum():,}: raw {raw_on2[exdiv].median():.1e}, fixed {on2[exdiv].median():.1e}, ordinary night {on2[~exdiv].median():.1e}; total change {on2.sum()/raw_on2.sum()-1:+.1%}")

print("\nSLIDE 9  decision 3, the flag and Netflix")
later_splits = p.split.fillna(0).replace(0, 1.0).groupby(p.symbol).transform(lambda s: s[::-1].cumprod()[::-1].shift(-1).fillna(1.0))
official = p.close * later_splits                                 # Yahoo's close in as-traded units
move = np.log(p.volare_close) - np.log(official)                  # 16:00 -> 16:05
print(f"  flagged days {flag.sum()}, typical five-minute move {move[flag].abs().median():.1%}")
n = p[(p.symbol == "NFLX") & (p.date == "2022-04-19")].index[0]
print(f"  Netflix 19 Apr 2022: official {official[n]:.2f}, VOLARE {p.volare_close[n]:.2f}, move {move[n]:+.1%}, next overnight {p.ret_overnight[n+1]:+.1%}")
print(f"  as yearly vol: rv5_ss {ann_vol(p.rv5_ss[n]):.0f}%, bv5_ss {ann_vol(p.bv5_ss[n]):.0f}%, medrv5 {ann_vol(p.medrv5[n]):.0f}%")

print("\nSLIDE 10  counted twice")
nxt = p.ret_overnight.groupby(p.symbol).shift(-1)                 # the overnight move into the next day
x, y = move[flag], nxt[flag]
print(f"  same sign {(np.sign(x) == np.sign(y)).mean():.0%}, correlation {np.corrcoef(x[y.notna()], y[y.notna()])[0, 1]:.2f}")

print("\nSLIDE 11  which measure")
normal = p.groupby("symbol")["rv5_ss"].transform("median")        # the stock's normal level
for name, v in [("keep rv5_ss", p.rv5_ss), ("bv5_ss", p.bv5_ss), ("rv5_ss minus move^2", np.maximum(p.rv5_ss - move**2, p.medrv5)), ("medrv5", p.medrv5)]:
    print(f"  {name:22s} day 0: {(v/normal)[flag].median():.1f}x normal")
rel = p.rv5_ss / normal
print(f"  for comparison: day -1 {rel.groupby(p.symbol).shift(1)[flag].median():.1f}x, day +1 {rel.groupby(p.symbol).shift(-1)[flag].median():.1f}x")
print(f"  days where move^2 exceeds the whole day's rv5_ss: {int((move[flag]**2 > p.rv5_ss[flag]).sum())}")

print("\nSLIDE 12  the cost")
print(f"  medrv5 / rv5_ss on ordinary days: {(p.medrv5/p.rv5_ss)[~flag].median():.0%};  replaced rows {flag.sum()} of {len(p):,} = {flag.mean():.1%}")

print("\nSLIDE 13  the finished table")
print(f"  mean squared return / mean truth: {r2.mean()/p.rv_target.mean():.3f};  median stock-day {ann_vol(p.rv_target.median()):.1f}% yearly vol")
yr = p.rv_target.groupby(p.date.dt.year).median().pipe(ann_vol)
print(f"  2017 {yr[2017]:.0f}%, 2020 {yr[2020]:.0f}%, 2022 {yr[2022]:.0f}%")
