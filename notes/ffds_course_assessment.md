# Bergmeir, "Forecasting for Data Scientists" (FFDS): what the thesis takes from it

Assessed 11 Nov 2026 from the transcripts of 15 of the 30 videos (1.03, 1.04, 1.10, 2.01-2.03, 2.05,
2.06, 2.10, 3.01, 3.02, 3.04-3.07). Playlist: youtube.com/playlist?list=PLSpAVARuzDa2KlLPVynFc5uBZ0U_cXF6X.
Slides: cbergmeir.com/talks/FFDS_Theory_{1,2,3}.pdf. The course is for ML practitioners learning
forecasting; the thesis author is the mirror case. Not citable as a video; cite the papers it rests on:
Hewamalage, Ackermann & Bergmeir 2023 (DMKD, "Forecast evaluation for data scientists"), Bergmeir &
Benitez 2012 (Inf. Sci.), Bergmeir, Hyndman & Koo 2018 (CSDA), Montero-Manso & Hyndman 2020 (IJF,
global models), Hyndman & Koehler 2006 (MASE). Page numbers to be checked before entering references.bib.

## Changes to the design or the code

1. **Hyperparameter tuning inside the training window (3.01).** For a purely autoregressive learner
   (LightGBM on a lag matrix, no state) ordinary k-fold cross-validation on the embedded rows is valid:
   with an adequate model the residuals are uncorrelated, so the overlap between rows does not bias the
   CV estimate (Bergmeir, Hyndman & Koo 2018). Consequence: no nested rolling validation needed for
   decision 4; tune LightGBM by blocked CV on pre-origin rows. For the 20-day target the rows overlap
   by construction, so use blocked folds with a 20-day gap. Check underfitting with Ljung-Box on the
   residuals.
2. **Leakage checklist as a unit test (3.01).** Leakage enters through anything computed on the full
   sample before the split: normalisation, smoothing or decomposition, feature extraction. The HAR lags
   and the per-stock scale used by the pooled model must be computed from pre-origin data only. Write a
   test that shifts the post-origin data and checks the forecast is unchanged.
3. **Tree saturation as an overconfidence mechanism (2.02).** A tree model cannot forecast outside the
   range of training targets (leaves average training values). Trained on 2015-2019 and asked for March
   2020, LightGBM on log variance cannot exceed the 2018 peaks; GARCH's recursion can. This is a
   concrete, testable cause of ML under-forecasting in crises for the regime chapter. Fix the course
   suggests (2.03): window-wise normalisation, here a ratio target log(rv_{t+h} / rv_22,t) or ratio
   features, which is stationary and lets the tree extrapolate the level. Run LightGBM both ways.
4. **Pooled HAR as the bridge row (2.01).** Pooled linear regression with long lags placed 19th in M5.
   A pooled HAR next to the per-stock HAR separates the pooling gain from the nonlinearity gain when
   LightGBM is compared with HAR. Global models predict each series in isolation; the cross-stock
   information enters only in the M6 correlation step. State that distinction in the model chapter.
5. **Per-stock scale in the pooled model (2.05).** Mean normalisation fails under level shifts; keep the
   scale as a feature. For the pooled LightGBM: include the stock's pre-origin long-run variance (or
   normalise by it) and record which in the model name.
6. **Record each model's training loss (1.04, 3.05).** A point forecast is the summary statistic that
   minimises the training loss: mean under L2, median under L1. GARCH is QML on the variance, HAR is OLS
   on the log (a conditional-median-type forecast of the level), LightGBM is L2 on the log. The
   comparison is loss-mismatched by construction, and the course's advice is to report measures for both
   when methods are trained under different losses. The mismatch is itself a candidate cause of ML
   overconfidence (decision 9's retransformation note). Add a `loss` field to the forecast table or
   encode it in `model`.
7. **Aggregation order (3.02, 3.04).** Three averaging dimensions: horizon, origin, series. Average
   within stock and horizon over origins first, then across stocks; never pool raw errors across stocks
   for scale-dependent losses (MSE on the variance scale is dominated by the volatile names). Report the
   mean error (bias) separately from accuracy; MSE = bias^2 + variance. Make this the scoring default.
8. **Conformal recalibration as a Milestone 3 row (3.06).** Analytical intervals that treat parameters as
   known are too narrow; conformal prediction fixes the width empirically from past rolling-origin
   errors. For each model, rescale the interval by the empirical quantile of past standardised errors
   (pre-origin only). The gap between raw and recalibrated coverage measures how much of the
   overconfidence is removable, which is a useful discussion point.
9. **Interval evaluation (3.07).** Coverage alone is gameable (narrow intervals most of the time, huge
   ones occasionally). Always pair it with the interval score or MSIS, which penalise width and
   exceedance. CRPS is available in closed form for the normal and t predictive distributions the
   models produce; cheap to add next to the interval score.

## Wording and justification for the manuscript

- 1.03: naive and mean forecasts are the two extremes of weighting the past; exponential smoothing sits
  between. GARCH(1,1) is exponential smoothing of squared returns plus mean reversion: a plain-words
  way to introduce it. The simulated random walks (readers see structure in pure noise) is a good
  figure idea for the overconfidence introduction.
- 1.04: "a forecast is a distribution; the point forecast is a statistic of it under a loss". The
  rainfall example (mode 0, median 0, mean 3.25) maps onto variance: skewed, so median under mean. This
  is why exp(log forecast) under-forecasts the variance mean, and why QLIKE (minimised by the
  conditional mean) punishes it.
- 1.10: M1 to M4 history, the 2018 Makridakis "concerns and way forward" paper rejected by ML venues,
  cherry-picked stock-forecasting papers. Frames the M6 chapter.
- 2.10: foundation-model papers that omit the competition winners from their comparison; benchmarks must
  be run under the same evaluation. Parallel to the thesis's insistence on the organisers' RPS code.
- 3.01: rolling-origin plots of forecast against realised are visually deceptive (the naive forecast
  looks fine as a shifted copy). Do not use overlaid variance paths as evidence; show scores.
- 3.05: relative measures need a benchmark that is meaningful on the series; the thesis's "relative to
  GARCH(1,1)" column (Hansen & Lunde 2005) is that. Do not invent measures.

## Not applicable

Seasonality, Prophet, TBATS, transformers, intermittent series, external regressors, MAPE family,
MASE/RMSSE (the variance proxy is noisy; Patton 2011's robust losses override the course here).
