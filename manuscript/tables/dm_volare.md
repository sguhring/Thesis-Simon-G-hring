Diebold-Mariano on QLIKE: the cross-sectional mean loss difference per origin, with
Newey-West standard errors (20 lags). A negative statistic means the row beats
the benchmark; |t| above 1.96 is the 5 percent level. Decision 13.

**Horizon 1** (2,176 origins)

| model | vs GARCH(1,1) | vs HAR pooled |
|---|---|---|
| naive | +6.08 | +11.86 |
| GARCH(1,1) | -- | +11.16 |
| GJR(1,1,1) | +1.47 | +11.78 |
| AdaVol | +1.44 | +4.18 |
| HAR | -10.94 | +0.21 |
| HAR, median | +1.87 | +10.64 |
| HAR pooled | -11.16 | -- |
| HAR pooled, median | +1.47 | +11.32 |
| LightGBM | -11.53 | -6.02 |
| LightGBM, median | -3.59 | +2.47 |
| LightGBM ratio | -9.23 | -3.70 |
| LightGBM ratio, median | -2.64 | +2.92 |

**Horizon 20** (2,157 origins)

| model | vs GARCH(1,1) | vs HAR pooled |
|---|---|---|
| naive | +5.48 | +8.29 |
| GARCH(1,1) | -- | +3.45 |
| GJR(1,1,1) | +1.05 | +3.69 |
| AdaVol | +1.44 | +2.06 |
| HAR | -1.53 | +0.49 |
| HAR, median | +1.04 | +2.09 |
| HAR pooled | -3.45 | -- |
| HAR pooled, median | +0.90 | +2.24 |
| LightGBM | +0.47 | +2.34 |
| LightGBM, median | +1.45 | +2.50 |
| LightGBM ratio | +1.30 | +2.64 |
| LightGBM ratio, median | +1.77 | +2.75 |
