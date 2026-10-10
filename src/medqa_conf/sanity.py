"""sanity_report.md (PREREGISTRATION.md section 9)."""
from __future__ import annotations

import collections

import numpy as np

from . import metrics as M
from . import parsing

SIGNAL_COLS = ("conf_stated", "conf_prob", "conf_agree")


def _pct(x):
    return f"{100 * x:.1f}%"


def _dist(series):
    c = collections.Counter(series)
    n = sum(c.values())
    return ", ".join(f"{k}: {v} ({_pct(v / n)})" for k, v in sorted(c.items()))


def sanity_stats(records, df, data_info, determinism, validity_by_setting) -> dict:
    cot = df[df.setting == "cot"]
    st = {}
    st["greedy_answer_parse_fail"] = float((cot.answer_parse_method == "none").mean())
    st["greedy_answer_parse_methods"] = dict(collections.Counter(cot.answer_parse_method))
    st["greedy_conf_missing_before_recovery"] = float(cot.stated_missing_before_recovery.mean())
    st["greedy_conf_missing_after_recovery"] = float(cot.conf_stated.isna().mean())
    st["n_stated_recovered"] = int(cot.stated_recovered.sum())
    n_samp = sum(len(r["cot"]["samples"]) for r in records)
    n_unparsed = sum(parsing.parse_answer(s["text"])[0] is None for r in records for s in r["cot"]["samples"])
    st["sample_answer_parse_fail"] = n_unparsed / n_samp if n_samp else float("nan")
    st["greedy_truncation"] = float(cot.greedy_truncated.mean())
    st["sample_truncation"] = float(cot.n_samples_truncated.sum() / n_samp) if n_samp else float("nan")
    st["cot_forced_answer"] = float(cot.forced_answer.mean())
    mm = cot.parsed_vs_argmax_mismatch.dropna()
    st["cot_parsed_vs_argmax_mismatch"] = float(mm.mean()) if len(mm) else float("nan")
    st["cot_parsed_vs_argmax_n"] = int(len(mm))
    for setting in ("cot", "direct"):
        ds = df[df.setting == setting]
        q = np.percentile(ds.letter_mass, [0, 5, 25, 50, 75, 95, 100]).tolist()
        st[f"{setting}_letter_mass_quantiles"] = dict(zip(["min", "p5", "p25", "median", "p75", "p95", "max"], q))
        st[f"{setting}_any_letter_missing_topk"] = float((ds.n_letters_missing_topk > 0).mean())
        st[f"{setting}_zero_letter_mass"] = int((ds.letter_mass == 0).sum())
        st[f"{setting}_conf_missing"] = int(ds.conf_stated.isna().sum())
        st[f"{setting}_stated_fraction_flag"] = int(ds.stated_fraction_flag.sum())
        st[f"{setting}_chosen_letters"] = dict(collections.Counter(ds.answer))
        st[f"{setting}_accuracy"] = float(ds.correct.mean())
        sig = {}
        for c in SIGNAL_COLS:
            v = ds[c].dropna().to_numpy(float)
            if not len(v):
                sig[c] = None
                continue
            uniq, cnt = np.unique(v, return_counts=True)
            idx = M.bin_index(v, M.equal_width_edges(15))
            sig[c] = {"hist_15bins": np.bincount(idx, minlength=15).tolist(),
                      "frac_tied": float(cnt[cnt > 1].sum() / len(v)), "n_unique": int(len(uniq))}
            if c == "conf_stated":
                top = sorted(zip(cnt, uniq), key=lambda t: (-t[0], t[1]))[:5]
                sig[c]["top5_values"] = [[float(u), int(k)] for k, u in top]
        st[f"{setting}_signals"] = sig
    st["gold_letters"] = dict(collections.Counter(cot.gold))
    st["determinism"] = determinism
    st["validity"] = validity_by_setting
    st["data"] = data_info
    return st


