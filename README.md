# Which confidence signal works for medical QA?

Pre-registered comparison of three confidence signals for open LLMs on MedQA (USMLE, 4 options, 1,273 test
questions): **stated confidence** (the model writes 0–100), **option probability** (probability of the chosen
letter) and **sample agreement** (share of 5 CoT samples that match the official answer). Primary metric: AUROC
for correctness; also ECE, adaptive ECE, Brier, overconfidence gap, selective accuracy at 80% coverage and AURC,
with paired bootstrap CIs, paired DeLong tests and Holm correction.

All choices (prompts, models, sampling, metrics, bins, hypotheses, decision rule, validity flags) are fixed in
[PREREGISTRATION.md](PREREGISTRATION.md), committed before any GPU run.

## Repository

```
config.py                    pre-registered constants + config hash
src/medqa_conf/
  data.py       load MedQA, fail loudly on counts/schema, clean options, gold-letter distribution
  prompts.py    verbatim prompts and prefills
  parsing.py    answer / confidence parsing
  backends.py   VLLMBackend, HFBackend (own seeded KV-cache decoding loop), MockBackend; smoke test
  generate.py   model calls 1–6, letter distribution, JSONL checkpoint every 50 q, resume, time budget
  signals.py    raw records -> per_question.csv
  metrics.py    AUROC, ECE, adaptive ECE, Brier, tie-aware selective accuracy / risk-coverage / AURC, Wilson
  stats.py      paired bootstrap, fast DeLong, Holm, cross-fitted Platt scaling
  report.py     summary.json / results_table.md / figures from the CSV alone; --from-csv; --combine
  sanity.py     sanity_report.md
  bundle.py     run_log.json, raw_examples.md, share bundle
  pipeline.py   orchestration (+ CPU mock run)
tests/                       CPU tests (toy example, sklearn equality, tie brute force, DeLong, parsing, e2e)
tools/build_kaggle_notebook.py   builds kaggle/*.ipynb with all source inlined
kaggle/generate_and_analyze.ipynb   one model per run (GPU)
kaggle/combine_models.ipynb         merges per-model outputs (CPU)
```

## Running on Kaggle

### Settings (once per notebook)

- **Accelerator:** GPU T4 x2. **Internet:** on.
- **Secret:** Add-ons → Secrets → `HF_TOKEN` = a Hugging Face read token, attached to the notebook.
- **Licences:** on Hugging Face, accept the licence/terms for `meta-llama/Llama-3.1-8B-Instruct` (gated) and
  `mistralai/Mistral-7B-Instruct-v0.3` with the same account as the token. Qwen needs nothing.
- Upload `kaggle/generate_and_analyze.ipynb` (File → Import Notebook). It is self-contained: the first code
  cells write the package to `/kaggle/working/medqa_src/`.

### Per model: pilot, then full run

1. In the first code cell set `MODEL_ID` and `PILOT = True`. **Save & Run All (Commit).**
   The pilot uses 20 **train** questions (never test). Its output (`outputs/<slug>_pilot/pilot_report.md`, also
   printed in the last cell) shows 3 fully rendered prompts with raw outputs, parse rates, letter mass,
   throughput and the projected full runtime. The last cell raises `PilotAbort` if the projection exceeds 11 h.
2. If the pilot looks right, set `PILOT = False` and commit again. Outputs go to
   `/kaggle/working/outputs/<model_slug>/`.
3. Repeat for each model (`Qwen/Qwen2.5-7B-Instruct`, `meta-llama/Llama-3.1-8B-Instruct`,
   `mistralai/Mistral-7B-Instruct-v0.3`).

Model slugs: `qwen2_5_7b_instruct`, `llama_3_1_8b_instruct`, `mistral_7b_instruct_v0_3` (pilot: `+_pilot`).

Optional knobs in the first cell: `BACKEND` (`"auto"` = vLLM with transformers fallback; `"vllm"`; `"hf"`),
`TIME_BUDGET_HOURS` (default 11.0), `MODEL_REVISION` (pin a commit hash; default: latest, resolved and logged).

### Backend selection

