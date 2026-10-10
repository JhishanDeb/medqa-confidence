"""Analysis from per_question.csv only: summary.json, results_table.md, figures; plus multi-model combine.

    python -m medqa_conf.report --from-csv outputs/<slug>/per_question.csv [--out DIR]
    python -m medqa_conf.report --combine DIR_OR_CSV [DIR_OR_CSV ...] --out DIR
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from . import metrics as M
from . import stats as S

SIGNALS = ("stated", "prob", "agree")
SIGNAL_COLS = {"stated": "conf_stated", "prob": "conf_prob", "agree": "conf_agree"}
PAIRS = (("stated", "prob"), ("stated", "agree"), ("prob", "agree"))
SETTINGS = ("cot", "direct")
SETTING_SEED_OFFSET = {"cot": 0, "direct": 1}


def default_config():
    try:
        from config import Config
    except ImportError:
        root = Path(__file__).resolve().parents[2]
        if (root / "config.py").exists():
            sys.path.insert(0, str(root))
        from config import Config
    return Config()


def analysis_params(cfg) -> dict:
    from config import ANALYSIS_KEYS
    return {k: getattr(cfg, k) for k in ANALYSIS_KEYS}


def read_csv(path) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"sample_answers": str, "answer": str, "gold": str, "majority_answer": str,
                                    "answer_parsed": str, "answer_parse_method": str, "meta_info": str,
                                    "qhash": str, "model": str, "setting": str},
                       keep_default_na=False, na_values=[""])


def _pair_key(a, b):
    return f"{a}_vs_{b}"


def _val_ci(v, boot, alpha):
    return {"value": v, "ci": S.percentile_ci(boot, alpha)}


# --------------------------------------------------------------------------------------- core block
def analyze_block(y, signals: dict, ap: dict, seed: int) -> dict:
    """Point estimates, bootstrap CIs, pairwise differences and DeLong for one set of rows."""
    y = np.asarray(y, int)
    n, alpha = len(y), ap["alpha"]
    if n == 0:
        return _empty_block(signals)
    boot = S.paired_bootstrap(y, signals, ap["n_boot"], seed, ap["n_bins"], ap["coverage"])
    acc = M.accuracy(y)
    out = {
        "n": n,
        "accuracy": {"value": acc, "wilson_ci": list(M.wilson_ci(int(y.sum()), n, alpha)),
                     "bootstrap_ci": S.percentile_ci(boot["accuracy"], alpha)},
        "references": {"k": M.coverage_k(n, ap["coverage"]), "random_selective_acc": acc,
                       "oracle_selective_acc": M.oracle_selective_accuracy(y, ap["coverage"])},
        "signals": {}, "pairs": {},
    }
    point = {}
    for s, conf in signals.items():
        point[s] = M.signal_metrics(conf, y, ap["n_bins"], ap["coverage"])
        vals = np.asarray(conf, float)
        uniq, cnt = np.unique(vals, return_counts=True)
        out["signals"][s] = {m: _val_ci(point[s][m], boot[s][m], alpha) for m in M.METRIC_NAMES}
        out["signals"][s]["frac_tied"] = float(cnt[cnt > 1].sum() / n)
        out["signals"][s]["n_unique"] = int(len(uniq))
    names = list(signals)
    pairs = [(a, b) for a, b in PAIRS if a in names and b in names]
    for a, b in pairs:
        d = {m: _val_ci(point[a][m] - point[b][m], boot[a][m] - boot[b][m], alpha) for m in M.METRIC_NAMES}
        d["delong"] = S.delong_paired(y, signals[a], signals[b])
        out["pairs"][_pair_key(a, b)] = d
    p_holm = S.holm([out["pairs"][_pair_key(a, b)]["delong"]["p"] for a, b in pairs])
    for (a, b), ph in zip(pairs, p_holm):
        pr = out["pairs"][_pair_key(a, b)]
        pr["p_holm_within_model"] = ph
        pr["supported_within_model"] = _supported(ph, pr["auroc"]["ci"], alpha)
    return out


def _empty_block(signals) -> dict:
    """Same structure as analyze_block, all values missing (no usable rows)."""
    na = {"value": math.nan, "ci": [None, None]}
    names = list(signals)
    out = {"n": 0, "accuracy": {"value": math.nan, "wilson_ci": [None, None], "bootstrap_ci": [None, None]},
           "references": {"k": 0, "random_selective_acc": math.nan, "oracle_selective_acc": math.nan},
           "signals": {s: dict({m: dict(na) for m in M.METRIC_NAMES}, frac_tied=math.nan, n_unique=0) for s in names},
           "pairs": {}}
    for a, b in PAIRS:
        if a in names and b in names:
            out["pairs"][_pair_key(a, b)] = dict(
                {m: dict(na) for m in M.METRIC_NAMES},
                delong={"auc1": math.nan, "auc2": math.nan, "diff": math.nan, "se": math.nan, "z": math.nan,
                        "p": math.nan}, p_holm_within_model=math.nan, supported_within_model=False)
    return out


def _supported(p_holm, ci, alpha):
    if p_holm is None or (isinstance(p_holm, float) and math.isnan(p_holm)) or ci[0] is None:
        return False
    return bool(p_holm < alpha and (ci[0] > 0 or ci[1] < 0))


def _direction(d):
    if d is None or math.isnan(d):
        return "NA"
    return "prob>agree" if d > 0 else ("agree>prob" if d < 0 else "equal")


def hypotheses(block: dict, holm_key: str = "p_holm_within_model", alpha: float = 0.05) -> dict:
    P = block["pairs"]

    def sup(pair, sign=None):
        pr = P[pair]
        ok = _supported(pr[holm_key], pr["auroc"]["ci"], alpha)
        if sign is not None:
            ok = ok and np.sign(pr["auroc"]["value"]) == sign
        return bool(ok)

    st = block["signals"]["stated"]
    gap_lo = st["overconfidence_gap"]["ci"][0]
    e1, e2 = P["stated_vs_prob"]["ece"]["ci"][0], P["stated_vs_agree"]["ece"]["ci"][0]
    return {
        "H1": {"stated_below_prob": sup("stated_vs_prob", -1), "stated_below_agree": sup("stated_vs_agree", -1),
               "supported": sup("stated_vs_prob", -1) and sup("stated_vs_agree", -1)},
        "H2": {"overconfident": bool(gap_lo is not None and gap_lo > 0),
               "ece_above_prob": bool(e1 is not None and e1 > 0), "ece_above_agree": bool(e2 is not None and e2 > 0),
               "supported": bool(gap_lo is not None and gap_lo > 0 and e1 is not None and e1 > 0
                                 and e2 is not None and e2 > 0)},
        "H3": {"prob_vs_agree_differ": sup("prob_vs_agree"), "supported": sup("prob_vs_agree"),
               "direction": _direction(P["prob_vs_agree"]["auroc"]["value"])},
    }


# ---------------------------------------------------------------------------------------- validity
def validity(df_model: pd.DataFrame, setting: str, ap: dict) -> dict:
    cot = df_model[df_model.setting == "cot"]
    ds = df_model[df_model.setting == setting]
    vals = {
        "accuracy": float(ds.correct.mean()),
        "greedy_parse_fail_rate": float((cot.answer_parse_method == "none").mean()),
        "median_letter_mass": float(ds.letter_mass.median()),
        "sample_truncation_rate": float(cot.n_samples_truncated.sum() / (5 * len(cot))) if len(cot) else math.nan,
    }
    flags = {
        "accuracy_below_min": vals["accuracy"] < ap["flag_min_accuracy"],
        "parse_fail_above_max": vals["greedy_parse_fail_rate"] > ap["flag_max_parse_fail"],
        "letter_mass_below_min": vals["median_letter_mass"] < ap["flag_min_median_letter_mass"],
        "truncation_above_max": vals["sample_truncation_rate"] > ap["flag_max_truncation"],
    }
    return {"values": vals, "flags": {k: bool(v) for k, v in flags.items()}, "flagged": bool(any(flags.values()))}


# ------------------------------------------------------------------------------------- exploratory
def _entropy(sample_str: str) -> float:
    from collections import Counter
    c = np.array(list(Counter(sample_str).values()), float)
    p = c / c.sum()
    return float(-(p * np.log(p)).sum())


def exploratory(cc: pd.DataFrame, ap: dict) -> dict:
    y = cc.correct.to_numpy(int)
    n = len(y)
    if n == 0:
        return {"label": "EXPLORATORY - not part of the pre-registered conclusions", "n": 0,
                "majority_vote_accuracy": {"value": None, "wilson_ci": [None, None]},
                "neg_sample_entropy_auroc": None, "rank_average_prob_agree_auroc": None,
                "platt_crossfit_ece": {}, "by_meta_info": {}}
    maj =(cc.majority_answer == cc.gold).to_numpy(int)
    ent = cc.sample_answers.map(_entropy).to_numpy(float)
    rank_avg = (rankdata(cc.conf_prob) + rankdata(cc.conf_agree)) / 2
    out = {
        "label": "EXPLORATORY - not part of the pre-registered conclusions",
        "majority_vote_accuracy": {"value": float(maj.mean()), "wilson_ci": list(M.wilson_ci(int(maj.sum()), n))},
        "neg_sample_entropy_auroc": M.auroc(-ent, y),
        "rank_average_prob_agree_auroc": M.auroc(rank_avg, y),
        "platt_crossfit_ece": {}, "by_meta_info": {},
    }
    for s in SIGNALS:
        cal = S.crossfit_platt(cc[SIGNAL_COLS[s]].to_numpy(float), y, ap["cv_folds"], ap["cv_seed"])
        out["platt_crossfit_ece"][s] = M.ece(cal, y, ap["n_bins"])
    for mi, g in cc.groupby("meta_info", sort=True):
        yg = g.correct.to_numpy(int)
        out["by_meta_info"][str(mi)] = {
            "n": int(len(g)), "accuracy": float(yg.mean()),
            "auroc": {s: M.auroc(g[SIGNAL_COLS[s]].to_numpy(float), yg) for s in SIGNALS},
            "ece": {s: M.ece(g[SIGNAL_COLS[s]].to_numpy(float), yg, ap["n_bins"]) for s in SIGNALS},
        }
    return out


# ------------------------------------------------------------------------------------------ driver
def analyze_frame(df: pd.DataFrame, ap: dict) -> dict:
    models = sorted(df.model.unique())
    if len(models) != 1:
        raise ValueError(f"expected one model per CSV, got {models}")
    summary = {"model": models[0], "analysis_params": ap, "n_rows": int(len(df)), "settings": {}}
    for setting in SETTINGS:
        ds = df[df.setting == setting].sort_values("qid", kind="stable")
        if not len(ds):
            continue
        seed = ap["boot_seed"] + SETTING_SEED_OFFSET[setting]
        sig_cols = [SIGNAL_COLS[s] for s in SIGNALS]
        mask = ds[sig_cols].notna().all(axis=1)
        cc = ds[mask]
        block = analyze_block(cc.correct, {s: cc[SIGNAL_COLS[s]].to_numpy(float) for s in SIGNALS}, ap, seed)
        block["n_total"] = int(len(ds))
        block["n_complete_case"] = int(mask.sum())
        block["n_dropped"] = int((~mask).sum())
        block["n_missing"] = {s: int(ds[SIGNAL_COLS[s]].isna().sum()) for s in SIGNALS}
        block["hypotheses"] = hypotheses(block, alpha=ap["alpha"])
        block["validity"] = validity(df, setting, ap)
        # sensitivity: impute missing conf_stated with its median
        imp = ds.copy()
        med = float(imp.conf_stated.median()) if imp.conf_stated.notna().any() else 0.5
        imp["conf_stated"] = imp.conf_stated.fillna(med)
        m2 = imp[sig_cols].notna().all(axis=1)
        imp = imp[m2]
        sens = analyze_block(imp.correct, {s: imp[SIGNAL_COLS[s]].to_numpy(float) for s in SIGNALS}, ap, seed)
        sens["imputed_value"] = med
        sens["n_imputed"] = int(ds.conf_stated.isna().sum())
        sens["hypotheses"] = hypotheses(sens, alpha=ap["alpha"])
        block["sensitivity_median_impute"] = sens
        block["exploratory"] = exploratory(cc, ap)
        summary["settings"][setting] = block
    return summary


def clean_json(x):
    if isinstance(x, dict):
        return {str(k): clean_json(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean_json(v) for v in x]
    if isinstance(x, (np.bool_, bool)):
        return bool(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        x = float(x)
        return None if (math.isnan(x) or math.isinf(x)) else x
    return x


def dump_json(obj, path):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(clean_json(obj), f, indent=2, sort_keys=True)
        f.write("\n")


# ------------------------------------------------------------------------------------------ tables
def _f(v, d=3):
    return "NA" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:.{d}f}"


def _fci(x, d=3):
    ci = x.get("ci") or [None, None]
    return f"{_f(x['value'], d)} [{_f(ci[0], d)}, {_f(ci[1], d)}]"


def _p(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "NA"
    return f"{v:.2e}" if v < 1e-3 else f"{v:.4f}"


_METRIC_LABELS = {"auroc": "AUROC", "ece": "ECE", "adaptive_ece": "adaptive ECE", "brier": "Brier",
                  "mean_conf": "mean conf", "overconfidence_gap": "overconf. gap",
                  "selective_acc": "sel. acc @80%", "aurc": "AURC"}


def block_tables(b: dict, holm_key="p_holm_within_model", sup_key="supported_within_model") -> list[str]:
    L = []
    acc = b["accuracy"]
    L.append(f"N = {b['n']}; accuracy = {_f(acc['value'])} (Wilson 95% CI {_f(acc['wilson_ci'][0])}–"
             f"{_f(acc['wilson_ci'][1])}); selective-accuracy references at k = {b['references']['k']}: "
             f"random {_f(b['references']['random_selective_acc'])}, oracle {_f(b['references']['oracle_selective_acc'])}")
    L.append("")
    L.append("| signal | " + " | ".join(_METRIC_LABELS[m] for m in M.METRIC_NAMES) + " |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for s, v in b["signals"].items():
        L.append(f"| {s} | " + " | ".join(_fci(v[m]) for m in M.METRIC_NAMES) + " |")
    L.append("")
    L.append("| pair (a − b) | ΔAUROC [95% CI] | DeLong z | p | p (Holm) | supported | ΔECE | Δsel. acc |")
    L.append("|---|---|---|---|---|---|---|---|")
    for k, pr in b["pairs"].items():
        dl = pr["delong"]
        L.append(f"| {k} | {_fci(pr['auroc'])} | {_f(dl['z'], 2)} | {_p(dl['p'])} | {_p(pr.get(holm_key))} | "
                 f"{'yes' if pr.get(sup_key) else 'no'} | {_fci(pr['ece'])} | {_fci(pr['selective_acc'])} |")
    return L


def results_markdown(summary: dict) -> str:
    L = [f"# Results: {summary['model']}", "",
         "All numbers are computed by `medqa_conf.report` from `per_question.csv`. "
         "Intervals are paired-bootstrap percentile 95% CIs (2,000 resamples) unless marked Wilson.", ""]
    for setting, b in summary["settings"].items():
        tag = "primary, pre-registered" if setting == "cot" else "secondary"
        L += [f"## Setting: {setting} ({tag})", "",
              f"Complete-case N used: {b['n_complete_case']} of {b['n_total']} (dropped {b['n_dropped']}; "
              f"missing per signal: {b['n_missing']})", ""]
        v = b["validity"]
        L.append(f"**Validity flags:** {'FLAGGED' if v['flagged'] else 'none'} — "
                 + ", ".join(f"{k} = {_f(x)}" for k, x in v["values"].items())
                 + (" — " + ", ".join(k for k, f in v["flags"].items() if f) if v["flagged"] else ""))
        L.append("")
        L += block_tables(b)
        L.append("")
        h = b["hypotheses"]
        L += ["**Hypotheses (decision rule: Holm-adjusted DeLong p < 0.05 and bootstrap CI excludes 0):**", "",
              f"- H1 (stated AUROC below prob and agree): {'supported' if h['H1']['supported'] else 'not supported'} "
              f"(below prob: {h['H1']['stated_below_prob']}, below agree: {h['H1']['stated_below_agree']})",
              f"- H2 (stated overconfident and highest ECE): {'supported' if h['H2']['supported'] else 'not supported'} "
              f"(overconfident: {h['H2']['overconfident']}, ECE above prob: {h['H2']['ece_above_prob']}, "
              f"ECE above agree: {h['H2']['ece_above_agree']})",
              f"- H3 (prob and agree AUROC differ): {'supported' if h['H3']['supported'] else 'not supported'} "
              f"(observed direction: {h['H3']['direction']})", ""]
        s = b["sensitivity_median_impute"]
        L += [f"### Sensitivity: missing conf_stated imputed with median ({_f(s['imputed_value'])}; "
              f"{s['n_imputed']} imputed)", ""] + block_tables(s) + [""]
        e = b["exploratory"]
        L += ["### Exploratory (not part of the pre-registered conclusions)", "",
              f"- Majority-vote accuracy (5 CoT samples): {_f(e['majority_vote_accuracy']['value'])} "
              f"(Wilson {_f(e['majority_vote_accuracy']['wilson_ci'][0])}–{_f(e['majority_vote_accuracy']['wilson_ci'][1])})",
              f"- AUROC of −entropy of the 5 sample answers: {_f(e['neg_sample_entropy_auroc'])}",
              f"- AUROC of rank-average(prob, agree): {_f(e['rank_average_prob_agree_auroc'])}",
              "- ECE after 5-fold cross-fitted Platt scaling: "
              + ", ".join(f"{k} {_f(v)}" for k, v in e["platt_crossfit_ece"].items()), "",
              "| meta_info | n | accuracy | AUROC stated | AUROC prob | AUROC agree | ECE stated | ECE prob | ECE agree |",
              "|---|---|---|---|---|---|---|---|---|"]
        for mi, g in e["by_meta_info"].items():
            L.append(f"| {mi} | {g['n']} | {_f(g['accuracy'])} | " + " | ".join(_f(g["auroc"][s]) for s in SIGNALS)
                     + " | " + " | ".join(_f(g["ece"][s]) for s in SIGNALS) + " |")
        L.append("")
    return "\n".join(L) + "\n"


# ----------------------------------------------------------------------------------------- figures
def make_figures(df: pd.DataFrame, out_dir: str, ap: dict) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(out_dir, exist_ok=True)
    paths = []
    model = df.model.iloc[0]
    for setting in SETTINGS:
        ds = df[df.setting == setting].sort_values("qid", kind="stable")
        cc = ds[ds[[SIGNAL_COLS[s] for s in SIGNALS]].notna().all(axis=1)]
        if not len(cc):
            continue
        y = cc.correct.to_numpy(int)
        # reliability
        fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
        for ax, s in zip(axes, SIGNALS):
            conf = cc[SIGNAL_COLS[s]].to_numpy(float)
            rb = M.reliability_bins(conf, y, ap["n_bins"])
            e = np.array(rb["edges"])
            mids = (e[:-1] + e[1:]) / 2
            acc = np.array(rb["accuracy"], float)
            cnt = np.array(rb["count"])
            ax.bar(mids[cnt > 0], acc[cnt > 0], width=e[1] - e[0], edgecolor="k", alpha=0.7, label="accuracy")
            ax.plot([0, 1], [0, 1], "k--", lw=1)
            ax.set_title(f"{s} (ECE {M.ece(conf, y, ap['n_bins']):.3f})")
            ax.set_xlabel("confidence")
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
        axes[0].set_ylabel("accuracy")
        fig.suptitle(f"Reliability — {model} — {setting} (N={len(cc)})")
        fig.tight_layout()
        p = os.path.join(out_dir, f"reliability_{setting}.png")
        fig.savefig(p, dpi=110)
        plt.close(fig)
        paths.append(p)
        # risk-coverage
        fig, ax = plt.subplots(figsize=(6, 4.5))
        for s in SIGNALS:
            conf = cc[SIGNAL_COLS[s]].to_numpy(float)
            cov, risk = M.risk_coverage(conf, y)
            ax.plot(cov, risk, label=f"{s} (AURC {M.aurc(conf, y):.3f})")
        cov, risk = M.risk_coverage(y.astype(float), y)
        ax.plot(cov, risk, "k:", label="oracle")
        ax.axhline(1 - y.mean(), color="gray", ls="--", lw=1, label="random")
        ax.axvline(ap["coverage"], color="gray", lw=0.8)
        ax.set_xlabel("coverage")
        ax.set_ylabel("risk (error rate)")
        ax.set_title(f"Risk–coverage — {model} — {setting}")
        ax.legend(fontsize=8)
        fig.tight_layout()
        p = os.path.join(out_dir, f"risk_coverage_{setting}.png")
        fig.savefig(p, dpi=110)
        plt.close(fig)
        paths.append(p)
        # histograms
        fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
        bins = M.equal_width_edges(ap["n_bins"])
        for ax, s in zip(axes, SIGNALS):
            conf = cc[SIGNAL_COLS[s]].to_numpy(float)
            ax.hist([conf[y == 1], conf[y == 0]], bins=bins, label=["correct", "wrong"], color=["tab:green", "tab:red"])
            ax.set_title(s)
            ax.set_xlabel("confidence")
        axes[0].legend()
        fig.suptitle(f"Signal histograms — {model} — {setting}")
        fig.tight_layout()
        p = os.path.join(out_dir, f"histograms_{setting}.png")
        fig.savefig(p, dpi=110)
        plt.close(fig)
        paths.append(p)
    return paths


# ------------------------------------------------------------------------------------- entrypoints
def report_from_csv(csv_path: str, out_dir: str | None = None, ap: dict | None = None, figures: bool = True) -> dict:
    out_dir = out_dir or os.path.dirname(os.path.abspath(csv_path))
    os.makedirs(out_dir, exist_ok=True)
    ap = ap or analysis_params(default_config())
    df = read_csv(csv_path)
    summary = analyze_frame(df, ap)
    dump_json(summary, os.path.join(out_dir, "summary.json"))
    with open(os.path.join(out_dir, "results_table.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(results_markdown(summary))
    if figures:
        make_figures(df, os.path.join(out_dir, "figures"), ap)
    return summary


def _find_csvs(paths) -> list[str]:
    out = []
    for p in paths:
        if os.path.isdir(p):
            out += glob.glob(os.path.join(p, "**", "per_question.csv"), recursive=True)
        elif p.endswith(".zip"):
            out.append(p)
        else:
            out.append(p)
    return sorted(set(out))


def _read_any(p) -> pd.DataFrame:
    if p.endswith(".zip"):
        with zipfile.ZipFile(p) as z:
            name = [n for n in z.namelist() if n.endswith("per_question.csv")][0]
            with z.open(name) as f:
                return read_csv(f)
    return read_csv(p)


def combine(paths, out_dir: str, ap: dict | None = None, prereg_path: str | None = None) -> dict:
    """Recompute every model from its CSV, then Holm across all pairs x non-flagged models per setting."""
    ap = ap or analysis_params(default_config())
    os.makedirs(out_dir, exist_ok=True)
    frames = [_read_any(p) for p in _find_csvs(paths)]
    frames = [f for f in frames if not f.model.iloc[0].endswith("_pilot")]
    by_model = {}
    for f in frames:
        m = f.model.iloc[0]
        if m in by_model:
            raise ValueError(f"model {m} appears twice")
        by_model[m] = (f, analyze_frame(f, ap))
    combined = {"analysis_params": ap, "models": sorted(by_model), "settings": {}}
    for setting in SETTINGS:
        fam, keys = [], []
        for m, (_, s) in sorted(by_model.items()):
            b = s["settings"].get(setting)
            if b is None or b["validity"]["flagged"]:
                continue
            for pk, pr in b["pairs"].items():
                fam.append(pr["delong"]["p"])
                keys.append((m, pk))
        adj = dict(zip(keys, S.holm(fam)))
        per_model = {}
        for m, (_, s) in sorted(by_model.items()):
            b = s["settings"].get(setting)
            if b is None:
                continue
            for pk, pr in b["pairs"].items():
                pr["p_holm_across_models"] = adj.get((m, pk))
                pr["supported_across_models"] = _supported(adj.get((m, pk)), pr["auroc"]["ci"], ap["alpha"]) \
                    if (m, pk) in adj else None
            b["hypotheses_across_models"] = (hypotheses(b, "p_holm_across_models", ap["alpha"])
                                             if not b["validity"]["flagged"] else None)
            per_model[m] = b
        combined["settings"][setting] = {
            "holm_family_size": len(fam), "excluded_flagged_models":
                sorted(m for m, (_, s) in by_model.items() if s["settings"].get(setting, {}).get("validity", {}).get("flagged")),
            "per_model": per_model}
    dump_json(combined, os.path.join(out_dir, "summary_all.json"))
    md = combined_markdown(combined)
    with open(os.path.join(out_dir, "results_all.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    figs = forest_plot(combined, os.path.join(out_dir, "figures"))
    bundle = os.path.join(out_dir, "share_bundle_all.zip")
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(os.path.join(out_dir, "summary_all.json"), "summary_all.json")
        z.write(os.path.join(out_dir, "results_all.md"), "results_all.md")
        for p in figs:
            z.write(p, "figures/" + os.path.basename(p))
        for m, (f, s) in sorted(by_model.items()):
            slug = m.split("/")[-1]
            z.writestr(f"{slug}/per_question.csv", f.to_csv(index=False, lineterminator="\n"))
            z.writestr(f"{slug}/summary.json", json.dumps(clean_json(s), indent=2, sort_keys=True) + "\n")
        if prereg_path and os.path.exists(prereg_path):
            z.write(prereg_path, "PREREGISTRATION.md")
    combined["bundle"] = bundle
    return combined


def combined_markdown(c: dict) -> str:
    L = ["# Combined results across models", "",
         "Recomputed from each model's `per_question.csv`. Holm correction across all pairs × non-flagged models "
         "within a setting. **The primary family is the CoT setting.**", ""]
    for setting, sb in c["settings"].items():
        L += [f"## Setting: {setting}{' (primary)' if setting == 'cot' else ' (secondary)'}", "",
              f"Holm family size: {sb['holm_family_size']}; flagged models excluded: {sb['excluded_flagged_models'] or 'none'}", "",
              "| model | N | accuracy | AUROC stated | AUROC prob | AUROC agree | ECE stated | ECE prob | ECE agree |",
              "|---|---|---|---|---|---|---|---|---|"]
        for m, b in sb["per_model"].items():
            sg = b["signals"]
            L.append(f"| {m}{' (FLAGGED)' if b['validity']['flagged'] else ''} | {b['n']} | {_f(b['accuracy']['value'])} | "
                     + " | ".join(_fci(sg[s]["auroc"]) for s in SIGNALS) + " | "
                     + " | ".join(_fci(sg[s]["ece"]) for s in SIGNALS) + " |")
        L += ["", "| model | pair | ΔAUROC [95% CI] | p | p (Holm, across models) | supported |", "|---|---|---|---|---|---|"]
        for m, b in sb["per_model"].items():
            for pk, pr in b["pairs"].items():
                sup = pr.get("supported_across_models")
                L.append(f"| {m} | {pk} | {_fci(pr['auroc'])} | {_p(pr['delong']['p'])} | {_p(pr.get('p_holm_across_models'))} | "
                         f"{'excluded' if sup is None else ('yes' if sup else 'no')} |")
        L += ["", "| model | H1 | H2 | H3 |", "|---|---|---|---|"]
        for m, b in sb["per_model"].items():
            h = b.get("hypotheses_across_models")
            if h is None:
                L.append(f"| {m} | excluded (flagged) | | |")
            else:
                L.append(f"| {m} | {h['H1']['supported']} | {h['H2']['supported']} | {h['H3']['supported']} ({h['H3']['direction']}) |")
        L.append("")
    return "\n".join(L) + "\n"


def forest_plot(c: dict, out_dir: str) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for setting, sb in c["settings"].items():
        models = list(sb["per_model"])
        if not models:
            continue
        fig, ax = plt.subplots(figsize=(7, 1.2 + 0.9 * len(models)))
        for j, s in enumerate(SIGNALS):
            for i, m in enumerate(models):
                a = sb["per_model"][m]["signals"][s]["auroc"]
                yv = i + (j - 1) * 0.22
                lo, hi = a["ci"]
                if lo is not None:
                    ax.plot([lo, hi], [yv, yv], color=f"C{j}")
                ax.plot(a["value"], yv, "o", color=f"C{j}", label=s if i == 0 else None)
        ax.set_yticks(range(len(models)))
        ax.set_yticklabels([m.split("/")[-1] for m in models])
        ax.set_xlabel("AUROC (95% bootstrap CI)")
        ax.set_title(f"AUROC by model — {setting}")
        ax.legend(fontsize=8)
        fig.tight_layout()
        p = os.path.join(out_dir, f"auroc_forest_{setting}.png")
        fig.savefig(p, dpi=110)
        plt.close(fig)
        paths.append(p)
    return paths


def main(argv=None):
    ap_ = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap_.add_argument("--from-csv", help="per_question.csv to analyse")
    ap_.add_argument("--combine", nargs="+", help="per-model output folders / CSVs / share bundles")
    ap_.add_argument("--out", help="output directory (default: the CSV's folder)")
    ap_.add_argument("--no-figures", action="store_true")
    ap_.add_argument("--prereg", default=None)
    a = ap_.parse_args(argv)
    if a.from_csv:
        report_from_csv(a.from_csv, a.out, figures=not a.no_figures)
        print(f"wrote summary.json to {a.out or os.path.dirname(os.path.abspath(a.from_csv))}")
    elif a.combine:
        c = combine(a.combine, a.out or "combined", prereg_path=a.prereg)
        print(f"wrote {c['bundle']}")
    else:
        ap_.error("give --from-csv or --combine")


if __name__ == "__main__":
    main()
