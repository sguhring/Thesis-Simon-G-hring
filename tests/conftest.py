"""Shared fixtures: a small synthetic feature table in the layout of data/processed/features.parquet."""
from __future__ import annotations

import copy

import numpy as np
import pandas as pd
import pytest

from thesis.features import har_lags
from thesis.paths import load_config


def simulate_garch(n: int, omega: float, alpha: float, beta: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Returns and their true conditional variances from a Gaussian GARCH(1,1)."""
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(n)
    x, s = np.empty(n), np.empty(n)
    s2 = omega / (1 - alpha - beta)
    for t in range(n):
        s[t] = s2
        x[t] = np.sqrt(s2) * z[t]
        s2 = omega + alpha * x[t] ** 2 + beta * s2
    return x, s


def synthetic_features(symbols=("AAA", "BBB"), n: int = 700, start: str = "2015-01-02", seed: int = 0,
                       horizons=(1, 20), lags=(1, 5, 22)) -> pd.DataFrame:
    """Two stocks of GARCH returns; the realised variance is the true variance times lognormal noise."""
    dates = pd.bdate_range(start, periods=n)
    frames = []
    for i, sym in enumerate(symbols):
        x, s = simulate_garch(n, 2e-6 * (i + 1), 0.08, 0.88, seed=seed + i)
        rng = np.random.default_rng(seed + 100 + i)
        rv = s * np.exp(0.3 * rng.standard_normal(n) - 0.045)
        g = pd.DataFrame({"symbol": sym, "date": dates, "ret": x, "rv_target": rv})
        log_rv = np.log(g["rv_target"]).rename("log_rv")
        g = pd.concat([g, har_lags(log_rv, list(lags))], axis=1)
        for h in horizons:
            fwd = g["rv_target"].shift(-1).rolling(h).mean().shift(-(h - 1))
            g[f"y_h{h}"] = np.log(fwd)
        frames.append(g)
    return pd.concat(frames, ignore_index=True)


@pytest.fixture(scope="session")
def features() -> pd.DataFrame:
    return synthetic_features()


@pytest.fixture(scope="session")
def cfg() -> dict:
    c = copy.deepcopy(load_config())
    c["evaluation"]["first_origin"] = "2017-06-01"     # four monthly windows inside 700 business days
    c["evaluation"]["n_sims"] = 300
    c["models"]["lightgbm"].update({"features": ["log_rv_m1", "log_rv_m5", "log_rv_m22", "log_rv_expanding"],
                                    "validation_days": 100, "n_estimators": 60, "min_child_samples": 20,
                                    "num_threads": 2})
    return c
