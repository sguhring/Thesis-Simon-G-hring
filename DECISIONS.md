# Decisions log

One entry per design choice that a reader of the manuscript could question. Status is
`open`, `decided` or `revisit`. The data chapter quotes this file.

## 1. Research question and structure (decided, 7 Oct 2026)

**Question** (fixed with Nicolò, 16 Sep 2026): Which models get volatility right? Overconfidence in
machine-learning and GARCH forecasts of stock return variance.

**Structure**: M6 first, then transfer.

1. M6 finding: forecasters were overconfident (Makridakis et al. 2025, Hypothesis 7), but the models
   behind the submissions could not be identified.
2. Model representation: reimplement 2-4 documented top-M6 methods plus the classic benchmarks
   (naive, GARCH, GJR) and HAR on realised variance.
3. M6 replication: score the reimplementations with the organisers' RPS/IR code against the 163-team
   leaderboard; redraw the overconfidence (calibration) curve with the identified models added.
4. Transfer: same models on VOLARE, 40 stocks, 2015-2026, where intraday realised variance is observed,
   so under-estimation can be tested directly (Mincer-Zarnowitz, coverage, MSIS, QLIKE) and by regime.
5. Results and discussion.

**Why**: the professor's framing is calibration, not accuracy. M6 gives an external yardstick and a
documented overconfidence result; VOLARE gives the realised variance that M6 lacks.

## 2. Target variance (decided, 12 Oct 2026)

VOLARE `rv5_ss` is open-to-close (09:30 to 16:05). Returns are close-to-close. Options:

- (a) target = rv5_ss + overnight^2, where overnight = log(open_t / close_{t-1}) from Yahoo.
- (b) target = rv5_ss only, and models forecast open-to-close variance.

**Decision: (a).** Evidence in `notebooks/decisions_2_3.ipynb`, checks 1 and 2.

- Size: mean squared daily return divided by the mean target is 0.99 under (a) and 1.63 under (b);
  by stock, (b) is between 1.20 and 1.98 for every one of the 40. Under (b) a model that is exactly
  right about close-to-close variance would appear to over-forecast by about 60 percent, so the test
  of "too little variance" would measure the missing hours, not the model.
- Cost: the overnight term is one squared return per day, so (a) is noisier. It is about 12 percent
  of the target on a typical day, 1 percent of days carry roughly half of all overnight variance, and
  the log target's standard deviation rises from (b) to (a). Scores that are robust to single large
  days (QLIKE, interval scores) are used; plain squared error is reported only as a robustness column.
- Dividends: the overnight return is measured from the ex-dividend previous close (close minus
  dividend). Without this, the 1,465 ex-dividend nights (1.2 percent of rows) show a median squared
  overnight move 2.5 times a normal night (3.8e-5 against 1.6e-5); with it they match normal nights.
  Total overnight variance changes by 0.3 percent. `config.yaml`: `dividend_adjust_overnight: true`.

## 3. After-close earnings days (decided, 12 Oct 2026)

459 stock-days where the VOLARE close (16:05) differs from the official close (16:00) by more than
1 percent; the flag is exactly that rule and all cases are after-close earnings releases (the ten
largest: NFLX, AMZN, CRM reporting days, e.g. NFLX 19 Apr 2022, 16:00 to 16:05 move -20 percent).
The jump lands in the last five minutes of the VOLARE window and therefore in that day's `rv5_ss`.

**Decision: replace `rv5_ss` by `medrv5` on the flagged days.** Evidence in
`notebooks/decisions_2_3.ipynb`, checks 3 to 6, and the comparison below.

- Attribution: the 16:00 to 16:05 move belongs to the next day's close-to-close return, and under
  decision 2(a) it already enters the target through the next overnight term (the five-minute move
  and the next overnight move have the same sign on nearly all flagged days and are strongly
  correlated). Keeping it in day 0 counts the same news twice.
- Which replacement: day-0 level as a multiple of the stock's normal `rv5_ss`, median over the 459
  days. `rv5_ss` 6.0; `bv5_ss` 3.2 (so bipower variation does not remove the jump, contrary to the
  earlier note); `rv5_ss` minus the squared five-minute move 2.2, and on 79 days that squared move
  exceeds the whole day's `rv5_ss` because subsampling smears the jump, so the subtraction is
  ill-defined; `medrv5` 1.6, next to the 1.5 of the two trading days before the announcement.
