# Pre-registration: Which confidence signal works for medical QA?

- Registered: 2026-10-10 (git commit date of this file is the authoritative timestamp)
- Status: written and committed **before any GPU run**. No model output on the MedQA test split has been seen.
- Any change to a pre-registered choice after this commit will be listed in a "Deviations" section appended to this file, with date and reason.

## 1. Research question

Which signal best separates right from wrong answers of open LLMs on MedQA (USMLE, 4 options, 1,273 test questions)?

- (a) **stated confidence** (`conf_stated`): the model writes a number from 0 to 100.
- (b) **option probability** (`conf_prob`): the probability of the chosen letter.
- (c) **sample agreement** (`conf_agree`): the share of 5 sampled answers that match the official answer.

Primary measure: AUROC for correctness. Secondary: calibration error (ECE), and selective accuracy when the model answers only its 80% most-confident questions.

## 2. Data

- HF dataset `GBaker/MedQA-USMLE-4-options` (CC-BY-4.0). Splits: train (10,178 rows), test (1,273 rows). The dataset revision (commit hash) is resolved at run time and logged.
- Fields used: `question`, `options` (dict A–D), `answer_idx` (gold letter), `answer` (gold text), `meta_info` (`step1` / `step2&3`).
- The run **fails** unless the test split has exactly 1,273 rows, every row has exactly the 4 option keys A, B, C, D, and every gold letter is in A–D.
- `qid` = row index in the test split. The sha1 of the raw question text is stored.
- Cleaning (only): question text and option texts are stripped of surrounding whitespace; an option text ending in a `"` with an odd number of `"` characters (an unbalanced, stray quote) has that trailing `"` removed and is stripped again. The number of cleaned options is logged. The gold-letter distribution is logged.
- The **test split is used only for the main run.** The pilot uses 20 questions from the **train** split (row indices drawn with `numpy.random.default_rng(BASE_SEED).choice(10178, 20, replace=False)`, sorted).

## 3. Models

One model per run:

1. `Qwen/Qwen2.5-7B-Instruct`
2. `meta-llama/Llama-3.1-8B-Instruct`
3. `mistralai/Mistral-7B-Instruct-v0.3`

- float16 (T4 has no bf16). No model families known to overflow in fp16.
- No system message: everything is in the single user message. (A chat template that injects its own default system text, e.g. Qwen2.5, is used as-is; the rendered prompt is logged.)
- Any "thinking mode" is disabled (`enable_thinking=False` is passed to the chat template).
- The exact HF revision (commit hash) is resolved, downloaded and logged.
- Hardware: Kaggle, 2× T4 16 GB. Backend: vLLM (tensor_parallel_size 2, float16, max_model_len 4096, top-20 logprobs) preferred; transformers fallback if vLLM cannot be installed/started (the switch is logged).

## 4. Prompts (verbatim)

Every prompt is built with the tokenizer's chat template (`add_generation_prompt=True`). "Prefill" means text appended after the generation prompt, as the start of the assistant turn. Prompts are tokenized without adding extra special tokens (the template already contains them).

Shared question block:

```
The following is a multiple-choice question from the US Medical Licensing Examination (USMLE). Choose the single best answer.

Question: {question}
A. {A}
B. {B}
C. {C}
D. {D}
```

**CoT user message** (main, pre-registered setting) = question block followed by:

```

Think through the problem step by step. Then finish with exactly these two lines:
Answer: <A, B, C or D>
Confidence: <a number from 0 to 100: the probability that your answer is correct>
```

**Direct user message** (secondary setting) = question block followed by:

```

Reply with exactly these two lines and nothing else:
Answer: <A, B, C or D>
Confidence: <a number from 0 to 100: the probability that your answer is correct>
```

## 5. Model calls per question

