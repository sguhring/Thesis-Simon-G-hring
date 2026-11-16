import numpy as np
import pandas as pd
import pytest

from thesis.evaluate.rolling import fit_windows, realised, run
from thesis.evaluate.run_scores import aggregate, interval_columns, row_scores
from thesis.models import MODELS


def test_fit_windows_are_first_trading_days_of_each_month(features, cfg):
    w = fit_windows(features["date"], cfg)
    origins = [a for a, _ in w]
    assert origins[0] == pd.Timestamp("2017-06-01")
    assert all(o.day <= 3 for o in origins)
    assert all(w[i][1] == w[i + 1][0] for i in range(len(w) - 1))
    assert w[-1][1] == features["date"].max() + pd.Timedelta(days=1)
    assert len({(o.year, o.month) for o in origins}) == len(origins)


def test_realised_is_the_forward_sum(features):
    t = realised(features, [1, 20])
    g = features[features["symbol"] == "AAA"].reset_index(drop=True)
    r1 = t[(t["symbol"] == "AAA") & (t["horizon"] == 1)].reset_index(drop=True)
    assert r1["ret_h"].iloc[10] == pytest.approx(g["ret"].iloc[11])
    assert r1["rv_h"].iloc[10] == pytest.approx(g["rv_target"].iloc[11])
    r20 = t[(t["symbol"] == "AAA") & (t["horizon"] == 20)].reset_index(drop=True)
    assert r20["ret_h"].iloc[10] == pytest.approx(g["ret"].iloc[11:31].sum())
    assert r20["rv_h"].iloc[-20:].isna().all() and r20["rv_h"].iloc[:-20].notna().all()


@pytest.fixture(scope="module")
def forecasts(features, cfg):
    return run(features, cfg, n_jobs=2, verbose=False)


def test_driver_covers_every_model_stock_day_and_horizon(forecasts, features, cfg):
    w = fit_windows(features["date"], cfg)
    n_days = int((features["date"].drop_duplicates() >= w[0][0]).sum())
    counts = forecasts.groupby(["model", "symbol", "horizon"]).size()
    expected = {"naive", "garch", "gjr", "har", "har_median", "har_pooled", "har_pooled_median",
                "adavol", "lgbm", "lgbm_median", "lgbm_ratio", "lgbm_ratio_median"}
    assert set(forecasts["model"]) == expected
    assert (counts == n_days).all()
    assert forecasts["fit_origin"].notna().all()


def test_no_leakage_from_data_after_the_forecast_origin(forecasts, features, cfg):
    """Rerunning on the data truncated at the end of the second window reproduces every forecast
    of the first two windows exactly, for every model."""
    w = fit_windows(features["date"], cfg)
    cut = w[1][1]
    short = features[features["date"] < cut]
    again = run(short, cfg, n_jobs=2, verbose=False)
    full = forecasts[forecasts["origin"] < cut].reset_index(drop=True)
    assert len(again) == len(full)
    qcols = [c for c in full.columns if c.startswith("q_")]
    for model in full["model"].unique():
        a = full[full["model"] == model].reset_index(drop=True)
        b = again[again["model"] == model].reset_index(drop=True)
        assert np.allclose(a["var"], b["var"]), model
        assert np.allclose(a[qcols], b[qcols]), model


def test_scores_pipeline_produces_finite_tables(forecasts, features, cfg):
    rows = row_scores(forecasts, realised(features, cfg["horizons"]), cfg)
    assert rows["qlike"].ge(0).all() and rows["mse"].ge(0).all()
    assert interval_columns(0.90) == ("q_0.05", "q_0.95") and interval_columns(0.99) == ("q_0.005", "q_0.995")
    by_stock, table = aggregate(rows, cfg)
    assert set(table["model"]) == set(forecasts["model"]) and set(table["horizon"]) == set(cfg["horizons"])
    for c in ("qlike", "cov90", "cov95", "cov99", "is95", "mz_beta", "qlike_rel_garch"):
        assert np.isfinite(table[c]).all(), c
    assert table["cov95"].between(0, 1).all()
    assert table.loc[table["model"] == "garch", "qlike_rel_garch"].eq(1.0).all()
    # on GARCH data with Gaussian shocks a GARCH-t one-day interval should cover close to its level
    g1 = table[(table["model"] == "garch") & (table["horizon"] == 1)].iloc[0]
    assert 0.85 < g1["cov95"] <= 1.0
