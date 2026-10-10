"""Paired bootstrap, fast DeLong (Sun & Xu 2014), Holm correction, cross-fitted Platt scaling."""
from __future__ import annotations

import math

import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm, rankdata

from . import metrics as M


# ------------------------------------------------------------------------------------------ DeLong
def _fast_delong(preds_sorted: np.ndarray, m: int):
    """preds_sorted: (k, n) with the m positives first. Returns (aucs, covariance)."""
    n = preds_sorted.shape[1] - m
    pos, neg = preds_sorted[:, :m], preds_sorted[:, m:]
    k = preds_sorted.shape[0]
    tx = np.vstack([rankdata(pos[r]) for r in range(k)])
    ty = np.vstack([rankdata(neg[r]) for r in range(k)])
    tz = np.vstack([rankdata(preds_sorted[r]) for r in range(k)])
    aucs = tz[:, :m].sum(axis=1) / m / n - (m + 1.0) / 2.0 / n
    v01 = (tz[:, :m] - tx) / n
    v10 = 1.0 - (tz[:, m:] - ty) / m
    sx = np.atleast_2d(np.cov(v01))
    sy = np.atleast_2d(np.cov(v10))
    return aucs, sx / m + sy / n


def delong_paired(y, s1, s2) -> dict:
    """Two-sided paired DeLong test of AUROC(s1) - AUROC(s2)."""
    y = np.asarray(y)
    order = np.concatenate([np.flatnonzero(y == 1), np.flatnonzero(y == 0)])
    m = int((y == 1).sum())
    if m == 0 or m == len(y):
        return {"auc1": math.nan, "auc2": math.nan, "diff": math.nan, "se": math.nan, "z": math.nan, "p": math.nan}
    preds = np.vstack([np.asarray(s1, float)[order], np.asarray(s2, float)[order]])
    aucs, cov = _fast_delong(preds, m)
    var = cov[0, 0] + cov[1, 1] - 2 * cov[0, 1]
    diff = aucs[0] - aucs[1]
    if var <= 1e-15:
        z, p = 0.0 if abs(diff) < 1e-12 else math.copysign(math.inf, diff), 1.0 if abs(diff) < 1e-12 else 0.0
        se = 0.0
    else:
        se = math.sqrt(var)
        z = diff / se
        p = 2 * norm.sf(abs(z))
    return {"auc1": float(aucs[0]), "auc2": float(aucs[1]), "diff": float(diff), "se": float(se),
            "z": float(z), "p": float(p)}


# -------------------------------------------------------------------------------------------- Holm
def holm(pvals) -> list[float]:
    p = np.asarray(pvals, float)
    out = np.full(len(p), np.nan)
    ok = ~np.isnan(p)
    idx = np.flatnonzero(ok)
    if len(idx) == 0:
        return out.tolist()
    order = idx[np.argsort(p[idx], kind="stable")]
    m = len(order)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p[i]))
        out[i] = running
    return out.tolist()


# --------------------------------------------------------------------------------------- bootstrap
def bootstrap_indices(n: int, n_boot: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).integers(0, n, size=(n_boot, n))


def paired_bootstrap(y, signals: dict, n_boot: int, seed: int, n_bins: int, coverage: float) -> dict:
    """Bootstrap replicates of every metric for every signal, sharing indices. Returns
    {"accuracy": array(B), signal: {metric: array(B)}}."""
    y = np.asarray(y, float)
    idx = bootstrap_indices(len(y), n_boot, seed)
    out = {"accuracy": np.empty(n_boot)}
    for s in signals:
        out[s] = {m: np.empty(n_boot) for m in M.METRIC_NAMES}
    for b in range(n_boot):
        ib = idx[b]
        yb = y[ib]
        out["accuracy"][b] = yb.mean()
        for s, conf in signals.items():
            r = M.signal_metrics(np.asarray(conf, float)[ib], yb, n_bins, coverage)
            for m in M.METRIC_NAMES:
                out[s][m][b] = r[m]
    return out


def percentile_ci(x, alpha: float = 0.05) -> list:
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    if len(x) == 0:
        return [None, None]
    return [float(np.percentile(x, 100 * alpha / 2)), float(np.percentile(x, 100 * (1 - alpha / 2)))]


# ------------------------------------------------------------------------------------------- Platt
def platt_fit(s, y) -> tuple[float, float]:
    s, y = np.asarray(s, float), np.asarray(y, float)

    def nll(w):
        z = w[0] * s + w[1]
        return float(np.sum(np.logaddexp(0, z) - y * z))

    def grad(w):
        p = 1 / (1 + np.exp(-(w[0] * s + w[1])))
        return np.array([np.sum((p - y) * s), np.sum(p - y)])

    res = minimize(nll, np.array([1.0, 0.0]), jac=grad, method="BFGS")
    return float(res.x[0]), float(res.x[1])


def crossfit_platt(s, y, folds: int, seed: int) -> np.ndarray:
    s, y = np.asarray(s, float), np.asarray(y, float)
    perm = np.random.default_rng(seed).permutation(len(s))
    out = np.empty(len(s))
    for test in np.array_split(perm, folds):
        train = np.setdiff1d(perm, test)
        if len(np.unique(y[train])) < 2:
            out[test] = y[train].mean()
            continue
        a, b = platt_fit(s[train], y[train])
        out[test] = 1 / (1 + np.exp(-(a * s[test] + b)))
    return out
