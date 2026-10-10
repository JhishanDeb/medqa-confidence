"""Raw records -> per_question table (one row per qid x setting; no raw text)."""
from __future__ import annotations

import collections
import math

import pandas as pd

from . import parsing
from .generate import letter_distribution

LETTERS = ("A", "B", "C", "D")
COLUMNS = [
    "model", "setting", "qid", "qhash", "meta_info", "gold", "answer", "correct",
    "p_A", "p_B", "p_C", "p_D", "letter_mass", "n_letters_missing_topk",
    "conf_prob", "conf_stated", "conf_agree",
    "stated_recovered", "stated_fraction_flag", "stated_missing_before_recovery",
    "sample_answers", "majority_answer", "n_samples_parsed",
    "answer_parsed", "answer_parse_method", "forced_answer", "parsed_vs_argmax_mismatch",
    "greedy_tokens", "greedy_truncated", "n_samples_truncated",
]


def majority_vote(sample_letters, official):
    parsed = [s for s in sample_letters if s is not None]
    if not parsed:
        return official
    cnt = collections.Counter(parsed)
    top = max(cnt.values())
    tied = sorted(L for L, c in cnt.items() if c == top)
    return official if official in tied else tied[0]


def _int_keys(d):
    return {int(k): v for k, v in d.items()}


def records_to_frame(records, model_id: str, letter_variants: dict) -> pd.DataFrame:
    rows = []
    for r in records:
        cot = r["cot"]
        sample_letters = [parsing.parse_answer(s["text"])[0] for s in cot["samples"]]
        sample_str = "".join(L if L is not None else "-" for L in sample_letters)
        n_trunc = sum(s["finish"] == "length" for s in cot["samples"])
        g = cot["greedy"]
        written, method = parsing.parse_answer(g["text"])
        common = dict(model=model_id, qid=r["qid"], qhash=r["qhash"], meta_info=r["meta_info"], gold=r["gold"],
                      sample_answers=sample_str, n_samples_parsed=sum(L is not None for L in sample_letters),
                      n_samples_truncated=n_trunc)

        # --- CoT
        d = letter_distribution(_int_keys(cot["logprobs"]), letter_variants)
        X = d["argmax"]
        c, frac = parsing.parse_confidence(g["text"])
        missing_before = int(math.isnan(c))
        recovered = 0
        if math.isnan(c) and cot.get("recovery") is not None:
            c, frac = parsing.parse_confidence_continuation(cot["recovery"]["text"])
            recovered = int(not math.isnan(c))
        rows.append(dict(common, setting="cot", **_letter_cols(d), answer=X, correct=int(X == r["gold"]),
                         conf_prob=d["p"][X], conf_stated=c,
                         conf_agree=sum(L == X for L in sample_letters) / len(sample_letters),
                         stated_recovered=recovered, stated_fraction_flag=int(frac),
                         stated_missing_before_recovery=missing_before,
                         majority_answer=majority_vote(sample_letters, X),
                         answer_parsed=written if written else "", answer_parse_method=method,
                         forced_answer=int(cot["forced_answer"]),
                         parsed_vs_argmax_mismatch=(int(written != X) if written else math.nan),
                         greedy_tokens=g["tokens"], greedy_truncated=int(g["finish"] == "length")))

        # --- Direct
        dr = r["direct"]
        d = letter_distribution(_int_keys(dr["logprobs"]), letter_variants)
        X = d["argmax"]
        cg = dr.get("confidence_gen")
        c, frac = parsing.parse_confidence_continuation(cg["text"] if cg else None)
        rows.append(dict(common, setting="direct", **_letter_cols(d), answer=X, correct=int(X == r["gold"]),
                         conf_prob=d["p"][X], conf_stated=c,
                         conf_agree=sum(L == X for L in sample_letters) / len(sample_letters),
                         stated_recovered=0, stated_fraction_flag=int(frac),
                         stated_missing_before_recovery=int(math.isnan(c)),
                         majority_answer=majority_vote(sample_letters, X),
                         answer_parsed="", answer_parse_method="", forced_answer=math.nan,
                         parsed_vs_argmax_mismatch=math.nan, greedy_tokens=math.nan, greedy_truncated=math.nan))
    df = pd.DataFrame(rows)[COLUMNS]
    return df.sort_values(["setting", "qid"], kind="stable").reset_index(drop=True)


def _letter_cols(d):
    out = {f"p_{L}": d["p"][L] for L in LETTERS}
    out["letter_mass"] = d["letter_mass"]
    out["n_letters_missing_topk"] = len(d["missing_letters"])
    return out
