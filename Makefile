# Pipeline, one target per artefact. `make all` rebuilds everything that is out of date.
PY = python
export PYTHONPATH := src

all: panel features

m6-data:
	$(PY) -m thesis.data.download_m6

panel: data/processed/panel.parquet
data/processed/panel.parquet: config.yaml src/thesis/data/build_panel.py data/raw/volare/realized_variance_stocks.csv data/raw/yahoo_prices.csv data/flags/volare_afterhours_flags.csv
	$(PY) -m thesis.data.build_panel

features: data/processed/features.parquet
data/processed/features.parquet: data/processed/panel.parquet src/thesis/features.py
	$(PY) -m thesis.features

test:
	$(PY) -m pytest -q

.PHONY: all m6-data panel features test
