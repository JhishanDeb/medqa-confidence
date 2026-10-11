# Sanity report: Qwen/Qwen2.5-7B-Instruct

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

- cot: letter_mass min 1.000, p5 1.000, p25 1.000, median 1.000, p75 1.000, p95 1.000, max 1.000; any letter missing from top-k: 0.0%; zero letter mass: 0
- direct: letter_mass min 1.000, p5 1.000, p25 1.000, median 1.000, p75 1.000, p95 1.000, max 1.000; any letter missing from top-k: 0.0%; zero letter mass: 0

## Truncation (finish_reason == length)

- Greedy: 0.0%; samples: 0.0%

## Position bias (chosen vs gold letters)

- gold: {'B': 5, 'C': 5, 'D': 5, 'A': 5}
- cot chosen: {'B': 2, 'C': 4, 'A': 9, 'D': 5} (accuracy 0.600)
- direct chosen: {'B': 3, 'A': 8, 'C': 4, 'D': 5} (accuracy 0.650)

## Signals (15 equal-width bins on [0,1])

- cot conf_stated: hist [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 15]; fraction tied 1.000; unique 3; top-5 values [[0.95, 13], [0.85, 5], [1.0, 2]]; fraction-format flags 0
- cot conf_prob: hist [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 19]; fraction tied 0.000; unique 20; fraction-format flags -
- cot conf_agree: hist [2, 0, 0, 0, 0, 0, 2, 0, 0, 1, 0, 0, 5, 0, 10]; fraction tied 0.950; unique 5; fraction-format flags -
- direct conf_stated: hist [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 16, 0, 4]; fraction tied 1.000; unique 2; top-5 values [[0.85, 16], [0.95, 4]]; fraction-format flags 0
- direct conf_prob: hist [0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 18]; fraction tied 0.000; unique 20; fraction-format flags -
- direct conf_agree: hist [2, 0, 0, 1, 0, 0, 2, 0, 0, 1, 0, 0, 5, 0, 9]; fraction tied 0.900; unique 6; fraction-format flags -

## Greedy determinism

- Re-ran CoT greedy on 10 questions: 7/10 byte-identical (differing qids: [2309, 3976, 5772])

## Validity flags (PREREGISTRATION.md section 8)

- cot: not flagged — values accuracy 0.600, greedy_parse_fail_rate 0.000, median_letter_mass 1.000, sample_truncation_rate 0.000 — flags accuracy_below_min=False, parse_fail_above_max=False, letter_mass_below_min=False, truncation_above_max=False
- direct: not flagged — values accuracy 0.650, greedy_parse_fail_rate 0.000, median_letter_mass 1.000, sample_truncation_rate 0.000 — flags accuracy_below_min=False, parse_fail_above_max=False, letter_mass_below_min=False, truncation_above_max=False