- Cost: on ordinary days `medrv5` is 93 percent of `rv5_ss`, so the replaced days run about 7 percent
  low. It touches 459 of 117,280 rows (0.4 percent) and the target's overall size is unchanged
  (squared return over target 1.006 against 0.990 before).
- Day +1 stays as it is in all variants: it is the market's reaction during trading hours.
- The earnings flag is kept as a feature (`earnings_afterclose`) and as a dummy for the regime and
  robustness tables. `config.yaml`: `earnings_days: medrv5`; `keep` and `bv5` remain available for
  the robustness column.

## 4. Forecast origins and horizons (decided)

Monthly origins from 2 Jan 2018 to Aug 2026 (about 104), re-estimation at every origin on an expanding
window, hyperparameters tuned only on data before the origin. Horizons 1 and 20 days. 20 days
matches the M6 window so the same RPS and interval scores apply in both settings.

## 5. Regimes (decided, revisit after exploration)

Calendar regimes listed in `config.yaml` plus VIX terciles over test days. Calendar windows are fixed
before any model is run so they cannot be tuned to results.

## 6. Which M6 methods to reimplement (open)

Candidates with a published description in the IJF M6 special issue (vol. 41, issue 4, 2025):

1. de Vilmarest & Werge, adaptive volatility (AdaVol) for probabilistic forecasting. Team AdaGaussMC,
   5th forecasting, 7th overall. pp. 1514-1520; free preprint arXiv 2303.01855; code
   https://github.com/nicklaswerge/AdaVol. Method: GARCH-type variance recursion with parameters
   updated online by projected AdaGrad (QML loss); returns independent Gaussian with class-specific
   mean; quintile probabilities by Monte Carlo; weights by SGD on expected IR. Daily prices only.
   -> Directly a variance model, so it sits next to GARCH(1,1) in every table. First pick.
2. Vilar, quasi-average predictions and regression to the trend. 5th overall. pp. 1505-1513
   (ScienceDirect S0169207024001341). Method: shrink predictions toward asset-class and temporal
   averages; low-variability forecasts. -> The "do not be overconfident" strategy made explicit; a
   natural foil to the ML models. Second pick.
3. Staněk, hypernetworks and adversarial portfolios. 1st duathlon, 4th forecasting. arXiv 2407.20352.
   Meta-learning: a hypernetwork generates the parameters of a base time-series model, validated on
   M4. -> Heavy to reimplement, no variance model at its core. Optional third, drop first.
4. Catlin, AutoTS, won the investment challenge, pp. 1485-1493. -> AutoML library wrapper; little
   to represent as a model. Not used.
- Supporting: Makridakis, Spiliotis & Michailidis, Avoiding overconfidence (pp. 1395-1403,
  S016920702400102X): symmetric quintile probabilities as a shrinkage benchmark.

The official repo has evaluation code and all submissions, but no team code. Pick methods whose
forecasting step produces a return distribution per asset (so variance and quantiles can be read off),
not only quintile probabilities.

**Team code found (7 Oct 2026), cloned to `external/` (git-ignored, own licences):**

| Repo | Team / rank | Licence | What is there |
|---|---|---|---|
| nicklaswerge/AdaVol | de Vilmarest & Werge, 5th forecasting | GPL-3.0 | One notebook: the online QML GARCH(p,q) recursion (`adavol`) with projected-gradient updates, demo on S&P 500. The M6 pipeline (Gaussian MC, RPS optimisation, portfolio) is NOT included; rebuild from the paper. |
| jmgvilar/M6competition | Vilar, team db21f28b, 5th overall | MIT | Full reproducibility notebook + data; produces the paper's Figures 1-5 (quintile histograms, RPS by strategy, returns, IR). Method fully runnable. |
| sebrad/M6 | SebastianR, 3rd forecasting track | none | R: linear models for the weekly conditional mean, bootstrap covariance from daily data, multivariate t(4) Monte Carlo, rank counting. The cleanest "distribution -> quintile probabilities" pipeline; no licence, so reimplement, do not copy. |
| stanek-fi/M6 | Staněk, 1st duathlon | none | Full R/torch code, unrefactored. Readme states the quintile predictions "predominantly model volatility" and carry little directional information: cite this. |
| aleksei-mashlakov/m6_competition | 16th forecasting | MIT | LightGBM multiclass on 20-day rank with isotonic recalibration. Candidate ML representative with code. |

