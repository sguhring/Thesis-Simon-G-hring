"""Draw the three figures of notes/literature_review_hypotheses.pdf and save the numbers they quote.

    python notes/lit_review_figures.py          # writes notes/figures/lit_*.png and lit_numbers.json
    python notes/build_literature_review_pdf.py

Figure 1 is a simulation (about a minute); the other two are closed-form.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

FIG = Path(__file__).resolve().parent / "figures"
INK, SECOND, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": AXIS, "axes.linewidth": 0.8,
    "axes.labelcolor": SECOND, "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": SECOND,
    "ytick.labelcolor": SECOND, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "figure.facecolor": "white",
    "axes.facecolor": "white", "savefig.dpi": 200, "savefig.bbox": "tight", "legend.frameon": False,
})


def quintile_probs(returns):
    """Share of simulated draws in which each asset lands in each quintile of the cross-section."""
    q = returns.argsort(axis=1).argsort(axis=1) // (returns.shape[1] // 5)
    return np.stack([(q == j).mean(axis=0) for j in range(5)], axis=1)


def expected_rps(p, q):
    """Expected RPS of forecast p when the outcome is drawn from q (both assets x 5)."""
    P, Q = p.cumsum(axis=1)[:, :4], q.cumsum(axis=1)[:, :4]
    return float((((P - Q) ** 2 + Q * (1 - Q)).sum(axis=1) / 5).mean())


def simulate(n_rounds=16, n_draws=6000, seed=7):
    """Three stylised forecasters of 100 assets, each scored for a grid of common variance factors k."""
    rng = np.random.default_rng(seed)
    sigma = np.concatenate([np.exp(rng.normal(np.log(0.09), 0.35, 50)),      # 50 'stocks'
                            np.exp(rng.normal(np.log(0.04), 0.45, 50))])     # 50 'funds'
    steep = np.exp(np.log(sigma).mean() + 2.0 * (np.log(sigma) - np.log(sigma).mean()))
    tau = 0.012                                                              # spread of the true 20-day means
    ks = np.array([0.25, 0.35, 0.5, 0.7, 1, 1.4, 2, 2.8, 4, 5.6, 8, 11, 16, 23, 32, 45, 64])
    res = {"ideal": 0.0, "var_only": np.zeros(len(ks)), "steep": np.zeros(len(ks)), "bold": np.zeros(len(ks)),
           "max_gap_scale_vs_shrink": 0.0, "max_gap_level": 0.0}
    for _ in range(n_rounds):
        mu = rng.normal(0, tau, 100)
        mu_hat = mu + rng.normal(0, 1.5 * tau, 100)                          # real signal, oversold
        z = rng.standard_normal((n_draws, 100))
        truth = quintile_probs(mu + sigma * z)
        res["ideal"] += expected_rps(truth, truth) / n_rounds
        for i, k in enumerate(ks):
            p_var = quintile_probs(np.sqrt(k) * sigma * z)
            p_bold = quintile_probs(mu_hat + np.sqrt(k) * sigma * z)
            res["var_only"][i] += expected_rps(p_var, truth) / n_rounds
            res["steep"][i] += expected_rps(quintile_probs(np.sqrt(k) * steep * z), truth) / n_rounds
            res["bold"][i] += expected_rps(p_bold, truth) / n_rounds
            shrunk = quintile_probs(mu_hat / np.sqrt(k) + sigma * z)
            res["max_gap_scale_vs_shrink"] = max(res["max_gap_scale_vs_shrink"], float(np.abs(p_bold - shrunk).max()))
            res["max_gap_level"] = max(res["max_gap_level"], float(np.abs(p_var - quintile_probs(sigma * z)).max()))
    return ks, res


def fig_inflation(numbers):
    ks, r = simulate()
    best = int(r["bold"].argmin())
    numbers.update(sim_ideal=r["ideal"], sim_var_only=float(r["var_only"][0]), sim_steep=float(r["steep"][0]),
                   sim_bold_k1=float(r["bold"][list(ks).index(1)]), sim_bold_best=float(r["bold"][best]),
                   sim_bold_best_k=float(ks[best]), sim_gap_scale_vs_shrink=r["max_gap_scale_vs_shrink"],
                   sim_gap_level=r["max_gap_level"])
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    ax.axhline(0.16, color=MUTED, lw=1)
    ax.plot(ks, r["bold"], color=ORANGE, lw=2)
    ax.plot(ks, r["steep"], color=AQUA, lw=2)
    ax.plot(ks, r["var_only"], color=BLUE, lw=2)
    ax.plot([ks[best]], [r["bold"][best]], "o", ms=7, color=ORANGE, mec="white", mew=1.5)
    ax.set_xscale("log")
    ax.set_xticks([0.25, 0.5, 1, 2, 4, 8, 16, 32, 64], ["0.25", "0.5", "1", "2", "4", "8", "16", "32", "64"])
    ax.minorticks_off()
    ax.set_xlim(0.22, 64)
    ax.set_ylim(0.153, 0.1665)
    ax.set_xlabel("common variance inflation factor k (every asset's variance multiplied by k)")
    ax.set_ylabel("expected RPS (lower is better)")
    ax.text(62, 0.16015, "equal-probability benchmark, 0.16", color=SECOND, va="bottom", ha="right", fontsize=8.5)
    ax.text(1.3, r["bold"][list(ks).index(1)] + 0.0012, "real signal on direction, oversold:\nk helps, best near k = %g" % ks[best],
            color=INK, fontsize=8.5, va="bottom")
    ax.text(4.3, r["steep"][0] + 0.00025, "no view on direction, differences in\nvariance between assets exaggerated: flat",
            color=INK, fontsize=8.5, va="bottom")
    ax.text(0.235, r["var_only"][0] - 0.00035, "no view on direction, variances right\n(or all halved, or all doubled): flat",
            color=INK, fontsize=8.5, va="top")
    fig.savefig(FIG / "lit_inflation_factor.png")
    plt.close(fig)


def fig_losses(numbers):
    a = np.exp(np.linspace(np.log(0.25), np.log(4), 301))                    # forecast / true variance
    qlike, mse, logmse = 1 / a + np.log(a) - 1, (a - 1) ** 2, np.log(a) ** 2
    numbers.update(qlike_half=float(1 / 0.5 + np.log(0.5) - 1), qlike_double=float(1 / 2 + np.log(2) - 1),
                   mse_half=0.25, mse_double=1.0, logmse_half=float(np.log(2) ** 2))
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    ax.plot(a, mse, color=ORANGE, lw=2)
    ax.plot(a, logmse, color=AQUA, lw=2)
    ax.plot(a, qlike, color=BLUE, lw=2)
    ax.axvline(1, color=AXIS, lw=0.8)
    ax.set_xscale("log")
    ax.set_xticks([0.25, 0.5, 1, 2, 4], ["a quarter", "half", "exactly right", "double", "four times"])
    ax.minorticks_off()
    ax.set_xlim(0.25, 4)
    ax.set_ylim(0, 2.6)
    ax.set_xlabel("forecast variance relative to the true variance")
    ax.set_ylabel("loss (true variance = 1)")
    ax.text(2.75, 2.52, "squared error on the variance:\nan over-forecast costs more", color=INK, fontsize=8.5, va="top")
    ax.text(4.12, logmse[-1], "squared error on\nthe log variance:\nsymmetric", color=INK, fontsize=8.5, va="center", clip_on=False)
    ax.text(4.12, qlike[-1], "QLIKE: an under-\nforecast costs more", color=INK, fontsize=8.5, va="center", clip_on=False)
    fig.savefig(FIG / "lit_loss_asymmetry.png")
    plt.close(fig)


def fig_tails(numbers):
    nu = np.arange(3, 31)
    levels = [(0.90, AQUA), (0.95, BLUE), (0.99, ORANGE)]
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    ax.plot([3, 30], [1, 1], color=MUTED, lw=1)
    for cov, colour in levels:
        ratio = stats.t.ppf(0.5 + cov / 2, nu) * np.sqrt((nu - 2) / nu) / stats.norm.ppf(0.5 + cov / 2)
        ax.plot(nu, ratio, color=colour, lw=2)
        for d in (4, 5, 8):
            numbers[f"t{d}_ratio_{int(cov * 100)}"] = float(ratio[d - 3])
            numbers[f"t{d}_half_{int(cov * 100)}"] = float(ratio[d - 3] * stats.norm.ppf(0.5 + cov / 2))
        numbers[f"gauss_half_{int(cov * 100)}"] = float(stats.norm.ppf(0.5 + cov / 2))
        # coverage of the Gaussian interval when the truth is a unit-variance t(5)
        numbers[f"t5_cov_gauss_{int(cov * 100)}"] = float(1 - 2 * stats.t.sf(stats.norm.ppf(0.5 + cov / 2) / np.sqrt(3 / 5), 5))
    numbers["raw_t5_widen_95"] = float(stats.t.ppf(0.975, 5) / stats.norm.ppf(0.975) - 1)   # t(5) not rescaled
    numbers["raw_t5_sd_excess"] = float(np.sqrt(5 / 3) - 1)
    ax.text(12, 1.098, "99% interval", color=INK, fontsize=8.5, va="bottom")
    ax.text(9, 1.026, "95% interval", color=INK, fontsize=8.5, va="bottom")
    ax.text(6.3, 0.955, "90% interval", color=INK, fontsize=8.5, va="top")
    ax.text(30.6, 1.0, "same width as\nthe Gaussian", color=SECOND, fontsize=8.5, va="center")
    ax.set_xlim(3, 35.5)
    ax.set_xticks([3, 4, 5, 8, 12, 20, 30])
    ax.set_ylim(0.8, 1.42)
    ax.set_xlabel("degrees of freedom of the Student-t (fewer = fatter tails)")
    ax.set_ylabel("interval width, Student-t / Gaussian\n(both with the same variance)")
    fig.savefig(FIG / "lit_student_t_width.png")
    plt.close(fig)


def jensen(numbers):
    for s in (0.3, 0.5, 0.7, 1.0):
        numbers[f"jensen_{s}"] = float(1 - np.exp(-s ** 2 / 2))


if __name__ == "__main__":
    numbers: dict = {}
    fig_inflation(numbers)
    fig_losses(numbers)
    fig_tails(numbers)
    jensen(numbers)
    (FIG / "lit_numbers.json").write_text(json.dumps(numbers, indent=1), encoding="utf-8")
    print(json.dumps(numbers, indent=1))
