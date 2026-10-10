"""End-to-end orchestration: generation -> per_question.csv -> report -> sanity -> bundle.

CPU mock run:  python -m medqa_conf.pipeline --mock --n 30 --out outputs_mock
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import time

from . import bundle, generate, prompts, report, sanity, signals

TEST_N = 1273
ANALYSIS_FULL_ESTIMATE_S = 900  # conservative allowance for bootstrap/report on 1,273 questions


class PilotAbort(RuntimeError):
    pass


def _garbage_stats(records):
    texts = [r["cot"]["greedy"]["text"] for r in records]
    printable = [sum(ch.isprintable() or ch in "\n\t" for ch in t) / max(1, len(t)) for t in texts]
    rep = []
    for t in texts:
        lines = [l for l in t.splitlines() if l.strip()]
        rep.append(max([lines.count(l) for l in set(lines)] or [0]))
    return {"min_printable_ratio": min(printable) if printable else None,
            "max_repeated_line": max(rep) if rep else None,
            "empty_outputs": sum(not t.strip() for t in texts)}


def pilot_report(records, df, questions, backend, cfg, gen_status, timings) -> tuple[str, dict]:
    rec = {r["qid"]: r for r in records}
    L = [f"# PILOT report: {cfg.model_id}", "",
         f"Pilot uses {len(questions)} **train** questions (indices {[q.qid for q in questions]}). "
         "Not part of the study.", ""]
    for q in questions[:3]:
        r = rec[q.qid]
        cp = backend.render(prompts.cot_message(q))
        dp = backend.render(prompts.direct_message(q))
        dist = generate.letter_distribution({int(k): v for k, v in r["direct"]["logprobs"].items()},
                                            backend.letter_variants)
        L += [f"## qid {q.qid} (gold {q.gold})", "", "### Rendered CoT prompt", "", "```", cp, "```", "",
              "### Raw greedy CoT output G", "", "```", r["cot"]["greedy"]["text"], "```", "",
              f"finish={r['cot']['greedy']['finish']}, tokens={r['cot']['greedy']['tokens']}, "
              f"sample answers={[s['text'][-60:] for s in r['cot']['samples']]}", "",
              "### Rendered Direct prompt + prefill", "", "```", dp + prompts.DIRECT_LETTER_PREFILL, "```", "",
              f"Direct p = { {k: round(v, 4) for k, v in dist['p'].items()} }, letter_mass {dist['letter_mass']:.4f}; "
              f"confidence generation after `Answer: {dist['argmax']}\\nConfidence:` = "
              f"{r['direct']['confidence_gen']['text']!r}", ""]
    cot = df[df.setting == "cot"]
    dirr = df[df.setting == "direct"]
    n_tok = sum(r["cot"]["greedy"]["tokens"] + sum(s["tokens"] for s in r["cot"]["samples"]) for r in records)
    gs = gen_status["generation_seconds"]
    spq = gen_status["seconds_per_question"] or 0.0
    setup = sum(timings.get(k, 0.0) for k in ("model_download", "smoke_test", "model_load", "install"))
    proj_s = setup + spq * TEST_N + timings.get("determinism", 0.0) + max(timings.get("analysis", 0.0), ANALYSIS_FULL_ESTIMATE_S)
    proj = {"seconds_per_question": spq, "generated_tokens": n_tok,
            "throughput_tokens_per_s": n_tok / gs if gs else None,
            "setup_seconds": setup, "projected_full_hours": proj_s / 3600,
            "max_hours": cfg.max_projected_hours, "abort": proj_s / 3600 > cfg.max_projected_hours}
    g = _garbage_stats(records)
    warn = []
    if (cot.answer_parse_method == "none").mean() > 0.10:
        warn.append("greedy answer parse failure > 10%")
    for s, d in (("cot", cot), ("direct", dirr)):
        if d.letter_mass.median() < 0.5:
            warn.append(f"{s} median letter_mass < 0.5")
    if g["min_printable_ratio"] is not None and g["min_printable_ratio"] < 0.95:
        warn.append("non-printable characters in greedy output (possible fp16 garbage)")
    if g["max_repeated_line"] and g["max_repeated_line"] >= 10:
        warn.append("a greedy output repeats one line >= 10 times (degenerate output?)")
    if g["empty_outputs"]:
        warn.append(f"{g['empty_outputs']} empty greedy outputs")
    L += ["## Rates", "",
          f"- Greedy answer parse rate: {1 - (cot.answer_parse_method == 'none').mean():.1%} "
          f"(methods {cot.answer_parse_method.value_counts().to_dict()})",
          f"- Greedy confidence parse rate before recovery: {1 - cot.stated_missing_before_recovery.mean():.1%}; "
          f"after: {1 - cot.conf_stated.isna().mean():.1%}",
          f"- Direct confidence parse rate: {1 - dirr.conf_stated.isna().mean():.1%}",
          f"- forced_answer: {cot.forced_answer.mean():.1%}; parsed-vs-argmax mismatch: "
          f"{cot.parsed_vs_argmax_mismatch.mean():.1%}",
          f"- letter_mass median: CoT {cot.letter_mass.median():.3f} (min {cot.letter_mass.min():.3f}), "
          f"Direct {dirr.letter_mass.median():.3f} (min {dirr.letter_mass.min():.3f})",
          f"- Truncation: greedy {cot.greedy_truncated.mean():.1%}, samples {cot.n_samples_truncated.sum() / (5 * len(cot)):.1%}",
          f"- Accuracy (train, 20 q — noisy): CoT {cot.correct.mean():.2f}, Direct {dirr.correct.mean():.2f}",
          f"- Output health: {g}", "",
          "## Throughput and projection", "",
          f"- {spq:.1f} s per question (all 6 calls), {proj['throughput_tokens_per_s'] or 0:.0f} generated tokens/s",
          f"- Setup (install + download + smoke test + load): {setup / 60:.1f} min",
          f"- Projected full run (1,273 questions): **{proj['projected_full_hours']:.2f} h** "
          f"(limit {cfg.max_projected_hours} h) → {'ABORT' if proj['abort'] else 'OK'}",
          "- The projection is conservative: the full run batches 50 questions per chunk vs 20 here.", "",
          "## Warnings", ""] + ([f"- {w}" for w in warn] or ["- none"])
    proj["warnings"] = warn
    proj["output_health"] = g
    return "\n".join(L) + "\n", proj


def run(cfg, backend, questions, data_info, out_dir, *, model_revision=None, dataset_revision=None,
        resume_roots=(), time_budget_s=None, t_start=None, timings=None, env=None, prereg_path=None,
        code_dir=None, backend_note=None, log=print) -> dict:
    t_start = t_start if t_start is not None else time.time()
    timings = dict(timings or {})
    os.makedirs(out_dir, exist_ok=True)
    run_log = {"config": cfg.to_dict(), "config_hash": cfg.config_hash(), "model_id": cfg.model_id,
               "model_revision": model_revision, "dataset_id": cfg.dataset_id, "dataset_revision": dataset_revision,
               "seeds": {"base_seed": cfg.base_seed, "sample_seed": "base_seed + qid", "boot_seed": cfg.boot_seed,
                         "cv_seed": cfg.cv_seed},
               "pilot": cfg.pilot, "backend": backend.info(), "backend_note": backend_note,
               "environment": env or {}, "data": data_info, "timings_seconds": timings}
    if questions:
        run_log["example_rendered_cot_prompt"] = backend.render(prompts.cot_message(questions[0]))

    t0 = time.time()
    st = generate.run_generation(backend, cfg, questions, out_dir, model_revision=model_revision,
                                 resume_roots=resume_roots, time_budget_s=time_budget_s, t_start=t_start, log=log)
    timings["generation"] = time.time() - t0
    run_log["generation"] = {k: v for k, v in st.items() if k != "records"}
    records = st["records"]
    if not st["complete"]:
        run_log["status"] = "incomplete"
        run_log["versions"] = bundle.package_versions()
        bundle.write_run_log(os.path.join(out_dir, "run_log.json"), run_log)
        log(f"[pipeline] INCOMPLETE: {len(records)}/{len(questions)} questions. Attach this notebook's output "
            "as input and re-run to resume.")
        return {"status": "incomplete", "out_dir": out_dir, "n_done": len(records)}

    t0 = time.time()
    det = generate.determinism_check(backend, cfg, questions, records, cfg.determinism_n)
    timings["determinism"] = time.time() - t0

    t0 = time.time()
    df = signals.records_to_frame(records, cfg.model_id + ("_pilot" if cfg.pilot else ""), backend.letter_variants)
    csv_path = os.path.join(out_dir, "per_question.csv")
    df.to_csv(csv_path, index=False, lineterminator="\n")
    ap = report.analysis_params(cfg)
    summary = report.report_from_csv(csv_path, out_dir, ap)  # computed from the saved CSV only
    df = report.read_csv(csv_path)
    timings["analysis"] = time.time() - t0

    t0 = time.time()
    validity = {s: b["validity"] for s, b in summary["settings"].items()}
    sst = sanity.sanity_stats(records, df, data_info, det, validity)
    with open(os.path.join(out_dir, "sanity_report.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(sanity.sanity_markdown(sst, cfg.model_id))
    generate.write_raw_generations(records, os.path.join(out_dir, "raw_generations.jsonl.gz"))
    with open(os.path.join(out_dir, "raw_examples.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(bundle.raw_examples_markdown(df, records, questions, cfg.model_id))
    result = {"status": "complete", "out_dir": out_dir, "csv": csv_path, "summary": summary}
    if cfg.pilot:
        md, proj = pilot_report(records, df, questions, backend, cfg, st, timings)
        with open(os.path.join(out_dir, "pilot_report.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        run_log["pilot_projection"] = proj
        result["pilot_report"] = md
        result["projection"] = proj
    timings["reports"] = time.time() - t0
    timings["total_wall"] = time.time() - t_start
    run_log["determinism"] = det
    run_log["status"] = "complete"
    run_log["versions"] = bundle.package_versions()
    bundle.write_run_log(os.path.join(out_dir, "run_log.json"), run_log)
    result["bundle"] = bundle.make_share_bundle(out_dir, cfg.model_slug, prereg_path, code_dir)
    log(f"[pipeline] done: {result['bundle']} ({os.path.getsize(result['bundle']) / 1e6:.2f} MB)")
    return result


def check_pilot(result) -> None:
    """Raise after all pilot files are written if the projected runtime is too long."""
    p = result.get("projection")
    if p and p["abort"]:
        raise PilotAbort(f"projected full runtime {p['projected_full_hours']:.2f} h exceeds {p['max_hours']} h")


# ------------------------------------------------------------------------------------ mock CLI
def run_mock(n: int, out_root: str, pilot: bool = False, accuracy: float = 0.62, model_id="mock/Mock-7B",
             time_budget_s=None, resume_roots=(), prereg_path=None, code_dir=None, log=print):
    from config import Config

    from . import data
    from .backends import MockBackend

    cfg = dataclasses.replace(Config(), model_id=model_id, pilot=pilot)
    test_rows = data.synthetic_rows(n, seed=1)
    train_rows = data.synthetic_rows(200, seed=2)
    qs, info = data.load_questions(cfg, train_rows, test_rows, expected_test=n, expected_train=None)
    key = {q.question: q.gold for q in qs}
    backend = MockBackend(key, accuracy=accuracy, seed=0)
    out_dir = os.path.join(out_root, cfg.model_slug)
    res = run(cfg, backend, qs, info, out_dir, model_revision="mock", dataset_revision="synthetic",
              resume_roots=resume_roots, time_budget_s=time_budget_s, prereg_path=prereg_path,
              code_dir=code_dir, env={"note": "CPU mock run"}, log=log)
    return cfg, qs, res


def main(argv=None):
    a = argparse.ArgumentParser()
    a.add_argument("--mock", action="store_true", required=True)
    a.add_argument("--n", type=int, default=30)
    a.add_argument("--out", default="outputs_mock")
    a.add_argument("--pilot", action="store_true")
    a.add_argument("--prereg", default="PREREGISTRATION.md")
    a = a.parse_args(argv)
    t = time.time()
    _, _, res = run_mock(a.n, a.out, pilot=a.pilot, prereg_path=a.prereg, code_dir="src")
    print(json.dumps({"status": res["status"], "bundle": res.get("bundle"), "seconds": round(time.time() - t, 1)}))


if __name__ == "__main__":
    main()
