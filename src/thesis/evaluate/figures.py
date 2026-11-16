"""Results figures and the Diebold-Mariano table for the manuscript (decision 13).

Reads data/processed/forecasts.parquet + realised.parquet (per-row QLIKE) and scores.parquet (the
aggregated coverage and Mincer-Zarnowitz columns), and writes

    manuscript/figures/fig_ladder.{pdf,png}            pooling against nonlinearity (decision 12)
    manuscript/figures/fig_qlike_regime.{pdf,png}      QLIKE by calendar regime and VIX tercile
    manuscript/figures/fig_coverage.{pdf,png}          coverage error by interval level
    manuscript/figures/fig_mz_beta.{pdf,png}           Mincer-Zarnowitz slopes with HAC intervals
    manuscript/figures/fig_mz_calibration.{pdf,png}    realised against forecast, by forecast decile
    manuscript/tables/dm_volare.md                     Diebold-Mariano against GARCH and pooled HAR

Aggregation everywhere follows decision 10: the mean over origins within a stock first, then the mean
across the 40 stocks, so a volatile name cannot dominate. Run: python -m thesis.evaluate.figures
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.colors import Normalize

from thesis.evaluate.scores import diebold_mariano, qlike
from thesis.evaluate.style import (AXIS, BLUE, FIG_W, INK, INK_2, MUTED, RED_POLE, SERIES, SURFACE,
                                   diverging_cmap, oklab_lightness, save, use_style, value_grid)
from thesis.paths import FEATURES, FIGURES, FORECASTS, REALISED, SCORES, TABLES, load_config

MODEL_ORDER = ["naive", "garch", "gjr", "adavol", "har", "har_median", "har_pooled",
               "har_pooled_median", "lgbm", "lgbm_median", "lgbm_ratio", "lgbm_ratio_median"]
MAIN = ["naive", "garch", "gjr", "adavol", "har", "har_pooled", "lgbm", "lgbm_ratio"]
LADDER = ["har", "har_pooled", "lgbm", "lgbm_ratio"]
CALIBRATION = ["garch", "har_pooled", "lgbm"]          # three series: the all-pairs colour cap
LABEL = {"naive": "naive", "garch": "GARCH(1,1)", "gjr": "GJR(1,1,1)", "adavol": "AdaVol",
         "har": "HAR", "har_median": "HAR, median", "har_pooled": "HAR pooled",
         "har_pooled_median": "HAR pooled, median", "lgbm": "LightGBM",
         "lgbm_median": "LightGBM, median", "lgbm_ratio": "LightGBM ratio",
         "lgbm_ratio_median": "LightGBM ratio, median"}
HAC_LAGS = 20                                          # decision 10: overlapping 20-day forecasts


# ---------- data ----------

def load_losses() -> pd.DataFrame:
    """One row per forecast with its QLIKE against the realised h-day variance."""
    fc = pd.read_parquet(FORECASTS, columns=["symbol", "origin", "horizon", "model", "var"])
    truth = pd.read_parquet(REALISED)
    d = fc.merge(truth, on=["symbol", "origin", "horizon"], how="inner").dropna(subset=["rv_h"])
    d["qlike"] = qlike(d["var"].to_numpy(), d["rv_h"].to_numpy())
    return d


def regime_of(dates: pd.Series, cfg: dict) -> tuple[pd.Series, list[str]]:
    """Calendar regime per date (config `regimes`). Days outside every window are `other`: the
    config windows do not tile the test period, so that column is shown, not dropped (decision 5)."""
    names = [k for k, v in cfg["regimes"].items() if isinstance(v, dict)]
    out = pd.Series("other", index=dates.index, dtype=object)
    for name in names:
        w = cfg["regimes"][name]
        inside = (dates >= pd.Timestamp(w["start"])) & (dates <= pd.Timestamp(w["end"]))
        out[inside] = name
    return out, names + ["other"]


def vix_tercile_of(dates: pd.Series, cfg: dict) -> tuple[pd.Series, list[str], np.ndarray]:
    """VIX tercile per date, cut on the distribution over the test days (decision 5)."""
    f = pd.read_parquet(FEATURES, columns=["date", "vix"])
    v = f.groupby("date")["vix"].first()
    v = v[v.index >= pd.Timestamp(cfg["evaluation"]["first_origin"])]
    cuts = v.quantile([1 / 3, 2 / 3]).to_numpy()
    names = ["VIX low", "VIX mid", "VIX high"]
    lab = pd.cut(v, [-np.inf, cuts[0], cuts[1], np.inf], labels=names)
    return dates.map(lab).astype(object), names, cuts


def mean_across_stocks(d: pd.DataFrame, keys: list[str], col: str = "qlike") -> pd.Series:
    """Decision 10: the mean over origins within each stock, then the mean across stocks."""
    per_stock = d.groupby(keys + ["symbol"], observed=True)[col].mean()
    return per_stock.groupby(keys, observed=True).mean()


def relative_to_garch(s: pd.Series) -> pd.Series:
    """Divide by the GARCH(1,1) value within the remaining index levels (Hansen and Lunde 2005)."""
    ref = s.xs("garch", level="model")
    other = s.index.droplevel("model")
    return pd.Series(s.to_numpy() / ref.reindex(other).to_numpy(), index=s.index)


# ---------- figures ----------

def fig_ladder(d: pd.DataFrame, cfg: dict) -> list:
    """Decision 12: the HAR to pooled HAR to LightGBM ladder, as a deviation from GARCH(1,1).

    A delta-to-target chart, so the bars grow from the GARCH rule rather than from zero: left of it
    beats GARCH, right of it loses to GARCH, and the two steps of the ladder are the two gaps.
    """
    rel = relative_to_garch(mean_across_stocks(d, ["model", "horizon"]))
    every = np.array([rel.loc[(m, h)] for h in cfg["horizons"] for m in LADDER])
    xlim = (min(every.min(), 1.0) - 0.24, max(every.max(), 1.0) + 0.06)
    fig, axes = plt.subplots(1, 2, figsize=(FIG_W, 2.6), layout="constrained", sharex=True)
    for ax, h in zip(axes, cfg["horizons"]):
        vals = np.array([rel.loc[(m, h)] for m in LADDER])
        y = np.arange(len(LADDER))[::-1]
        ax.barh(y, vals - 1.0, left=1.0, height=0.5, zorder=2, linewidth=0,
                color=[BLUE if v < 1 else RED_POLE for v in vals])
        ax.axvline(1.0, color=AXIS, lw=0.9, zorder=3)
        for yi, v in zip(y, vals):
            ax.text(v + (-0.012 if v < 1 else 0.012), yi, f"{v:.3f}", va="center", color=INK_2,
                    fontsize=7, ha="right" if v < 1 else "left")
        for (a, b), name in ((("har", "har_pooled"), "pooling"),
                             (("har_pooled", "lgbm"), "nonlinearity")):
            ya, yb = y[LADDER.index(a)], y[LADDER.index(b)]
            va, vb = rel.loc[(a, h)], rel.loc[(b, h)]
            x = min(va, vb) - 0.06
            ax.plot([x, x], [ya, yb], color=MUTED, lw=0.6, zorder=2)
            ax.text(x - 0.01, (ya + yb) / 2, f"{name}\n{vb - va:+.3f}", ha="right", va="center",
                    fontsize=6.5, color=MUTED, linespacing=1.3)
        ax.set_yticks(y)
        ax.set_yticklabels([LABEL[m] for m in LADDER])
        ax.set_xlim(*xlim)
        ax.set_title(f"horizon {h} day" + ("s" if h > 1 else ""), loc="left")
        ax.set_xlabel("QLIKE relative to GARCH(1,1)")
        value_grid(ax)
    fig.suptitle("Pooling buys almost nothing; the functional form helps at one day and hurts at twenty",
                 x=0.0, ha="left", fontsize=9, color=INK)
    return save(fig, "fig_ladder", FIGURES)


def fig_qlike_regime(d: pd.DataFrame, cfg: dict) -> list:
    """QLIKE relative to GARCH(1,1) by calendar regime and by VIX tercile: a grid, so a heatmap,
    with the diverging pair centred on the GARCH rule (blue beats it, red loses to it)."""
    d = d[d["model"].isin(MAIN)].copy()
    d["regime"], reg_names = regime_of(d["origin"], cfg)
    d["vix"], vix_names, cuts = vix_tercile_of(d["origin"], cfg)
    panels = [("regime", reg_names, "calendar regime"), ("vix", vix_names, "VIX tercile")]
    tables = {}
    for key, names, _ in panels:
        rel = relative_to_garch(mean_across_stocks(d, ["model", "horizon", key]))
        tables[key] = rel.unstack(key).reindex(columns=names)
    spread = np.concatenate([t.to_numpy().ravel() for t in tables.values()])
    # One cell (AdaVol in covid) is twice GARCH and would flatten every other cell, so the colour
    # scale is cut at the 90th percentile of the deviations, rounded up to a twentieth, and the
    # extremes saturate. The printed numbers stay exact.
    r = float(np.ceil(np.nanquantile(np.abs(spread - 1.0), 0.90) * 20) / 20)
    norm, cmap = Normalize(1 - r, 1 + r), diverging_cmap()
    fig, axes = plt.subplots(2, 2, figsize=(FIG_W, 4.6), layout="constrained",
                             gridspec_kw={"width_ratios": [len(reg_names), len(vix_names)]})
    for row, h in enumerate(cfg["horizons"]):
        for col, (key, names, nice) in enumerate(panels):
            ax = axes[row, col]
            t = tables[key].xs(h, level="horizon").reindex(MAIN)
            values = t.to_numpy()
            ax.imshow(values, cmap=cmap, norm=norm, aspect="auto")
            for i in range(values.shape[0]):
                for j in range(values.shape[1]):
                    v = values[i, j]
                    fill = tuple(float(c) for c in cmap(norm(v))[:3])
                    ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.2,
                            color="#ffffff" if oklab_lightness(fill) < 0.62 else INK)
            ax.set_xticks(range(values.shape[1]))
            ax.set_xticklabels([n.replace("_", " ").replace("VIX ", "") for n in names],
                               rotation=30, ha="right")
            ax.set_yticks(range(len(MAIN)))
            ax.set_yticklabels([LABEL[m] for m in MAIN] if col == 0 else [""] * len(MAIN))
            ax.set_title(f"horizon {h}: {nice}", loc="left", fontsize=7.5)
            # the surface gap that separates touching fills, as a minor grid in the surface colour
            ax.set_xticks(np.arange(values.shape[1] + 1) - 0.5, minor=True)
            ax.set_yticks(np.arange(values.shape[0] + 1) - 0.5, minor=True)
            ax.grid(which="minor", color=SURFACE, linewidth=1.4)
            ax.tick_params(length=0)
            ax.tick_params(which="minor", length=0)
            for sp in ax.spines.values():
                sp.set_visible(False)
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=axes, shrink=0.5,
                      aspect=26, pad=0.015, ticks=[1 - r, 1.0, 1 + r])
    cb.ax.set_yticklabels(["beats\nGARCH", "GARCH(1,1)", "loses to\nGARCH"], fontsize=6.5)
    cb.outline.set_visible(False)
    fig.suptitle("QLIKE relative to GARCH(1,1). Colour saturates beyond "
                 f"{r:.2f}; VIX terciles cut at {cuts[0]:.1f} and {cuts[1]:.1f}",
                 x=0.0, ha="left", fontsize=9, color=INK)
    return save(fig, "fig_qlike_regime", FIGURES)


def fig_coverage(table: pd.DataFrame, cfg: dict) -> list:
    """Empirical minus nominal coverage, in percentage points, one marker per interval level.
    Below zero is an interval that is too narrow: the signature the thesis is looking for."""
    levels = cfg["evaluation"]["interval_levels"]
    fig, axes = plt.subplots(1, 2, figsize=(FIG_W, 3.6), layout="constrained", sharey=True,
                             sharex=True)
    y = np.arange(len(MODEL_ORDER))[::-1]
    for ax, h in zip(axes, cfg["horizons"]):
        t = table[table["horizon"] == h].set_index("model").reindex(MODEL_ORDER)
        for j, lv in enumerate(levels):
            err = 100.0 * (t[f"cov{int(round(lv * 100))}"].to_numpy() - lv)
            ax.plot(err, y, "o", ms=5, color=SERIES[j], markeredgecolor=SURFACE, mew=1.0,
                    label=f"{int(round(lv * 100))}%", zorder=3, linestyle="none")
        ax.axvline(0.0, color=AXIS, lw=0.9, zorder=2)
        ax.set_title(f"horizon {h} day" + ("s" if h > 1 else ""), loc="left")
        ax.set_xlabel("empirical minus nominal coverage (pp)")
        value_grid(ax)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels([LABEL[m] for m in MODEL_ORDER])
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, title="central interval", loc="outside lower center", ncols=3,
               title_fontsize=7, handletextpad=0.2, columnspacing=1.4)
    fig.suptitle("The retransformation moves coverage more than the choice of model does",
                 x=0.0, ha="left", fontsize=9, color=INK)
    return save(fig, "fig_coverage", FIGURES)


def fig_mz_beta(table: pd.DataFrame, cfg: dict) -> list:
    """Mincer-Zarnowitz slope with its 95 percent HAC interval. A slope below one means the forecast
    moves too little with the truth: too low when variance is high, too high when it is low."""
    fig, axes = plt.subplots(1, 2, figsize=(FIG_W, 3.6), layout="constrained", sharey=True,
                             sharex=True)
    y = np.arange(len(MODEL_ORDER))[::-1]
    for ax, h in zip(axes, cfg["horizons"]):
        t = table[table["horizon"] == h].set_index("model").reindex(MODEL_ORDER)
        b, se, p = t["mz_beta"].to_numpy(), t["mz_se_beta"].to_numpy(), t["mz_wald_p"].to_numpy()
        ax.errorbar(b, y, xerr=1.96 * se, fmt="none", ecolor=MUTED, elinewidth=0.9, capsize=1.6,
                    zorder=2)
        bad = p < 0.05
        ax.plot(b[bad], y[bad], "o", ms=5, color=BLUE, markeredgecolor=SURFACE, mew=1.0, zorder=3,
                linestyle="none", label="rejects unbiasedness")
        ax.plot(b[~bad], y[~bad], "o", ms=5, markerfacecolor=SURFACE, markeredgecolor=BLUE, mew=1.2,
                zorder=3, linestyle="none", label="does not reject")
        ax.axvline(1.0, color=AXIS, lw=0.9, zorder=1)
        ax.set_title(f"horizon {h} day" + ("s" if h > 1 else ""), loc="left")
        ax.set_xlabel("Mincer-Zarnowitz slope on log variance")
        value_grid(ax)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels([LABEL[m] for m in MODEL_ORDER])
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncols=2, handletextpad=0.2,
               columnspacing=1.4)
    fig.suptitle("Every model rejects unbiasedness; only LightGBM at one day has a slope near one",
                 x=0.0, ha="left", fontsize=9, color=INK)
    return save(fig, "fig_mz_beta", FIGURES)


def fig_mz_calibration(d: pd.DataFrame, cfg: dict, n_bins: int = 10) -> list:
    """Realised against forecast variance by forecast decile, on the log scale.

    Every line sits below the 45-degree line by construction: the mean of the log is below the log
    of the mean, and the realised variance is right-skewed. What the figure is for is the slope and
    how the gap changes from the low deciles to the high ones -- a line that flattens towards the
    right is a model that does not raise its forecast enough when variance is high.
    """
    fig, axes = plt.subplots(1, 2, figsize=(FIG_W, 3.2), layout="constrained")
    for ax, h in zip(axes, cfg["horizons"]):
        lo, hi = np.inf, -np.inf
        for j, m in enumerate(CALIBRATION):
            g = d[(d["model"] == m) & (d["horizon"] == h)]
            x, yv = np.log(g["var"].to_numpy()), np.log(g["rv_h"].to_numpy())
            edges = np.quantile(x, np.linspace(0, 1, n_bins + 1))
            which = np.clip(np.digitize(x, edges[1:-1]), 0, n_bins - 1)
            bx = np.array([x[which == k].mean() for k in range(n_bins)])
            by = np.array([yv[which == k].mean() for k in range(n_bins)])
            ax.plot(bx, by, "-o", ms=4.5, color=SERIES[j], markeredgecolor=SURFACE, mew=0.9,
                    zorder=3, label=LABEL[m])
            lo, hi = min(lo, bx.min(), by.min()), max(hi, bx.max(), by.max())
        # The three lines converge at the right edge, so end labels would collide: the legend
        # carries identity instead (data-visualisation guidance, "when end-labels collide").
        pad = 0.08 * (hi - lo)
        ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad], color=AXIS, lw=0.9, zorder=1)
        ax.text(lo - 0.5 * pad, lo - 0.2 * pad, "45 degrees", fontsize=6.5, color=MUTED,
                ha="left", va="bottom", rotation=45, rotation_mode="anchor")
        ax.set_xlim(lo - pad, hi + pad)
        ax.set_ylim(lo - pad, hi + pad)
        ax.set_title(f"horizon {h} day" + ("s" if h > 1 else ""), loc="left")
        ax.set_xlabel("mean log forecast variance")
        if h == cfg["horizons"][0]:
            ax.set_ylabel("mean log realised variance")
        value_grid(ax, axis="both")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncols=3, handletextpad=0.2,
               columnspacing=1.4)
    fig.suptitle("Conditional calibration by forecast decile: GARCH falls away as the forecast rises",
                 x=0.0, ha="left", fontsize=9, color=INK)
    return save(fig, "fig_mz_calibration", FIGURES)


# ---------- Diebold-Mariano ----------

def dm_table(d: pd.DataFrame, cfg: dict, benchmarks=("garch", "har_pooled")) -> str:
    """Decision 13: average the per-stock QLIKE difference across the 40 stocks at each origin, then
    test the resulting series with Newey-West standard errors (20 lags, the forecast overlap).
    Averaging first keeps the cross-sectional dependence out of the standard error."""
    daily = d.groupby(["horizon", "model", "origin"], observed=True)["qlike"].mean().unstack("model")
    lines = ["Diebold-Mariano on QLIKE: the cross-sectional mean loss difference per origin, with",
             f"Newey-West standard errors ({HAC_LAGS} lags). A negative statistic means the row beats",
             "the benchmark; |t| above 1.96 is the 5 percent level. Decision 13."]
    rows = []
    for h in cfg["horizons"]:
        wide = daily.xs(h, level="horizon")
        for m in MODEL_ORDER:
            rec = {"horizon": h, "model": LABEL[m], "n": len(wide)}
            for b in benchmarks:
                if m == b:
                    rec[b] = np.nan
                    continue
                pair = wide[[m, b]].dropna()
                rec[b] = diebold_mariano(pair[m].to_numpy(), pair[b].to_numpy(), HAC_LAGS)["stat"]
            rows.append(rec)
    t = pd.DataFrame(rows)
    for h in cfg["horizons"]:
        sub = t[t["horizon"] == h]
        lines.append(f"\n**Horizon {h}** ({int(sub['n'].iloc[0]):,} origins)\n")
        lines.append("| model | vs GARCH(1,1) | vs HAR pooled |")
        lines.append("|---|---|---|")
        for _, r in sub.iterrows():
            cells = ["--" if pd.isna(r[b]) else f"{r[b]:+.2f}" for b in benchmarks]
            lines.append(f"| {r['model']} | " + " | ".join(cells) + " |")
    md = "\n".join(lines) + "\n"
    (TABLES / "dm_volare.md").write_text(md, encoding="utf-8")
    return md


def main() -> None:
    cfg = load_config()
    use_style()
    d = load_losses()
    table = pd.read_parquet(SCORES)
    print(f"{len(d):,} scored forecasts, {d['model'].nunique()} models")
    written = []
    written += fig_ladder(d, cfg)
    written += fig_qlike_regime(d, cfg)
    written += fig_coverage(table, cfg)
    written += fig_mz_beta(table, cfg)
    written += fig_mz_calibration(d, cfg)
    print(dm_table(d, cfg))
    for p in written:
        print("saved", p)
    print("saved", TABLES / "dm_volare.md")


if __name__ == "__main__":
    main()