The install cell pins the preinstalled torch in a pip constraints file and asks pip (dry run first) for the
newest vLLM release built for exactly that torch. vLLM wheels are `abi3`, so the Python 3.13 image is fine.
Then the model loads in a **subprocess smoke test** (TP=2, fp16, 8 tokens and one logprob call), so a failed
start can't leave the kernel holding GPU memory. If any step fails, the notebook switches to the transformers
backend and records why in `run_log.json` (`backend_note`). The pilot projection then measures that backend.

### Resuming an interrupted run

Generation writes `outputs/<slug>/checkpoint.jsonl` every 50 questions. Generation also stops on its own
before `TIME_BUDGET_HOURS`, keeping the checkpoint, and the last cell prints `RUN INCOMPLETE`. To resume:

1. Open the notebook → **Add Input** → *Notebook Output Files* → select the previous version of this notebook.
2. Keep `MODEL_ID` / `PILOT` unchanged and **Save & Run All** again.

On start, the notebook searches `/kaggle/input/**/<slug>/checkpoint.jsonl`. It reuses the finished questions
only when model id, config hash, model revision and backend all match; a different revision or backend stops
the run with an explanation, because mixing outputs is not allowed. Leave `MODEL_REVISION = None` only if the HF
repo did not change in between; otherwise pin the hash from the first run's `run_log.json`.

### Where the results are

`/kaggle/working/outputs/<slug>/` (download from the notebook's Output tab):

| file | content |
|---|---|
| `share_bundle_<slug>.zip` | everything below + PREREGISTRATION.md + source code; **no raw generations**; < 5 MB (checked) |
| `per_question.csv` | one row per qid × setting, no raw text |
| `summary.json`, `results_table.md` | every metric, CI, test statistic, p-value, hypothesis verdict |
| `figures/` | reliability diagrams, risk–coverage curves, histograms (per setting) |
| `sanity_report.md`, `run_log.json`, `raw_examples.md` | diagnostics, versions/GPU/revision/seeds/config hash/timings, 12 examples |
| `raw_generations.jsonl.gz`, `checkpoint.jsonl` | raw text (not in the bundle) |

### Combining models

Upload `kaggle/combine_models.ipynb` (CPU is enough). Add each model's run output (or its
`share_bundle_<slug>.zip`) as input and run all. It recomputes every model from its `per_question.csv`,
applies Holm across all pairs × non-flagged models within each setting (CoT = primary family), and writes
`/kaggle/working/combined/share_bundle_all.zip`. Pilot outputs are ignored.

## How the runtime projection works

In the pilot, `seconds_per_question` = generation wall time for the 20 pilot questions (all six calls, chunked
like the main run) / 20. Projected full run = setup (vLLM install + download + smoke test + model load, as
measured) + `seconds_per_question × 1273` + the measured determinism re-run + max(measured analysis, 15 min).
The projection is conservative: the main run batches 50 questions per chunk (about 300 sequences for vLLM),
the pilot only 20. The pilot aborts if the projection is over 11 h. Even then, a run that gets close can
finish over two sessions with resume.

## Local use (CPU)

```bash
pip install numpy scipy pandas scikit-learn matplotlib pytest nbformat nbclient ipykernel
```

```bash
python -m pytest -q
```

```bash
PYTHONPATH=src:. python -m medqa_conf.pipeline --mock --n 1273 --out outputs_mock
```

```bash
PYTHONPATH=src:. python -m medqa_conf.report --from-csv outputs_mock/mock_7b/per_question.csv --out /tmp/repro
```

```bash
python tools/build_kaggle_notebook.py --execute-mock
```

The first `--from-csv` command recomputes `summary.json` byte-for-byte from the CSV (a test checks this).
`--execute-mock` rebuilds both notebooks and runs them top to bottom on CPU with the mock backend
(`MEDQA_MOCK=1`, never set on Kaggle). Always rebuild the notebooks after editing `src/`.
On Windows, use `;` instead of `:` in `PYTHONPATH`.

## Notes on interpretation

- The official answer in each setting is argmax of the letter distribution `p`. All three signals are scored
  against it. In CoT, the letter written in the reasoning can differ; `sanity_report.md` reports how often.
- Complete-case analysis drops questions with a missing signal (practically only `conf_stated`), so N and
  k = floor(0.8·N) can be slightly below 1,273 / 1,018. The median-imputation sensitivity analysis uses all
  questions.
- Exploratory analyses (majority vote, entropy, rank average, by `meta_info`, Platt-scaled ECE) are labelled as
  such and are not part of the conclusions.
