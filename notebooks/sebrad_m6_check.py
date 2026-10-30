# %% [markdown]
# # SebastianR in M6: does the published recipe reproduce what the team submitted?
#
# Team 7cb34dbb (SebastianR, 3rd in forecasting) published the final version of its code, used for
# submissions 8 to 12 (`external/sebrad_M6/generate_rank_probabilities.r`). Its four steps:
#
# 1. a stack of linear models on weekly data predicts each asset's mean return,
# 2. the covariance matrix is the sample covariance of daily log returns over the last three years,
#    recomputed on a bootstrap sample of the days for every simulation,
# 3. daily returns are drawn from a multivariate t with 4 degrees of freedom and that matrix as scale
#    (unscaled, so the simulated variance is twice the sample variance), and summed over the period,
# 4. quintile probabilities are the shares of simulations in which an asset ranks 1-20, 21-40, ...
#
# This file rebuilds steps 2 to 4 at the 12 M6 dates with the mean set to zero. Step 1 needs weekly
# data for several hundred extra tickers and is not rebuilt, so the comparison is also made with the
# direction removed from both sides ("folded": Rank1 averaged with Rank5, Rank2 with Rank4).
#
# Run it as a script (`python notebooks/sebrad_m6_check.py`, about three minutes) or cell by cell.

# %%
from __future__ import annotations

import numpy as np
import pandas as pd

from thesis.evaluate.scores import m6_quintile_targets, rps
from thesis.paths import EXTERNAL, RAW_M6, load_config

TEAM = "7cb34dbb"
LEADERBOARD_RPS = 0.15649      # sheet "Global" of ijf_summary_leaderboard.xlsx, team SebastianR
RANKS = ["Rank1", "Rank2", "Rank3", "Rank4", "Rank5"]
ENDS = pd.to_datetime(["2022-04-01", "2022-04-29", "2022-05-27", "2022-06-24", "2022-07-22", "2022-08-19",
                       "2022-09-16", "2022-10-14", "2022-11-11", "2022-12-09", "2023-01-06", "2023-02-03"])
STARTS = ENDS - pd.Timedelta(days=28)
LABELS = [f"{k} Submission" for k in ("1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th", "11th", "12th")]
YEARS, DF = 3, 4               # var_train_years and the t degrees of freedom in the published code
N_SIMS = 2_500                 # the published code uses 10,000; 2,500 keeps the run short
rng = np.random.default_rng(load_config()["seed"])

# %% [markdown]
# ## 1. Data, realised quintiles and the team's submissions

# %%
vilar = EXTERNAL / "jmgvilar_M6competition" / "data"
universe = pd.read_csv(vilar / "M6_Universe.csv").replace({"symbol": {"EG": "RE"}})   # Everest Re was RE in 2022
prices = pd.read_csv(vilar / "AdjClose.csv.gz", index_col=0, parse_dates=True, low_memory=False)
prices = prices.apply(pd.to_numeric, errors="coerce").rename(columns={"EG": "RE"})
symbols = sorted(universe["symbol"])
# log close differences on each asset's own trading days; the code drops moves of 40 percent or more
returns = pd.DataFrame({s: np.log(prices[s].dropna()).diff() for s in symbols}).reindex(prices.index)
returns = returns.where(returns.abs() < 0.4)

official = pd.read_csv(RAW_M6 / "assets_m6.csv", parse_dates=["date"])
official = official.pivot(index="date", columns="symbol", values="price").sort_index().ffill()[symbols]
targets = [m6_quintile_targets((official.loc[s:e].iloc[-1] / official.loc[s:e].iloc[0] - 1).to_numpy())
           for s, e in zip(STARTS, ENDS)]

submissions = pd.read_csv(RAW_M6 / "ijf_submissions.csv")
team = submissions[submissions["Team"] == TEAM]
team_probs = np.array([team[team["Evaluation"] == lab].set_index("Symbol").loc[symbols, RANKS].to_numpy() for lab in LABELS])


def score(probs, periods: slice = slice(None)) -> float:
    return float(np.mean([rps(p, t).mean() for p, t in zip(probs[periods], targets[periods])]))


