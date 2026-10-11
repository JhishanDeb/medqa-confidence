# Results: meta-llama/Llama-3.1-8B-Instruct

All numbers are computed by `medqa_conf.report` from `per_question.csv`. Intervals are paired-bootstrap percentile 95% CIs (2,000 resamples) unless marked Wilson.

## Setting: cot (primary, pre-registered)

Complete-case N used: 1273 of 1273 (dropped 0; missing per signal: {'stated': 0, 'prob': 0, 'agree': 0})

**Validity flags:** none — accuracy = 0.690, greedy_parse_fail_rate = 0.013, median_letter_mass = 0.999, sample_truncation_rate = 0.002

N = 1273; accuracy = 0.690 (Wilson 95% CI 0.665–0.715); selective-accuracy references at k = 1018: random 0.690, oracle 0.863

| signal | AUROC | ECE | adaptive ECE | Brier | mean conf | overconf. gap | sel. acc @80% | AURC |
|---|---|---|---|---|---|---|---|---|
| stated | 0.653 [0.624, 0.682] | 0.166 [0.143, 0.192] | 0.164 [0.141, 0.190] | 0.228 [0.211, 0.247] | 0.855 [0.850, 0.859] | 0.164 [0.141, 0.190] | 0.734 [0.708, 0.760] | 0.224 [0.197, 0.253] |
| prob | 0.696 [0.666, 0.725] | 0.287 [0.262, 0.313] | 0.287 [0.262, 0.312] | 0.287 [0.263, 0.311] | 0.977 [0.973, 0.982] | 0.287 [0.262, 0.312] | 0.742 [0.713, 0.767] | 0.181 [0.159, 0.206] |
| agree | 0.807 [0.781, 0.832] | 0.083 [0.065, 0.105] | 0.081 [0.068, 0.104] | 0.162 [0.148, 0.176] | 0.728 [0.710, 0.745] | 0.038 [0.016, 0.061] | 0.790 [0.761, 0.816] | 0.144 [0.123, 0.166] |

| pair (a − b) | ΔAUROC [95% CI] | DeLong z | p | p (Holm) | supported | ΔECE | Δsel. acc |
|---|---|---|---|---|---|---|---|
| stated_vs_prob | -0.043 [-0.078, -0.009] | -2.40 | 0.0166 | 0.0166 | yes | -0.121 [-0.126, -0.115] | -0.007 [-0.021, 0.007] |
| stated_vs_agree | -0.155 [-0.190, -0.122] | -8.70 | 3.37e-18 | 1.01e-17 | yes | 0.083 [0.060, 0.105] | -0.056 [-0.069, -0.043] |
| prob_vs_agree | -0.112 [-0.144, -0.079] | -6.64 | 3.11e-11 | 6.22e-11 | yes | 0.204 [0.180, 0.225] | -0.048 [-0.064, -0.033] |

**Hypotheses (decision rule: Holm-adjusted DeLong p < 0.05 and bootstrap CI excludes 0):**

- H1 (stated AUROC below prob and agree): supported (below prob: True, below agree: True)
- H2 (stated overconfident and highest ECE): not supported (overconfident: True, ECE above prob: False, ECE above agree: True)
- H3 (prob and agree AUROC differ): supported (observed direction: agree>prob)

### Sensitivity: missing conf_stated imputed with median (0.900; 0 imputed)

N = 1273; accuracy = 0.690 (Wilson 95% CI 0.665–0.715); selective-accuracy references at k = 1018: random 0.690, oracle 0.863

| signal | AUROC | ECE | adaptive ECE | Brier | mean conf | overconf. gap | sel. acc @80% | AURC |
|---|---|---|---|---|---|---|---|---|
| stated | 0.653 [0.624, 0.682] | 0.166 [0.143, 0.192] | 0.164 [0.141, 0.190] | 0.228 [0.211, 0.247] | 0.855 [0.850, 0.859] | 0.164 [0.141, 0.190] | 0.734 [0.708, 0.760] | 0.224 [0.197, 0.253] |
| prob | 0.696 [0.666, 0.725] | 0.287 [0.262, 0.313] | 0.287 [0.262, 0.312] | 0.287 [0.263, 0.311] | 0.977 [0.973, 0.982] | 0.287 [0.262, 0.312] | 0.742 [0.713, 0.767] | 0.181 [0.159, 0.206] |
| agree | 0.807 [0.781, 0.832] | 0.083 [0.065, 0.105] | 0.081 [0.068, 0.104] | 0.162 [0.148, 0.176] | 0.728 [0.710, 0.745] | 0.038 [0.016, 0.061] | 0.790 [0.761, 0.816] | 0.144 [0.123, 0.166] |