Validation plan: (1) run Vilar's notebook and check its RPS series against team db21f28b in
`ijf_summary_leaderboard.xlsx`; (2) run `adavol` on one M6 asset and compare the fitted path with
arch's GARCH(1,1); (3) use sebrad's bootstrap-covariance + t Monte Carlo as the common
"distribution -> ranks" step for every model in the M6 setting.

**AdaVol rebuilt from the papers and checked (12 Oct 2026).** Code: `src/thesis/models/adavol.py`.
Checks: `notebooks/adavol_vs_authors.py`, `notebooks/adavol_m6_check.py`.

- With the notebook's three implementation choices switched on, the rebuild reproduces the authors'
  parameter paths on the S&P 500 (19,183 days, 1950-2026) to 4e-15.
- The notebook departs from Table 1 of the paper in three places: the initialisation, which estimate
  feeds the variance forecast (theta_{t-1} instead of theta_t), and the projection (off by one in the
  threshold, so it lands inside the constraint set). Only the initialisation matters: beta after ten
  years is 0.69 with the notebook's and 0.30 with Table 1's; at the end of the sample 0.82 and 0.79.
- Cause: with the published learning rate 0.1 the first steps move each parameter by 0.1, so the path
  depends on the first few returns for thousands of days. Starting 1, 5 or 21 days later moves beta at
  the end of 1959 from 0.30 to 0.54, 0.79, 0.43. A learning rate of 0.03 removes most of this.
- 40 stocks, one day ahead, from 2018: mean QLIKE 0.475 (notebook version), 0.473 (Table 1), 0.451
  (Table 1 with learning rate 0.03); GARCH(1,1) fitted once on the whole sample 0.425. The two versions'
  variance forecasts differ by 2 percent on average, so the choice between them is immaterial here.
- M6: the scoring code reproduces the leaderboard RPS of team b1002bc9 (AdaGaussMC) exactly, 0.15692.
  The forecasting step as the paper describes it (independent assets) gives 0.1582 and probabilities
  that correlate 0.32 with the team's submissions. With a 250-day correlation matrix: 0.1561 and 0.76.
  The submissions were not produced with independent assets and cannot be reproduced exactly from the
  paper. For the RPS the dependence assumption matters about forty times more than the AdaVol version.

**Vilar checked against the team's submissions (12 Oct 2026).** Check: `notebooks/vilar_m6_check.py`.
The notebook redraws the paper's figures on its own date grid and does not output the submissions, so
its forecasting rule (cell 9) was applied at the 12 M6 submission dates. The "mixed" rule (half the
asset's own quintile frequencies, half its class's) correlates 0.975 with what team db21f28b submitted,
0.995 for submissions 10-12, and scores 0.15705 against the team's 0.15729 (reproduced exactly from
the submissions). Submissions 1-9 fit a slightly lower weight on the asset's own history (about 0.4),
so the rule was still being adjusted early in the competition. The method yields quintile
probabilities only, no variance, so it enters the M6 chapter and not the VOLARE tests.

**SebastianR checked against the team's submissions (12 Oct 2026).** Check: `notebooks/sebrad_m6_check.py`.
The published code is the final version, used for submissions 8-12. Its covariance, sampling and rank
steps were rebuilt with the mean set to zero (the mean model, a stack of linear models on weekly data
for several hundred extra tickers, was not): three-year sample covariance of daily log returns,
bootstrapped; multivariate t(4) with that matrix unscaled, so the simulated variance is twice the
sample variance; rank counting. Correlation with what team 7cb34dbb submitted: 0.99 for submissions
8-12 and 0.97 for 1-7 (the first submission is the outlier, 0.88); with the direction folded out 1.00
and 0.98. RPS of the rebuild 0.1562 to 0.1564 depending on the simulation run, against the team's
0.15649 (reproduced exactly). The team's forecasts carry little direction (mean |Rank5 - Rank1| 0.02),
so a zero-mean model with a historical covariance reaches the top of the forecasting leaderboard.
A common scale factor cannot change ranks, so the doubling of the variance is invisible in M6 and only
testable on VOLARE.

