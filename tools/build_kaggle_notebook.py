"""Build the two self-contained Kaggle notebooks (all src code inlined via %%writefile cells).

    python tools/build_kaggle_notebook.py                 # writes kaggle/*.ipynb
    python tools/build_kaggle_notebook.py --execute-mock  # also runs both notebooks on CPU with MEDQA_MOCK=1
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "medqa_conf")
MODULES = ["__init__.py", "data.py", "prompts.py", "parsing.py", "backends.py", "generate.py", "signals.py",
           "metrics.py", "stats.py", "report.py", "sanity.py", "bundle.py", "pipeline.py"]


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def writefile_cells() -> list:
    cells = [new_code_cell("import os\nos.makedirs('medqa_src/medqa_conf', exist_ok=True)")]
    cells.append(new_code_cell("%%writefile medqa_src/config.py\n" + _read(os.path.join(ROOT, "config.py"))))
    for m in MODULES:
        cells.append(new_code_cell(f"%%writefile medqa_src/medqa_conf/{m}\n" + _read(os.path.join(SRC, m))))
    cells.append(new_code_cell("%%writefile medqa_src/PREREGISTRATION.md\n" + _read(os.path.join(ROOT, "PREREGISTRATION.md"))))
    return cells


SETTINGS = '''\
# ============ the only settings you normally change ============
MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"   # or "meta-llama/Llama-3.1-8B-Instruct", "mistralai/Mistral-7B-Instruct-v0.3"
PILOT = True                            # True: 20 TRAIN questions + runtime projection. False: full test run.
# ============ optional ============
BACKEND = "auto"          # "auto" = vLLM, falling back to transformers if vLLM fails; or "vllm" / "hf"
TIME_BUDGET_HOURS = 11.0  # generation stops cleanly (checkpoint kept) before Kaggle's 12 h limit
MODEL_REVISION = None     # None = latest commit (resolved and logged); or pin a commit hash

import os, sys, time, json, subprocess, platform
T_START = time.time()
MOCK = os.environ.get("MEDQA_MOCK") == "1"   # CPU self-test of this notebook; never set on Kaggle

def sh(cmd, timeout=None, cwd=None, env=None):
    r = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, timeout=timeout,
                       cwd=cwd, env=env)
    return r.returncode, (r.stdout or "") + (r.stderr or "")

# torch is queried in a subprocess so that the kernel does not import it before vLLM is installed
_probe = ("import json, torch; print(json.dumps({'torch': torch.__version__, 'cuda': torch.version.cuda, "
          "'gpus': [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]}))")
code, out = sh([sys.executable, "-c", _probe])
ENV = {"python": sys.version.split()[0], "platform": platform.platform()}
try:
    ENV.update(json.loads(out.strip().splitlines()[-1]))
except Exception:
    ENV["torch_probe_error"] = out[-500:]
ENV["nvidia_smi"] = sh("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader")[1].strip()
print("Python :", ENV["python"])
print("torch  :", ENV.get("torch"), "| CUDA:", ENV.get("cuda"))
print("GPUs   :", ENV.get("gpus"), "|", ENV["nvidia_smi"])
print("MODEL_ID =", MODEL_ID, "| PILOT =", PILOT, "| BACKEND =", BACKEND, "| MOCK =", MOCK)
'''

PATHS = '''\
import sys
WORK = "/kaggle/working" if os.path.isdir("/kaggle/working") else os.getcwd()
SRC_DIR = os.path.abspath("medqa_src")
sys.path.insert(0, SRC_DIR)
CACHE = "/tmp/hf_cache"                      # model + dataset cache stays out of /kaggle/working
os.environ["HF_HOME"] = CACHE
os.environ.setdefault("VLLM_WORKER_MULTIPROC_METHOD", "spawn")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
OUT_ROOT = os.path.join(WORK, "outputs")
RESUME_ROOTS = ["/kaggle/input"]            # previous runs attached as notebook input
PREREG = os.path.join(SRC_DIR, "PREREGISTRATION.md")
HF_TOKEN = None
try:
    from kaggle_secrets import UserSecretsClient
    HF_TOKEN = UserSecretsClient().get_secret("HF_TOKEN")
except Exception:
    HF_TOKEN = os.environ.get("HF_TOKEN")
if HF_TOKEN:
    os.environ["HF_TOKEN"] = HF_TOKEN
print("HF_TOKEN available:", bool(HF_TOKEN))
TIMINGS = {}
'''

INSTALL = '''\
# Install vLLM compatible with the PREINSTALLED torch (torch is pinned via a constraints file, so pip picks the
# newest vLLM release built for exactly this torch; wheels are abi3, so Python 3.13 is fine). The dry run checks
# that such a wheel exists before anything is installed. Any failure -> transformers fallback (logged).
t0 = time.time()
BACKEND_NOTE = {"requested": BACKEND}

def _pkg_versions(names):
    code = "import importlib.metadata as m, json\\nout={}\\n" + "".join(
        f"\\ntry: out['{n}']=m.version('{n}')\\nexcept Exception: pass" for n in names) + "\\nprint(json.dumps(out))"
    return json.loads(sh([sys.executable, "-c", code])[1].strip().splitlines()[-1])

def _wheel_exists(url):
    import urllib.request
    try:
        urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=60)
        return True
    except Exception:
        return False

def install_vllm():
    import re
    have = _pkg_versions(["vllm"])
    if "vllm" in have:
        return True, f"vllm {have['vllm']} already installed"
    pins = _pkg_versions(["torch"])
    if "torch" not in pins:
        return False, "torch not installed"
    torch_pub, _, torch_cuda = pins["torch"].partition("+")  # e.g. "2.11.0", "cu128"
    with open("/tmp/vllm_constraints.txt", "w") as f:  # only torch: vLLM may pin other torchaudio/vision
        f.write(f"torch=={torch_pub}\\n")
    base = [sys.executable, "-m", "pip", "install", "--prefer-binary", "-c", "/tmp/vllm_constraints.txt"]
    code, out = sh(base + ["--only-binary", "vllm", "--dry-run", "vllm"], timeout=1200)  # wheel available?
    BACKEND_NOTE["vllm_dry_run_tail"] = out[-1500:]
    m = re.search(r"Would install .*?\\bvllm-(\\d+\\.\\d+\\.\\d+(?:\\.post\\d+)?)\\b", out, re.S)
    if code != 0 or not m:
        return False, "no vLLM release built for this torch version (dry run failed)"
    ver = m.group(1)
    # The PyPI wheel can target a different CUDA major than torch (vLLM 0.26 on PyPI is built for CUDA 13; the
    # Kaggle torch is cu128 -> "libcudart.so.13 not found"). The GitHub release also ships CUDA 12.x builds
    # ("+cu129"); for a CUDA 12 torch, install one of those (same torch version, same CUDA major).
    target = ["vllm"]
    if torch_cuda.startswith("cu12"):
        tags = []
        for t in (torch_cuda, "cu129", "cu128", "cu126"):
            if t not in tags:
                tags.append(t)
        for t in tags:
            url = (f"https://github.com/vllm-project/vllm/releases/download/v{ver}/"
                   f"vllm-{ver}+{t}-cp38-abi3-manylinux_2_28_x86_64.whl")
            if _wheel_exists(url):
                target = [url]
                break
    BACKEND_NOTE["vllm_wheel"] = target[0]
    code, out = sh(base + ["-q"] + target, timeout=2400)
    BACKEND_NOTE["vllm_install_tail"] = out[-1500:]
    after = _pkg_versions(["vllm", "torch"])
    if code != 0 or "vllm" not in after:
        return False, "pip install vllm failed"
    if after.get("torch") != pins.get("torch"):
        return False, f"vLLM install changed torch {pins.get('torch')} -> {after.get('torch')}"
    # torchcodec (optional video decoding pulled in by vLLM) can be built for another torch; it then fails with
    # OSError, which vLLM's optional import does not catch. Text-only study -> remove it if it cannot load.
    if "torchcodec" in _pkg_versions(["torchcodec"]) and sh([sys.executable, "-c", "import torchcodec"])[0] != 0:
        sh([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchcodec"])
        BACKEND_NOTE["removed_broken_torchcodec"] = True
    code, out = sh([sys.executable, "-c", "from vllm import LLM, SamplingParams"], timeout=900)
    if code != 0:  # fail here in seconds, not after the model download
        BACKEND_NOTE["vllm_import_error"] = out[-3000:]
        return False, "vLLM installed but cannot be imported: " + out.strip().splitlines()[-1][:300]
    return True, f"installed vllm {after['vllm']} ({target[0]}) for torch {after['torch']}"

USE_VLLM = False
if MOCK:
    BACKEND_NOTE["install"] = "mock mode: nothing installed"
elif BACKEND in ("auto", "vllm"):
    try:
        USE_VLLM, msg = install_vllm()
    except Exception as e:
        USE_VLLM, msg = False, f"vLLM install error: {e!r}"
    BACKEND_NOTE["install"] = msg
    print(msg)
    if not USE_VLLM and BACKEND == "vllm":
        raise RuntimeError("BACKEND='vllm' requested but vLLM is unavailable: " + msg)
if not MOCK:
    if sh([sys.executable, "-c", "import datasets"])[0] != 0:
        sh([sys.executable, "-m", "pip", "install", "-q", "datasets"])
TIMINGS["install"] = time.time() - t0
print(BACKEND_NOTE)
'''

DATA = '''\
import dataclasses
from config import Config, TEST_ROWS, TRAIN_ROWS
from medqa_conf import data, pipeline, report
cfg = Config(model_id=MODEL_ID, pilot=PILOT)
print("config hash:", cfg.config_hash(), "| model slug:", cfg.model_slug)
t0 = time.time()
if MOCK:
    train_rows, test_rows, DATASET_REVISION = data.synthetic_rows(200, 2), data.synthetic_rows(30, 1), "synthetic"
    QUESTIONS, DATA_INFO = data.load_questions(cfg, train_rows, test_rows, expected_test=30, expected_train=None)
else:
    train_rows, test_rows, DATASET_REVISION = data.load_hf_splits(cfg.dataset_id, cache_dir=os.path.join(CACHE, "datasets"))
    QUESTIONS, DATA_INFO = data.load_questions(cfg, train_rows, test_rows, TEST_ROWS, TRAIN_ROWS)  # fails loudly
TIMINGS["data"] = time.time() - t0
print("dataset revision:", DATASET_REVISION)
print(json.dumps({k: v for k, v in DATA_INFO.items() if k != "pilot_train_indices"}, indent=1))
'''

MODEL = '''\
from medqa_conf import backends
t0 = time.time()
if MOCK:
    MODEL_PATH, MODEL_REV = None, "mock"
    BACKEND_OBJ = backends.MockBackend({q.question: q.gold for q in QUESTIONS})
else:
    MODEL_PATH, MODEL_REV = backends.download_model(MODEL_ID, os.path.join(CACHE, "hub"), MODEL_REVISION, HF_TOKEN)
    print("model revision:", MODEL_REV, "->", MODEL_PATH)
TIMINGS["model_download"] = time.time() - t0

if not MOCK and USE_VLLM:
    t0 = time.time()
    SMOKE_ENV = dict(os.environ, PYTHONPATH=SRC_DIR)
    code, out = sh([sys.executable, "-c", "import config, medqa_conf.backends"], cwd=SRC_DIR, env=SMOKE_ENV)
    if code != 0:  # a setup bug, not a vLLM failure: stop instead of silently falling back
        raise RuntimeError("cannot import medqa_conf in a subprocess:\\n" + out[-2000:])
    try:
        code, out = sh([sys.executable, "-m", "medqa_conf.backends", MODEL_PATH, "vllm"], timeout=1800,
                       cwd=SRC_DIR, env=SMOKE_ENV)
    except subprocess.TimeoutExpired:
        code, out = 1, "smoke test timed out"
    ok = code == 0 and "SMOKE_RESULT" in out
    BACKEND_NOTE["vllm_smoke_test"] = "ok" if ok else out[-3000:]
    TIMINGS["smoke_test"] = time.time() - t0
    if ok:
        print(out[out.index("SMOKE_RESULT"):][:1500])
    else:
        print("vLLM smoke test FAILED -> switching to transformers backend\\n", out[-3000:])
        if BACKEND == "vllm":
            raise RuntimeError("vLLM smoke test failed")
        USE_VLLM = False

t0 = time.time()
if not MOCK:
    if USE_VLLM:
        BACKEND_OBJ = backends.VLLMBackend(MODEL_PATH, cfg)
    else:
        BACKEND_NOTE["switched_to_hf"] = BACKEND != "hf"
        BACKEND_OBJ = backends.HFBackend(MODEL_PATH, cfg)
TIMINGS["model_load"] = time.time() - t0
BACKEND_NOTE["used"] = BACKEND_OBJ.name
print("backend:", BACKEND_OBJ.name, json.dumps(BACKEND_OBJ.info(), default=str)[:800])
'''

RUN = '''\
OUT_DIR = os.path.join(OUT_ROOT, cfg.model_slug)
RESULT = pipeline.run(cfg, BACKEND_OBJ, QUESTIONS, DATA_INFO, OUT_DIR, model_revision=MODEL_REV,
                      dataset_revision=DATASET_REVISION, resume_roots=RESUME_ROOTS,
                      time_budget_s=TIME_BUDGET_HOURS * 3600, t_start=T_START, timings=TIMINGS, env=ENV,
                      prereg_path=PREREG, code_dir=SRC_DIR, backend_note=BACKEND_NOTE)
print(RESULT["status"], "->", OUT_DIR)
'''

FINISH = '''\
if RESULT["status"] != "complete":
    print("=" * 80)
    print(f"RUN INCOMPLETE: {RESULT['n_done']}/{len(QUESTIONS)} questions are checkpointed in {OUT_DIR}/checkpoint.jsonl")
    print("To resume: open this notebook, Add Input -> Notebook Output -> this notebook's version, then Save & Run All.")
    print("=" * 80)
elif PILOT:
    print(RESULT["pilot_report"])
    print(open(os.path.join(OUT_DIR, "sanity_report.md"), encoding="utf-8").read())
    pipeline.check_pilot(RESULT)   # raises PilotAbort if the projected full run exceeds 11 h
    print("PILOT OK -> set PILOT = False and run again for the full test-split run.")
else:
    print(open(os.path.join(OUT_DIR, "results_table.md"), encoding="utf-8").read()[:6000])
    print("Share bundle:", RESULT["bundle"])
'''

GEN_INTRO = """\
# MedQA confidence signals — generation + analysis (one model per run)

