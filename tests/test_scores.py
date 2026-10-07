import numpy as np
import pandas as pd

from thesis.evaluate.scores import (coverage, information_ratio, interval_score, m6_quintile_targets,
                                    m6_quintiles, qlike, rps)


def test_rps_uniform_is_016_on_average():
    probs = np.full((5, 5), 0.2)
    outcomes = np.arange(1, 6)
    assert abs(rps(probs, outcomes).mean() - 0.16) < 1e-12


def test_rps_perfect_forecast_is_zero():
    probs = np.eye(5)
    assert rps(probs, np.arange(1, 6)).max() == 0.0


def test_quintiles_balanced_without_ties():
    r = np.random.default_rng(0).normal(size=100)
    q = m6_quintiles(r)
    assert sorted(pd.Series(q).value_counts().tolist()) == [20] * 5
    assert q[r.argmax()] == 5 and q[r.argmin()] == 1
    t = m6_quintile_targets(r)
    assert np.allclose(t.sum(axis=1), 1.0) and set(np.unique(t)) == {0.0, 1.0}


def test_quintile_targets_split_ties_like_official_code():
    # 10 assets: positions 1..10, blocks of 2. Assets 1 and 2 tie at the top of block 1 / bottom of block 2.
    r = np.array([0.0, 0.1, 0.1, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
    t = m6_quintile_targets(r)
    assert np.allclose(t[0], [1, 0, 0, 0, 0])
    assert np.allclose(t[1], [0.5, 0.5, 0, 0, 0]) and np.allclose(t[2], [0.5, 0.5, 0, 0, 0])
    assert np.allclose(t[-1], [0, 0, 0, 0, 1])
    # rps accepts the fractional matrix
    assert rps(np.full((10, 5), 0.2), t).shape == (10,)


def test_information_ratio_matches_official_definition():
    px = pd.DataFrame({"A": [100, 101, 99, 102], "B": [50, 50, 51, 51]})
    w = pd.Series({"A": 0.5, "B": 0.5})
    simple = px.pct_change().iloc[1:]
    ret = np.log1p(0.5 * simple["A"] + 0.5 * simple["B"])
    out = information_ratio(w, px)
    assert abs(out["ir"] - ret.sum() / ret.std(ddof=1)) < 1e-12


def test_qlike_zero_at_truth():
    rv = np.array([1e-4, 2e-4])
    assert np.allclose(qlike(rv, rv), 0.0)


def test_interval_score_penalises_misses():
    lo, hi, y = np.array([-1.0]), np.array([1.0]), np.array([2.0])
    assert interval_score(lo, hi, y, 0.95)[0] > 2.0
    assert coverage(lo, hi, y)[0] == 0.0
