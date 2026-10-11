# Sanity report: meta-llama/Llama-3.1-8B-Instruct

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

- Greedy answer parse failure: 1.3% (methods: {'answer_line': 1253, 'none': 17, 'answer_is': 3})
- Greedy confidence missing before recovery: 1.3%; after recovery: 0.0% (16 recovered)
- Sample answer parse failure: 1.6%
- CoT forced_answer (no 'Answer:' in G): 1.4%
- CoT parsed letter ≠ argmax p: 0.2% (of 1256 parsed)
- Direct confidence missing: 0

## Letter distribution

- cot: letter_mass min 0.084, p5 0.991, p25 0.998, median 0.999, p75 1.000, p95 1.000, max 1.000; any letter missing from top-k: 1.6%; zero letter mass: 0
- direct: letter_mass min 0.961, p5 0.995, p25 0.997, median 0.998, p75 0.999, p95 0.999, max 1.000; any letter missing from top-k: 0.0%; zero letter mass: 0

## Truncation (finish_reason == length)

- Greedy: 1.2%; samples: 0.2%

## Position bias (chosen vs gold letters)

- gold: {'B': 309, 'D': 265, 'C': 346, 'A': 353}
- cot chosen: {'A': 346, 'C': 342, 'B': 406, 'D': 179} (accuracy 0.690)
- direct chosen: {'B': 418, 'D': 190, 'C': 303, 'A': 362} (accuracy 0.606)

## Signals (15 equal-width bins on [0,1])

- cot conf_stated: hist [3, 0, 0, 2, 0, 0, 7, 0, 0, 19, 3, 0, 461, 759, 19]; fraction tied 0.999; unique 10; top-5 values [[0.9, 759], [0.8, 450], [0.6, 19], [1.0, 18], [0.85, 11]]; fraction-format flags 0
- cot conf_prob: hist [0, 0, 0, 0, 0, 0, 4, 11, 12, 13, 10, 9, 13, 20, 1181]; fraction tied 0.000; unique 1273; fraction-format flags -
- cot conf_agree: hist [79, 0, 0, 106, 0, 0, 110, 0, 0, 172, 0, 0, 237, 0, 569]; fraction tied 1.000; unique 6; fraction-format flags -
- direct conf_stated: hist [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1088, 156, 28]; fraction tied 0.999; unique 5; top-5 values [[0.8, 1088], [0.9, 156], [1.0, 25], [0.95, 3], [0.0, 1]]; fraction-format flags 0
- direct conf_prob: hist [0, 0, 0, 0, 3, 19, 51, 68, 77, 73, 72, 86, 104, 130, 590]; fraction tied 0.000; unique 1273; fraction-format flags -
- direct conf_agree: hist [148, 0, 0, 120, 0, 0, 142, 0, 0, 127, 0, 0, 205, 0, 531]; fraction tied 1.000; unique 6; fraction-format flags -

## Greedy determinism

- Re-ran CoT greedy on 10 questions: 7/10 byte-identical (differing qids: [0, 3, 5])

## Validity flags (PREREGISTRATION.md section 8)

- cot: not flagged — values accuracy 0.690, greedy_parse_fail_rate 0.013, median_letter_mass 0.999, sample_truncation_rate 0.002 — flags accuracy_below_min=False, parse_fail_above_max=False, letter_mass_below_min=False, truncation_above_max=False
- direct: not flagged — values accuracy 0.606, greedy_parse_fail_rate 0.013, median_letter_mass 0.998, sample_truncation_rate 0.002 — flags accuracy_below_min=False, parse_fail_above_max=False, letter_mass_below_min=False, truncation_above_max=False
