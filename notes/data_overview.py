"""Data overview for Milestone 1: coverage, summary statistics and three exploration charts.

Writes notes/figures/overview_*.png and prints the numbers used on the overview slides.
Run:  python notes/data_overview.py
"""
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from thesis.paths import PANEL, RAW_M6, ROOT

FIG = ROOT / "notes" / "figures"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e1e0d9", "#fcfcfb"
plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 10, "figure.dpi": 110,
                     "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE})


def tidy(ax, title, subtitle=None):
    ax.set_title(title, loc="left", color=INK, fontsize=11.5, fontweight="bold", pad=26 if subtitle else 8)
    if subtitle:
        ax.annotate(subtitle, xy=(0, 1), xycoords="axes fraction", xytext=(0, 8), textcoords="offset points", color=MUTED, fontsize=9.5)
    ax.grid(color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, length=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#c3c2b7")


ann_vol = lambda v: 100 * np.sqrt(252 * v)
p = pd.read_parquet(PANEL).sort_values(["symbol", "date"]).reset_index(drop=True)
out = {}

# ---------- coverage ----------
m6 = pd.read_csv(RAW_M6 / "assets_m6.csv")
sub = pd.read_csv(RAW_M6 / "ijf_submissions.csv", usecols=["Team", "Submission", "IsActive"])
out.update(n_rows=len(p), n_stocks=p.symbol.nunique(), n_days=p.date.nunique(), start=str(p.date.min().date()), end=str(p.date.max().date()),
           m6_assets=int(m6.symbol.nunique()), m6_start=str(pd.to_datetime(m6.date).min().date()), m6_end=str(pd.to_datetime(m6.date).max().date()),
           m6_rows=len(m6), m6_teams=int(sub.Team.nunique()), m6_submission_rows=len(sub))
print("COVERAGE", json.dumps({k: out[k] for k in list(out)}, indent=0))

# ---------- summary statistics ----------
vol = ann_vol(p.rv_target)
q = vol.quantile([0.01, 0.1, 0.5, 0.9, 0.99])
by_stock = p.groupby("symbol").rv_target.median().pipe(ann_vol).sort_values()
out.update(vol_p01=float(q[0.01]), vol_p10=float(q[0.1]), vol_med=float(q[0.5]), vol_p90=float(q[0.9]), vol_p99=float(q[0.99]), vol_max=float(vol.max()),
           calm_stock=by_stock.index[0], calm_vol=float(by_stock.iloc[0]), wild_stock=by_stock.index[-1], wild_vol=float(by_stock.iloc[-1]),
           ret_med_abs=float(100 * p.ret.abs().median()), ret_max=float(100 * p.ret.min()), ret_max_sym=p.loc[p.ret.idxmin(), "symbol"],
           ret_max_date=str(p.loc[p.ret.idxmin(), "date"].date()), vix_med=float(p.vix.median()), vix_max=float(p.vix.max()),
           n_flag=int(p.earnings_afterclose.sum()), n_exdiv=int((p.dividend.fillna(0) > 0).sum()), n_splits=int((p.split.fillna(0) > 0).sum()))
print("\nSUMMARY  daily truth as yearly vol: p1 %.0f%%, p10 %.0f%%, median %.1f%%, p90 %.0f%%, p99 %.0f%%, max %.0f%%" % tuple(out[k] for k in ["vol_p01", "vol_p10", "vol_med", "vol_p90", "vol_p99", "vol_max"]))
print("  calmest stock %s %.0f%%, wildest %s %.0f%%; median |daily return| %.2f%%, largest %s %.0f%% on %s; VIX median %.0f, max %.0f"
      % (out["calm_stock"], out["calm_vol"], out["wild_stock"], out["wild_vol"], out["ret_med_abs"], out["ret_max_sym"], out["ret_max"], out["ret_max_date"], out["vix_med"], out["vix_max"]))

# ---------- insight 1: persistence (autocorrelation of log variance) ----------
lags = [1, 2, 5, 10, 22, 44, 66, 132, 252]
acf = pd.DataFrame({L: p.groupby("symbol").log_rv_target.apply(lambda s: s.autocorr(L)) for L in lags})
med_acf = acf.median()
ret_acf = pd.Series({L: p.groupby("symbol").ret.apply(lambda s: s.autocorr(L)).median() for L in lags})
out.update(acf1=float(med_acf[1]), acf22=float(med_acf[22]), acf66=float(med_acf[66]), acf252=float(med_acf[252]), ret_acf1=float(ret_acf[1]))
fig, ax = plt.subplots(figsize=(9, 4.2))
ax.plot(lags, med_acf.values, color=BLUE, lw=2, marker="o", ms=5, markeredgecolor=SURFACE, label="log variance (the target)")
ax.plot(lags, ret_acf.values, color=ORANGE, lw=2, marker="o", ms=5, markeredgecolor=SURFACE, label="daily return")
ax.axhline(0, color=INK, lw=1)
ax.set_xscale("log"); ax.set_xticks(lags); ax.set_xticklabels([str(L) for L in lags])
ax.set_xlabel("lag in trading days", color=MUTED); ax.set_ylabel("autocorrelation, median over 40 stocks", color=MUTED)
for L in (1, 22, 252):
    ax.annotate(f"{med_acf[L]:.2f}", (L, med_acf[L]), xytext=(0, 8), textcoords="offset points", ha="center", color=INK, fontsize=9)
tidy(ax, "Variance is persistent, returns are not", "Yesterday predicts today; a year ago still carries information. This is why GARCH and HAR work at all.")
ax.legend(loc="upper right", frameon=False, labelcolor=INK)
fig.savefig(FIG / "overview_persistence.png", dpi=160, bbox_inches="tight"); plt.close(fig)

# ---------- insight 2: commonality (one market factor in variance) ----------
wide = p.pivot(index="date", columns="symbol", values="log_rv_target")
z = (wide - wide.mean()) / wide.std()
eig = np.linalg.eigvalsh(np.cov(z.T.values))[::-1]
share1 = eig[0] / eig.sum()
corr_mkt = p.groupby("symbol").apply(lambda g: np.corrcoef(g.log_rv_target, np.log(g.mkt_rv))[0, 1]).median()
corr_vix = np.corrcoef(np.log(p.groupby("date").mkt_rv.first()), np.log(p.groupby("date").vix.first()))[0, 1]
out.update(pc1_share=float(share1), corr_mkt=float(corr_mkt), corr_vix=float(corr_vix))
mkt = p.groupby("date").mkt_rv.first().pipe(ann_vol).rolling(22).median()
fig, ax = plt.subplots(figsize=(9, 4.2))
ax.plot(mkt.index, mkt.values, color=BLUE, lw=1.6)
for label, d in [("Volmageddon", "2018-02-05"), ("Covid", "2020-03-16"), ("rate shock", "2022-06-13"), ("tariff shock", "2025-04-08")]:
    d = pd.Timestamp(d); y = mkt.loc[d:].iloc[0] if d in mkt.index or True else 0
    ax.annotate(label, (d, mkt.loc[:d].iloc[-1] if len(mkt.loc[:d]) else 0), xytext=(0, 10), textcoords="offset points", ha="center", color=INK, fontsize=9)
ax.set_ylabel("typical stock's variance, as yearly vol %", color=MUTED)
tidy(ax, "One market-wide level of risk, with four stress episodes", "Cross-sectional median of the 40 stocks' realised variance, 22-day rolling median, expressed as yearly volatility.")
fig.savefig(FIG / "overview_market.png", dpi=160, bbox_inches="tight"); plt.close(fig)

# ---------- insight 3: the cross-section (calm and wild stocks) ----------
fig, ax = plt.subplots(figsize=(8.5, 9.5))
y = np.arange(len(by_stock))
p10 = p.groupby("symbol").rv_target.quantile(0.10).pipe(ann_vol).reindex(by_stock.index)
p90 = p.groupby("symbol").rv_target.quantile(0.90).pipe(ann_vol).reindex(by_stock.index)
ax.hlines(y, p10, p90, color=GRID, lw=3)
ax.scatter(by_stock.values, y, s=42, color=BLUE, edgecolor=SURFACE, linewidth=1.2, zorder=3)
ax.set_yticks(y, by_stock.index); ax.set_ylim(-1, len(y))
ax.set_xlabel("daily truth as yearly volatility %: median dot, 10th to 90th percentile bar", color=MUTED)
tidy(ax, "Forty stocks, a three-fold range of normal risk", f"{by_stock.index[0]} is the calmest at {by_stock.iloc[0]:.0f}%, {by_stock.index[-1]} the wildest at {by_stock.iloc[-1]:.0f}%. Every stock's own range is wider than the gap between stocks.")
ax.grid(axis="y", visible=False)
fig.savefig(FIG / "overview_cross_section.png", dpi=160, bbox_inches="tight"); plt.close(fig)

print("\nINSIGHTS  autocorrelation of log variance: lag 1 %.2f, lag 22 %.2f, lag 66 %.2f, lag 252 %.2f; of returns at lag 1 %.2f" % (out["acf1"], out["acf22"], out["acf66"], out["acf252"], out["ret_acf1"]))
print("  first principal component of the 40 log-variance series explains %.0f%%; median correlation of a stock's log variance with the market level %.2f; market level vs VIX %.2f" % (100 * share1, corr_mkt, corr_vix))
json.dump(out, open(FIG / "data_overview_numbers.json", "w"), indent=1)
print("saved figures and", FIG / "data_overview_numbers.json")
