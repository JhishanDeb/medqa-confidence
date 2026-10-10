"""run_log.json, raw_examples.md and the share bundle."""
from __future__ import annotations

import importlib
import json
import os
import platform
import sys
import zipfile

from . import prompts

MAX_BUNDLE_BYTES = 5 * 1024 * 1024
BUNDLE_FILES = ("per_question.csv", "summary.json", "results_table.md", "sanity_report.md", "run_log.json",
                "raw_examples.md")


def package_versions() -> dict:
    out = {"python": sys.version.split()[0], "platform": platform.platform()}
    for name in ("numpy", "scipy", "pandas", "sklearn", "matplotlib", "torch", "transformers", "vllm",
                 "datasets", "huggingface_hub", "tokenizers"):
        try:
            mod = sys.modules.get(name) or importlib.import_module(name)
            out[name] = getattr(mod, "__version__", "?")
        except Exception:
            out[name] = None
    try:
        import torch
        out["cuda"] = torch.version.cuda
        out["gpus"] = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
    except Exception:
        out.setdefault("gpus", [])
    return out


def _trunc(text: str, limit: int = 1500) -> str:
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    h = limit // 2
    return text[:h] + f"\n…[{len(text) - limit} characters truncated]…\n" + text[-h:]


def raw_examples_markdown(df, records, questions, model: str) -> str:
    cot = df[df.setting == "cot"].copy()
    rec = {r["qid"]: r for r in records}
    qs = {q.qid: q for q in questions}
    cc = cot.sort_values(["conf_prob", "qid"], ascending=[False, True], kind="stable")
    picks = [("confident & correct (top conf_prob)", cc[cc.correct == 1].head(4)),
             ("confident & wrong (top conf_prob)", cc[cc.correct == 0].head(4))]
    prob = []
    for cond in (cot.answer_parse_method == "none", cot.forced_answer == 1, cot.stated_recovered == 1,
                 cot.conf_stated.isna()):
        for qid in cot[cond].qid:
            if qid not in prob:
                prob.append(qid)
    picks.append(("parse failure / forced answer / recovered confidence",
                  cot[cot.qid.isin(prob[:4])].set_index("qid").loc[prob[:4]].reset_index()))
    L = [f"# Raw examples: {model} (CoT setting)", "",
         "Reasoning longer than 1,500 characters is truncated in the middle.", ""]
    for title, rows in picks:
        L += [f"## {title}", ""]
        if not len(rows):
            L += ["_none_", ""]
        for _, row in rows.iterrows():
            r, q = rec[int(row.qid)], qs[int(row.qid)]
            L += [f"### qid {int(row.qid)} — gold {row.gold}, official answer {row.answer}, "
                  f"written {row.answer_parsed or 'none'} ({row.answer_parse_method})", "",
                  f"conf_stated {row.conf_stated}, conf_prob {row.conf_prob:.3f}, conf_agree {row.conf_agree}, "
                  f"samples `{row.sample_answers}`, forced_answer {int(row.forced_answer)}, "
                  f"stated_recovered {int(row.stated_recovered)}, letter_mass {row.letter_mass:.3f}", "",
                  "**Question block**", "", "```", prompts.question_block(q), "```", "",
                  "**Greedy output G**", "", "```", _trunc(r["cot"]["greedy"]["text"]), "```", ""]
            if r["cot"].get("recovery"):
                L += [f"Recovery generation: `{r['cot']['recovery']['text']!r}`", ""]
    return "\n".join(L) + "\n"


def write_run_log(path: str, payload: dict) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=2, sort_keys=True, default=str)
        f.write("\n")


def make_share_bundle(out_dir: str, slug: str, prereg_path: str | None, code_dir: str | None = None) -> str:
    path = os.path.join(out_dir, f"share_bundle_{slug}.zip")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in BUNDLE_FILES:
            p = os.path.join(out_dir, f)
            if os.path.exists(p):
                z.write(p, f)
        figdir = os.path.join(out_dir, "figures")
        if os.path.isdir(figdir):
            for f in sorted(os.listdir(figdir)):
                z.write(os.path.join(figdir, f), "figures/" + f)
        if prereg_path and os.path.exists(prereg_path):
            z.write(prereg_path, "PREREGISTRATION.md")
        if code_dir and os.path.isdir(code_dir):
            for root, _, files in os.walk(code_dir):
                for f in sorted(files):
                    if f.endswith(".py"):
                        full = os.path.join(root, f)
                        z.write(full, "code/" + os.path.relpath(full, code_dir).replace(os.sep, "/"))
    size = os.path.getsize(path)
    if size >= MAX_BUNDLE_BYTES:
        raise RuntimeError(f"share bundle is {size / 1e6:.2f} MB (limit 5 MB)")
    return path
