import numpy as np
import pandas as pd
import pytest

from thesis.evaluate.rolling import fit_windows
from thesis.models import MODELS
from thesis.models import adavol_forecast, garch, har, lightgbm_model, naive
from thesis.models.adavol import adavol
from thesis.models.base import qcol

QCOLS = ["q_0.005", "q_0.025", "q_0.05", "q_0.25", "q_0.5", "q_0.75", "q_0.95", "q_0.975", "q_0.995"]


def one(features, sym="AAA"):
    return features[features["symbol"] == sym].reset_index(drop=True)


def check_contract(fc: pd.DataFrame, windows, horizons, n_days: int):
    assert list(fc.columns[:6]) == ["symbol", "origin", "fit_origin", "horizon", "model", "var"]
    assert [qcol(float(c[2:])) for c in QCOLS] == QCOLS and all(c in fc.columns for c in QCOLS)
    assert (fc["var"] > 0).all() and np.isfinite(fc[QCOLS].to_numpy()).all()
    q = fc[QCOLS].to_numpy()
    assert (np.diff(q, axis=1) > 0).all(), "quantiles must increase with the level"
    for h in horizons:
        for model, g in fc[fc["horizon"] == h].groupby("model"):
            assert len(g) == n_days, (model, h, len(g))
            assert g["origin"].is_monotonic_increasing and g["origin"].is_unique
    for fit_origin, until in windows:
        g = fc[(fc["origin"] >= fit_origin) & (fc["origin"] < until)]
        assert (g["fit_origin"] == fit_origin).all()


def test_qcol_is_stable_against_float_noise():
    assert qcol(0.04999999999999999) == "q_0.05" and qcol(1 - 0.025) == "q_0.975" and qcol(0.5) == "q_0.5"


@pytest.mark.parametrize("name", list(MODELS))
def test_every_model_satisfies_the_contract(features, cfg, name):
    g = one(features)
    windows = fit_windows(g["date"], cfg)
    fc = MODELS[name](g, windows, cfg["horizons"], cfg)
    n_days = int((g["date"] >= windows[0][0]).sum())
    check_contract(fc, windows, cfg["horizons"], n_days)


def test_naive_is_the_window_mean_times_h(features, cfg):
    g = one(features)
    windows = fit_windows(g["date"], cfg)
    fc = naive.fit_predict(g, windows, cfg["horizons"], cfg)
    w = cfg["models"]["naive"]["window"]
    day = windows[1][0]
    k = int(g["date"].searchsorted(day))
    expected = g["rv_target"].iloc[k - w + 1:k + 1].mean()
    v1 = fc[(fc["horizon"] == 1) & (fc["origin"] == day)]["var"].item()
    v20 = fc[(fc["horizon"] == 20) & (fc["origin"] == day)]["var"].item()
    assert v1 == pytest.approx(expected) and v20 == pytest.approx(20 * expected)
    # normal quantiles: the median is zero and the 97.5% quantile is 1.96 sd
    row = fc[(fc["horizon"] == 1) & (fc["origin"] == day)].iloc[0]
    assert row["q_0.5"] == pytest.approx(0.0, abs=1e-12)
    assert row["q_0.975"] == pytest.approx(1.959964 * np.sqrt(v1), rel=1e-5)


def test_har_recovers_a_linear_log_variance_rule(features, cfg):
    g = one(features).copy()
    rng = np.random.default_rng(3)
    b = np.array([-0.5, 0.4, 0.3, 0.2])
    X = g[["log_rv_m1", "log_rv_m5", "log_rv_m22"]].to_numpy()
    for h in cfg["horizons"]:
        g[f"y_h{h}"] = b[0] + X @ b[1:] + 0.01 * rng.standard_normal(len(g))
    windows = fit_windows(g["date"], cfg)
    fc = har.fit_predict(g, windows, cfg["horizons"], cfg)
    m = (fc["model"] == "har_median") & (fc["horizon"] == 20)
    pred = np.log(fc[m]["var"].to_numpy() / 20)
    truth = (b[0] + X @ b[1:])[g["date"].searchsorted(fc[m]["origin"].to_numpy())]
    assert np.abs(pred - truth).max() < 0.02
    # the mean-corrected row is exp(s^2 / 2) above the median row, by a little here (s = 0.01)
    mean_row = fc[(fc["model"] == "har") & (fc["horizon"] == 20)]["var"].to_numpy()
    ratio = mean_row / fc[m]["var"].to_numpy()
    assert np.allclose(ratio, ratio[0]) and 1.0 < ratio[0] < 1.001


def test_har_fits_only_on_targets_observed_by_the_fit_origin(features, cfg):
    g = one(features).copy()
    windows = fit_windows(g["date"], cfg)
    fo = windows[1][0]
    k = int(g["date"].searchsorted(fo))
    base = har.fit_predict(g, windows[1:2], [20], cfg)
    # corrupting the 20-day targets of the rows whose window reaches past the fit origin must not
    # change the forecasts; corrupting an earlier row must
    later = g.copy()
    later.loc[k - 19:, "y_h20"] += 5.0
    assert np.allclose(har.fit_predict(later, windows[1:2], [20], cfg)["var"], base["var"])
    earlier = g.copy()
    earlier.loc[k - 20, "y_h20"] += 5.0
    assert not np.allclose(har.fit_predict(earlier, windows[1:2], [20], cfg)["var"], base["var"])


