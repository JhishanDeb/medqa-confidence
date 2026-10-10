import itertools
import math

import numpy as np
import pytest
from sklearn.metrics import roc_auc_score

from medqa_conf import metrics as M

CORRECT = np.array([1, 1, 1, 1, 0, 1, 1, 0, 1, 0])
STATED = np.array([.95, .95, .90, .90, .90, .90, .80, .90, .80, .85])
PROB = np.array([.95, .90, .85, .80, .75, .70, .60, .55, .50, .40])
AGREE = np.array([1.0, 1.0, 1.0, .8, .6, 1.0, .8, .4, .6, .4])
EDGES = [0.4, 0.6, 0.8, 1.0]


@pytest.mark.parametrize("conf,auc,sel,ece", [
    (STATED, 12 / 21, 0.625, 0.185),
    (PROB, 17 / 21, 0.75, 0.100),
    (AGREE, 20.5 / 21, 0.875, 0.140),
])
def test_toy_example(conf, auc, sel, ece):
    assert M.auroc(conf, CORRECT) == pytest.approx(auc, abs=1e-12)
    assert M.coverage_k(10, 0.8) == 8
    assert M.selective_accuracy(conf, CORRECT, 0.8) == pytest.approx(sel, abs=1e-12)
    assert M.ece(conf, CORRECT, edges=EDGES) == pytest.approx(ece, abs=1e-12)


def test_toy_accuracy_and_mean():
    assert M.accuracy(CORRECT) == pytest.approx(0.70)
    assert float(np.mean(STATED)) == pytest.approx(0.885)
    assert M.overconfidence_gap(STATED, CORRECT) == pytest.approx(0.185)


def test_auroc_matches_sklearn_heavy_ties():
    rng = np.random.default_rng(0)
    for _ in range(1000):
        n = int(rng.integers(2, 60))
        y = rng.integers(0, 2, n)
        if y.min() == y.max():
            y[0] = 1 - y[0]
        s = rng.integers(0, int(rng.integers(1, 6)) + 1, n) / 5.0  # few distinct values -> heavy ties
        assert M.auroc(s, y) == pytest.approx(roc_auc_score(y, s), abs=1e-12)


def test_auroc_single_class_nan():
    assert math.isnan(M.auroc([0.1, 0.2], [1, 1]))


def _brute_selective(conf, y, k):
    """Average top-k accuracy over all orderings of tied groups."""
    conf, y = np.asarray(conf), np.asarray(y)
    vals = sorted(set(conf), reverse=True)
    groups = [list(np.flatnonzero(conf == v)) for v in vals]
    accs = []
    for perms in itertools.product(*[list(itertools.permutations(g)) for g in groups]):
        order = [i for p in perms for i in p]
        accs.append(y[order[:k]].mean())
    return float(np.mean(accs))


def test_selective_ties_straddling_cutoff_bruteforce():
    conf = np.array([.9, .8, .8, .8, .8, .5, .5, .3])
    y = np.array([1, 1, 0, 0, 1, 1, 0, 0])
    for cov in (0.25, 0.5, 0.625, 0.75):
        k = M.coverage_k(len(y), cov)
        assert M.selective_accuracy(conf, y, cov) == pytest.approx(_brute_selective(conf, y, k), abs=1e-12)
    # explicit: k=3 -> 1 above + 2 of the 4 tied (acc 0.5) -> (1 + 1)/3
    assert M.selective_accuracy(conf, y, 3 / 8) == pytest.approx(2 / 3)


def test_expected_correct_curve_matches_bruteforce_every_k():
    rng = np.random.default_rng(3)
    conf = rng.integers(0, 3, 7) / 2
    y = rng.integers(0, 2, 7)
    curve = M.expected_correct_curve(conf, y)
    for k in range(1, 8):
        assert curve[k - 1] / k == pytest.approx(_brute_selective(conf, y, k), abs=1e-12)


def test_oracle_and_references():
    assert M.oracle_selective_accuracy(CORRECT, 0.8) == 7 / 8
    assert M.coverage_k(1273, 0.8) == 1018


def test_ece_bins_left_closed_last_includes_one():
    edges = M.equal_width_edges(15)
    assert edges[12] == 0.8 == 4 / 5 and edges[3] == 0.2
    idx = M.bin_index([0.0, 0.2, 0.8, 1.0, 0.7999], edges)
    assert list(idx) == [0, 3, 12, 14, 11]
    with pytest.raises(ValueError):
        M.bin_index([1.01], edges)


def test_ece_default_15_bins_perfect_calibration():
    conf = np.array([1.0] * 4 + [0.0] * 4)
    y = np.array([1] * 4 + [0] * 4)
    assert M.ece(conf, y) == 0.0
    assert M.adaptive_ece(conf, y, 2) == 0.0


def test_adaptive_ece_and_brier():
    conf = np.array([0.1, 0.2, 0.8, 0.9])
    y = np.array([0, 1, 1, 1])
    # 2 equal-mass bins: {0.1,0.2} acc .5 conf .15 ; {0.8,0.9} acc 1 conf .85
    assert M.adaptive_ece(conf, y, 2) == pytest.approx((abs(1 - 0.3) + abs(2 - 1.7)) / 4)
    assert M.brier(conf, y) == pytest.approx(np.mean((conf - y) ** 2))


def test_aurc_tie_aware():
    conf = np.array([0.5, 0.5])
    y = np.array([1, 0])
    # k=1: expected risk 0.5 ; k=2: 0.5
    assert M.aurc(conf, y) == pytest.approx(0.5)
    assert M.aurc(np.array([0.9, 0.1]), y) == pytest.approx((0 + 0.5) / 2)


def test_wilson():
    lo, hi = M.wilson_ci(7, 10)
    assert lo == pytest.approx(0.3968, abs=1e-3) and hi == pytest.approx(0.8922, abs=1e-3)