Further public code in the forecasting top 10 (not cloned): danielweitzenfeld/m6_public, 1st place,
Bayesian dynamic factor model in PyMC with a Student-t scale per asset driven by last week's
volatility and an earnings dummy; no licence. miguel-data-sc/FinQBoost, 2nd place, boosting straight to
quintile probabilities, no variance.

Open: which AdaVol the thesis reports (Table 1 as published; learning rate tuned on pre-origin data as
a robustness row). The common "distribution -> ranks" step must carry correlation.

## 7. Bloomberg (decided)

Not a dependency. All models run on VOLARE + Yahoo. Implied volatility, if it arrives, becomes one
extra feature block and one robustness table.

## 8. What gets cut first if time runs short (decided)

1. Neural network with distributional output. 2. Fourth M6 method. 3. VIX-tercile split (keep calendar
regimes). The M6 replication chapter is now core and is not cut.

## 9. Target variable, by horizon and setting (decided, 12 Oct 2026)

The daily truth is fixed by decisions 2 and 3: `rv_target_t = intraday_t + o_t^2`, with `intraday_t` =
`rv5_ss` (or `medrv5` on the 459 after-close earnings days) and `o_t` the dividend-adjusted overnight
return. Everything below derives from it. Built by `src/thesis/features.py`.

**VOLARE setting (40 stocks, 2015-2026).**

- `y_h1  = log( rv_target_{t+1} )`: the log of tomorrow's variance.
- `y_h20 = log( mean of rv_target over t+1 .. t+20 )`: the log of the *average daily* variance over the
  next 20 trading days, as in the HAR literature (Corsi 2009; Christensen et al. 2023). Not the sum.
- The variance of the 20-day cumulative return, which the interval and coverage scores need, is the
  sum of the daily variances, i.e. 20 times the average (daily returns are treated as uncorrelated;
  the cross term was measured at +0.1 percent of the stick). So a model forecasts the average and the
  scoring code multiplies by h before building return intervals.
- Models work on the log scale because the variance spans four orders of magnitude. A model that
  forecasts the log must state how it returns to the variance scale: the plain exponential gives the
  conditional median of the variance, which is below its mean, and the gap grows with forecast
  uncertainty. Each model records its retransformation (none, or the residual-variance correction
  exp(mu + s^2/2)) in the forecast table's `model` name, because this is one of the candidate causes of
  machine-learning overconfidence (hypothesis on the training objective).

**M6 setting (100 assets, 2022-2023).** No intraday data, so the truth for the 20-day window is the sum
of squared daily log returns over the window (close-to-close, from the organisers' price file). This
is a noisier proxy than VOLARE's, which is why the M6 chapter carries the external yardstick (RPS,
calibration curve) and the VOLARE chapter carries the variance inference.

**Scoring.** Accuracy losses (QLIKE, MSE) compare the variance forecast with the realised variance on
the variance scale, never on the log scale (Patton 2011). Calibration scores (coverage, interval
score, PIT) compare return quantiles derived from the variance forecast with the realised h-day return.

## 10. Benchmark model specifications and the forecast schedule (decided provisionally, 16 Nov 2026)

Set when the benchmark models and the rolling-origin driver were written (`src/thesis/models/`,
`src/thesis/evaluate/rolling.py`). Each point is a choice Nicolò may want to change; none is costly to
change because every model writes the same table and the driver reruns in minutes.

**Forecast schedule (the reading of decision 4).** Parameters are re-estimated at the first trading
day of every month from January 2018 (104 fit origins, expanding window). Between two fit origins the
parameters are held fixed and a forecast is issued on every trading day with the data up to that day.
So the test set has about 2,170 one-day forecasts per stock and model, not 104, and the regime
windows hold enough days to be read (the covid window has about 95, not 5). The 20-day forecasts of
consecutive days overlap, so their errors are correlated and every test on them uses HAC standard
errors (Mincer-Zarnowitz; Diebold-Mariano when added). The table records both dates: `origin` (the
day the forecast is made) and `fit_origin`. Rationale: Hewamalage, Ackermann & Bergmeir (2023) and
the course notes in `notes/ffds_course_assessment.md`; it is how a forecaster would run these models.

