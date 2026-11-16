import numpy as np
import pandas as pd
import pytest

from thesis.evaluate.scores import (coverage, diebold_mariano, information_ratio, interval_score,
                                    m6_quintile_targets, m6_quintiles, newey_west_var, qlike, rps)


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


def test_newey_west_with_zero_lags_is_the_plain_variance():
    d = np.random.default_rng(1).normal(size=200)
    assert newey_west_var(d, 0) == pytest.approx(d.var())


def test_newey_west_inflates_the_variance_under_positive_autocorrelation():
    rng = np.random.default_rng(2)
    e = rng.normal(size=4000)
    d = e[1:] + e[:-1]                      # MA(1), positive first-order autocorrelation
    assert newey_west_var(d, 10) > 1.5 * newey_west_var(d, 0)


def test_diebold_mariano_sign_and_scale():
    rng = np.random.default_rng(3)
    better = rng.normal(1.0, 1.0, size=500)
    worse = rng.normal(1.3, 1.0, size=500)
    out = diebold_mariano(better, worse, maxlags=0)
    assert out["mean_diff"] < 0 and out["stat"] < -2 and out["p"] < 0.05 and out["n"] == 500
    # with zero lags the statistic is the one-sample t of the differences
    d = better - worse
    assert out["stat"] == pytest.approx(d.mean() / np.sqrt(d.var() / len(d)))
    # the reverse comparison flips the sign only
    rev = diebold_mariano(worse, better, maxlags=0)
    assert rev["stat"] == pytest.approx(-out["stat"]) and rev["p"] == pytest.approx(out["p"])


def test_diebold_mariano_of_a_model_against_itself_is_undefined_not_significant():
    loss = np.random.default_rng(4).normal(size=100)
    out = diebold_mariano(loss, loss, maxlags=5)
    assert out["mean_diff"] == 0.0 and np.isnan(out["stat"])


def test_diebold_mariano_hac_widens_the_interval_on_overlapping_losses():
    rng = np.random.default_rng(5)
    e = rng.normal(size=3000)
    a = e[1:] + e[:-1] + 0.05               # overlapping forecasts: autocorrelated differences
    b = np.zeros_like(a)
    naive_stat = abs(diebold_mariano(a, b, maxlags=0)["stat"])
    hac_stat = abs(diebold_mariano(a, b, maxlags=20)["stat"])
    assert hac_stat < naive_stat
