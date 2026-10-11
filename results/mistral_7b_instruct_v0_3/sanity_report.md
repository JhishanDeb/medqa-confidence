# Sanity report: mistralai/Mistral-7B-Instruct-v0.3

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

- Greedy answer parse failure: 0.3% (methods: {'answer_line': 1269, 'none': 4})
- Greedy confidence missing before recovery: 0.3%; after recovery: 0.0% (4 recovered)
- Sample answer parse failure: 0.3%
- CoT forced_answer (no 'Answer:' in G): 0.0%
- CoT parsed letter ≠ argmax p: 0.0% (of 1269 parsed)
- Direct confidence missing: 0

## Letter distribution

- cot: letter_mass min 0.130, p5 0.998, p25 1.000, median 1.000, p75 1.000, p95 1.000, max 1.000; any letter missing from top-k: 15.9%; zero letter mass: 0
- direct: letter_mass min 0.009, p5 0.935, p25 0.999, median 1.000, p75 1.000, p95 1.000, max 1.000; any letter missing from top-k: 21.8%; zero letter mass: 0

## Truncation (finish_reason == length)

- Greedy: 0.0%; samples: 0.0%

## Position bias (chosen vs gold letters)

- gold: {'B': 309, 'D': 265, 'C': 346, 'A': 353}
- cot chosen: {'A': 501, 'B': 348, 'C': 224, 'D': 200} (accuracy 0.513)
- direct chosen: {'A': 523, 'B': 310, 'C': 250, 'D': 190} (accuracy 0.491)

## Signals (15 equal-width bins on [0,1])

- cot conf_stated: hist [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 33, 26, 1214]; fraction tied 1.000; unique 6; top-5 values [[0.95, 956], [1.0, 254], [0.85, 31], [0.9, 26], [0.99, 4]]; fraction-format flags 0
- cot conf_prob: hist [0, 0, 0, 0, 1, 1, 4, 20, 29, 43, 39, 30, 48, 75, 983]; fraction tied 0.006; unique 1266; fraction-format flags -
- cot conf_agree: hist [3, 0, 0, 6, 0, 0, 30, 0, 0, 41, 0, 0, 83, 0, 1110]; fraction tied 1.000; unique 6; fraction-format flags -
- direct conf_stated: hist [0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 58, 3, 1210]; fraction tied 0.997; unique 9; top-5 values [[0.95, 864], [0.99, 222], [1.0, 122], [0.85, 58], [0.9, 3]]; fraction-format flags 0
- direct conf_prob: hist [0, 0, 0, 0, 0, 1, 7, 22, 48, 39, 54, 56, 66, 81, 899]; fraction tied 0.008; unique 1264; fraction-format flags -
- direct conf_agree: hist [103, 0, 0, 33, 0, 0, 27, 0, 0, 37, 0, 0, 56, 0, 1017]; fraction tied 1.000; unique 6; fraction-format flags -

## Greedy determinism

- Re-ran CoT greedy on 10 questions: 10/10 byte-identical

## Validity flags (PREREGISTRATION.md section 8)

- cot: not flagged — values accuracy 0.513, greedy_parse_fail_rate 0.003, median_letter_mass 1.000, sample_truncation_rate 0.000 — flags accuracy_below_min=False, parse_fail_above_max=False, letter_mass_below_min=False, truncation_above_max=False
- direct: not flagged — values accuracy 0.491, greedy_parse_fail_rate 0.003, median_letter_mass 1.000, sample_truncation_rate 0.000 — flags accuracy_below_min=False, parse_fail_above_max=False, letter_mass_below_min=False, truncation_above_max=False
