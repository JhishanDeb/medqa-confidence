# Sanity report: mistralai/Mistral-7B-Instruct-v0.3

## [fail] checks

- PASS dataset counts and schema: test split = 1273 rows, 4 options A–D, gold in A–D (run would have stopped otherwise). Split used: train (20 questions).
- PASS no NaN/inf in any returned logprob (run would have stopped otherwise).

## Data

- Options cleaned (whitespace / stray trailing quote): test 43, used split 1
- Gold answer text ≠ option text after cleaning: 0
- Gold-letter distribution (used split): {'A': 5, 'B': 5, 'C': 5, 'D': 5}
- Gold-letter distribution (test split): {'A': 353, 'B': 309, 'C': 346, 'D': 265}
- meta_info (used split): {'step1': 13, 'step2&3': 7}

## Parsing

- Greedy answer parse failure: 0.0% (methods: {'answer_line': 20})
- Greedy confidence missing before recovery: 0.0%; after recovery: 0.0% (0 recovered)
- Sample answer parse failure: 0.0%
- CoT forced_answer (no 'Answer:' in G): 0.0%
- CoT parsed letter ≠ argmax p: 0.0% (of 20 parsed)
- Direct confidence missing: 0

## Letter distribution

- cot: letter_mass min 0.999, p5 1.000, p25 1.000, median 1.000, p75 1.000, p95 1.000, max 1.000; any letter missing from top-k: 10.0%; zero letter mass: 0
- direct: letter_mass min 0.970, p5 0.994, p25 0.999, median 1.000, p75 1.000, p95 1.000, max 1.000; any letter missing from top-k: 15.0%; zero letter mass: 0

## Truncation (finish_reason == length)

- Greedy: 0.0%; samples: 0.0%

## Position bias (chosen vs gold letters)

- gold: {'B': 5, 'C': 5, 'D': 5, 'A': 5}
- cot chosen: {'B': 3, 'A': 8, 'D': 6, 'C': 3} (accuracy 0.450)
- direct chosen: {'B': 4, 'A': 8, 'C': 3, 'D': 5} (accuracy 0.550)

## Signals (15 equal-width bins on [0,1])

- cot conf_stated: hist [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 19]; fraction tied 0.950; unique 3; top-5 values [[0.95, 12], [1.0, 7], [0.9, 1]]; fraction-format flags 0
- cot conf_prob: hist [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 1, 16]; fraction tied 0.000; unique 20; fraction-format flags -
- cot conf_agree: hist [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 2, 0, 17]; fraction tied 0.950; unique 3; fraction-format flags -
- direct conf_stated: hist [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 19]; fraction tied 0.950; unique 4; top-5 values [[0.95, 12], [0.99, 5], [1.0, 2], [0.9, 1]]; fraction-format flags 0
- direct conf_prob: hist [0, 0, 0, 0, 0, 0, 0, 2, 2, 0, 1, 1, 1, 2, 11]; fraction tied 0.000; unique 20; fraction-format flags -
- direct conf_agree: hist [3, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 14]; fraction tied 0.850; unique 5; fraction-format flags -

## Greedy determinism

- Re-ran CoT greedy on 10 questions: 10/10 byte-identical

## Validity flags (PREREGISTRATION.md section 8)

- cot: not flagged — values accuracy 0.450, greedy_parse_fail_rate 0.000, median_letter_mass 1.000, sample_truncation_rate 0.000 — flags accuracy_below_min=False, parse_fail_above_max=False, letter_mass_below_min=False, truncation_above_max=False
- direct: not flagged — values accuracy 0.550, greedy_parse_fail_rate 0.000, median_letter_mass 1.000, sample_truncation_rate 0.000 — flags accuracy_below_min=False, parse_fail_above_max=False, letter_mass_below_min=False, truncation_above_max=False