| # | Call | Settings |
|---|---|---|
| 1 | CoT greedy → text `G` | temperature 0, max_new_tokens 1024 |
| 2 | CoT samples → `S1..S5` | n = 5, temperature 0.7, top_p 1.0, no top-k, no repetition penalty, max_new_tokens 1024, seed = BASE_SEED + qid |
| 3 | CoT letter probability | prompt = chat prompt + `G` up to and including its last `Answer:` (exact, case-sensitive string). If `G` has no `Answer:`, prefix = `G.rstrip() + "\nAnswer:"` and flag `forced_answer`. Read next-token log-probabilities → letter distribution `p`. **Official CoT answer X = argmax p.** |
| 4 | CoT stated confidence | parsed from `G`. Only if none can be parsed: prefill = CoT prefix + `" {X}\nConfidence:"`, greedy, max 6 new tokens; flag `stated_recovered`. |
| 5 | Direct letter probability | prefill `Answer:`; next-token log-probabilities → `p`. **Official Direct answer X = argmax p.** |
| 6 | Direct stated confidence | prefill `Answer: {X}\nConfidence:`, greedy, max 6 new tokens. |

Seeds: `BASE_SEED = 12345`; engine seed = BASE_SEED; bootstrap seed = 2026; cross-fitting seed = 2026. Model-provided generation-config defaults (e.g. top_k, repetition_penalty) are overridden by the values above; EOS token ids are taken from the model's generation config.

### Letter distribution

- For each letter L, sum the probabilities of the single-token variants `"L"` and `" L"` (the variants present in the vocabulary are detected and their token ids logged).
- `letter_mass` = total probability on the 4 letters before renormalising; `p` = distribution renormalised over the 4 letters.
- With vLLM top-20 logprobs, a variant missing from the top 20 contributes 0; the frequency of any letter missing is logged. With the transformers backend the full distribution is used.
- argmax ties (practically impossible) are broken alphabetically.
- If `letter_mass` is 0 (no letter in the top 20), `p` is uniform and the answer is A; the count is reported.
- In CoT, the letter written in `G` is also parsed; the rate at which it disagrees with argmax p is reported.

### Answer parsing

- Primary: the **last** match of `answer` (case-insensitive word) optionally followed by `**`, then `:`, then optional `**`, optional `(` or `[`, then one capital letter A–D not followed by another letter. Tolerates `**Answer:** C`, `**Answer: C**`, `Answer: (C)`, `Final Answer: C`.
- Fallback: last match of `answer is` followed by an optional `:`/`(`/`**`/"option" and a capital A–D (not followed by a letter).
- Otherwise None. The method used (`answer_line`, `answer_is`, `none`) is recorded.

## 6. Signals (per setting)

