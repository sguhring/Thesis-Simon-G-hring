"""Score the forecast table against the realised values and write the results tables.

Per row: QLIKE and MSE of the variance forecast against the realised h-day variance; coverage and
interval score of the central 90/95/99 percent return intervals against the realised h-day return.
Aggregation (per Hewamalage et al. 2023): average over origins within each stock and horizon first,
then across stocks, so no stock dominates a scale-dependent loss. Mincer-Zarnowitz is estimated on the
pooled rows per model and horizon with HAC standard errors.

Writes  data/processed/scores_by_stock.parquet   (model, horizon, symbol, n, scores)
        data/processed/scores.parquet            (model, horizon, scores averaged across stocks + MZ)
        manuscript/tables/scores_volare.md       (the headline table)
Run:    python -m thesis.evaluate.run_scores
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from thesis.evaluate.scores import coverage, interval_score, mincer_zarnowitz, mse, qlike
from thesis.models.base import qcol
from thesis.paths import FORECASTS, PROCESSED, REALISED, SCORES, TABLES, load_config

SCORES_BY_STOCK = PROCESSED / "scores_by_stock.parquet"


def interval_columns(level: float) -> tuple[str, str]:
    alpha = 1.0 - level
    return qcol(alpha / 2), qcol(1.0 - alpha / 2)


def row_scores(fc: pd.DataFrame, truth: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """One row per forecast with its losses; forecasts whose truth is not yet observed are dropped."""
    d = fc.merge(truth, on=["symbol", "origin", "horizon"], how="inner").dropna(subset=["ret_h", "rv_h"])
    d["qlike"] = qlike(d["var"].to_numpy(), d["rv_h"].to_numpy())
    d["mse"] = mse(d["var"].to_numpy(), d["rv_h"].to_numpy())
    d["log_ratio"] = np.log(d["rv_h"] / d["var"])            # > 0: realised above forecast (bias)
    for lv in cfg["evaluation"]["interval_levels"]:
        lo, hi = interval_columns(lv)
        tag = f"{int(round(lv * 100))}"
        d[f"cov{tag}"] = coverage(d[lo].to_numpy(), d[hi].to_numpy(), d["ret_h"].to_numpy())
        d[f"is{tag}"] = interval_score(d[lo].to_numpy(), d[hi].to_numpy(), d["ret_h"].to_numpy(), lv)
    return d


def aggregate(rows: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    score_cols = ["qlike", "mse", "log_ratio"] + [c for c in rows.columns if c.startswith(("cov", "is"))]
    by_stock = (rows.groupby(["model", "horizon", "symbol"])[score_cols].mean()
                .join(rows.groupby(["model", "horizon", "symbol"]).size().rename("n")).reset_index())
    table = by_stock.groupby(["model", "horizon"])[score_cols].mean()
    table["n"] = by_stock.groupby(["model", "horizon"])["n"].sum()
    mz = []
    for (model, h), g in rows.groupby(["model", "horizon"]):
        r = mincer_zarnowitz(g["var"].to_numpy(), g["rv_h"].to_numpy(), log=True)
        mz.append({"model": model, "horizon": h, "mz_alpha": r["alpha"], "mz_beta": r["beta"],
                   "mz_se_beta": r["se_beta"], "mz_r2": r["r2"], "mz_wald_p": r["wald_p"]})
    table = table.join(pd.DataFrame(mz).set_index(["model", "horizon"]))
    # QLIKE relative to GARCH(1,1), the Hansen & Lunde (2005) yardstick
    if "garch" in table.index.get_level_values("model"):
        ref = table.xs("garch", level="model")["qlike"]
        table["qlike_rel_garch"] = table["qlike"] / table.index.get_level_values("horizon").map(ref).to_numpy()
    return by_stock, table.reset_index()


def markdown_table(table: pd.DataFrame, cfg: dict) -> str:
    lines = []
    for h in cfg["horizons"]:
        t = table[table["horizon"] == h].sort_values("qlike")
        cols = ["model", "n", "qlike", "qlike_rel_garch", "mse", "log_ratio", "mz_beta", "cov90", "cov95", "cov99", "is95"]
        cols = [c for c in cols if c in t.columns]
        lines.append(f"\n**Horizon {h}** (mean over stocks of the per-stock mean over origins; MSE x 1e6; "
                     "log_ratio = mean log(realised / forecast); cov = empirical coverage of the central interval)\n")
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("|" + "---|" * len(cols))
        for _, r in t.iterrows():
            cells = []
            for c in cols:
                v = r[c]
                if c == "model":
                    cells.append(str(v))
                elif c == "n":
                    cells.append(f"{int(v):,}")
                elif c == "mse":
                    cells.append(f"{1e6 * v:.3f}")
                else:
                    cells.append(f"{v:.3f}")
            lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def main() -> None:
    cfg = load_config()
    fc = pd.read_parquet(FORECASTS)
    truth = pd.read_parquet(REALISED)
    rows = row_scores(fc, truth, cfg)
    by_stock, table = aggregate(rows, cfg)
    by_stock.to_parquet(SCORES_BY_STOCK, index=False)
    table.to_parquet(SCORES, index=False)
    md = markdown_table(table, cfg)
    (TABLES / "scores_volare.md").write_text(md, encoding="utf-8")
    print(md)
    print("saved", SCORES, SCORES_BY_STOCK, TABLES / "scores_volare.md")


if __name__ == "__main__":
    main()
