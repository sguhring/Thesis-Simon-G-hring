# %% [markdown]
# # AdaVol in M6: does the method in the paper reproduce what the team submitted?
#
# Team AdaGaussMC (id b1002bc9, 5th in forecasting) published no code for the M6 step, only its
# description in de Vilmarest & Werge (2025), section 4.1:
#
# 1. demean daily log returns with the average return of the asset's class over 2015-2020,
# 2. run AdaVol, and at the submission date freeze its variance: every one of the next 20 daily
#    returns is N(class mean, that variance),
# 3. assets are independent; VXX is drawn from its own past daily returns,
# 4. quintile probabilities are the Monte Carlo frequencies of each asset's rank.
#
# This file rebuilds those four steps and compares the result with the team's 12 real submissions.
# A first pass, not part of the pipeline: prices come from the copy in `external/jmgvilar_M6competition`
# (adjusted closes of all 100 assets since 2000), because the repository has no M6 price history yet.
#
# Run it as a script (`python notebooks/adavol_m6_check.py`) or cell by cell in VS Code.

# %%
from __future__ import annotations

import numpy as np
import pandas as pd

from thesis.evaluate.scores import m6_quintile_targets, rps
from thesis.models.adavol import adavol
from thesis.models.base import quintile_probs_from_samples
from thesis.paths import EXTERNAL, RAW_M6, load_config

TEAM = "b1002bc9"
LEADERBOARD_RPS = 0.15692      # sheet "Global" of ijf_summary_leaderboard.xlsx, team AdaGaussMC_STU
RANKS = ["Rank1", "Rank2", "Rank3", "Rank4", "Rank5"]
# the organisers' period ends (Baseline for evaluating the hypotheses.R); each period starts 28 days earlier
ENDS = pd.to_datetime(["2022-04-01", "2022-04-29", "2022-05-27", "2022-06-24", "2022-07-22", "2022-08-19",
                       "2022-09-16", "2022-10-14", "2022-11-11", "2022-12-09", "2023-01-06", "2023-02-03"])
STARTS = ENDS - pd.Timedelta(days=28)
LABELS = [f"{k} Submission" for k in ("1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th", "11th", "12th")]
N_SIMS, HORIZON = 100_000, 20
rng = np.random.default_rng(load_config()["seed"])

# %% [markdown]
# ## 1. Data: price history, asset classes, realised quintiles, the team's submissions

# %%
vilar = EXTERNAL / "jmgvilar_M6competition" / "data"
universe = pd.read_csv(vilar / "M6_Universe.csv").replace({"symbol": {"EG": "RE"}})   # Everest Re was RE in 2022
prices = pd.read_csv(vilar / "AdjClose.csv.gz", index_col=0, parse_dates=True, low_memory=False)
prices = prices.apply(pd.to_numeric, errors="coerce").rename(columns={"EG": "RE"})
symbols = sorted(universe["symbol"])
returns = np.log(prices[symbols]).diff()
u = universe.set_index("symbol").loc[symbols]
asset_class = u["GICS_sector/ETF_type"].where(u["class"] == "ETF", "Stock")   # Stock, Equities, Fixed Income, ...

official = pd.read_csv(RAW_M6 / "assets_m6.csv", parse_dates=["date"])
official = official.pivot(index="date", columns="symbol", values="price").sort_index().ffill()[symbols]
targets = [m6_quintile_targets((official.loc[s:e].iloc[-1] / official.loc[s:e].iloc[0] - 1).to_numpy())
           for s, e in zip(STARTS, ENDS)]

submissions = pd.read_csv(RAW_M6 / "ijf_submissions.csv")
team = submissions[submissions["Team"] == TEAM]
team_probs = [team[team["Evaluation"] == lab].set_index("Symbol").loc[symbols, RANKS].to_numpy() for lab in LABELS]


def score(probs: list[np.ndarray]) -> float:
    return float(np.mean([rps(p, t).mean() for p, t in zip(probs, targets)]))