| pair (a − b) | ΔAUROC [95% CI] | DeLong z | p | p (Holm) | supported | ΔECE | Δsel. acc |
|---|---|---|---|---|---|---|---|
| stated_vs_prob | -0.043 [-0.078, -0.009] | -2.40 | 0.0166 | 0.0166 | yes | -0.121 [-0.126, -0.115] | -0.007 [-0.021, 0.007] |
| stated_vs_agree | -0.155 [-0.190, -0.122] | -8.70 | 3.37e-18 | 1.01e-17 | yes | 0.083 [0.060, 0.105] | -0.056 [-0.069, -0.043] |
| prob_vs_agree | -0.112 [-0.144, -0.079] | -6.64 | 3.11e-11 | 6.22e-11 | yes | 0.204 [0.180, 0.225] | -0.048 [-0.064, -0.033] |

### Exploratory (not part of the pre-registered conclusions)

- Majority-vote accuracy (5 CoT samples): 0.732 (Wilson 0.707–0.756)
- AUROC of −entropy of the 5 sample answers: 0.749
- AUROC of rank-average(prob, agree): 0.798
- ECE after 5-fold cross-fitted Platt scaling: stated 0.039, prob 0.007, agree 0.054

| meta_info | n | accuracy | AUROC stated | AUROC prob | AUROC agree | ECE stated | ECE prob | ECE agree |
|---|---|---|---|---|---|---|---|---|
| step1 | 679 | 0.680 | 0.670 | 0.722 | 0.810 | 0.178 | 0.294 | 0.091 |
| step2&3 | 594 | 0.702 | 0.633 | 0.664 | 0.804 | 0.154 | 0.280 | 0.073 |

## Setting: direct (secondary)

Complete-case N used: 1273 of 1273 (dropped 0; missing per signal: {'stated': 0, 'prob': 0, 'agree': 0})

**Validity flags:** none — accuracy = 0.606, greedy_parse_fail_rate = 0.013, median_letter_mass = 0.998, sample_truncation_rate = 0.002

N = 1273; accuracy = 0.606 (Wilson 95% CI 0.579–0.633); selective-accuracy references at k = 1018: random 0.606, oracle 0.758

| signal | AUROC | ECE | adaptive ECE | Brier | mean conf | overconf. gap | sel. acc @80% | AURC |
|---|---|---|---|---|---|---|---|---|
| stated | 0.564 [0.545, 0.581] | 0.209 [0.184, 0.237] | 0.209 [0.184, 0.237] | 0.278 [0.261, 0.294] | 0.816 [0.813, 0.818] | 0.209 [0.184, 0.237] | 0.616 [0.589, 0.642] | 0.329 [0.298, 0.360] |
| prob | 0.756 [0.727, 0.783] | 0.223 [0.200, 0.249] | 0.223 [0.200, 0.249] | 0.251 [0.234, 0.269] | 0.830 [0.819, 0.840] | 0.223 [0.199, 0.249] | 0.681 [0.649, 0.708] | 0.208 [0.184, 0.234] |
| agree | 0.862 [0.842, 0.883] | 0.080 [0.063, 0.102] | 0.081 [0.064, 0.101] | 0.146 [0.133, 0.161] | 0.669 [0.650, 0.689] | 0.063 [0.041, 0.084] | 0.727 [0.696, 0.757] | 0.169 [0.148, 0.192] |

