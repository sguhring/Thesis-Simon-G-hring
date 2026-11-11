"""AdaVol: a GARCH(p, q) whose parameters are updated after every observation.

Written from the published equations, not from the authors' notebook (github.com/nicklaswerge/AdaVol,
GPL-3.0):

[WW] Werge & Wintenberger (2022), AdaVol: an adaptive recursive volatility prediction method,
     Econometrics and Statistics 23, 19-35, arXiv 2006.02077. The algorithm is their Table 1.
[VW] de Vilmarest & Werge (2025), An adaptive volatility method for probabilistic forecasting and its
     application to the M6 financial forecasting competition, IJF 41(4), arXiv 2303.01855. Algorithm 1
     is the same recursion.

Model (WW eq. 3.5): a GARCH(p, q) written around its long-run variance gamma2,

    sigma2_t - gamma2 = sum_i alpha_i (x_{t-i}^2 - gamma2) + sum_j beta_j (sigma2_{t-j} - gamma2)

gamma2 is the running sample variance (variance targeting), so only theta = (alpha_1..alpha_p,
beta_1..beta_q) is estimated. After each observation theta takes one AdaGrad step on the Gaussian
quasi-likelihood loss  l_t = (x_t^2 / sigma2_t + log sigma2_t) / 2  (WW eq. 2.3) and is projected back
onto {theta >= 0, sum(theta) <= 1} (WW eq. 3.3). One pass over the data, no re-estimation.

The authors' notebook departs from Table 1 in three places. Each one is an argument of `adavol`, so
notebooks/adavol_vs_authors.py can reproduce the notebook exactly and measure what each one changes:

x0             The notebook spends its first observation on initialisation: the running mean starts
               there and the first variance is its square. Table 1 starts the mean at 0 and sets the
               first variance to x_1^2.
forecast_with  The notebook forecasts sigma2_{t+1} with theta_{t-1}. Table 1 and VW Algorithm 1 use the
               estimate that has just been updated, theta_t.
project        The notebook's projection (a widely circulated gist) divides the excess by one less than
               the number of positive coordinates, an off-by-one against Duchi et al. (2008), so a step
               that leaves the set lands inside it, not on the boundary sum(theta) = 1 where
               `project_garch` puts it.

Two quirks of Table 1 are kept deliberately, and the authors' notebook has them too: the mean update
divides by t + 1, so the zero it starts from is counted like an observation forever; and the gradient
uses the gamma2 that has just been updated with x_t, although the forecast it differentiates was built
from the previous gamma2 (Table 1 updates gamma2 before the gradient and writes gamma2 in theta_t
without a time index).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


@dataclass(frozen=True)
class AdaVolFit:
    """Output of `adavol` for n observations. Index t belongs to observation x[t]."""
    theta: np.ndarray    # (n, p+q)  estimate after x[t] has been seen
    sigma2: np.ndarray   # (n+1,)    sigma2[t] = variance forecast for x[t], made before seeing it.
    #                                sigma2[0] is the starting value; sigma2[n] is for the next, unseen day
    gamma2: np.ndarray   # (n,)      running sample variance, the long-run level of the recursion


def project_garch(v: np.ndarray) -> np.ndarray:
    """Closest point to v in {theta >= 0, sum(theta) <= 1} (Duchi et al. 2008, Figure 1)."""
    w = np.maximum(v, 0.0)
    if w.sum() <= 1.0:
        return w
    u = np.sort(w)[::-1]
    excess = np.cumsum(u) - 1.0
    k = np.arange(1, len(u) + 1)
    rho = k[u - excess / k > 0][-1]          # number of coordinates that stay positive
    return np.maximum(w - excess[rho - 1] / rho, 0.0)


def adavol(x, theta0=(0.05, 0.90), p: int = 1, q: int = 1, eta: float = 0.1, eps: float = 1e-8, *,
           x0: float | None = None, forecast_with: str = "updated",
           project: Callable[[np.ndarray], np.ndarray] = project_garch) -> AdaVolFit:
    """Run AdaVol over the (demeaned) returns x. Defaults follow WW Table 1; theta0 is WW eq. 4.8.

    x0, forecast_with and project switch on the authors' notebook behaviour (see the module docstring).
    """
    x = np.asarray(x, dtype=float)
    if x.ndim != 1 or len(x) == 0:
        raise ValueError("x must be a one-dimensional array with at least one return")
    theta = np.array(theta0, dtype=float)
    if p < 1 or q < 0 or theta.shape != (p + q,):
        raise ValueError("need p >= 1, q >= 0 and one starting value per parameter")
    if (theta < 0).any() or theta.sum() > 1:
        raise ValueError("theta0 must lie in the feasible set {theta >= 0, sum(theta) <= 1}")
    if forecast_with not in ("updated", "previous"):
        raise ValueError("forecast_with must be 'updated' or 'previous'")
    n = len(x)
    out = AdaVolFit(np.empty((n, p + q)), np.empty(n + 1), np.empty(n))

    # Table 1 initialisation. With x0 the mean and the first variance start from that observation.
    mu = 0.0 if x0 is None else float(x0)
    sig = float(x[0] if x0 is None else x0) ** 2
    if not sig > 0:
        raise ValueError("the starting variance is zero: drop leading zero returns first")
    gamma2 = 0.0
    G = np.full(p + q, eps)                 # accumulated squared gradients (AdaGrad)
    x2_lags = np.zeros(p)                   # x_{t-1}^2 .. x_{t-p}^2
    if x0 is not None:
        x2_lags[0] = sig
    s2_lags = np.zeros(q)                   # sigma2_{t-1} .. sigma2_{t-q}
    ds_lags = np.zeros((q, p + q))          # their gradients with respect to theta

    for k in range(n):
        t = k + 1
        out.sigma2[k] = sig
        mu = (t * mu + x[k]) / (t + 1)
        gamma2 = ((t - 1) * gamma2 + (x[k] - mu) ** 2) / t

        # gradient of l_t at the previous estimate (WW eq. 2.7 and the recursion below eq. 2.8).
        # At t = 1 the variance is the constant x_1^2 (Table 1), so its derivative is zero; the
        # recursion formula would fabricate one from the empty lags. The notebook applies the
        # formula from the start, which x0 keeps.
        if k == 0 and x0 is None:
            ds = np.zeros(p + q)
        else:
            ds = np.concatenate((x2_lags, s2_lags)) - gamma2 + theta[p:] @ ds_lags
        g = ds * (sig - x[k] ** 2) / (2.0 * sig ** 2)
        G += g * g
        new = project(theta - eta * g / np.sqrt(G))

        # variance forecast for the next observation (WW eq. 3.5). Table 1 prints the lags as t-i and
        # t-j, one step too far back for a forecast of t+1; eq. 3.5 is followed here.
        x2_lags = np.r_[x[k] ** 2, x2_lags][:p]
        s2_lags = np.r_[sig, s2_lags][:q]
        ds_lags = np.vstack((ds, ds_lags))[:q]
        th = new if forecast_with == "updated" else theta
        sig = gamma2 + th[:p] @ (x2_lags - gamma2) + th[p:] @ (s2_lags - gamma2)
        if not sig > 0:
            raise ValueError(f"the variance forecast after observation {k} is not positive "
                             "(a zero return with theta on the boundary sum(theta) = 1): "
                             "drop zero returns first")

        theta = new
        out.theta[k] = theta
        out.gamma2[k] = gamma2
    out.sigma2[n] = sig
    return out
