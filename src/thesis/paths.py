"""Project paths and config loader. Import this instead of writing paths by hand."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = ROOT / "config.yaml"

DATA = ROOT / "data"
RAW = DATA / "raw"
RAW_VOLARE = RAW / "volare" / "realized_variance_stocks.csv"
RAW_YAHOO = RAW / "yahoo_prices.csv"
RAW_M6 = RAW / "m6"
FLAGS = DATA / "flags" / "volare_afterhours_flags.csv"
PROCESSED = DATA / "processed"
PANEL = PROCESSED / "panel.parquet"
FEATURES = PROCESSED / "features.parquet"
FORECASTS = PROCESSED / "forecasts.parquet"
REALISED = PROCESSED / "realised.parquet"
SCORES = PROCESSED / "scores.parquet"

EXTERNAL = ROOT / "external"   # other teams' M6 code, cloned for validation only (git-ignored)

OUTPUTS = ROOT / "outputs"
FIGURES = ROOT / "manuscript" / "figures"
TABLES = ROOT / "manuscript" / "tables"

for _d in (PROCESSED, RAW_M6, OUTPUTS, FIGURES, TABLES):
    _d.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    with open(CONFIG_FILE, encoding="utf-8") as fh:
        return yaml.safe_load(fh)
