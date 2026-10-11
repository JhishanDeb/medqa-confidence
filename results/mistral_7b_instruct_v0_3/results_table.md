# Results: mistralai/Mistral-7B-Instruct-v0.3

All numbers are computed by `medqa_conf.report` from `per_question.csv`. Intervals are paired-bootstrap percentile 95% CIs (2,000 resamples) unless marked Wilson.

## Setting: cot (primary, pre-registered)

Complete-case N used: 1273 of 1273 (dropped 0; missing per signal: {'stated': 0, 'prob': 0, 'agree': 0})

**Validity flags:** none — accuracy = 0.513, greedy_parse_fail_rate = 0.003, median_letter_mass = 1.000, sample_truncation_rate = 0.000

N = 1273; accuracy = 0.513 (Wilson 95% CI 0.486–0.540); selective-accuracy references at k = 1018: random 0.513, oracle 0.641

| signal | AUROC | ECE | adaptive ECE | Brier | mean conf | overconf. gap | sel. acc @80% | AURC |
|---|---|---|---|---|---|---|---|---|
| stated | 0.515 [0.493, 0.539] | 0.443 [0.415, 0.470] | 0.443 [0.415, 0.470] | 0.446 [0.421, 0.470] | 0.956 [0.955, 0.958] | 0.443 [0.415, 0.470] | 0.518 [0.491, 0.547] | 0.475 [0.439, 0.511] |
| prob | 0.652 [0.621, 0.678] | 0.423 [0.397, 0.451] | 0.423 [0.396, 0.450] | 0.425 [0.402, 0.450] | 0.936 [0.929, 0.943] | 0.423 [0.396, 0.450] | 0.551 [0.520, 0.582] | 0.354 [0.321, 0.390] |
| agree | 0.539 [0.522, 0.556] | 0.447 [0.421, 0.476] | 0.441 [0.414, 0.467] | 0.451 [0.425, 0.477] | 0.954 [0.945, 0.962] | 0.441 [0.414, 0.467] | 0.535 [0.505, 0.564] | 0.466 [0.438, 0.496] |

| pair (a − b) | ΔAUROC [95% CI] | DeLong z | p | p (Holm) | supported | ΔECE | Δsel. acc |
|---|---|---|---|---|---|---|---|
| stated_vs_prob | -0.136 [-0.169, -0.099] | -7.45 | 9.19e-14 | 1.84e-13 | yes | 0.020 [0.012, 0.027] | -0.033 [-0.048, -0.018] |
| stated_vs_agree | -0.023 [-0.053, 0.007] | -1.50 | 0.1348 | 0.1348 | no | -0.003 [-0.014, 0.004] | -0.017 [-0.029, -0.005] |
| prob_vs_agree | 0.113 [0.088, 0.138] | 8.65 | 5.35e-18 | 1.61e-17 | yes | -0.023 [-0.033, -0.017] | 0.016 [0.005, 0.027] |

**Hypotheses (decision rule: Holm-adjusted DeLong p < 0.05 and bootstrap CI excludes 0):**

- H1 (stated AUROC below prob and agree): not supported (below prob: True, below agree: False)
- H2 (stated overconfident and highest ECE): not supported (overconfident: True, ECE above prob: True, ECE above agree: False)
- H3 (prob and agree AUROC differ): supported (observed direction: prob>agree)

### Sensitivity: missing conf_stated imputed with median (0.950; 0 imputed)

N = 1273; accuracy = 0.513 (Wilson 95% CI 0.486–0.540); selective-accuracy references at k = 1018: random 0.513, oracle 0.641

