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