| pair (a − b) | ΔAUROC [95% CI] | DeLong z | p | p (Holm) | supported | ΔECE | Δsel. acc |
|---|---|---|---|---|---|---|---|
| stated_vs_prob | -0.192 [-0.220, -0.163] | -13.33 | 1.51e-40 | 3.02e-40 | yes | -0.014 [-0.025, -0.004] | -0.065 [-0.077, -0.051] |
| stated_vs_agree | -0.299 [-0.324, -0.273] | -22.36 | 1.00e-110 | 3.01e-110 | yes | 0.129 [0.105, 0.148] | -0.112 [-0.121, -0.101] |
| prob_vs_agree | -0.106 [-0.134, -0.080] | -7.97 | 1.54e-15 | 1.54e-15 | yes | 0.143 [0.122, 0.161] | -0.047 [-0.061, -0.032] |

**Hypotheses (decision rule: Holm-adjusted DeLong p < 0.05 and bootstrap CI excludes 0):**

- H1 (stated AUROC below prob and agree): supported (below prob: True, below agree: True)
- H2 (stated overconfident and highest ECE): not supported (overconfident: True, ECE above prob: False, ECE above agree: True)
- H3 (prob and agree AUROC differ): supported (observed direction: agree>prob)

### Sensitivity: missing conf_stated imputed with median (0.800; 0 imputed)

N = 1273; accuracy = 0.606 (Wilson 95% CI 0.579–0.633); selective-accuracy references at k = 1018: random 0.606, oracle 0.758

| signal | AUROC | ECE | adaptive ECE | Brier | mean conf | overconf. gap | sel. acc @80% | AURC |
|---|---|---|---|---|---|---|---|---|
| stated | 0.564 [0.545, 0.581] | 0.209 [0.184, 0.237] | 0.209 [0.184, 0.237] | 0.278 [0.261, 0.294] | 0.816 [0.813, 0.818] | 0.209 [0.184, 0.237] | 0.616 [0.589, 0.642] | 0.329 [0.298, 0.360] |
| prob | 0.756 [0.727, 0.783] | 0.223 [0.200, 0.249] | 0.223 [0.200, 0.249] | 0.251 [0.234, 0.269] | 0.830 [0.819, 0.840] | 0.223 [0.199, 0.249] | 0.681 [0.649, 0.708] | 0.208 [0.184, 0.234] |
| agree | 0.862 [0.842, 0.883] | 0.080 [0.063, 0.102] | 0.081 [0.064, 0.101] | 0.146 [0.133, 0.161] | 0.669 [0.650, 0.689] | 0.063 [0.041, 0.084] | 0.727 [0.696, 0.757] | 0.169 [0.148, 0.192] |

| pair (a − b) | ΔAUROC [95% CI] | DeLong z | p | p (Holm) | supported | ΔECE | Δsel. acc |
|---|---|---|---|---|---|---|---|
| stated_vs_prob | -0.192 [-0.220, -0.163] | -13.33 | 1.51e-40 | 3.02e-40 | yes | -0.014 [-0.025, -0.004] | -0.065 [-0.077, -0.051] |
| stated_vs_agree | -0.299 [-0.324, -0.273] | -22.36 | 1.00e-110 | 3.01e-110 | yes | 0.129 [0.105, 0.148] | -0.112 [-0.121, -0.101] |
| prob_vs_agree | -0.106 [-0.134, -0.080] | -7.97 | 1.54e-15 | 1.54e-15 | yes | 0.143 [0.122, 0.161] | -0.047 [-0.061, -0.032] |

### Exploratory (not part of the pre-registered conclusions)

- Majority-vote accuracy (5 CoT samples): 0.738 (Wilson 0.713–0.761)
- AUROC of −entropy of the 5 sample answers: 0.742
- AUROC of rank-average(prob, agree): 0.851
- ECE after 5-fold cross-fitted Platt scaling: stated 0.024, prob 0.073, agree 0.041

| meta_info | n | accuracy | AUROC stated | AUROC prob | AUROC agree | ECE stated | ECE prob | ECE agree |
|---|---|---|---|---|---|---|---|---|
| step1 | 679 | 0.595 | 0.560 | 0.751 | 0.863 | 0.222 | 0.225 | 0.088 |
| step2&3 | 594 | 0.620 | 0.568 | 0.762 | 0.861 | 0.196 | 0.222 | 0.071 |