| signal | AUROC | ECE | adaptive ECE | Brier | mean conf | overconf. gap | sel. acc @80% | AURC |
|---|---|---|---|---|---|---|---|---|
| stated | 0.515 [0.493, 0.539] | 0.443 [0.415, 0.470] | 0.443 [0.415, 0.470] | 0.446 [0.421, 0.470] | 0.956 [0.955, 0.958] | 0.443 [0.415, 0.470] | 0.518 [0.491, 0.547] | 0.475 [0.439, 0.511] |
| prob | 0.652 [0.621, 0.678] | 0.423 [0.397, 0.451] | 0.423 [0.396, 0.450] | 0.425 [0.402, 0.450] | 0.936 [0.929, 0.943] | 0.423 [0.396, 0.450] | 0.551 [0.520, 0.582] | 0.354 [0.321, 0.390] |
| agree | 0.539 [0.522, 0.556] | 0.447 [0.421, 0.476] | 0.441 [0.414, 0.467] | 0.451 [0.425, 0.477] | 0.954 [0.945, 0.962] | 0.441 [0.414, 0.467] | 0.535 [0.505, 0.564] | 0.466 [0.438, 0.496] |

| pair (a − b) | ΔAUROC [95% CI] | DeLong z | p | p (Holm) | supported | ΔECE | Δsel. acc |
|---|---|---|---|---|---|---|---|
| stated_vs_prob | -0.136 [-0.169, -0.099] | -7.45 | 9.19e-14 | 1.84e-13 | yes | 0.020 [0.012, 0.027] | -0.033 [-0.048, -0.018] |
| stated_vs_agree | -0.023 [-0.053, 0.007] | -1.50 | 0.1348 | 0.1348 | no | -0.003 [-0.014, 0.004] | -0.017 [-0.029, -0.005] |
| prob_vs_agree | 0.113 [0.088, 0.138] | 8.65 | 5.35e-18 | 1.61e-17 | yes | -0.023 [-0.033, -0.017] | 0.016 [0.005, 0.027] |

### Exploratory (not part of the pre-registered conclusions)

- Majority-vote accuracy (5 CoT samples): 0.509 (Wilson 0.482–0.536)
- AUROC of −entropy of the 5 sample answers: 0.539
- AUROC of rank-average(prob, agree): 0.651
- ECE after 5-fold cross-fitted Platt scaling: stated 0.008, prob 0.035, agree 0.031

| meta_info | n | accuracy | AUROC stated | AUROC prob | AUROC agree | ECE stated | ECE prob | ECE agree |
|---|---|---|---|---|---|---|---|---|
| step1 | 679 | 0.505 | 0.527 | 0.659 | 0.529 | 0.457 | 0.432 | 0.461 |
| step2&3 | 594 | 0.522 | 0.507 | 0.645 | 0.549 | 0.428 | 0.417 | 0.439 |

## Setting: direct (secondary)

Complete-case N used: 1273 of 1273 (dropped 0; missing per signal: {'stated': 0, 'prob': 0, 'agree': 0})

**Validity flags:** none — accuracy = 0.491, greedy_parse_fail_rate = 0.003, median_letter_mass = 1.000, sample_truncation_rate = 0.000

N = 1273; accuracy = 0.491 (Wilson 95% CI 0.464–0.518); selective-accuracy references at k = 1018: random 0.491, oracle 0.614

| signal | AUROC | ECE | adaptive ECE | Brier | mean conf | overconf. gap | sel. acc @80% | AURC |
|---|---|---|---|---|---|---|---|---|
| stated | 0.526 [0.501, 0.553] | 0.465 [0.438, 0.491] | 0.465 [0.438, 0.491] | 0.465 [0.440, 0.489] | 0.956 [0.954, 0.958] | 0.465 [0.438, 0.491] | 0.500 [0.472, 0.529] | 0.492 [0.455, 0.527] |
| prob | 0.661 [0.632, 0.691] | 0.426 [0.399, 0.453] | 0.426 [0.398, 0.452] | 0.425 [0.400, 0.448] | 0.917 [0.909, 0.924] | 0.426 [0.398, 0.452] | 0.528 [0.499, 0.560] | 0.368 [0.333, 0.401] |
| agree | 0.579 [0.558, 0.600] | 0.425 [0.398, 0.452] | 0.417 [0.388, 0.443] | 0.426 [0.400, 0.451] | 0.865 [0.848, 0.882] | 0.374 [0.345, 0.403] | 0.539 [0.509, 0.569] | 0.466 [0.435, 0.495] |

