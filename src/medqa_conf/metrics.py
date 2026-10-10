"""Metrics (PREREGISTRATION.md section 7). All functions take numpy arrays: conf in [0,1], y in {0,1}."""
from __future__ import annotations

import math

import numpy as np
from scipy.stats import norm, rankdata


def accuracy(y) -> float:
    return float(np.mean(y))


def wilson_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    if n == 0:
        return (math.nan, math.nan)
    z = norm.ppf(1 - alpha / 2)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (c - h, c + h)


def auroc(conf, y) -> float:
    """Mann-Whitney AUROC, ties count 1/2 (== sklearn.metrics.roc_auc_score)."""
    conf, y = np.asarray(conf, float), np.asarray(y)
    n1 = int(y.sum())
    n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return math.nan
    r = rankdata(conf)  # average ranks for ties
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def equal_width_edges(n_bins: int) -> np.ndarray:
    # i / n (true division) so that edges like 12/15 equal 0.8 == 4/5 exactly (conf_agree takes k/5 values)
    return np.array([i / n_bins for i in range(n_bins + 1)])


def bin_index(conf, edges) -> np.ndarray:
    """Left-closed bins [e_i, e_{i+1}); the last bin also includes the right edge."""
    conf, edges = np.asarray(conf, float), np.asarray(edges, float)
    if np.any(conf < edges[0]) or np.any(conf > edges[-1]):
        raise ValueError("confidence outside the bin edges")
    idx = np.searchsorted(edges, conf, side="right") - 1
    return np.minimum(idx, len(edges) - 2)


def ece(conf, y, n_bins: int = 15, edges=None) -> float:
    conf, y = np.asarray(conf, float), np.asarray(y, float)
    edges = equal_width_edges(n_bins) if edges is None else np.asarray(edges, float)
    idx = bin_index(conf, edges)
    nb = len(edges) - 1
    cnt = np.bincount(idx, minlength=nb)
    sc = np.bincount(idx, weights=conf, minlength=nb)
    sy = np.bincount(idx, weights=y, minlength=nb)
    m = cnt > 0
    return float(np.sum(np.abs(sy[m] - sc[m])) / len(conf))


def reliability_bins(conf, y, n_bins: int = 15, edges=None) -> dict:
    conf, y = np.asarray(conf, float), np.asarray(y, float)
    edges = equal_width_edges(n_bins) if edges is None else np.asarray(edges, float)
    idx = bin_index(conf, edges)
    nb = len(edges) - 1
    cnt = np.bincount(idx, minlength=nb)
    with np.errstate(invalid="ignore", divide="ignore"):
        mc = np.bincount(idx, weights=conf, minlength=nb) / cnt
        acc = np.bincount(idx, weights=y, minlength=nb) / cnt
    return {"edges": edges.tolist(), "count": cnt.tolist(), "mean_conf": mc.tolist(), "accuracy": acc.tolist()}


def adaptive_ece(conf, y, n_bins: int = 15) -> float:
    """Equal-mass bins: stable sort by confidence, split into n_bins contiguous groups (np.array_split)."""
    conf, y = np.asarray(conf, float), np.asarray(y, float)
    order = np.argsort(conf, kind="stable")
    tot = 0.0
    for g in np.array_split(order, n_bins):
        if len(g):
            tot += abs(y[g].sum() - conf[g].sum())
    return float(tot / len(conf))


def brier(conf, y) -> float:
    conf, y = np.asarray(conf, float), np.asarray(y, float)
    return float(np.mean((conf - y) ** 2))


def overconfidence_gap(conf, y) -> float:
    return float(np.mean(conf) - np.mean(y))


def expected_correct_curve(conf, y) -> np.ndarray:
    """E[#correct among the top-k] for k = 1..N under random tie-breaking (exact)."""
    conf, y = np.asarray(conf, float), np.asarray(y, float)
    n = len(conf)
    order = np.argsort(-conf, kind="stable")
    cs, ys = conf[order], y[order]
    new_group = np.ones(n, bool)
    new_group[1:] = cs[1:] != cs[:-1]
    gid = np.cumsum(new_group) - 1
    starts = np.flatnonzero(new_group)
    sizes = np.diff(np.append(starts, n))
    gcorr = np.bincount(gid, weights=ys)
    corr_before = np.concatenate([[0.0], np.cumsum(gcorr)[:-1]])
    k = np.arange(1, n + 1)
    g = gid[k - 1]
    return corr_before[g] + (k - starts[g]) * gcorr[g] / sizes[g]


def coverage_k(n: int, coverage: float) -> int:
    return int(math.floor(round(coverage * n, 9)))


def selective_accuracy(conf, y, coverage: float = 0.8) -> float:
    n = len(conf)
    k = coverage_k(n, coverage)
    if k == 0:
        return math.nan
    return float(expected_correct_curve(conf, y)[k - 1] / k)


def oracle_selective_accuracy(y, coverage: float = 0.8) -> float:
    k = coverage_k(len(y), coverage)
    return float(min(int(np.sum(y)), k) / k)


def risk_coverage(conf, y) -> tuple[np.ndarray, np.ndarray]:
    n = len(conf)
    k = np.arange(1, n + 1)
    return k / n, 1.0 - expected_correct_curve(conf, y) / k


def aurc(conf, y) -> float:
    return float(np.mean(risk_coverage(conf, y)[1]))


def signal_metrics(conf, y, n_bins: int = 15, coverage: float = 0.8) -> dict:
    n = len(conf)
    curve = expected_correct_curve(conf, y)  # shared by selective accuracy and AURC
    k = coverage_k(n, coverage)
    return {
        "auroc": auroc(conf, y),
        "ece": ece(conf, y, n_bins),
        "adaptive_ece": adaptive_ece(conf, y, n_bins),
        "brier": brier(conf, y),
        "mean_conf": float(np.mean(conf)),
        "overconfidence_gap": overconfidence_gap(conf, y),
        "selective_acc": float(curve[k - 1] / k) if k else math.nan,
        "aurc": float(np.mean(1.0 - curve / np.arange(1, n + 1))),
    }


METRIC_NAMES = ("auroc", "ece", "adaptive_ece", "brier", "mean_conf", "overconfidence_gap",
                "selective_acc", "aurc")