Pre-registered study: *Which confidence signal works for medical QA?* (see `PREREGISTRATION.md`, inlined below).

**Before running:** Accelerator = **GPU T4 x2**, Internet = **on**, Kaggle secret **`HF_TOKEN`** (needed for Llama;
accept the model licence on Hugging Face first). Edit only `MODEL_ID` and `PILOT` in the first cell, then
**Save & Run All (Commit)**.

1. `PILOT = True`: 20 *train* questions; prints prompts, raw outputs, parse rates, letter mass, throughput and the
   projected full runtime; aborts if > 11 h.
2. `PILOT = False`: full run on the 1,273 test questions. Outputs: `/kaggle/working/outputs/<model_slug>/`, including
   `share_bundle_<model_slug>.zip`.
3. **Resume**: if a run stopped early, add this notebook's previous output as an input and run again; finished
   questions are skipped (same model + config hash + revision + backend required).
"""

COMBINE_INTRO = """\
# MedQA confidence signals — combine models (CPU only)

Add each model's run output (or its `share_bundle_<model>.zip`) as notebook input, then Save & Run All.
Everything is recomputed from the per-model `per_question.csv` files; Holm correction is applied across all
pairs × non-flagged models within each setting (CoT = primary family). Output: `/kaggle/working/combined/share_bundle_all.zip`.
"""

COMBINE_RUN = '''\
import glob, os, sys, time
MOCK = os.environ.get("MEDQA_MOCK") == "1"
INPUTS = ["/kaggle/input"] if os.path.isdir("/kaggle/input") else [os.environ.get("MEDQA_COMBINE_INPUT", "outputs")]
print("Python", sys.version.split()[0])
sys.path.insert(0, os.path.abspath("medqa_src"))
from medqa_conf import report
WORK = "/kaggle/working" if os.path.isdir("/kaggle/working") else os.getcwd()
csvs = report._find_csvs(INPUTS)
zips = [] if csvs else sorted(glob.glob(os.path.join(INPUTS[0], "**", "share_bundle_*.zip"), recursive=True))
zips = [z for z in zips if not z.endswith("share_bundle_all.zip")]
print("found CSVs:", csvs, "\\nfound bundles:", zips)
t0 = time.time()
C = report.combine(csvs or zips, os.path.join(WORK, "combined"), prereg_path="medqa_src/PREREGISTRATION.md")
print(open(os.path.join(WORK, "combined", "results_all.md"), encoding="utf-8").read())
print("models:", C["models"], "| bundle:", C["bundle"], f"| {time.time() - t0:.1f}s")
'''


def build_generate() -> nbformat.NotebookNode:
    nb = new_notebook()
    nb.cells = [new_markdown_cell(GEN_INTRO), new_code_cell(SETTINGS),
                new_markdown_cell("## Source code (inlined; written to `medqa_src/`)")]
    nb.cells += writefile_cells()
    nb.cells += [new_markdown_cell("## Paths, secrets"), new_code_cell(PATHS),
                 new_markdown_cell("## Install vLLM (or fall back to transformers)"), new_code_cell(INSTALL),
                 new_markdown_cell("## Data (fails loudly on schema/count problems)"), new_code_cell(DATA),
                 new_markdown_cell("## Model: download exact revision, vLLM smoke test, load"), new_code_cell(MODEL),
                 new_markdown_cell("## Generate (checkpoint every 50 questions, resume) → analyse → bundle"),
                 new_code_cell(RUN), new_markdown_cell("## Pilot report / results"), new_code_cell(FINISH)]
    _meta(nb, gpu=True)
    return nb


def build_combine() -> nbformat.NotebookNode:
    nb = new_notebook()
    nb.cells = [new_markdown_cell(COMBINE_INTRO)] + writefile_cells() + [new_code_cell(COMBINE_RUN)]
    _meta(nb, gpu=False)
    return nb


def _meta(nb, gpu):
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb.metadata["language_info"] = {"name": "python"}
    nb.metadata["kaggle"] = {"accelerator": "nvidiaTeslaT4" if gpu else "none", "isInternetEnabled": gpu,
                             "isGpuEnabled": gpu, "language": "python", "sourceType": "notebook"}


def execute_mock(nb_paths):
    """Run notebooks top to bottom on CPU in MOCK mode, in a temp working dir."""
    from nbclient import NotebookClient
    work = tempfile.mkdtemp(prefix="medqa_nb_")
    os.environ["MEDQA_MOCK"] = "1"
    for pilot in (True, False):
        nb = nbformat.read(nb_paths[0], as_version=4)
        if not pilot:
            nb.cells[1].source = nb.cells[1].source.replace("PILOT = True ", "PILOT = False")
        NotebookClient(nb, timeout=1800, kernel_name="python3", resources={"metadata": {"path": work}}).execute()
        print(f"generate notebook OK (PILOT={pilot}) in {work}")
    os.environ["MEDQA_COMBINE_INPUT"] = os.path.join(work, "outputs")
    nb = nbformat.read(nb_paths[1], as_version=4)
    NotebookClient(nb, timeout=1800, kernel_name="python3", resources={"metadata": {"path": work}}).execute()
    print("combine notebook OK")
    for root, _, files in os.walk(os.path.join(work, "outputs")):
        for f in files:
            if f.endswith(".zip"):
                print(" ", os.path.join(root, f), os.path.getsize(os.path.join(root, f)))
    return work


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--execute-mock", action="store_true")
    a = a.parse_args()
    out = os.path.join(ROOT, "kaggle")
    os.makedirs(out, exist_ok=True)
    paths = [os.path.join(out, "generate_and_analyze.ipynb"), os.path.join(out, "combine_models.ipynb")]
    for p, nb in zip(paths, (build_generate(), build_combine())):
        nbformat.validate(nb)
        nbformat.write(nb, p)
        print("wrote", p, os.path.getsize(p), "bytes")
    if a.execute_mock:
        work = execute_mock(paths)
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