def test_garch_horizon_20_variance_is_the_sum_of_daily_forecasts(features, cfg):
    g = one(features)
    windows = fit_windows(g["date"], cfg)[:1]
    fc = garch.fit_predict(g, windows, [1, 20], cfg, spec="garch")
    v1 = fc[fc["horizon"] == 1].set_index("origin")["var"]
    v20 = fc[fc["horizon"] == 20].set_index("origin")["var"]
    ratio = v20 / v1
    assert ((ratio > 5) & (ratio < 40)).all()         # persistent model: close to 20 x the daily variance
    # the simulated 20-day quantiles have the right scale: the 95% half-width is a few sd of the sum
    row = fc[fc["horizon"] == 20].iloc[0]
    half = (row["q_0.975"] - row["q_0.025"]) / 2
    assert 1.5 * np.sqrt(row["var"]) < half < 3.0 * np.sqrt(row["var"])
    # the seed makes the simulation reproducible
    again = garch.fit_predict(g, windows, [1, 20], cfg, spec="garch")
    assert np.array_equal(fc[QCOLS].to_numpy(), again[QCOLS].to_numpy())


def test_gjr_has_the_asymmetry_term(features, cfg):
    g = one(features)
    windows = fit_windows(g["date"], cfg)[:1]
    a = garch.fit_predict(g, windows, [1], cfg, spec="garch")["var"].to_numpy()
    b = garch.fit_predict(g, windows, [1], cfg, spec="gjr")["var"].to_numpy()
    assert a.shape == b.shape and not np.allclose(a, b)


def test_adavol_rows_are_the_recursion_and_its_closed_form_sum(features, cfg):
    g = one(features)
    windows = fit_windows(g["date"], cfg)
    fc = adavol_forecast.fit_predict(g, windows, [1, 20], cfg)
    fit = adavol(g["ret"].to_numpy(), tuple(cfg["models"]["adavol"]["theta0"]), eta=cfg["models"]["adavol"]["eta"])
    k = int(g["date"].searchsorted(windows[0][0]))
    v1 = fc[fc["horizon"] == 1]["var"].to_numpy()
    assert np.allclose(v1, fit.sigma2[k + 1:k + 1 + len(v1)])
    # closed form against the explicit h-step recursion at the first origin
    a_b, g2, s = fit.theta[k].sum(), fit.gamma2[k], fit.sigma2[k + 1]
    total, step = 0.0, s
    for _ in range(20):
        total += step
        step = g2 + a_b * (step - g2)
    assert fc[fc["horizon"] == 20]["var"].iloc[0] == pytest.approx(total)


def test_lightgbm_pooled_rows_and_variants(features, cfg):
    windows = fit_windows(features["date"], cfg)[:2]
    fc = lightgbm_model.fit_predict(features, windows, [1, 20], cfg)
    assert set(fc["symbol"]) == {"AAA", "BBB"}
    assert set(fc["model"]) == {"lgbm", "lgbm_median", "lgbm_ratio", "lgbm_ratio_median"}
    n_days = int(((features["date"] >= windows[0][0]) & (features["date"] < windows[1][1])).sum())
    assert (fc.groupby(["model", "horizon"]).size() == n_days).all()
    diag = fc.attrs["diagnostics"]
    assert len(diag) == 2 * 2 * 2 and (diag["n_trees"] >= 1).all() and (diag["s2_val"] > 0).all()
    # the mean-corrected row is exp(s2/2) above the median row, by the validation residual variance
    first = (fc["horizon"] == 1) & (fc["fit_origin"] == windows[0][0])
    a = fc[first & (fc["model"] == "lgbm")]["var"].to_numpy()
    b = fc[first & (fc["model"] == "lgbm_median")]["var"].to_numpy()
    s2 = diag[(diag["variant"] == "level") & (diag["horizon"] == 1)]["s2_val"].iloc[0]
    assert np.allclose(a / b, np.exp(s2 / 2))
    # the ratio and level variants are different models
    r = fc[first & (fc["model"] == "lgbm_ratio_median")]["var"].to_numpy()
    assert r.shape == b.shape and not np.allclose(r, b)


def test_lightgbm_scale_feature_uses_only_the_past(features):
    f = lightgbm_model.add_scale_feature(features)
    g = f[f["symbol"] == "AAA"].reset_index(drop=True)
    assert g["log_rv_expanding"].iloc[30] == pytest.approx(g["log_rv_m1"].iloc[:31].mean())


def test_multi_step_sum_handles_unit_persistence():
    out = adavol_forecast.multi_step_sum(np.array([2.0, 2.0]), np.array([1.0, 1.0]), np.array([1.0, 0.5]), 3)
    assert out[0] == pytest.approx(6.0)                  # 3 days at the full gap: 1 + 1 each
    assert out[1] == pytest.approx(3 + 1 * (1 + 0.5 + 0.25))
