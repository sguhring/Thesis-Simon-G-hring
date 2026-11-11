import numpy as np
import pytest

from thesis.models.adavol import adavol, project_garch


def simulate_garch(n: int, omega: float, alpha: float, beta: float, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(n)
    x = np.empty(n)
    s2 = omega / (1 - alpha - beta)
    for t in range(n):
        x[t] = np.sqrt(s2) * z[t]
        s2 = omega + alpha * x[t] ** 2 + beta * s2
    return x


def test_projection_leaves_feasible_points_alone():
    v = np.array([0.05, 0.90])
    assert np.array_equal(project_garch(v), v)
    assert np.array_equal(project_garch(np.array([-0.05, 0.80])), [0.0, 0.80])


def test_projection_is_the_closest_feasible_point():
    assert np.allclose(project_garch(np.array([0.10, 0.95])), [0.075, 0.925])
    rng = np.random.default_rng(0)
    feasible = rng.dirichlet(np.ones(4), size=2000)[:, :3]         # theta >= 0, sum <= 1
    for v in rng.normal(0.5, 0.6, size=(200, 3)):
        w = project_garch(v)
        assert (w >= 0).all() and w.sum() <= 1 + 1e-12
        assert np.linalg.norm(v - w) <= np.linalg.norm(v - feasible, axis=1).min() + 1e-12


def test_first_two_steps_match_table_1_by_hand():
    x1, x2, a, b = 0.01, 0.03, 0.05, 0.90
    fit = adavol([x1, x2], (a, b))
    # step 1: sigma2_1 = x1^2, so the gradient is zero and theta does not move
    assert np.array_equal(fit.theta[0], [a, b])
    # mean = x1/2, sample variance = x1^2/4, forecast = gamma2 + (a + b)(x1^2 - gamma2)
    assert fit.sigma2[1] == pytest.approx(x1 ** 2 * (0.25 + 0.75 * (a + b)))
    # step 2: the gradient is positive in both coordinates and AdaGrad's first move is a full step of
    # eta = 0.1, giving (-0.05, 0.80), which the projection clips to (0, 0.80)
    assert np.allclose(fit.theta[1], [0.0, 0.80], atol=1e-6)


def test_forecasts_use_only_past_observations():
    x = simulate_garch(1500, 2e-6, 0.10, 0.85, seed=1)
    later = x.copy()
    later[500:] *= 3.0
    a, b = adavol(x), adavol(later)
    assert np.array_equal(a.sigma2[:501], b.sigma2[:501])
    assert np.array_equal(a.theta[:500], b.theta[:500])
    assert not np.allclose(a.sigma2[501:], b.sigma2[501:])


def test_scaling_the_returns_scales_the_variance_and_nothing_else():
    x = simulate_garch(1500, 2e-6, 0.10, 0.85, seed=2)
    a, b = adavol(x), adavol(100.0 * x)
    assert np.allclose(a.theta, b.theta)
    assert np.allclose(1e4 * a.sigma2, b.sigma2)


def test_recovers_garch_parameters_on_simulated_data():
    # the setting of WW Figure 7: true (alpha, beta) = (0.2, 0.7), start at (0.1, 0.8), n = 20,000
    x = simulate_garch(20_000, 1e-5, 0.2, 0.7, seed=3)
    fit = adavol(x, (0.1, 0.8))
    assert np.allclose(fit.theta[-5000:].mean(axis=0), [0.2, 0.7], atol=0.05)
    assert fit.gamma2[-1] == pytest.approx(x.var(), rel=1e-3)
    assert ((fit.theta >= 0).all() and (fit.theta.sum(axis=1) <= 1 + 1e-12).all())


def test_pure_arch_runs_without_beta():
    x = simulate_garch(3000, 5e-5, 0.4, 0.0, seed=4)
    fit = adavol(x, (0.2,), p=1, q=0)
    assert fit.theta.shape == (3000, 1) and np.isfinite(fit.sigma2).all()


def test_leading_zero_return_is_rejected():
    with pytest.raises(ValueError):
        adavol([0.0, 0.01, -0.02])


def test_bad_inputs_are_rejected():
    with pytest.raises(ValueError):
        adavol([])                                  # no observations
    with pytest.raises(ValueError):
        adavol(np.zeros((5, 2)))                    # not one-dimensional
    with pytest.raises(ValueError):
        adavol([0.01, 0.02], (0.5, 0.9))            # sum(theta0) > 1
    with pytest.raises(ValueError):
        adavol([0.01, 0.02], (-0.1, 0.9))           # negative coordinate


def test_interior_zero_returns_stay_finite():
    x = simulate_garch(500, 2e-6, 0.10, 0.85, seed=5)
    x[100] = 0.0
    fit = adavol(x)
    assert np.isfinite(fit.sigma2).all() and np.isfinite(fit.theta).all()


def test_step_two_gradient_carries_no_derivative_of_the_constant_start():
    # sigma2_1 = x1^2 is a constant, so the gradient recursion starts from a zero lag:
    # ds_2 = (x1^2 - gamma2_2) in both coordinates, with no beta * (fabricated ds_1) term
    a, b, eta, eps = 0.05, 0.90, 0.1, 1e-8
    x1 = 0.01
    x2 = x1 * np.sqrt(0.9625 * 1.001)               # forecast close to x2^2: a small gradient
    fit = adavol([x1, x2], (a, b), eta=eta, eps=eps)
    g2_1 = x1 ** 2 / 4                              # sample variance after x1 (mean x1 / 2)
    sig2 = g2_1 + (a + b) * (x1 ** 2 - g2_1)        # forecast for x2
    mu2 = (2 * (x1 / 2) + x2) / 3
    g2_2 = (g2_1 + (x2 - mu2) ** 2) / 2
    ds = np.full(2, x1 ** 2 - g2_2)
    g = ds * (sig2 - x2 ** 2) / (2 * sig2 ** 2)
    expected = project_garch(np.array([a, b]) - eta * g / np.sqrt(eps + g * g))
    assert np.allclose(fit.theta[1], expected, atol=1e-14)
