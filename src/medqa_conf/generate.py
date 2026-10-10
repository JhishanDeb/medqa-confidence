"""Model calls 1-6 per question, chunked, with JSONL checkpointing, resume and a time budget."""
from __future__ import annotations

import glob
import gzip
import json
import math
import os
import time

from . import parsing, prompts
from .backends import GenRequest

LETTERS = ("A", "B", "C", "D")


class ResumeMismatchError(RuntimeError):
    pass


def letter_distribution(logprobs: dict, letter_variants: dict) -> dict:
    """Sum the probability of the 'L' and ' L' variants, then renormalise over A-D."""
    raw, missing = {}, []
    for L in LETTERS:
        present = [logprobs[t] for t in letter_variants[L] if t in logprobs]
        if not present:
            missing.append(L)
        raw[L] = sum(math.exp(v) for v in present)
    mass = sum(raw.values())
    if mass > 0:
        p = {L: raw[L] / mass for L in LETTERS}
    else:
        p = {L: 0.25 for L in LETTERS}
    best = max(LETTERS, key=lambda L: (p[L], -LETTERS.index(L)))  # ties -> alphabetical
    return {"p": p, "letter_mass": mass, "argmax": best, "missing_letters": missing}


def _gen_dict(o):
    return {"text": o.text, "tokens": o.n_tokens, "finish": o.finish_reason}


def process_chunk(backend, cfg, qs) -> list[dict]:
    """Run calls 1-6 for a list of Questions; returns raw records (one per question)."""
    cot_prompts = [backend.render(prompts.cot_message(q)) for q in qs]
    dir_prompts = [backend.render(prompts.direct_message(q)) for q in qs]
    reqs = []
    for q, cp in zip(qs, cot_prompts):
        reqs.append(GenRequest(cp, cfg.greedy_max_new_tokens, temperature=0.0))
    for q, cp in zip(qs, cot_prompts):
        reqs.append(GenRequest(cp, cfg.sample_max_new_tokens, temperature=cfg.sample_temperature,
                               top_p=cfg.sample_top_p, n=cfg.n_samples, seed=cfg.base_seed + q.qid))
    outs = backend.generate(reqs)
    greedy = [o[0] for o in outs[: len(qs)]]
    samples = outs[len(qs):]
    for s in samples:
        if len(s) != cfg.n_samples:
            raise RuntimeError(f"expected {cfg.n_samples} samples, got {len(s)}")

    # calls 3 and 5: next-token letter distributions
    cot_prefixes = [prompts.cot_letter_prefix(g.text) for g in greedy]
    lp_prompts = [cp + pre for cp, (pre, _) in zip(cot_prompts, cot_prefixes)]
    lp_prompts += [dp + prompts.DIRECT_LETTER_PREFILL for dp in dir_prompts]
    lps = backend.next_token_logprobs(lp_prompts)
    cot_lp, dir_lp = lps[: len(qs)], lps[len(qs):]
    cot_dist = [letter_distribution(lp, backend.letter_variants) for lp in cot_lp]
    dir_dist = [letter_distribution(lp, backend.letter_variants) for lp in dir_lp]

    # calls 4 (only if needed) and 6
    conf_reqs, conf_owner = [], []
    for i, (g, (pre, _)) in enumerate(zip(greedy, cot_prefixes)):
        c, _f = parsing.parse_confidence(g.text)
        if math.isnan(c):
            conf_reqs.append(GenRequest(cot_prompts[i] + prompts.cot_recovery_prefill(pre, cot_dist[i]["argmax"]),
                                        cfg.confidence_max_new_tokens, temperature=0.0))
            conf_owner.append(("cot", i))
    for i, dp in enumerate(dir_prompts):
        conf_reqs.append(GenRequest(dp + prompts.direct_conf_prefill(dir_dist[i]["argmax"]),
                                    cfg.confidence_max_new_tokens, temperature=0.0))
        conf_owner.append(("direct", i))
    conf_outs = backend.generate(conf_reqs) if conf_reqs else []
    recovery = {i: None for i in range(len(qs))}
    dconf = {}
    for (kind, i), o in zip(conf_owner, conf_outs):
        (recovery if kind == "cot" else dconf)[i] = _gen_dict(o[0])

    recs = []
    for i, q in enumerate(qs):
        recs.append({
            "qid": q.qid, "qhash": q.qhash, "meta_info": q.meta_info, "gold": q.gold,
            "cot": {"greedy": _gen_dict(greedy[i]),
                    "samples": [_gen_dict(o) for o in samples[i]],
                    "forced_answer": cot_prefixes[i][1],
                    "logprobs": {str(k): v for k, v in cot_lp[i].items()},
                    "recovery": recovery[i]},
            "direct": {"logprobs": {str(k): v for k, v in dir_lp[i].items()},
                       "confidence_gen": dconf[i]},
        })
    return recs


