# Prep notes: dissertation seminar, 9 Sep 2026, 16:00

## The proposal in one paragraph

Extend the flagship stock-level study, Christensen, Siggaard & Veliyev (2023, JFEC), from 2001-2017 DJIA data to 2015-2026 using the new open VOLARE realised-volatility library (40 US large caps, Dow 30 plus 10 S&P 100 names). Add what that literature leaves out: GARCH-type models estimated on daily returns, a regime split (VIX terciles, COVID 2020, 2022 tightening, 2025 tariff shock), and an economic-value test (1-day VaR backtests, vol-targeting). Models: GARCH(1,1), GJR, Realized GARCH; HAR-RV, log-HAR, HARQ, HAR-RS; ridge/LASSO, random forest, LightGBM, feed-forward NN, first on HAR-only lags then on an extended feature set; hybrids. Evaluation with QLIKE and MSE, Diebold-Mariano, Model Confidence Set, Mincer-Zarnowitz.

## Literature you should be able to talk about

| Paper | What they do | Why it matters for me |
|---|---|---|
| Hansen & Lunde (2005), *J. Applied Econometrics* | 330 GARCH-type models on DM/USD and IBM. "Does anything beat a GARCH(1,1)?" | Nothing beats GARCH(1,1) on FX; leverage models win on IBM. Origin of the "GARCH is hard to beat" claim. |
| Corsi (2009), *JFEC* | HAR-RV: daily, weekly, monthly RV lags | The real benchmark once the target is realised variance. |
| Bollerslev, Patton & Quaedvlieg (2016), *J. Econometrics* | HARQ: let the daily-lag coefficient shrink when realised quarticity (measurement error) is high | VOLARE ships rq, so HARQ is a free, strong benchmark. |
| Patton & Sheppard (2015), *REStat* | Signed semivariances: negative-return volatility predicts future volatility more | VOLARE ships rsp/rsn, so HAR-RS and semivariance features are free. |
| Patton (2011), *J. Econometrics* | Which loss functions are robust when the volatility proxy is noisy | Justifies QLIKE and MSE only. |
| Hansen, Lunde & Nason (2011), *Econometrica* | Model Confidence Set | Standard multi-model test in this literature. |
| Bucci (2020), *JFEC* | LSTM vs ARFIMA etc. on monthly S&P 500 RV, 1950-2017 | LSTM wins, mostly in high-vol periods. Monthly, single index: low frequency. |
| Christensen, Siggaard & Veliyev (2023), *JFEC*; updated arXiv Jan 2026 | Regularisation, trees, NNs vs HAR family; 29 DJIA stocks, 2001-2017, TAQ 5-min RV | ML beats HAR even with only HAR lags; gains larger at 5-22 days; ML extracts more from extra predictors; variable importance via accumulated local effects (ALE). This is the paper I extend. |
| Zhang, Zhang, Cucuringu & Qian (2024), *JFEC* | Intraday RV, ~100 US stocks, LOBSTER; pool stocks, add market-vol proxy | Pooling across stocks and a market-volatility feature help; NNs > trees > linear. Motivates pooled training and ES-futures RV as a feature. |
| Rahimikia & Poon (2020), SSRN | ML with HAR vars, limit-order-book and news, 23 NASDAQ stocks | ML beats HAR on ~90% of days but not in extreme-volatility episodes. Motivates the regime hypothesis H2. |
| Reisenhofer, Bayer & Hautsch (2022), arXiv | HARNet: dilated CNN that nests HAR | Neural nets that start from HAR improve on it. Optional extra model. |
| Dudek, Fiszeder, Kobus & Orzeszko (2024), *Applied Soft Computing* | BTC, ETH, LTC, XMR daily/weekly vol; HAR, GARCH, LASSO, ridge, SVR, MLP, RF, LSTM | No single winner; HAR and ridge do as well as LSTM and RF. Reason not to lead with crypto. |
| Brini (2026), arXiv, July 2026 | Nine zero-shot time-series foundation models vs eight econometric models on VOLARE, 50 assets | Foundation models barely beat log-HAR; equal-weight TTM + log-HAR most robust. Shows VOLARE is already used in the literature and that combinations matter. |
| Cipollini, Cruciani, Gallo, Insana, Otranto & Spagnolo (2026), arXiv, Feb 2026 | VOLARE: open realised-measure library, CC-BY-4.0, from Kibot tick data | The dataset. 40 stocks from 2 Jan 2015, 5 FX pairs and 5 futures from Sep 2009, monthly updates. Measures: rv1, rv5 (+ subsampled), bv, rsp/rsn, rq, medrv, minrv, rk, Parkinson, Garman-Klass, realised range, plus multivariate covariances. |

## The gap, in one sentence each

- Stock-level ML-vs-HAR evidence stops in 2017 (Christensen) or 2020 (Zhang) and relies on proprietary TAQ/LOBSTER data.
- GARCH is usually dropped once the target is realised variance, so "ML vs GARCH" and "ML vs HAR" are rarely in the same table.
- Regime dependence and economic value (VaR coverage, vol-targeting) are rarely tested together.
- 2015-2026 contains four distinct stress episodes (Volmageddon 2018, COVID 2020, 2022 tightening, 2025 tariff shock), which is exactly what a regime analysis needs.

## Hypotheses

