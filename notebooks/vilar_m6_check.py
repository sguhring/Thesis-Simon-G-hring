# %% [markdown]
# # Vilar in M6: does the published notebook's rule reproduce what the team submitted?
#
# Team db21f28b (Vilar, 5th overall, 8th in forecasting) published a notebook that redraws the
# paper's figures on its own grid of dates. It does not output the competition submissions. This file
# takes the forecasting rule from that notebook (cell 9) and applies it at the 12 M6 submission dates:
#
# - every day, each asset gets the quintile (1-5) of its trailing 20-day return among the 100 assets;
# - "temporal": the asset's own share of days in each quintile, weighted 0.2 (last 100 days),
#   0.2 (last 200 days) and 0.6 (whole history);
# - "type": the average share over the last 1,000 days of all ETFs or of all stocks (VXX on its own,
#   DRE uniform);
# - "mixed": half of each.
#
# Run it as a script (`python notebooks/vilar_m6_check.py`) or cell by cell in VS Code.

# %%
from __future__ import annotations

import numpy as np
import pandas as pd

from thesis.evaluate.scores import m6_quintile_targets, rps
from thesis.paths import EXTERNAL, RAW_M6

TEAM = "db21f28b"
LEADERBOARD_RPS = 0.15729      # sheet "Global" of ijf_summary_leaderboard.xlsx, team "21"
RANKS = ["Rank1", "Rank2", "Rank3", "Rank4", "Rank5"]
ENDS = pd.to_datetime(["2022-04-01", "2022-04-29", "2022-05-27", "2022-06-24", "2022-07-22", "2022-08-19",
                       "2022-09-16", "2022-10-14", "2022-11-11", "2022-12-09", "2023-01-06", "2023-02-03"])
STARTS = ENDS - pd.Timedelta(days=28)
LABELS = [f"{k} Submission" for k in ("1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th", "11th", "12th")]
LAG = 20

# %% [markdown]
# ## 1. Data, realised quintiles and the team's submissions

# %%
vilar = EXTERNAL / "jmgvilar_M6competition" / "data"
universe = pd.read_csv(vilar / "M6_Universe.csv").replace({"symbol": {"EG": "RE"}})   # Everest Re was RE in 2022
prices = pd.read_csv(vilar / "AdjClose.csv.gz", index_col=0, parse_dates=True, low_memory=False)
prices = prices.apply(pd.to_numeric, errors="coerce").rename(columns={"EG": "RE"})
symbols = sorted(universe["symbol"])
kind = universe.set_index("symbol")["class"]
etfs = [s for s in symbols if kind[s] == "ETF" and s != "VXX"]
stocks = [s for s in symbols if kind[s] == "Stock" and s != "DRE"]

official = pd.read_csv(RAW_M6 / "assets_m6.csv", parse_dates=["date"])
official = official.pivot(index="date", columns="symbol", values="price").sort_index().ffill()[symbols]
targets = [m6_quintile_targets((official.loc[s:e].iloc[-1] / official.loc[s:e].iloc[0] - 1).to_numpy())
           for s, e in zip(STARTS, ENDS)]

submissions = pd.read_csv(RAW_M6 / "ijf_submissions.csv")
team = submissions[submissions["Team"] == TEAM]
team_probs = np.array([team[team["Evaluation"] == lab].set_index("Symbol").loc[symbols, RANKS].to_numpy() for lab in LABELS])


def score(probs) -> float:
    return float(np.mean([rps(p, t).mean() for p, t in zip(probs, targets)]))


team_rps = score(team_probs)
print(f"1. the team's RPS recomputed from its submissions: {team_rps:.5f}   leaderboard: {LEADERBOARD_RPS}")
assert abs(team_rps - LEADERBOARD_RPS) < 5e-6, "the scoring code no longer reproduces the leaderboard"

# %% [markdown]
# ## 2. The notebook's rule at each submission date (only data up to that date)

# %%
quintile = 1 + np.log(prices[symbols]).diff(LAG).dropna(how="all").apply(
    lambda day: pd.qcut(day, 5, duplicates="drop", labels=False), axis=1)


def shares(block: pd.DataFrame) -> pd.DataFrame:
    """(5, n_assets): share of days each asset spent in each quintile; uniform without data."""
    return pd.DataFrame({s: np.full(5, 0.2) if block[s].notna().sum() == 0
                         else np.array([(block[s].dropna() == k).mean() for k in range(1, 6)]) for s in block.columns})


rules = {"temporal": [], "type": [], "mixed": []}
for start in STARTS:
    q = quintile.loc[:start]
    temporal = (0.2 * shares(q.iloc[-5 * LAG:]) + 0.2 * shares(q.iloc[-10 * LAG:]) + 0.6 * shares(q.iloc[-400 * LAG:]))
    recent = shares(q.iloc[-50 * LAG:])
    by_type = pd.DataFrame({s: recent[etfs].mean(axis=1) if s in etfs else recent[stocks].mean(axis=1) if s in stocks
                            else recent["VXX"] if s == "VXX" else pd.Series(np.full(5, 0.2)) for s in symbols})
    rules["temporal"].append(temporal[symbols].to_numpy().T)
    rules["type"].append(by_type[symbols].to_numpy().T)
    rules["mixed"].append((0.5 * temporal + 0.5 * by_type)[symbols].to_numpy().T)

# %% [markdown]
# ## 3. Comparison with the team

# %%
print("\n3. RPS over the 12 periods, and how close the probabilities are to the team's")
print(f"{'':30s}{'RPS':>9s}{'mean |dp|':>11s}{'corr':>7s}{'corr, submissions 1-9':>23s}{'10-12':>7s}")
print(f"{'team db21f28b, as submitted':30s}{team_rps:9.5f}")
for name, probs in rules.items():
    p = np.array(probs)
    corr = lambda a, b: float(np.corrcoef(a.ravel(), b.ravel())[0, 1])
    print(f"{'notebook rule: ' + name:30s}{score(p):9.5f}{np.abs(p - team_probs).mean():11.4f}{corr(p, team_probs):7.3f}"
          f"{corr(p[:9], team_probs[:9]):23.3f}{corr(p[9:], team_probs[9:]):7.3f}")