team_rps = score(team_probs)
print(f"1. the team's RPS recomputed from its submissions: {team_rps:.5f}   leaderboard: {LEADERBOARD_RPS}")
assert abs(team_rps - LEADERBOARD_RPS) < 5e-6, "the scoring code no longer reproduces the leaderboard"

# %% [markdown]
# ## 2. Steps 1 and 2: class means and the frozen AdaVol variance at each submission date

# %%
class_mean = {c: float(returns.loc["2015":"2020", asset_class.index[asset_class == c]].stack().mean())
              for c in asset_class.unique()}
mean = np.array([class_mean[asset_class[s]] for s in symbols])

variance = np.empty((len(STARTS), len(symbols)))          # next-day variance known at each start date
for j, s in enumerate(symbols):
    r = returns.loc["2015":, s].dropna()
    fit = adavol((r - mean[j]).to_numpy())
    variance[:, j] = fit.sigma2[r.index.searchsorted(STARTS, side="right")]

vxx_past = returns.loc["2015":"2020", "VXX"].dropna().to_numpy()

# %% [markdown]
# ## 3. Steps 3 and 4, twice: independent assets as the paper says, and correlated assets
#
# The correlated version keeps everything else and only draws the 100 returns with the correlation
# matrix of the last 250 trading days before the submission.

# %%
def correlation_before(date: pd.Timestamp, days: int = 250) -> np.ndarray:
    c = returns.loc[:date].iloc[-days:].corr(min_periods=60).fillna(0.0).to_numpy().copy()
    np.fill_diagonal(c, 1.0)
    vals, vecs = np.linalg.eigh(c)                        # pairwise estimates: force positive definite
    c = (vecs * np.clip(vals, 1e-6, None)) @ vecs.T
    d = np.sqrt(np.diag(c))
    return c / np.outer(d, d)


def quintile_probs(var: np.ndarray, corr: np.ndarray | None) -> np.ndarray:
    z = rng.standard_normal((N_SIMS, len(symbols)))
    if corr is not None:
        z = z @ np.linalg.cholesky(corr).T
    sims = HORIZON * mean + np.sqrt(HORIZON * var) * z    # sum of 20 daily N(mean, var) draws
    sims[:, symbols.index("VXX")] = rng.choice(vxx_past, size=(N_SIMS, HORIZON)).sum(axis=1)
    return quintile_probs_from_samples(sims)


independent = [quintile_probs(variance[i], None) for i in range(len(STARTS))]
correlated = [quintile_probs(variance[i], correlation_before(STARTS[i])) for i in range(len(STARTS))]

# %% [markdown]
# ## 4. Comparison with the team

# %%
def against_team(probs: list[np.ndarray]) -> tuple[float, float]:
    mine, theirs = np.concatenate(probs).ravel(), np.concatenate(team_probs).ravel()
    return float(np.abs(mine - theirs).mean()), float(np.corrcoef(mine, theirs)[0, 1])


print("\n4. RPS over the 12 periods, and how close the probabilities are to the team's")
print(f"{'':38s}{'RPS':>9s}{'mean |dp|':>11s}{'corr':>7s}")
print(f"{'uniform 0.2 (M6 benchmark)':38s}{0.16:9.5f}")
print(f"{'team AdaGaussMC, as submitted':38s}{team_rps:9.5f}")
for name, probs in (("rebuild, independent assets (paper)", independent), ("rebuild, correlated assets", correlated)):
    print(f"{name:38s}{score(probs):9.5f}{against_team(probs)[0]:11.4f}{against_team(probs)[1]:7.2f}")

i = 1
print(f"\n   {LABELS[i]} (Rank1 = lowest return ... Rank5 = highest):   team | independent | correlated")
for s in ("IVV", "SHY", "TLT", "AMZN", "XOM", "VXX"):
    j = symbols.index(s)
    print(f"   {s:5s} {np.round(team_probs[i][j], 2)} | {np.round(independent[i][j], 2)} | {np.round(correlated[i][j], 2)}")
