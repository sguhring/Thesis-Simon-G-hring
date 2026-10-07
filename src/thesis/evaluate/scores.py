"""All scoring functions in one place. Each takes forecasts and realisations as arrays and returns
per-observation losses (so Diebold-Mariano and regime splits can be computed downstream).

Accuracy:     qlike, mse                      (variance forecast vs realised variance)
Calibration:  coverage, interval_score, msis  (quantile forecasts vs realised return)
              pinball                         (single quantile)
              mincer_zarnowitz                (slope < 1 means under-estimation)
M6:           rps, m6_quintiles, information_ratio
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


# ---------- accuracy of the variance forecast ----------

def qlike(var_fc: np.ndarray, rv: np.ndarray) -> np.ndarray:
    r = rv / var_fc
    return r - np.log(r) - 1.0


def mse(var_fc: np.ndarray, rv: np.ndarray) -> np.ndarray:
    return (var_fc - rv) ** 2


def mincer_zarnowitz(var_fc: np.ndarray, rv: np.ndarray, log: bool = True) -> dict:
    """Regress realised on forecast. Slope below 1 (with intercept above 0) is the signature of
    forecasts that are too small when volatility is high."""
    y, x = (np.log(rv), np.log(var_fc)) if log else (rv, var_fc)
    res = sm.OLS(y, sm.add_constant(x)).fit(cov_type="HAC", cov_kwds={"maxlags": 20})
    a, b = res.params
    # joint test of alpha = 0 and beta = 1 (unbiased, efficient forecast)
    wald = res.wald_test((np.eye(2), np.array([0.0, 1.0])), scalar=True)
    return {"alpha": float(a), "beta": float(b), "se_alpha": float(res.bse[0]),
            "se_beta": float(res.bse[1]), "r2": float(res.rsquared),
            "wald_p": float(wald.pvalue)}


# ---------- calibration of the return distribution ----------

def coverage(lower: np.ndarray, upper: np.ndarray, y: np.ndarray) -> np.ndarray:
    return ((y >= lower) & (y <= upper)).astype(float)


def interval_score(lower: np.ndarray, upper: np.ndarray, y: np.ndarray, level: float) -> np.ndarray:
    """Gneiting-Raftery interval score for a central (level) interval; alpha = 1 - level.
    M4's MSIS is this divided by an in-sample scale; see msis()."""
    alpha = 1.0 - level
    width = upper - lower
    below = (2.0 / alpha) * (lower - y) * (y < lower)
    above = (2.0 / alpha) * (y - upper) * (y > upper)
    return width + below + above


def msis(lower, upper, y, level: float, scale: float) -> np.ndarray:
    """Mean scaled interval score (M4). scale = in-sample mean absolute (seasonal) naive error of the
    series; for returns use the mean absolute return of the training window."""
    return interval_score(lower, upper, y, level) / scale


def pinball(q_fc: np.ndarray, y: np.ndarray, tau: float) -> np.ndarray:
    d = y - q_fc
    return np.maximum(tau * d, (tau - 1) * d)


# ---------- M6 scores (Makridakis et al. 2025, organisers' definitions) ----------

def m6_quintile_targets(period_returns: np.ndarray) -> np.ndarray:
    """Outcome matrix (n_assets, 5) exactly as the organisers' RPS code builds it.

    Assets are ranked by percentage return over the period with rank(method='min'). Rank positions
    1..n are cut into five equal blocks (quintile 1 = lowest returns). Tied assets share the block
    membership of the positions they occupy, so a tie straddling two quintiles gets a fractional
    outcome (e.g. 0.5 / 0.5) rather than a one-hot vector.
    """
    r = pd.Series(np.asarray(period_returns, dtype=float))
    n = len(r)
    pos = r.rank(method="min").astype(int).to_numpy()
    edges = [int(0.2 * k * n) for k in range(6)]           # 0, n/5, 2n/5, ..., n

    def block(position: int) -> int:
        for k in range(5):
            if edges[k] < position <= edges[k + 1]:
                return k
        return 4

    out = np.zeros((n, 5))
    for start in np.unique(pos):
        members = np.where(pos == start)[0]
        occupied = range(start, start + len(members))      # positions the tie group fills
        share = np.zeros(5)
        for p in occupied:
            share[block(p)] += 1.0 / len(members)
        out[members] = share
    return out


def m6_quintiles(period_returns: np.ndarray) -> np.ndarray:
    """Integer quintile 1..5 per asset (argmax of the target matrix); ties resolved to the block
    with the largest share. Use m6_quintile_targets for scoring."""
    return m6_quintile_targets(period_returns).argmax(axis=1) + 1


def rps(probs: np.ndarray, outcome) -> np.ndarray:
    """probs: (n_assets, 5).  outcome: (n_assets,) integer quintiles in 1..5, or an (n_assets, 5)
    target matrix from m6_quintile_targets.
    RPS_i = (1/5) * sum_k ( cumsum(p)_k - cumsum(o)_k )^2.  Uniform 0.2 gives 0.16 on average."""
    probs = np.asarray(probs, dtype=float)
    outcome = np.asarray(outcome)
    if outcome.ndim == 1:
        o = np.zeros_like(probs)
        o[np.arange(len(outcome)), outcome.astype(int) - 1] = 1.0
    else:
        o = outcome.astype(float)
    return ((probs.cumsum(axis=1) - o.cumsum(axis=1)) ** 2).mean(axis=1)


def information_ratio(weights: pd.Series, daily_prices: pd.DataFrame) -> dict:
    """M6 investment score, as in the organisers' IR_calculation.

    weights: index = symbol, sum |w| <= 1.  daily_prices: columns = symbols, rows = trading days of
    the evaluation period including the last day before it.
    Daily portfolio return  R_t = sum_i w_i * (S_{i,t} / S_{i,t-1} - 1);  ret_t = ln(1 + R_t);
    IR = sum(ret) / sd(ret)  (sample standard deviation)."""
    px = daily_prices[weights.index]
    simple = px.pct_change().iloc[1:]
    port = np.log1p(simple.mul(weights.values, axis=1).sum(axis=1))
    sdp = port.std(ddof=1)
    return {"ret_sum": float(port.sum()), "sdp": float(sdp),
            "ir": float(port.sum() / sdp) if sdp > 0 else np.nan}