- **conf_stated** = parsed number / 100, clipped to [0, 1]. Last match of `confidence` (case-insensitive) with optional `**`, `:`, optional `**`, then a number (`85`, `85.5`, `.9`); `%` and extra spaces tolerated. If the value is ≤ 1 **and** contains a decimal point it is a fraction (used as-is) and `stated_fraction_flag` is set. For the 6-token generations (CoT recovery, Direct), the first number in the generated text is parsed with the same rule. Missing after recovery → NaN; the count is reported.
- **conf_prob** = p[official answer], range [0.25, 1].
- **conf_agree** = (# of the 5 CoT samples whose parsed answer equals the official answer) / 5. An unparsable sample counts as disagreeing. The Direct setting uses the **same 5 CoT samples**.
- All three signals are scored against the **same official answer** X (section 5). y = 1 iff X equals the gold letter.

**Exploratory analyses** (labelled exploratory, excluded from main conclusions): majority-vote accuracy over the 5 samples (ties broken by the setting's official answer, then alphabetically; with no parsable sample, the official answer); entropy (natural log) of the 5 sample answers, with "unparsed" as its own category; rank-average of conf_prob and conf_agree (mean of average ranks); results by `meta_info`; ECE after 5-fold cross-fitted Platt scaling (unregularised logistic regression on the raw signal, folds shuffled with seed 2026).

## 7. Metrics and statistics

Per model × setting × signal:

- **Accuracy** with Wilson 95% CI.
- **AUROC** for correctness, ties count ½ (identical to `sklearn.metrics.roc_auc_score`).
- **ECE**: 15 equal-width bins on [0, 1], edges `i/15`; bins left-closed, the last bin also includes 1.0; weighted mean |accuracy − mean confidence|. (The function accepts custom edges.)
- **Adaptive ECE**: 15 equal-mass bins: items sorted by confidence (stable sort, ties kept in qid order) and split into 15 contiguous groups with `numpy.array_split`.
- **Brier score**; **overconfidence gap** = mean confidence − accuracy.
- **Selective accuracy at 80% coverage**: k = floor(0.8·N) (1,018 for N = 1,273), questions ranked by confidence, highest first. Ties at the cutoff: exact expected accuracy under random tie-breaking = (correct above the tied group + needed × accuracy of the tied group) / k. References: overall accuracy (random ranking) and oracle min(#correct, k)/k.
- **Risk–coverage curve and AURC**, tie-aware: for every k = 1..N the expected risk under random tie-breaking; AURC = mean over k.
- **Paired bootstrap**: 2,000 resamples of questions; within a model × setting all signals use the same indices; percentile 95% CIs for every metric and every pairwise difference.
- **DeLong**: paired fast DeLong (Sun & Xu 2014) for the 3 pairwise AUROC differences; two-sided p.
- **Holm**: per-model report: across that model's 3 pairs; combined report: across all pairs × (non-flagged) models within a setting. **The primary family is the CoT setting.**
- **Missing values**: primary analysis is complete-case (a question with any NaN signal is dropped for all signals; N used is reported). Sensitivity analysis: missing conf_stated imputed with its median.

## 8. Hypotheses and decision rule

- **H1**: in the CoT setting, conf_stated has a lower AUROC than both conf_prob and conf_agree, for each model.
- **H2**: conf_stated is overconfident (mean confidence − accuracy > 0) and has the highest ECE.
- **H3** (two-sided, no direction predicted): conf_prob and conf_agree differ in AUROC.

**Decision rule.** An AUROC difference is "supported" when the Holm-adjusted DeLong p < 0.05 **and** the paired bootstrap 95% CI of the difference excludes 0 (and, for H1, the difference has the predicted sign). DeLong applies only to AUROC, so H2 is judged by bootstrap alone: supported when the 95% CI of the overconfidence gap lies above 0 **and** the 95% CIs of ECE(stated) − ECE(prob) and ECE(stated) − ECE(agree) both lie above 0. Effect sizes with CIs are always reported. H1/H2/H3 are evaluated on the primary (complete-case, CoT) analysis; Direct results are secondary.

**Validity flags.** A model (per setting) is flagged, reported separately and excluded from the main comparison if any of these hold:

- accuracy < 40%;
- answer parse failure > 10% of CoT greedy outputs;
- median letter_mass < 0.5;
- truncation (finish_reason == "length") > 10% of CoT samples.

Parse failure and truncation are properties of the CoT generations and apply to both settings of that model.

## 9. Sanity checks (written to `sanity_report.md`)

[fail] = stops the run.

- [fail] dataset counts and schema; [fail] NaN or inf in any returned logprob.
- Parse-failure rates (greedy answer; greedy confidence before and after recovery; samples).
- letter_mass distribution, rate of any letter missing from top-k, CoT parsed-vs-argmax mismatch rate.
- Truncation rates; chosen vs gold letter distribution; per-signal histogram counts and fraction of tied values (and the 5 most common conf_stated values).
- Greedy determinism: greedy CoT re-run on 10 questions, number of identical outputs.
- Validity flags.

## 10. Pilot

20 train questions (section 2), same pipeline, used only to check formatting, parse rates, letter_mass, NaN/garbage output and throughput. The run aborts if the projected full runtime exceeds 11 hours. Pilot results are not part of the study.
