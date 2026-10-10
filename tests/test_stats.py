import numpy as np
import pytest
from scipy.stats import norm

from medqa_conf import metrics as M
from medqa_conf import stats as S


def test_delong_identical_signals():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 200)
    s = rng.random(200)
    r = S.delong_paired(y, s, s)
    assert r["z"] == 0 and r["p"] == 1


def test_delong_aucs_match_mann_whitney():
    rng = np.random.default_rng(1)
    y = rng.integers(0, 2, 150)
    a = y + rng.normal(0, 1, 150)
    b = np.round(y * 0.5 + rng.normal(0, 1, 150), 1)  # with ties
    r = S.delong_paired(y, a, b)
    assert r["auc1"] == pytest.approx(M.auroc(a, y), abs=1e-12)
    assert r["auc2"] == pytest.approx(M.auroc(b, y), abs=1e-12)


def test_delong_vs_bootstrap_pvalue():
    rng = np.random.default_rng(7)
    n = 400
    y = rng.integers(0, 2, n)
    a = y * 1.0 + rng.normal(0, 1, n)
    b = y * 0.7 + rng.normal(0, 1, n) + 0.3 * (a - y)
    r = S.delong_paired(y, a, b)
    idx = S.bootstrap_indices(n, 2000, 11)
    diffs = np.array([M.auroc(a[i], y[i]) - M.auroc(b[i], y[i]) for i in idx])
    p_boot = 2 * norm.sf(abs(diffs.mean() / diffs.std(ddof=1)))
    assert abs(r["diff"] - diffs.mean()) < 0.01
    assert r["se"] == pytest.approx(diffs.std(ddof=1), rel=0.15)
    assert abs(r["p"] - p_boot) < 0.05


def test_holm():
    adj = S.holm([0.01, 0.04, 0.03])
    assert adj == pytest.approx([0.03, 0.06, 0.06])
    adj = S.holm([0.5, float("nan"), 0.01])
    assert adj[0] == pytest.approx(0.5) and np.isnan(adj[1]) and adj[2] == pytest.approx(0.02)
    assert S.holm([0.9, 0.8]) == pytest.approx([1.0, 1.0])  # 2 * 0.8 capped at 1, monotone
    assert S.holm([0.2, 0.3]) == pytest.approx([0.4, 0.4])


def test_paired_bootstrap_shares_indices_and_is_deterministic():
    rng = np.random.default_rng(2)
    y = rng.integers(0, 2, 50)
    s = rng.random(50)
    b1 = S.paired_bootstrap(y, {"x": s, "y": s}, 100, 5, 15, 0.8)
    b2 = S.paired_bootstrap(y, {"x": s, "y": s}, 100, 5, 15, 0.8)
    assert np.array_equal(b1["x"]["auroc"], b1["y"]["auroc"], equal_nan=True)  # same indices
    assert np.array_equal(b1["x"]["ece"], b2["x"]["ece"])  # same seed
    ci = S.percentile_ci(b1["x"]["auroc"])
    assert ci[0] <= M.auroc(s, y) <= ci[1]


def test_platt_crossfit_improves_ece_for_miscalibrated_signal():
    rng = np.random.default_rng(4)
    p_true = rng.random(1000)
    y = (rng.random(1000) < p_true).astype(int)
    s = 0.5 + 0.5 * p_true  # overconfident monotone transform
    cal = S.crossfit_platt(s, y, 5, 2026)
    assert M.ece(cal, y) < M.ece(s, y)
    assert M.auroc(cal, y) == pytest.approx(M.auroc(s, y), abs=0.02)
