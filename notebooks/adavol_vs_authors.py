# %% [markdown]
# # AdaVol: the rebuild from the paper against the authors' notebook
#
# `src/thesis/models/adavol.py` was written from the equations in Werge & Wintenberger (2022).
# This file checks it against the authors' own notebook, on the data the notebook uses (S&P 500
# since 1950) and on the 40 thesis stocks.
#
# Run it as a script (`python notebooks/adavol_vs_authors.py`) or cell by cell in VS Code.
# It needs the authors' repository: `git clone https://github.com/nicklaswerge/AdaVol external/nicklaswerge_AdaVol`

# %%
from __future__ import annotations

import json
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from arch import arch_model

from thesis.evaluate.scores import qlike
from thesis.models.adavol import adavol, project_garch
from thesis.paths import EXTERNAL, OUTPUTS, PANEL, RAW, load_config

AUTHORS_NOTEBOOK = EXTERNAL / "nicklaswerge_AdaVol" / "AdaVol - An Adaptive Recursive Volatility Prediction Method.ipynb"
SP500_FILE = RAW / "sp500_gspc.csv"
SAMPLE = ("1950-01-01", "2026-09-30")     # fixed end date so the numbers below do not move
THETA0 = (0.05, 0.90)                     # the notebook's starting values, WW eq. 4.8


# %% [markdown]
# ## 1. The authors' functions, loaded from their notebook
#
# Nothing is copied into this repository (their code is GPL-3.0). The four cells that define the
# projection and `adavol` are executed from the cloned file. The notebook was written for NumPy 1 and
# stops with an error on NumPy 2, so two things are adjusted while loading. Neither changes a number:
# run unmodified on NumPy 1.26, the notebook gives bit-identical output (checked on 12 Oct 2026).

# %%
def load_authors_functions() -> dict:
    cells = json.loads(AUTHORS_NOTEBOOK.read_text(encoding="utf-8"))["cells"]
    source = "\n\n".join("".join(c["source"]) for c in cells
                         if c["cell_type"] == "code" and "".join(c["source"]).lstrip().startswith(("def ", "# https")))
    # (a) NumPy 2 no longer stores a one-element array into a single array slot
    old = "sigma2_hat[0] = gamma2_hat*"
    assert source.count(old) == 1, "the authors' notebook has changed; re-check this loader"
    source = source.replace(old, "sigma2_hat[:1] = gamma2_hat*")
    # (b) np.alltrue was removed in NumPy 2
    if not hasattr(np, "alltrue"):
        np.alltrue = np.all
    namespace = {"np": np}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        exec(source, namespace)
    return namespace


authors = load_authors_functions()
authors_adavol, authors_project = authors["adavol"], authors["proj_l1ball"]


# %% [markdown]
# ## 2. The data of the authors' demo
#
# Daily log returns of the S&P 500 from Yahoo, zero returns removed, from 1950 on: the notebook's own
# recipe. The paper reports 17,672 observations up to September 2020.

# %%
def sp500_returns() -> pd.Series:
    if not SP500_FILE.exists():
        import yfinance as yf
        h = yf.Ticker("^GSPC").history(period="max", auto_adjust=True)
        if h.empty:
            raise RuntimeError("Yahoo returned no data for ^GSPC")
        h.index = pd.to_datetime(h.index).tz_localize(None).normalize()
        h["Close"].rename("close").rename_axis("date").to_csv(SP500_FILE)
    close = pd.read_csv(SP500_FILE, index_col="date", parse_dates=True)["close"]
    r = np.log(close).diff().dropna()
    return r[r != 0].loc[SAMPLE[0]:SAMPLE[1]]


sp = sp500_returns()
x = sp.to_numpy()
print(f"S&P 500: {len(x):,} returns, {sp.index[0].date()} to {sp.index[-1].date()}"
      f" ({(sp.index <= '2020-09-30').sum():,} up to Sep 2020; the paper has 17,672)")


# %% [markdown]
# ## 3. Same settings, same numbers?
#
# The notebook departs from the paper's Table 1 in three places (see the docstring of
# `thesis.models.adavol`). With all three switched to the notebook's behaviour, the rebuild has to
# reproduce the notebook's parameter paths.

# %%
PAPER = dict(first_obs_init=False, forecast_with="updated", project=project_garch)
NOTEBOOK = dict(first_obs_init=True, forecast_with="previous", project=authors_project)


def run(xs: np.ndarray, first_obs_init: bool, **kw) -> tuple[np.ndarray, np.ndarray]:
    """theta and sigma2, both aligned so that row k belongs to xs[k]."""
    if first_obs_init:                                   # the notebook spends xs[0] on initialisation
        f = adavol(xs[1:], THETA0, x0=xs[0], **kw)
        return np.vstack((THETA0, f.theta)), np.r_[np.nan, f.sigma2[:-1]]
    f = adavol(xs, THETA0, **kw)
    return f.theta, f.sigma2[:-1]