def sanity_markdown(st: dict, model: str) -> str:
    d = st["data"]
    L = [f"# Sanity report: {model}", "",
         "## [fail] checks", "",
         f"- PASS dataset counts and schema: test split = {d['test']['n_questions']} rows, 4 options A–D, gold in A–D "
         f"(run would have stopped otherwise). Split used: {d['used_split']} ({d['used']['n_questions']} questions).",
         f"- PASS no NaN/inf in any returned logprob (run would have stopped otherwise).", "",
         "## Data", "",
         f"- Options cleaned (whitespace / stray trailing quote): test {d['test']['n_options_cleaned']}, "
         f"used split {d['used']['n_options_cleaned']}",
         f"- Gold answer text ≠ option text after cleaning: {d['used']['n_answer_text_mismatch']}",
         f"- Gold-letter distribution (used split): {d['used']['gold_distribution']}",
         f"- Gold-letter distribution (test split): {d['test']['gold_distribution']}",
         f"- meta_info (used split): {d['used']['meta_info_distribution']}", "",
         "## Parsing", "",
         f"- Greedy answer parse failure: {_pct(st['greedy_answer_parse_fail'])} (methods: {st['greedy_answer_parse_methods']})",
         f"- Greedy confidence missing before recovery: {_pct(st['greedy_conf_missing_before_recovery'])}; "
         f"after recovery: {_pct(st['greedy_conf_missing_after_recovery'])} ({st['n_stated_recovered']} recovered)",
         f"- Sample answer parse failure: {_pct(st['sample_answer_parse_fail'])}",
         f"- CoT forced_answer (no 'Answer:' in G): {_pct(st['cot_forced_answer'])}",
         f"- CoT parsed letter ≠ argmax p: {_pct(st['cot_parsed_vs_argmax_mismatch'])} (of {st['cot_parsed_vs_argmax_n']} parsed)",
         f"- Direct confidence missing: {st['direct_conf_missing']}", "",
         "## Letter distribution", ""]
    for s in ("cot", "direct"):
        q = st[f"{s}_letter_mass_quantiles"]
        L.append(f"- {s}: letter_mass " + ", ".join(f"{k} {v:.3f}" for k, v in q.items())
                 + f"; any letter missing from top-k: {_pct(st[f'{s}_any_letter_missing_topk'])}; "
                 f"zero letter mass: {st[f'{s}_zero_letter_mass']}")
    L += ["", "## Truncation (finish_reason == length)", "",
          f"- Greedy: {_pct(st['greedy_truncation'])}; samples: {_pct(st['sample_truncation'])}", "",
          "## Position bias (chosen vs gold letters)", "",
          f"- gold: {st['gold_letters']}"]
    for s in ("cot", "direct"):
        L.append(f"- {s} chosen: {st[f'{s}_chosen_letters']} (accuracy {st[f'{s}_accuracy']:.3f})")
    L += ["", "## Signals (15 equal-width bins on [0,1])", ""]
    for s in ("cot", "direct"):
        for c, v in st[f"{s}_signals"].items():
            if v is None:
                L.append(f"- {s} {c}: no values")
                continue
            extra = f"; top-5 values {v['top5_values']}" if "top5_values" in v else ""
            L.append(f"- {s} {c}: hist {v['hist_15bins']}; fraction tied {v['frac_tied']:.3f}; "
                     f"unique {v['n_unique']}{extra}; fraction-format flags {st[f'{s}_stated_fraction_flag'] if c == 'conf_stated' else '-'}")
    det = st["determinism"]
    L += ["", "## Greedy determinism", "",
          f"- Re-ran CoT greedy on {det['n']} questions: {det['identical']}/{det['n']} byte-identical"
          + (f" (differing qids: {det['qids_differing']})" if det["qids_differing"] else ""), "",
          "## Validity flags (PREREGISTRATION.md section 8)", ""]
    for s, v in st["validity"].items():
        L.append(f"- {s}: {'FLAGGED' if v['flagged'] else 'not flagged'} — values "
                 + ", ".join(f"{k} {x:.3f}" for k, x in v["values"].items())
                 + " — flags " + ", ".join(f"{k}={x}" for k, x in v["flags"].items()))
    return "\n".join(L) + "\n"
