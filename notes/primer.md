# Primer: the six ideas the thesis rests on

Read this before the papers. Each idea has the plain-words version, one formula, and why it matters here.

## 1. Variance clusters, and GARCH tracks the clusters

Big moves are followed by big moves. GARCH(1,1) says today's expected variance is a weighted mix of a
long-run level, yesterday's squared surprise, and yesterday's expected variance:

    sigma2_t = omega + alpha * r_{t-1}^2 + beta * sigma2_{t-1}

alpha + beta close to 1 means shocks persist for weeks. GJR adds a term that lets negative returns
raise variance more than positive ones. AdaVol is the same recursion with alpha and beta updated
online by a gradient step instead of being re-estimated by maximum likelihood.

Why it matters: GARCH is the practitioner benchmark and needs only daily returns, so it can run in
both the M6 and the VOLARE setting.

## 2. Realised variance makes the "truth" observable

Squared daily returns are an unbiased but very noisy estimate of the day's variance. Summing squared
five-minute returns over the day gives a far more precise one:

    RV_t = sum over intraday intervals of r_{t,i}^2

HAR forecasts tomorrow's RV from averages of past RV over 1, 5 and 22 days. It is the benchmark the
ML-volatility literature compares against.

Why it matters: in VOLARE you can say "the forecast was 3, the truth was 5" with little noise. In M6
you cannot, which is why the VOLARE chapter carries the inference.

## 3. Only two losses are safe when the truth is a proxy

If you score variance forecasts against a noisy proxy, most losses reward biased forecasts. Patton
(2011) shows MSE and QLIKE are the exceptions:

    QLIKE = RV/F - log(RV/F) - 1       (F = forecast variance)

QLIKE punishes under-forecasts (F too small) much harder than over-forecasts, which is the behaviour a
risk manager wants.

Why it matters: it justifies the accuracy columns of your tables and answers a question Nicolò will ask.

## 4. Calibration versus sharpness

A probabilistic forecast is calibrated if things it calls 90 percent likely happen 90 percent of the
time. It is sharp if its distributions are narrow. The goal is to be as sharp as possible while staying
calibrated. Overconfidence is sharpness bought by giving up calibration.

Checks: coverage of a 95 percent interval should be 0.95; the probability integral transform
(forecast CDF evaluated at the outcome) should be uniform. A hump in the middle of the PIT histogram
means the forecast distributions were too narrow.

Why it matters: this is the precise meaning of the word "overconfidence" in the title.

## 5. Proper scores cannot be gamed

A score is proper if the forecaster's best strategy is to report their honest distribution. QLIKE,
the interval score and the ranked probability score are all proper. The M6 RPS, for five quintiles:

    RPS = (1/5) * sum_k ( cumulative forecast prob_k - cumulative outcome_k )^2

Equal probabilities of 0.2 score 0.16 on average. Being confidently wrong scores worse than admitting
ignorance.

Why it matters: it is the official M6 score, and because it is proper, the variance-inflation test is
meaningful: if inflating the variance lowers the RPS, the original variance was too small.

## 6. Mincer-Zarnowitz: the one regression that reads as a verdict

Regress the realised value on the forecast:

    RV_t = a + b * F_t + error

An unbiased, efficient forecast has a = 0 and b = 1. b above 1 with a below 0 means the forecast is
too small exactly when volatility is high, which is the signature of underestimated risk.

Why it matters: one slope per model and regime is the most readable evidence you can put in the
headline table.

## How they fit together

M6 gives rank probabilities and an official proper score (5), where overconfidence showed up as a
calibration failure (4). Rank scores cannot see a uniform variance error, so the thesis adds a direct
variance test (6) on a precise truth (2), scored with safe losses (3), for the models practitioners
use (1).
