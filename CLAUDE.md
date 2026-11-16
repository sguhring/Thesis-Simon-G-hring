# Working notes for Claude Code sessions in this repo

Read this first, then `DECISIONS.md` (open items at the end of entry 6) and `README.md` (milestones).

## What this is

Master's dissertation, Católica Lisbon, 2025/26: "Which models get volatility right? Overconfidence in
machine-learning and GARCH forecasts of stock return variance." Supervisor: Nicolò Bertani.
Two settings: the M6 competition (100 assets, 2022-23, scored with the organisers' RPS against the
leaderboard) and VOLARE (40 US stocks, 2015-2026, realised variance observed, so under-estimation can
be tested directly).

## Where things live

- `config.yaml`: frozen design values. Never hard-code a value that belongs here.
- `DECISIONS.md`: one entry per design choice, with status and evidence. Any choice a reader could
  question goes here before it goes into code. Nicolò's feedback is logged here too.
- `src/thesis/`: the package. `models/base.py` is the forecast-table contract every model must
  return; `evaluate/scores.py` reads only that table. `features.py` builds the targets of decision 9.
- `notebooks/`: exploration and validation scripts only. Nothing the manuscript depends on lives here.
  `00_project_overview.ipynb` is the orientation notebook: it opens each artefact of the chain in turn
  and runs one model live, but rebuilds nothing. Keep it read-only, or it becomes a second source of
  truth that drifts from the package.
- `manuscript/index.qmd`: Quarto source, still a chapter skeleton. Figures and tables are generated
  by the pipeline into `manuscript/figures` and `manuscript/tables`.
- `notes/`: seminar prep, the Milestone 1 figures and scripts, the primer.
- `external/`: other teams' M6 code, git-ignored, own licences. Reimplement, do not copy.

## Environment

- Use the repo venv: `.venv\Scripts\python` (Python 3.14, installed with uv, has `-e .` and all of
  `requirements.txt` plus ipykernel). Do not use the system Python.
- `pytest` is configured in `pyproject.toml` (pythonpath `src`, testpaths `tests`). The suite takes
  about a minute. Run it before committing model or scoring changes.
- The Makefile assumes `python` on PATH and `PYTHONPATH=src`; from the venv, call the modules
  directly: `.venv\Scripts\python -m thesis.data.build_panel`, `-m thesis.features`.
- Raw data are present locally and git-ignored (VOLARE csv, Yahoo prices, M6 files). Processed
  parquet files are rebuilt by the pipeline. Downloads on this machine are slow; use long timeouts.
- Git: `origin` is github.com/sguhring/Thesis-Simon-G-hring. Commit only when asked. Files are LF;
  the CRLF warning on Windows is harmless.

## Conventions

- Plain words first, one formula second, and say why it matters for the thesis. The author is still
  building the volatility-econometrics background; visual breakdowns are welcome.
- Every model is a function `forecast(train_panel, origin, horizon, cfg)` returning the table in
  `models/base.py`. Hyperparameters are tuned only on data before the origin (decision 4).
- Accuracy losses on the variance scale (QLIKE, MSE), never on the log scale. Calibration scores on
  the h-day return (coverage, interval score, MSIS, PIT). Decision 9 has the exact definitions.
- A model that forecasts on the log scale records its retransformation in its `model` name.
- Nothing from claude.ai chats is visible here. Anything decided verbally is lost unless it is written
  into `DECISIONS.md` or the memory notes.

## Status (16 Nov 2026)

Done: clean panel and features, decisions 1 to 5 and 7 to 10, data chapter material, Milestone 1 deck,
AdaVol rebuilt and validated (`models/adavol.py`), Vilar and SebastianR checked as scripts, scoring
functions with tests. Benchmark models naive, GARCH, GJR, HAR (+ `har_median`), pooled HAR
(+ `har_pooled_median`, entry 12) and AdaVol as forecast-table models (`models/`, registry
`MODELS`), the rolling-origin driver
(`evaluate/rolling.py`: monthly refits, a forecast every trading day, `forecasts.parquet` +
`realised.parquet`) and the scores run (`evaluate/run_scores.py`, writes
`manuscript/tables/scores_volare.md`), all with tests (`tests/test_models.py`, `tests/test_rolling.py`,
including a no-leakage test). `notes/ffds_course_assessment.md` lists design consequences taken from
Bergmeir's forecasting course (tree saturation, loss field, pooled HAR, conformal row, CRPS).

LightGBM is in (`models/lightgbm_model.py`, entry 11): pooled, direct per horizon, level and ratio
targets, each with a `_median` row; one full run takes about 23 minutes. The VOLARE forecast table
holds twelve model rows (2.09 million forecasts) and `manuscript/tables/scores_volare.md` is the first
results table. The pooled HAR row splits the LightGBM-vs-HAR gap (entry 12): at h = 1 pooling is worth
nothing and the whole ML gain is the functional form; at h = 20 pooling helps a little (0.922 against
0.935 relative to GARCH, the best QLIKE in the table) while the nonlinearity costs 0.106, so the
LightGBM failure at 20 days is the trees overfitting, not the pooling. The cumulative-loss figure
sharpens that: LightGBM's whole 20-day deficit against GARCH is the six weeks of covid (-5.9 before
it, -39.8 by 31 Mar 2020, -18.2 by 2026), while against the pooled HAR it is behind before covid and
keeps losing ground after. `lgbm_ratio`, which entry 11 introduced to survive exactly such a crisis,
does twice as badly through it as the level variant -- that reasoning needs checking before it goes
in the manuscript.

Results figures and the model comparison are in (`evaluate/figures.py`, `evaluate/style.py`, entry
13): the ladder, QLIKE by regime and VIX tercile, coverage by level, Mincer-Zarnowitz slopes, the
calibration plot, the cumulative loss against a benchmark over time and the volatility path with
forecasts, written to `manuscript/figures` as PDF and PNG by `make figures`, plus
Diebold-Mariano with Newey-West on the cross-sectional mean loss per origin
(`manuscript/tables/dm_volare.md`). Every number in the manuscript is generated, none typed by hand.

Milestone 2 (due 9 Nov, overdue): forecast table and scores for all models in both settings, results
chapter draft. Still missing, in order:

1. M6-setting pipeline as a module: distribution to quintile probabilities, with correlation, reusing
   the common "distribution to ranks" step for every model. This is the largest piece left and the
   main schedule risk: the three validation scripts and the RPS/IR functions exist, but nothing joins
   them and no model writes `p_q1..p_q5` yet.
2. Results chapter draft in `manuscript/index.qmd`.
3. Smaller: MSIS and PIT in `run_scores.py` (both functions already sit in `evaluate/scores.py`);
   decision 5's regime windows leave 325 of the 2,177 test days unassigned, 294 of them the most
   recent fourteen months (entry 13) -- to settle with Nicolò before the results chapter.

Open with Nicolò (asked 15 Oct 2026, answers not yet logged): which AdaVol to report; whether the
correlated AdaVol variant may be shown; a fourth M6 method or that time on VOLARE; medrv5 as main
specification. Log the answers in `DECISIONS.md` entry 6 as soon as they are known.

Milestone 3 (7 Dec): regime and calibration analysis, discussion, final manuscript.
