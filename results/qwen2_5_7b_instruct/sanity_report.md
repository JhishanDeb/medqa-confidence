# Sanity report: Qwen/Qwen2.5-7B-Instruct

## [fail] checks

- PASS dataset counts and schema: test split = 1273 rows, 4 options A–D, gold in A–D (run would have stopped otherwise). Split used: test (1273 questions).
- PASS no NaN/inf in any returned logprob (run would have stopped otherwise).

## Data

- Options cleaned (whitespace / stray trailing quote): test 43, used split 43
- Gold answer text ≠ option text after cleaning: 0
- Gold-letter distribution (used split): {'A': 353, 'B': 309, 'C': 346, 'D': 265}
- Gold-letter distribution (test split): {'A': 353, 'B': 309, 'C': 346, 'D': 265}
- meta_info (used split): {'step1': 679, 'step2&3': 594}

## Parsing

- Greedy answer parse failure: 0.2% (methods: {'answer_line': 1270, 'none': 3})
- Greedy confidence missing before recovery: 0.0%; after recovery: 0.0% (0 recovered)
- Sample answer parse failure: 0.2%
- CoT forced_answer (no 'Answer:' in G): 0.2%
- CoT parsed letter ≠ argmax p: 0.0% (of 1270 parsed)
- Direct confidence missing: 0

## Letter distribution

- cot: letter_mass min 0.529, p5 1.000, p25 1.000, median 1.000, p75 1.000, p95 1.000, max 1.000; any letter missing from top-k: 0.4%; zero letter mass: 0
- direct: letter_mass min 0.973, p5 1.000, p25 1.000, median 1.000, p75 1.000, p95 1.000, max 1.000; any letter missing from top-k: 0.2%; zero letter mass: 0

## Truncation (finish_reason == length)

- Greedy: 0.0%; samples: 0.0%

## Position bias (chosen vs gold letters)

- gold: {'B': 309, 'D': 265, 'C': 346, 'A': 353}
- cot chosen: {'A': 322, 'B': 339, 'D': 274, 'C': 338} (accuracy 0.639)
- direct chosen: {'A': 338, 'C': 330, 'B': 335, 'D': 270} (accuracy 0.597)

## Signals (15 equal-width bins on [0,1])

- cot conf_stated: hist [1, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 132, 5, 1133]; fraction tied 0.999; unique 7; top-5 values [[0.95, 973], [1.0, 160], [0.85, 126], [0.8, 6], [0.9, 5]]; fraction-format flags 0
- cot conf_prob: hist [0, 0, 0, 0, 0, 0, 3, 3, 4, 14, 10, 6, 14, 18, 1201]; fraction tied 0.002; unique 1272; fraction-format flags -
- cot conf_agree: hist [68, 0, 0, 83, 0, 0, 93, 0, 0, 133, 0, 0, 220, 0, 676]; fraction tied 1.000; unique 6; fraction-format flags -
- direct conf_stated: hist [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 909, 0, 362]; fraction tied 0.998; unique 6; top-5 values [[0.85, 907], [0.95, 350], [1.0, 12], [0.8, 2], [0.7, 1]]; fraction-format flags 0
- direct conf_prob: hist [0, 0, 0, 0, 1, 3, 8, 22, 22, 26, 26, 36, 39, 68, 1022]; fraction tied 0.000; unique 1273; fraction-format flags -
- direct conf_agree: hist [88, 0, 0, 97, 0, 0, 114, 0, 0, 120, 0, 0, 201, 0, 653]; fraction tied 1.000; unique 6; fraction-format flags -

## Greedy determinism

- Re-ran CoT greedy on 10 questions: 9/10 byte-identical (differing qids: [1])

## Validity flags (PREREGISTRATION.md section 8)

- cot: not flagged — values accuracy 0.639, greedy_parse_fail_rate 0.002, median_letter_mass 1.000, sample_truncation_rate 0.000 — flags accuracy_below_min=False, parse_fail_above_max=False, letter_mass_below_min=False, truncation_above_max=False
- direct: not flagged — values accuracy 0.597, greedy_parse_fail_rate 0.002, median_letter_mass 1.000, sample_truncation_rate 0.000 — flags accuracy_below_min=False, parse_fail_above_max=False, letter_mass_below_min=False, truncation_above_max=False