with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    theta_authors = authors_adavol(x, np.array(THETA0), p=1, q=1).T      # (n, 2), their own code
theta_same, sigma2_same = run(x, **NOTEBOOK)
gap = np.abs(theta_same - theta_authors).max()
print(f"\n3. rebuild with the notebook's settings vs the notebook itself: largest difference in alpha or beta"
      f" over {len(x):,} days = {gap:.1e}")
assert gap < 1e-10


# %% [markdown]
# ## 4. One departure at a time
#
# Each row moves one of the three settings from the notebook's version to the paper's. The loss is the
# average Gaussian quasi-likelihood loss of the one-day-ahead forecasts (lower is better), skipping
# the first 250 days. Every forecast is made before the day is seen. The last row is an ordinary
# GARCH(1,1) estimated once on the whole sample, so it has seen the future; it is there as a yardstick.

# %%
def ql_loss(sigma2: np.ndarray, xs: np.ndarray, skip: int = 250) -> float:
    return float(np.mean(xs[skip:] ** 2 / sigma2[skip:] + np.log(sigma2[skip:])) / 2)


def after(theta: np.ndarray, dates: pd.DatetimeIndex, day: str) -> np.ndarray:
    return theta[dates.searchsorted(pd.Timestamp(day), side="right") - 1]


variants = {
    "authors' notebook":                run(x, **NOTEBOOK),
    "  projection as in the paper":     run(x, **{**NOTEBOOK, "project": project_garch}),
    "  forecast with theta_t (paper)":  run(x, **{**NOTEBOOK, "forecast_with": "updated"}),
    "  initialisation as in Table 1":   run(x, **{**NOTEBOOK, "first_obs_init": False}),
    "paper, Table 1 (all three)":       run(x, **PAPER),
}
print("\n4. S&P 500, alpha and beta after 10 years, 40 years and at the end")
print(f"{'':34s}{'1959':>14s}{'1989':>14s}{sp.index[-1].year:>14d}{'QL loss':>10s}")
for name, (th, s2) in variants.items():
    cells = "".join("   %.3f %.3f" % tuple(after(th, sp.index, d)) for d in ("1959-12-31", "1989-12-31", SAMPLE[1]))
    print(f"{name:34s}{cells}{ql_loss(s2, x):10.4f}")

garch = arch_model(100 * x, mean="Zero", vol="GARCH", p=1, q=1).fit(disp="off")
garch_s2 = garch.conditional_volatility ** 2 / 1e4
print(f"{'GARCH(1,1), whole sample at once':34s}{'':28s}   %.3f %.3f{ql_loss(garch_s2, x):10.4f}"
      % (garch.params["alpha[1]"], garch.params["beta[1]"]))
s2_paper = variants["paper, Table 1 (all three)"][1]
print("correlation of log variance with that GARCH: notebook %.3f, paper %.3f" % (
    np.corrcoef(np.log(sigma2_same[250:]), np.log(garch_s2[250:]))[0, 1],
    np.corrcoef(np.log(s2_paper[250:]), np.log(garch_s2[250:]))[0, 1]))


# %% [markdown]
# ## 5. How long do the first days matter?
#
# AdaGrad's first steps are as large as the learning rate (0.1 per parameter), whatever the size of
# the gradient. So the first handful of returns decide where beta goes, and the step size then
# shrinks, which makes the way back slow. Dropping a few days at the start is enough to see it.

# %%
print("\n5a. paper settings, started m days later: beta at the end of 1959 / 1989 / the sample")
for m in (0, 1, 5, 21):
    th, _ = run(x[m:], **PAPER)
    print(f"   m = {m:2d}:  " + "  ".join("%.3f" % after(th, sp.index[m:], d)[1] for d in ("1959-12-31", "1989-12-31", SAMPLE[1])))

print("5b. a smaller learning rate: beta at the end of 1959 / the sample, and the loss")
for eta in (0.1, 0.03, 0.01):
    for like, kw in (("notebook", NOTEBOOK), ("paper", PAPER)):
        th, s2 = run(x, eta=eta, **kw)
        print(f"   eta = {eta:<4}  {like:8s}  {after(th, sp.index, '1959-12-31')[1]:.3f}  {th[-1, 1]:.3f}  {ql_loss(s2, x):.4f}")


# %% [markdown]
# ## 6. The picture: the notebook's result and the rebuild from Table 1

# %%
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e1e0d9", "#fcfcfb"
BLUE, ORANGE = "#2a78d6", "#eb6834"       # validated pair (colour-blind safe, 3:1 on the surface)
plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 10})