- H1: ML beats HAR/GARCH mainly at 5- and 22-day horizons, not at 1 day (Christensen et al.).
- H2: The ML advantage shrinks or vanishes in the top VIX tercile (Rahimikia & Poon).
- H3: Most of the ML gain comes from extra predictors (rq, semivariances, VIX, market RV), not from nonlinearity in HAR lags alone.
- H4: QLIKE improvements show up as better VaR coverage, but vol-targeted Sharpe differences are small.

## Questions Nicolò is likely to ask

1. **"Isn't this just a replication?"** It is an extension with open data, a new sample with four stress regimes, GARCH added back, and an economic-value chapter. Replicability (public code, open data) is itself a contribution; the original uses TAQ.
2. **"Why not HAR only, why GARCH?"** Because the research question is ML vs GARCH; GARCH is what practitioners and textbooks use, and it only needs daily returns. Keeping both lets me say whether ML beats the practitioner benchmark and the academic benchmark.
3. **"Why realised variance from 5-min data?"** Squared daily returns are an unbiased but very noisy proxy; VOLARE gives a clean 5-min subsampled RV for free. Robustness: rv1, rk, log target.
4. **"Pooled or stock-by-stock?"** Both. Stock-by-stock matches GARCH and HAR; pooled is what Zhang et al. show helps ML. I report both and treat pooling as one of the sources of the ML gain.
5. **"How do you avoid overfitting?"** Rolling window with a fixed validation year for hyperparameters, yearly re-fit, no tuning on test data, 40 stocks x 3 horizons so no single series can drive the result, MCS instead of cherry-picking one loss.
6. **"Is one semester enough?"** GARCH, HAR and LightGBM are cheap. The feed-forward NN is small. LSTM is optional and the first thing to cut.
7. **"What if VOLARE does not work?"** Fallback A: Kaggle 1-min S&P 500 bars 2008-2021 plus one month of Polygon.io Starter (29 USD, 5 years of minute data) to reach 2026, computing RV myself. Fallback B: Binance 1-min klines for BTC/ETH since 2017, same design on crypto.

## Syllabus milestones (from the seminar PDF)

| Date | Session | What must be ready |
|---|---|---|
| 9 Sep | Session 1, group | Research question + at least one backup; detailed data list; data collection strategy |
| 16 Sep | Session 2, group | Final research question; data in hand or tested collection strategy; set of models |
| Week of 5 Oct | Milestone 1, individual | Data collected, cleaned, explored with visuals and summary stats. Manuscript started |
| Week of 9 Nov | Milestone 2, individual | Models estimated, validated, compared |
| Week of 7 Dec | Milestone 3, individual | Conclusions, critical discussion, final manuscript reviewed. Drafts not accepted |

This means the modelling must be done by early November and the text by early December. Plan for the core (GARCH, HAR, LightGBM, three horizons, QLIKE, DM, MCS, regime split, VaR) and treat the neural net, hybrid and FX chapter as optional.

Other syllabus points that matter: Kaggle datasets are discouraged (VOLARE is an academic library, seven months old, not Kaggle). Output is a manuscript plus code; sharing code on GitHub is recommended. Session 3 focuses on data exploration, so plan a proper descriptive chapter: RV time series per stock, cross-sectional correlation of RV, VIX overlay, distribution of log RV, crisis windows.

## To do before the individual meeting

- Register/download from volare.unime.it today and confirm: bulk CSV for all 40 stocks, rv5_ss and rq present, data reaches mid-2026.
- Pull AAPL end to end: VOLARE RV, Yahoo returns, VIX; fit GARCH(1,1) and HAR-RV; produce one QLIKE table for h = 1. That proves the pipeline in a day.
- Read Christensen et al. (2023) in full, Section 2 (data) and Section 5 (results), and skim Zhang et al. (2024) Section 4.

## Sources

- Christensen, Siggaard & Veliyev, JFEC 21(5), 2023: https://academic.oup.com/jfec/article-abstract/21/5/1680/6612759 ; arXiv Jan 2026 version: https://arxiv.org/abs/2601.13014
- Zhang, Zhang, Cucuringu & Qian, JFEC 22(2), 2024: https://academic.oup.com/jfec/article/22/2/492/7081291
- Rahimikia & Poon, SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3707796
- Bucci, JFEC 18(3), 2020: https://academic.oup.com/jfec/article-abstract/18/3/502/5856840
- Reisenhofer, Bayer & Hautsch, HARNet: https://arxiv.org/abs/2205.07719
- Dudek et al. 2024: https://www.sciencedirect.com/science/article/pii/S156849462301150X
- Brini 2026, foundation models on VOLARE: https://arxiv.org/abs/2607.05291
- VOLARE paper: https://arxiv.org/abs/2602.19732 ; data: https://volare.unime.it
- Bollerslev, Patton & Quaedvlieg HARQ: https://www.sciencedirect.com/science/article/abs/pii/S0169207020300467 (see also Duke working paper)
- Patton & Sheppard 2015: https://public.econ.duke.edu/~ap172/Patton_Sheppard_REStat_2015.pdf
- Kaggle 1-min S&P 500 2008-21: https://www.kaggle.com/datasets/gratefuldata/intraday-stock-data-1-min-sp-500-200821
- Polygon.io pricing: https://apicostcalc.com/polygon.html
- Binance public data: https://github.com/binance/binance-public-data