# ----------------------------------------------------------------------------------- checkpointing
def checkpoint_header(cfg, backend_info: dict, model_revision: str | None) -> dict:
    return {"type": "header", "model_id": cfg.model_id, "config_hash": cfg.config_hash(),
            "model_revision": model_revision, "backend": backend_info.get("backend")}


def read_checkpoint(path: str):
    header, recs = None, {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:  # torn last line from a killed session
                continue
            if d.get("type") == "header":
                header = d
            else:
                recs[d["qid"]] = d
    return header, recs


def find_resume_checkpoints(cfg, search_roots) -> list[str]:
    found = []
    for root in search_roots:
        if root and os.path.isdir(root):
            found += glob.glob(os.path.join(root, "**", cfg.model_slug, "checkpoint.jsonl"), recursive=True)
    return sorted(set(found))


def load_resume(cfg, header: dict, paths, log=print) -> dict:
    """Records from previous checkpoints with the same model + config hash. Mismatched revision or
    backend raises (mixing outputs from different weights/engines is not allowed)."""
    recs = {}
    for p in paths:
        h, r = read_checkpoint(p)
        if h is None or h.get("model_id") != header["model_id"] or h.get("config_hash") != header["config_hash"]:
            log(f"[resume] ignoring {p}: different model or config hash")
            continue
        for key in ("model_revision", "backend"):
            if h.get(key) != header.get(key):
                raise ResumeMismatchError(
                    f"checkpoint {p} has {key}={h.get(key)!r} but this run has {header.get(key)!r}. "
                    "Detach that input (start fresh) or pin the same revision/backend.")
        log(f"[resume] {len(r)} finished questions from {p}")
        recs.update(r)
    return recs


def run_generation(backend, cfg, questions, out_dir, model_revision=None, resume_roots=(),
                   time_budget_s: float | None = None, t_start: float | None = None, log=print) -> dict:
    """Generate for all questions; checkpoint every cfg.checkpoint_every. Returns a status dict."""
    os.makedirs(out_dir, exist_ok=True)
    t_start = t_start if t_start is not None else time.time()
    ck_path = os.path.join(out_dir, "checkpoint.jsonl")
    header = checkpoint_header(cfg, backend.info(), model_revision)
    prev_paths = find_resume_checkpoints(cfg, list(resume_roots))
    if os.path.exists(ck_path):
        prev_paths.append(ck_path)
    done = load_resume(cfg, header, prev_paths, log=log)
    wanted = {q.qid for q in questions}
    done = {k: v for k, v in done.items() if k in wanted}
    with open(ck_path + ".tmp", "w", encoding="utf-8") as f:  # rewrite: header + resumed records
        f.write(json.dumps(header) + "\n")
        for k in sorted(done):
            f.write(json.dumps(done[k]) + "\n")
    os.replace(ck_path + ".tmp", ck_path)

    todo = [q for q in questions if q.qid not in done]
    log(f"[generate] {len(done)} resumed, {len(todo)} to do")
    chunk_times, n_new, stopped_early = [], 0, False
    for b in range(0, len(todo), cfg.checkpoint_every):
        if time_budget_s is not None and chunk_times:
            est = max(chunk_times)
            if time.time() - t_start + est > time_budget_s:
                log(f"[generate] time budget reached; stopping with {len(todo) - b} questions left")
                stopped_early = True
                break
        chunk = todo[b:b + cfg.checkpoint_every]
        t0 = time.time()
        recs = process_chunk(backend, cfg, chunk)
        with open(ck_path, "a", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r) + "\n")
            f.flush()
            os.fsync(f.fileno())
        for r in recs:
            done[r["qid"]] = r
        dt = time.time() - t0
        chunk_times.append(dt)
        n_new += len(chunk)
        log(f"[generate] {len(done)}/{len(questions)} done ({dt:.1f}s for {len(chunk)} q)")
    gen_time = sum(chunk_times)
    return {"records": [done[k] for k in sorted(done)], "complete": len(done) == len(questions),
            "n_resumed": len(questions) - len(todo), "n_generated": n_new, "stopped_early": stopped_early,
            "generation_seconds": gen_time,
            "seconds_per_question": gen_time / n_new if n_new else None,
            "checkpoint": ck_path}


def determinism_check(backend, cfg, questions, records, n: int) -> dict:
    """Re-run CoT greedy on the first n questions; count byte-identical outputs."""
    qs = questions[:n]
    by_qid = {r["qid"]: r for r in records}
    reqs = [GenRequest(backend.render(prompts.cot_message(q)), cfg.greedy_max_new_tokens, temperature=0.0)
            for q in qs]
    outs = backend.generate(reqs)
    same = [o[0].text == by_qid[q.qid]["cot"]["greedy"]["text"] for q, o in zip(qs, outs)]
    return {"n": len(qs), "identical": int(sum(same)), "qids_differing": [q.qid for q, s in zip(qs, same) if not s]}


def write_raw_generations(records, path):
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