th_paper = variants["paper, Table 1 (all three)"][0]
fig, axes = plt.subplots(2, 1, figsize=(10, 6.4), sharex=True, facecolor=SURFACE)
for ax, col, name in zip(axes, (0, 1), ("alpha", "beta")):
    ax.set_facecolor(SURFACE)
    ax.plot(sp.index, theta_authors[:, col], color=BLUE, lw=1.6, label="authors' notebook (the rebuild with its settings is identical)")
    ax.plot(sp.index, th_paper[:, col], color=ORANGE, lw=1.6, label="rebuild from the paper's Table 1")
    for series, dy in ((theta_authors, 1), (th_paper, -1)):
        ax.annotate(f"{series[-1, col]:.2f}", (sp.index[-1], series[-1, col]), xytext=(6, 5 * dy * (1 if col == 1 else -1)),
                    textcoords="offset points", color=INK, fontsize=9, va="center")
    ax.set_title(f"{name}: " + ("reaction to yesterday's squared return" if col == 0 else "weight on yesterday's variance"),
                 loc="left", color=INK, fontsize=10.5, fontweight="bold")
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, length=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#c3c2b7")
    ax.set_ylim(0, 0.5 if col == 0 else 1.0)
    ax.margins(x=0.01)
axes[0].legend(loc="upper right", frameon=False, labelcolor=INK, fontsize=9)
fig.suptitle("AdaVol on the S&P 500: the paper's algorithm and the authors' notebook take decades to agree",
             x=0.065, ha="left", color=INK, fontsize=12.5, fontweight="bold")
fig.text(0.065, 0.925, "Parameter estimates after each day, 1950 to 2026. Same data and starting values; nearly all of the gap comes from how the first observation is used.",
         color=MUTED, fontsize=9.5)
fig.subplots_adjust(top=0.86, hspace=0.28, left=0.065, right=0.95, bottom=0.07)
OUTPUTS.mkdir(exist_ok=True)
fig.savefig(OUTPUTS / "adavol_vs_authors.png", dpi=160, facecolor=SURFACE)
print("\n6. figure saved to outputs/adavol_vs_authors.png")


# %% [markdown]
# ## 7. Does the choice matter on the thesis data?
#
# The 40 stocks have 2,932 days each, so every forecast sits in the stretch where the start still
# matters. The target is the realised variance of the panel (`rv_target`), forecasts are one day
# ahead, scored from the first forecast origin in `config.yaml` onwards.

# %%
cfg = load_config()
panel = pd.read_parquet(PANEL, columns=["symbol", "date", "ret", "rv_target"]).dropna(subset=["ret"])
first_origin = pd.Timestamp(cfg["evaluation"]["first_origin"])
settings = {"notebook settings": NOTEBOOK, "paper settings": PAPER, "paper settings, eta = 0.03": {**PAPER, "eta": 0.03}}
rows, gaps = [], []
for sym, g in panel.groupby("symbol"):
    g = g[g["ret"].ne(0).cummax()]                      # the recursion cannot start on a zero return
    xs, rv, test = g["ret"].to_numpy(), g["rv_target"].to_numpy(), (g["date"] >= first_origin).to_numpy()
    fc = {name: run(xs, **kw) for name, kw in settings.items()}
    fit = arch_model(100 * xs, mean="Zero", vol="GARCH", p=1, q=1).fit(disp="off")
    fc["GARCH(1,1), whole sample at once"] = (np.tile([fit.params["alpha[1]"], fit.params["beta[1]"]], (len(xs), 1)),
                                              fit.conditional_volatility ** 2 / 1e4)
    for name, (th, s2) in fc.items():
        rows.append({"model": name, "symbol": sym, "qlike": qlike(s2[test], rv[test]).mean(),
                     "realised / forecast": rv[test].mean() / s2[test].mean(),
                     "alpha": th[-1, 0], "beta": th[-1, 1]})
    gaps.append(np.abs(np.log(fc["paper settings"][1][test] / fc["notebook settings"][1][test])).mean())
res = pd.DataFrame(rows)
table = res.groupby("model", sort=False).agg(qlike=("qlike", "mean"), ratio=("realised / forecast", "mean"),
                                             alpha=("alpha", "median"), beta=("beta", "median"),
                                             beta_min=("beta", "min"), beta_max=("beta", "max"))
print(f"\n7. 40 stocks, one-day-ahead forecasts from {first_origin.date()}: mean QLIKE, mean realised/forecast variance,"
      "\n   median final alpha and beta, range of final beta across stocks")
print(table.round(3).to_string())
wins = res.pivot(index="symbol", columns="model", values="qlike")
print("stocks where the paper settings have the lower QLIKE than the notebook settings: %d of %d" % (
    (wins["paper settings"] < wins["notebook settings"]).sum(), len(wins)))
print("typical gap between the two variance forecasts (mean |log ratio|, average over stocks): %.3f" % np.mean(gaps))