**`var` is the variance of the h-day cumulative return**, the sum of the h daily variance forecasts,
as the contract in `models/base.py` says. The realised counterpart is the sum of `rv_target` over the
h days (`realised.parquet`). This is h times the average of decision 9, so QLIKE, which is invariant
to a common scale, is unchanged by the choice; it matters only for the return intervals, which need
the cumulative variance.

**Naive**: the mean of `rv_target` over the last 22 trading days, times h.

**GARCH(1,1) and GJR-GARCH(1,1,1)**: `arch`, constant mean, Student-t innovations with the degrees
of freedom estimated, maximum likelihood on returns in percent. One-day quantiles are analytic. The
20-day variance is the analytic sum of the daily forecasts; the 20-day return quantiles come from
2,000 simulated paths of the fitted model (`config.evaluation.n_sims`, seeded), because the sum of
twenty t shocks with changing variance has no closed form. Analytic variance and simulated quantiles
differ by Monte Carlo error only.

**HAR** (Corsi 2009): OLS of `y_h` on the 1-, 5- and 22-day averages of log `rv_target`, one
regression per stock and horizon, on the rows whose target is fully observed at the fit origin
(t + h <= fit origin). Two rows are written from the same fit: `har` = h exp(mu + s^2/2), the
conditional mean under normal residuals, and `har_median` = h exp(mu), so the retransformation gap of
decision 9 is visible in every table.

**AdaVol**: WW Table 1 as published (theta0 = (0.05, 0.90), eta = 0.1), one online pass per stock, no
re-estimation. The h-day variance is the closed-form sum of the GARCH recursion with theta frozen at
the origin. Which AdaVol the thesis reports is still the open point of entry 6; the config holds the
choice.

**Return shape for variance-only models** (naive, HAR, AdaVol): normal, `config.models.<m>.dist`. This
is the authors' choice for AdaVol (de Vilmarest & Werge 2025) and the simplest for the others; it
means the calibration comparison against the GARCH-t rows mixes two effects, the variance forecast and
the tail shape. To separate them a later run sets every model to the same shape (all normal, or all t
with a common df) as a robustness table. Open.

**Aggregation of scores**: per stock and horizon, the mean over forecast days; then the mean across
the 40 stocks (`run_scores.py`). The pooled regression (Mincer-Zarnowitz) uses all rows with HAC
standard errors. QLIKE is also reported relative to GARCH(1,1), the Hansen & Lunde (2005) yardstick.

## 11. The machine-learning representative: LightGBM (decided provisionally, 16 Nov 2026)

