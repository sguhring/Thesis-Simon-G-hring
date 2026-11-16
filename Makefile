# Pipeline, one target per artefact. `make all` rebuilds everything that is out of date.
PY = python
export PYTHONPATH := src

all: panel features forecasts scores figures

m6-data:
	$(PY) -m thesis.data.download_m6

forecasts: data/processed/forecasts.parquet
data/processed/forecasts.parquet: data/processed/features.parquet config.yaml src/thesis/models/*.py src/thesis/evaluate/rolling.py
	$(PY) -m thesis.evaluate.rolling

scores: data/processed/scores.parquet
data/processed/scores.parquet: data/processed/forecasts.parquet src/thesis/evaluate/run_scores.py src/thesis/evaluate/scores.py
	$(PY) -m thesis.evaluate.run_scores

panel: data/processed/panel.parquet
data/processed/panel.parquet: config.yaml src/thesis/data/build_panel.py data/raw/volare/realized_variance_stocks.csv data/raw/yahoo_prices.csv data/flags/volare_afterhours_flags.csv
	$(PY) -m thesis.data.build_panel

features: data/processed/features.parquet
data/processed/features.parquet: data/processed/panel.parquet src/thesis/features.py
	$(PY) -m thesis.features

figures: manuscript/figures/fig_ladder.pdf
manuscript/figures/fig_ladder.pdf: data/processed/scores.parquet src/thesis/evaluate/figures.py src/thesis/evaluate/style.py
	$(PY) -m thesis.evaluate.figures

test:
	$(PY) -m pytest -q

.PHONY: all m6-data panel features forecasts scores figures test