| pair (a − b) | ΔAUROC [95% CI] | DeLong z | p | p (Holm) | supported | ΔECE | Δsel. acc |
|---|---|---|---|---|---|---|---|
| stated_vs_prob | -0.135 [-0.167, -0.098] | -7.48 | 7.64e-14 | 2.29e-13 | yes | 0.039 [0.031, 0.047] | -0.029 [-0.043, -0.014] |
| stated_vs_agree | -0.053 [-0.085, -0.021] | -3.10 | 0.0019 | 0.0019 | yes | 0.040 [0.022, 0.059] | -0.039 [-0.052, -0.024] |
| prob_vs_agree | 0.082 [0.055, 0.107] | 5.99 | 2.14e-09 | 4.28e-09 | yes | 0.001 [-0.017, 0.020] | -0.010 [-0.023, 0.005] |

**Hypotheses (decision rule: Holm-adjusted DeLong p < 0.05 and bootstrap CI excludes 0):**

- H1 (stated AUROC below prob and agree): supported (below prob: True, below agree: True)
- H2 (stated overconfident and highest ECE): supported (overconfident: True, ECE above prob: True, ECE above agree: True)
- H3 (prob and agree AUROC differ): supported (observed direction: prob>agree)

### Sensitivity: missing conf_stated imputed with median (0.950; 0 imputed)

N = 1273; accuracy = 0.491 (Wilson 95% CI 0.464–0.518); selective-accuracy references at k = 1018: random 0.491, oracle 0.614

| signal | AUROC | ECE | adaptive ECE | Brier | mean conf | overconf. gap | sel. acc @80% | AURC |
|---|---|---|---|---|---|---|---|---|
| stated | 0.526 [0.501, 0.553] | 0.465 [0.438, 0.491] | 0.465 [0.438, 0.491] | 0.465 [0.440, 0.489] | 0.956 [0.954, 0.958] | 0.465 [0.438, 0.491] | 0.500 [0.472, 0.529] | 0.492 [0.455, 0.527] |
| prob | 0.661 [0.632, 0.691] | 0.426 [0.399, 0.453] | 0.426 [0.398, 0.452] | 0.425 [0.400, 0.448] | 0.917 [0.909, 0.924] | 0.426 [0.398, 0.452] | 0.528 [0.499, 0.560] | 0.368 [0.333, 0.401] |
| agree | 0.579 [0.558, 0.600] | 0.425 [0.398, 0.452] | 0.417 [0.388, 0.443] | 0.426 [0.400, 0.451] | 0.865 [0.848, 0.882] | 0.374 [0.345, 0.403] | 0.539 [0.509, 0.569] | 0.466 [0.435, 0.495] |

| pair (a − b) | ΔAUROC [95% CI] | DeLong z | p | p (Holm) | supported | ΔECE | Δsel. acc |
|---|---|---|---|---|---|---|---|
| stated_vs_prob | -0.135 [-0.167, -0.098] | -7.48 | 7.64e-14 | 2.29e-13 | yes | 0.039 [0.031, 0.047] | -0.029 [-0.043, -0.014] |
| stated_vs_agree | -0.053 [-0.085, -0.021] | -3.10 | 0.0019 | 0.0019 | yes | 0.040 [0.022, 0.059] | -0.039 [-0.052, -0.024] |
| prob_vs_agree | 0.082 [0.055, 0.107] | 5.99 | 2.14e-09 | 4.28e-09 | yes | 0.001 [-0.017, 0.020] | -0.010 [-0.023, 0.005] |

### Exploratory (not part of the pre-registered conclusions)

- Majority-vote accuracy (5 CoT samples): 0.509 (Wilson 0.482–0.536)
- AUROC of −entropy of the 5 sample answers: 0.537
- AUROC of rank-average(prob, agree): 0.669
- ECE after 5-fold cross-fitted Platt scaling: stated 0.033, prob 0.055, agree 0.030

| meta_info | n | accuracy | AUROC stated | AUROC prob | AUROC agree | ECE stated | ECE prob | ECE agree |
|---|---|---|---|---|---|---|---|---|
| step1 | 679 | 0.489 | 0.549 | 0.682 | 0.564 | 0.472 | 0.430 | 0.438 |
| step2&3 | 594 | 0.493 | 0.502 | 0.638 | 0.595 | 0.458 | 0.422 | 0.411 |