`src/thesis/models/lightgbm_model.py`, config `models.lightgbm`. Gradient-boosted trees are the
method that won M5 and the standard ML choice for tabular forecasting (Bergmeir's course, part 2.06);
Christensen et al. (2023) and Zhang et al. (2024) use them for realised variance.

- **Pooled across the 40 stocks** (a global model, Montero-Manso & Hyndman 2020): one model per
  horizon on all stock-days, with the stock's expanding mean of log rv as a feature so the model
  knows each stock's scale. GARCH and HAR are per stock; the pooled HAR row (entry 12) separates the
  pooling gain from the nonlinearity gain.
- **Direct forecasting**: one model for h = 1 and one for h = 20, target `y_h` of decision 9.
- **Two targets, both reported.** `lgbm`: the log level. `lgbm_ratio`: the log ratio to the last 22
  days, prediction added back. A tree's leaves average training targets, so a level model trained
  before a crisis cannot forecast variance above what it has seen (tree saturation); the ratio target
  is stationary and removes that ceiling. The gap between the two rows in the crisis regimes measures
  the mechanism.
- **Number of trees** by early stopping on the last 250 trading days before each fit origin, with an
  h-day gap so no validation target overlaps a training row; the model is then refitted on all
  training rows with that number of trees. The other hyperparameters are frozen in the config
  (learning rate 0.03, 15 leaves, min 100 rows per leaf, 80 percent feature and row subsampling, L2
  1.0), not tuned, so that the ML row is not favoured by a search the classical rows did not get.
  Nothing after the fit origin is used (tested with the no-leakage test of the driver).
- **Retransformation** as for HAR: `*_median` = h exp(mu); the unsuffixed row = h exp(mu + s^2/2) with
  s^2 the validation residual variance (out of sample, unlike HAR's in-sample s^2, because boosted
  trees fit their training rows too closely).
- **Features** (all through day t): log rv averages over 1, 5, 22 days; signed semivariances and the
  quarticity (day t); market realised variance averages; log VIX; yesterday's return and its negative
  part; jump share; weekday; the after-close earnings flag; the expanding mean of log rv.
- **Return shape**: normal, as the other variance-only models (entry 10, open).
- Re-estimated at every monthly fit origin like the other models; one pooled fit takes seconds.

## 12. Pooled HAR, the bridge row between HAR and LightGBM (decided, 16 Nov 2026)

`src/thesis/models/har_pooled.py`, config `models.har_pooled`. The HAR regression of entry 10, fitted
once on all 40 stocks stacked instead of once per stock. Rows `har_pooled` and `har_pooled_median`.

**Why.** The LightGBM-vs-HAR comparison of entry 11 changes two things at once: LightGBM is pooled and
nonlinear, HAR is per stock and linear, so the QLIKE gap (0.789 against 0.870 relative to GARCH at
h = 1) cannot be attributed to either. With the pooled linear row the gap splits into a pooling effect
(`har` -> `har_pooled`) and a nonlinearity effect (`har_pooled` -> `lgbm`), measured on the same data,
the same schedule and the same loss. It also carries the h = 20 result, where `lgbm` (1.028) loses to
`har` (0.935): if the pooled row sits near 1.03 the cost is pooling, if it sits near 0.935 the cost is
the nonlinearity. Pooled linear regression with long lags placed 19th in M5 (Bergmeir's course, part
2.01; `notes/ffds_course_assessment.md` item 4). A global model is a different claim from a nonlinear
one and the model chapter states them separately.

**Stock scale.** Per stock the intercept absorbs each stock's volatility level; one shared intercept
cannot. On the log scale a level difference is an additive shift and the regressors are log rv of the
same stock, so a model with b1 + b5 + b22 = 1 would be exactly scale-free; the fitted sum is below 1
(mean reversion), so some level dependence survives. Two options:

- (a) add the stock's expanding mean of log rv (`log_rv_expanding`) as a fourth regressor;
- (b) stock fixed effects, i.e. 40 intercepts.

**Decision: (a).** It is the feature the pooled LightGBM already receives (entry 11; course item 5), so
the pooled HAR becomes the literal linear counterpart of the LightGBM feature set restricted to the
HAR lags, and the `har_pooled` -> `lgbm` step isolates the functional form. (b) reintroduces 40
stock-specific parameters, so it is no longer the pooled end of the ladder and the pooling effect would
no longer be what the step measures; it stays available as a robustness row (`scale_feature: false`
plus dummies) if a reader asks for it. Parameters along the ladder: `har` 4 per stock (160 in all),
`har_pooled` 5, `lgbm` several hundred trees.

**Everything else follows entry 10 unchanged**, so that `har` and `har_pooled` differ in exactly one
thing: OLS at every monthly fit origin on the rows whose target is fully observed by then
(t + h <= fit origin, now on the global trading-day index of the balanced panel), expanding window, no
hyperparameter tuning (OLS has none to tune, which is also why this row cannot be accused of the
search the classical rows did not get), the in-sample residual variance for the retransformation
(`har_pooled` = h exp(mu + s^2/2), `har_pooled_median` = h exp(mu)) rather than LightGBM's validation
residuals, and a normal return shape. One fit per window and horizon on about 80,000 rows.

**Evidence (16 Nov 2026).** One run, 166 s, `--models har_pooled`; the VOLARE forecast table now holds
twelve model rows (2,089,920 forecasts). QLIKE relative to GARCH(1,1), from
`manuscript/tables/scores_volare.md`:

| horizon | `har` (per stock) | `har_pooled` | `lgbm` | pooling effect | nonlinearity effect |
|---|---|---|---|---|---|
| 1  | 0.870 | 0.869 | 0.789 | -0.001 | **-0.080** |
| 20 | 0.935 | 0.922 | 1.028 | **-0.013** | **+0.106** |

- At h = 1 pooling is worth nothing (0.870 against 0.869): with about 2,170 pre-origin rows per stock
  for four parameters there is no data-scarcity gain to collect, which is the condition under which
  global models pay (Montero-Manso & Hyndman 2020). The entire LightGBM advantage at h = 1 is the
  functional form, not the 40-fold training set.
- At h = 20 the two effects point in opposite directions: pooling helps a little (not significantly,
  see below) and the nonlinearity costs ten times as much as pooling saves. `har_pooled` is the best model in the table at h = 20 on
  QLIKE (0.922) and on MSE (154.3 against 158.0 for `har`, 175.8 for `lgbm`), with five parameters.
  So the h = 20 failure of LightGBM is overfitting of the 20-day target by the trees, not the pooling.
- The pooling step is not statistically significant at either horizon: Diebold-Mariano of
  `har_pooled` against `har` on the cross-sectional mean QLIKE gives +0.21 at h = 1 and +0.49 at
  h = 20 (decision 13), so the honest statement is that pooling buys nothing measurable here, at
  h = 20 included. The nonlinearity step is significant both times and in opposite directions:
  `lgbm` against `har_pooled` is -6.02 at h = 1 and +2.34 at h = 20.
- Pooling also improves the Mincer-Zarnowitz slope, 0.970 -> 0.984 at h = 1 and 0.933 -> 0.960 at
  h = 20, and `har_pooled` has the coverage closest to nominal of any row at h = 20 (0.904 / 0.944 /
  0.979 against 0.90 / 0.95 / 0.99). Sharing one rule across the panel appears to damp the
  stock-specific estimation noise that the per-stock fit carries into the tail of the distribution.
- The fitted rule is stable across the 104 windows: the three HAR lag coefficients sum to 0.897 at
  h = 1 and 0.70 at h = 20 (the mean reversion the single shared intercept cannot absorb is taken up
  by the scale feature), with in-sample residual variance 0.43 and 0.35.

## 13. Results figures and the Diebold-Mariano test (decided, 16 Nov 2026)

`src/thesis/evaluate/figures.py` (figures and the DM table), `src/thesis/evaluate/style.py` (one
palette and one set of matplotlib settings), `evaluate/scores.py` (`diebold_mariano`,
`newey_west_var`). Run with `make figures`. Everything is rebuilt from `forecasts.parquet` and
`scores.parquet`, so no number in the manuscript is typed by hand.

**The Diebold-Mariano construction.** The 20-day forecasts of consecutive origins overlap and the 40
stocks move together, so a test on the pooled 2.1 million rows would be wrong twice over. The loss
difference is therefore averaged across the 40 stocks at each origin first, which leaves one series
of about 2,170 daily differences and takes the cross-sectional dependence out of the problem
altogether; that series is then tested with Newey-West standard errors and 20 lags, the same lag
length decision 10 uses for Mincer-Zarnowitz. The loss is QLIKE. Benchmarks: GARCH(1,1), the Hansen
and Lunde yardstick, and the pooled HAR, the best model in the table. Averaging first is the
conservative reading of the cross-section: it tests whether a model beats another *on the average
stock-day*, not whether it does so for some stock. A per-stock version with a panel correction is a
Milestone 3 robustness row if a reader asks for it.

**What the figures show** (`manuscript/figures/`, PDF for the Quarto PDF and PNG for the docx):

- `fig_ladder` the pooling and nonlinearity steps of entry 12, as deviations from GARCH(1,1).
- `fig_qlike_regime` QLIKE relative to GARCH by calendar regime and VIX tercile, a model-by-regime
  grid, so a heatmap, with the diverging pair centred on the GARCH rule.
- `fig_coverage` empirical minus nominal coverage at the 90, 95 and 99 percent levels.
- `fig_mz_beta` the Mincer-Zarnowitz slope with its 95 percent HAC interval, against the line at one.
- `fig_mz_calibration` mean log realised against mean log forecast by forecast decile, for GARCH,
  pooled HAR and LightGBM, with the 45-degree line.

**Choices inside the figures that a reader could question.** (i) The regime figure shows the eight
primary model rows, not the four `_median` rows, which have their own column in the scores table and
their own panel in `fig_coverage`; (ii) the calibration figure shows three models because a
scatter-type chart with more than three series cannot keep its colours distinguishable under
colour-blind simulation; (iii) the heatmap's colour saturates at the 90th percentile of the
deviations, because one cell (AdaVol in covid, 2.07) would otherwise flatten every other cell, and
the printed numbers stay exact; (iv) every line in `fig_mz_calibration` sits below the 45-degree line
by construction, since the mean of the log is below the log of the mean for a right-skewed variable,
so the figure is read for its slope and for how the gap changes across deciles, not for its level.

**The regime windows do not tile the test period.** 325 of the 2,177 test days fall outside every
window of decision 5: 2 Jan to 14 Feb 2020 (31 days) and 1 Jul 2025 to 31 Aug 2026 (294 days, the
most recent fourteen months). They are shown as a column named `other` rather than dropped. Decision
5 is marked "revisit after exploration" and this is the revision it needs: either extend
`post_2023`/add a window for 2025-26, or state in the manuscript that the regime table covers 85
percent of the test days. To be settled with Nicolò before the results chapter is written.

**Two time-series figures added (16 Nov 2026).** The five figures above all collapse time: four
compare models on a model axis and the regime heatmap buckets 2,177 days into seven windows. Two
line charts restore the time dimension, and one of them changes how the h = 20 result reads.

- `fig_loss_over_time` the cumulative QLIKE saved against a benchmark, origin by origin: the same
  loss difference the Diebold-Mariano test averages, left unaveraged, so a steady climb (a persistent
  edge) can be told from a cliff (one episode). Three pairs, the ones the DM table and entry 12 turn
  on. The axis is the forecast origin, so at h = 20 the damage from an episode begins up to twenty
  trading days before the shaded covid band, which is drawn on origin dates.
- `fig_volatility_path` the cross-sectional mean annualised volatility of the 40 stocks, realised
  against three models' one-day forecasts, over the whole test period and zoomed on covid. The
  "look at the data" figure, and the visual form of a Mincer-Zarnowitz slope below one: at the peak
  realised volatility reaches about 220 percent a year while every model tops out between 100 and
  118, LightGBM lowest.

**What the cumulative figure shows**, cumulative QLIKE saved against GARCH(1,1) at h = 20:

| pair | 14 Feb 2020 | 31 Mar 2020 | 31 Aug 2026 |
|---|---|---|---|
| LightGBM vs GARCH | -5.9 | -39.8 | -18.2 |
| pooled HAR vs GARCH | +6.1 | +1.9 | +50.6 |
| LightGBM vs pooled HAR | -12.0 | -41.7 | -68.8 |

- LightGBM's whole 20-day deficit against GARCH is one episode: roughly level with GARCH for the
  first two years, then about 34 points lost in six weeks, then a slow recovery of about 25 points
  over the following six years. The headline 1.028 is a six-week event, not a standing weakness, and
  the results chapter should say so rather than leaving the ratio to carry the claim.
- Against the pooled HAR the deficit is not only covid: LightGBM is already behind before it (-12.0)
  and keeps losing ground afterwards, to -68.8. The pooled HAR dips by only four points through covid
  and then climbs steadily. That is the row the ML model actually has to beat.
- At h = 1 the picture is the opposite and reassuring: LightGBM is +43.7 against GARCH before covid,
  gives back about one point during it and ends at +197.5. The one-day advantage is persistent.
- **The ratio target made the crisis worse, not better.** `lgbm_ratio` was introduced in entry 11 to
  remove the tree-saturation ceiling precisely so that a crisis could be forecast (course item 3).
  Through covid it loses about 61 cumulative points against GARCH where the level variant loses about
  28, and it ends at -63.1 against the level variant's -18.2. The mechanism either does not work as
  argued or is dominated by the extra variance the ratio introduces; this needs a direct look at the
  2020 forecasts before entry 11's reasoning can stand in the manuscript. It is also the likely
  source of the h = 20 MSE blow-up (1391.9) already flagged in the scores table.
