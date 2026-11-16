"""Model registry. Every entry is  fit_predict(stock, windows, horizons, cfg) -> forecast table.

stock     one stock's rows of data/processed/features.parquet, sorted by date (a pooled model, marked
          with the attribute `pooled = True`, receives the rows of all stocks instead)
windows   list of (fit_origin, until): parameters are estimated with the data up to and including
          fit_origin; forecasts are issued for every trading day in [fit_origin, until) with the data
          up to that day (decision 4)
horizons  config.horizons
cfg       config.yaml as a dict

The table's columns are documented in `thesis.models.base`.
"""
from __future__ import annotations

from functools import partial

from thesis.models import adavol_forecast, garch, har, lightgbm_model, naive

MODELS = {
    "naive": naive.fit_predict,
    "garch": partial(garch.fit_predict, spec="garch"),
    "gjr": partial(garch.fit_predict, spec="gjr"),
    "har": har.fit_predict,
    "adavol": adavol_forecast.fit_predict,
    "lgbm": lightgbm_model.fit_predict,       # pooled: receives all stocks at once (attribute `pooled`)
}


def is_pooled(name: str) -> bool:
    return bool(getattr(MODELS[name], "pooled", False))