team_rps = score(team_probs)
print(f"1. the team's RPS recomputed from its submissions: {team_rps:.5f}   leaderboard: {LEADERBOARD_RPS}")
assert abs(team_rps - LEADERBOARD_RPS) < 5e-6, "the scoring code no longer reproduces the leaderboard"

# %% [markdown]
# ## 2. Steps 2 to 4 of the published code, at each submission date

# %%
def rank_probabilities(i: int) -> np.ndarray:
    monday = STARTS[i] + pd.Timedelta(days=3)                        # first day of the evaluation period
    window = returns.loc[(returns.index > monday - pd.Timedelta(days=round(YEARS * 365))) & (returns.index < monday)]
    window = window.dropna(how="all")
    # an asset that has stopped trading (DRE after its takeover) is left out and gets 0.2, as in the code
    alive = [s for s in symbols if window[s].iloc[-10:].abs().sum() > 0 and window[s].notna().sum() > 60]
    x = window[alive].to_numpy()
    seen = np.isfinite(x).astype(float)
    x = np.nan_to_num(x)
    days = len(official.loc[STARTS[i]:ENDS[i]]) - 1                  # trading days in the period
    totals = np.empty((N_SIMS, len(alive)))
    for b in range(N_SIMS):
        count = np.bincount(rng.integers(0, len(x), len(x)), minlength=len(x)).astype(float)   # bootstrap the days
        xc, n, sx = x * count[:, None], (seen * count[:, None]).T @ seen, (x * count[:, None]).T @ seen
        cov = (xc.T @ x - sx * sx.T / np.maximum(n, 1)) / np.maximum(n - 1, 1)                # pairwise complete
        vals, vecs = np.linalg.eigh(cov)
        z = rng.standard_normal((days, len(alive))) @ (vecs * np.sqrt(np.clip(vals, 1e-12, None))).T
        z /= np.sqrt(rng.chisquare(DF, size=days) / DF)[:, None]     # multivariate t: one mixing draw per day
        totals[b] = z.sum(axis=0)
    quintile = np.minimum(totals.argsort(axis=1).argsort(axis=1) // 20, 4)   # ranks 1-20 -> Rank1, as in the code
    probs = np.full((len(symbols), 5), 0.2)                          # an asset without data stays uniform
    for a, s in enumerate(alive):
        probs[symbols.index(s)] = [(quintile[:, a] == k).mean() for k in range(5)]
    return probs


rebuild = np.array([rank_probabilities(i) for i in range(len(STARTS))])

# %% [markdown]
# ## 3. Comparison with the team

# %%
def fold(p: np.ndarray) -> np.ndarray:
    """Remove the direction: average Rank1 with Rank5 and Rank2 with Rank4."""
    return np.stack([(p[..., 0] + p[..., 4]) / 2, (p[..., 1] + p[..., 3]) / 2, p[..., 2]], axis=-1)


def corr(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.corrcoef(a.ravel(), b.ravel())[0, 1])


print("\n3. the rebuild (no mean model) against the team's submissions")
print(f"{'submissions':14s}{'RPS team':>10s}{'RPS rebuild':>13s}{'mean |dp|':>11s}{'corr':>7s}{'corr, folded':>14s}")
for name, sl in (("1 to 7", slice(0, 7)), ("8 to 12", slice(7, 12)), ("all 12", slice(0, 12))):
    print(f"{name:14s}{score(team_probs, sl):10.5f}{score(rebuild, sl):13.5f}{np.abs(rebuild[sl] - team_probs[sl]).mean():11.4f}"
          f"{corr(rebuild[sl], team_probs[sl]):7.2f}{corr(fold(rebuild[sl]), fold(team_probs[sl])):14.2f}")
tilt = np.abs(team_probs[..., 4] - team_probs[..., 0]).mean(axis=1)
print("how much direction the team's forecasts carry, mean |Rank5 - Rank1|: submissions 1-7 %.3f, 8-12 %.3f"
      % (tilt[:7].mean(), tilt[7:].mean()))
