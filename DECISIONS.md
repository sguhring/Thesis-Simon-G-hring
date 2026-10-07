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

## 2. Target variance (open, decide before Milestone 1)

VOLARE `rv5_ss` is open-to-close (09:30 to 16:05). Returns are close-to-close. Options:

- (a) target = rv5_ss + overnight^2, where overnight = log(open_t / close_{t-1}) from Yahoo.
- (b) target = rv5_ss only, and models forecast open-to-close variance.

Leaning (a): it keeps GARCH on daily returns comparable with HAR on realised measures, and it is the
quantity a risk manager needs. Dividend ex-dates produce a small spurious overnight move; ignored.

## 3. After-close earnings days (open)

459 stock-days where the VOLARE close differs from the official close by more than 1 percent. All are
after-close earnings releases; the post-announcement jump lands in `rv5` (about 5x median), `bv5` is
unaffected. Options: keep as is, replace by `bv5_ss`, or keep and flag with a dummy. Current setting
in `config.yaml`: `flag_only`. Robustness table will show `bv5`.

## 4. Forecast origins and horizons (decided)

Monthly origins from 2 Jan 2018 to Aug 2026 (about 104), re-estimation at every origin on an expanding
window, hyperparameters tuned only on data before the origin. Horizons 1 and 20 days. 20 days
matches the M6 window so the same RPS and interval scores apply in both settings.

## 5. Regimes (decided, revisit after exploration)

Calendar regimes listed in `config.yaml` plus VIX terciles over test days. Calendar windows are fixed
before any model is run so they cannot be tuned to results.

## 6. Which M6 methods to reimplement (open)

Candidates with a published description in the IJF M6 special issue (vol. 41, issue 4, 2025):

- de Vilmarest & Werge, adaptive volatility method for probabilistic forecasting (pp. 1514-1520).
- Quasi-average predictions and regression to the trend (5th overall; pp. 1505-1513).
- Stanvek, hypernetworks and adversarial portfolios (1st duathlon, 4th forecasting; arXiv 2406.19105).
- Catlin, AutoTS (won the investment challenge; pp. 1485-1493).
- Robust returns ranking prediction and portfolio optimization for M6 (ScienceDirect S0169207024000359).
- Makridakis, Spiliotis & Michailidis, Avoiding overconfidence: symmetric quintile probabilities.

The official repo has evaluation code and all submissions, but no team code. Pick the 2-4 whose
forecasting step produces a return distribution per asset (so variance and quantiles can be read off),
not only quintile probabilities. Rule out methods whose description is too thin to reimplement.

## 7. Bloomberg (decided)

Not a dependency. All models run on VOLARE + Yahoo. Implied volatility, if it arrives, becomes one
extra feature block and one robustness table.

## 8. What gets cut first if time runs short (decided)

1. Neural network with distributional output. 2. Fourth M6 method. 3. VIX-tercile split (keep calendar
regimes). The M6 replication chapter is now core and is not cut.
