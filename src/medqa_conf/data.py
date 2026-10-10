"""Dataset loading, fail-loud validation and light cleaning."""
from __future__ import annotations

import collections
import dataclasses
import hashlib

import numpy as np

LETTERS = ("A", "B", "C", "D")


class DataValidationError(RuntimeError):
    pass


@dataclasses.dataclass
class Question:
    qid: int
    question: str
    options: dict  # letter -> cleaned text
    gold: str
    answer_text: str
    meta_info: str
    qhash: str  # sha1 of the raw question text


def clean_option(text: str) -> str:
    """Strip whitespace and a stray (unbalanced) trailing double quote."""
    out = text.strip()
    while out.endswith('"') and out.count('"') % 2 == 1:
        out = out[:-1].strip()
    return out


def validate_rows(rows: list[dict], expected_n: int | None, split: str) -> None:
    if expected_n is not None and len(rows) != expected_n:
        raise DataValidationError(f"{split}: expected exactly {expected_n} rows, got {len(rows)}")
    for i, r in enumerate(rows):
        opts = r.get("options")
        if not isinstance(opts, dict) or sorted(opts.keys()) != list(LETTERS):
            raise DataValidationError(f"{split} row {i}: options keys {None if not isinstance(opts, dict) else sorted(opts)} != A-D")
        if any(not isinstance(v, str) or not v.strip() for v in opts.values()):
            raise DataValidationError(f"{split} row {i}: empty option text")
        if r.get("answer_idx") not in LETTERS:
            raise DataValidationError(f"{split} row {i}: gold letter {r.get('answer_idx')!r} not in A-D")
        if not isinstance(r.get("question"), str) or not r["question"].strip():
            raise DataValidationError(f"{split} row {i}: empty question")


def build_questions(rows: list[dict], indices=None) -> tuple[list[Question], dict]:
    """Clean rows into Questions. `indices` selects rows (qid = row index)."""
    if indices is None:
        indices = range(len(rows))
    qs, n_cleaned, answer_text_mismatch = [], 0, 0
    for i in indices:
        r = rows[i]
        opts = {}
        for L in LETTERS:
            raw = r["options"][L]
            c = clean_option(raw)
            n_cleaned += int(c != raw)
            opts[L] = c
        gold = r["answer_idx"]
        ans = clean_option(r.get("answer", "") or "")
        answer_text_mismatch += int(ans != opts[gold])
        qs.append(Question(qid=int(i), question=r["question"].strip(), options=opts, gold=gold,
                           answer_text=ans, meta_info=str(r.get("meta_info", "")),
                           qhash=hashlib.sha1(r["question"].encode("utf-8")).hexdigest()))
    stats = {
        "n_questions": len(qs),
        "n_options_cleaned": n_cleaned,
        "n_answer_text_mismatch": answer_text_mismatch,
        "gold_distribution": dict(sorted(collections.Counter(q.gold for q in qs).items())),
        "meta_info_distribution": dict(sorted(collections.Counter(q.meta_info for q in qs).items())),
    }
    return qs, stats


def pilot_indices(n_train: int, n: int, seed: int) -> list[int]:
    rng = np.random.default_rng(seed)
    return sorted(int(i) for i in rng.choice(n_train, size=n, replace=False))


def load_hf_splits(dataset_id: str, cache_dir: str | None = None, revision: str | None = None):
    """Return (train_rows, test_rows, dataset_revision). Needs `datasets` + network."""
    import datasets
    from huggingface_hub import HfApi

    if revision is None:
        try:
            revision = HfApi().dataset_info(dataset_id).sha
        except Exception:  # offline / API hiccup: still load, but record it
            revision = None
    ds = datasets.load_dataset(dataset_id, cache_dir=cache_dir, revision=revision)
    return [dict(r) for r in ds["train"]], [dict(r) for r in ds["test"]], revision


def load_questions(cfg, train_rows: list[dict], test_rows: list[dict],
                   expected_test=1273, expected_train=10178) -> tuple[list[Question], dict]:
    """Validate and select the questions for this run (test for the main run, train for the pilot)."""
    validate_rows(test_rows, expected_test, "test")  # always fail loudly on the test schema
    test_qs, test_stats = build_questions(test_rows)
    info = {"test": test_stats, "n_train_rows": len(train_rows)}
    if expected_train is not None and len(train_rows) != expected_train:
        info["warning_train_rows"] = f"expected {expected_train} train rows, got {len(train_rows)}"
    if cfg.pilot:
        idx = pilot_indices(len(train_rows), cfg.pilot_n, cfg.base_seed)
        sub = [train_rows[i] for i in idx]
        validate_rows(sub, None, "train(pilot)")
        qs, st = build_questions(train_rows, idx)
        info["used_split"] = "train"
        info["pilot_train_indices"] = idx
        info["used"] = st
        return qs, info
    info["used_split"] = "test"
    info["used"] = test_stats
    return test_qs, info


def synthetic_rows(n: int, seed: int = 0) -> list[dict]:
    """Fake MedQA-shaped rows for CPU tests (some options carry the trailing '\\n\"' defect)."""
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        opts = {L: f"Option {L} for case {i}: finding {rng.integers(1000)}" for L in LETTERS}
        if i % 7 == 0:
            opts["C"] = opts["C"] + '\n"'
        gold = LETTERS[int(rng.integers(4))]
        rows.append({
            "question": f"A {20 + i % 60}-year-old patient presents with symptom #{i}. Which is the best next step?",
            "options": opts, "answer_idx": gold, "answer": clean_option(opts[gold]),
            "meta_info": "step1" if i % 2 == 0 else "step2&3",
        })
    return rows
