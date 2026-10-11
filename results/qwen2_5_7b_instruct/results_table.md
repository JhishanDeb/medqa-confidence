# Results: Qwen/Qwen2.5-7B-Instruct

All numbers are computed by `medqa_conf.report` from `per_question.csv`. Intervals are paired-bootstrap percentile 95% CIs (2,000 resamples) unless marked Wilson.

## Setting: cot (primary, pre-registered)

Complete-case N used: 1273 of 1273 (dropped 0; missing per signal: {'stated': 0, 'prob': 0, 'agree': 0})

**Validity flags:** none — accuracy = 0.639, greedy_parse_fail_rate = 0.002, median_letter_mass = 1.000, sample_truncation_rate = 0.000

N = 1273; accuracy = 0.639 (Wilson 95% CI 0.613–0.665); selective-accuracy references at k = 1018: random 0.639, oracle 0.800

| signal | AUROC | ECE | adaptive ECE | Brier | mean conf | overconf. gap | sel. acc @80% | AURC |
|---|---|---|---|---|---|---|---|---|
| stated | 0.587 [0.563, 0.612] | 0.306 [0.279, 0.331] | 0.305 [0.278, 0.330] | 0.317 [0.293, 0.339] | 0.944 [0.941, 0.947] | 0.305 [0.278, 0.330] | 0.673 [0.647, 0.702] | 0.302 [0.270, 0.334] |
| prob | 0.653 [0.621, 0.683] | 0.346 [0.320, 0.373] | 0.345 [0.318, 0.371] | 0.347 [0.322, 0.373] | 0.984 [0.981, 0.988] | 0.345 [0.318, 0.371] | 0.692 [0.661, 0.718] | 0.262 [0.231, 0.294] |
| agree | 0.689 [0.661, 0.718] | 0.192 [0.170, 0.217] | 0.192 [0.168, 0.217] | 0.242 [0.223, 0.262] | 0.774 [0.757, 0.791] | 0.135 [0.110, 0.160] | 0.706 [0.678, 0.735] | 0.253 [0.224, 0.282] |

| pair (a − b) | ΔAUROC [95% CI] | DeLong z | p | p (Holm) | supported | ΔECE | Δsel. acc |
|---|---|---|---|---|---|---|---|
| stated_vs_prob | -0.066 [-0.103, -0.029] | -3.58 | 3.40e-04 | 6.80e-04 | yes | -0.040 [-0.046, -0.036] | -0.018 [-0.032, -0.001] |
| stated_vs_agree | -0.103 [-0.141, -0.065] | -5.67 | 1.42e-08 | 4.25e-08 | yes | 0.114 [0.089, 0.135] | -0.033 [-0.048, -0.017] |
| prob_vs_agree | -0.036 [-0.069, -0.004] | -2.22 | 0.0261 | 0.0261 | yes | 0.154 [0.131, 0.176] | -0.015 [-0.032, -0.000] |

**Hypotheses (decision rule: Holm-adjusted DeLong p < 0.05 and bootstrap CI excludes 0):**

- H1 (stated AUROC below prob and agree): supported (below prob: True, below agree: True)
- H2 (stated overconfident and highest ECE): not supported (overconfident: True, ECE above prob: False, ECE above agree: True)
- H3 (prob and agree AUROC differ): supported (observed direction: agree>prob)

### Sensitivity: missing conf_stated imputed with median (0.950; 0 imputed)

N = 1273; accuracy = 0.639 (Wilson 95% CI 0.613–0.665); selective-accuracy references at k = 1018: random 0.639, oracle 0.800

| signal | AUROC | ECE | adaptive ECE | Brier | mean conf | overconf. gap | sel. acc @80% | AURC |
|---|---|---|---|---|---|---|---|---|
| stated | 0.587 [0.563, 0.612] | 0.306 [0.279, 0.331] | 0.305 [0.278, 0.330] | 0.317 [0.293, 0.339] | 0.944 [0.941, 0.947] | 0.305 [0.278, 0.330] | 0.673 [0.647, 0.702] | 0.302 [0.270, 0.334] |
| prob | 0.653 [0.621, 0.683] | 0.346 [0.320, 0.373] | 0.345 [0.318, 0.371] | 0.347 [0.322, 0.373] | 0.984 [0.981, 0.988] | 0.345 [0.318, 0.371] | 0.692 [0.661, 0.718] | 0.262 [0.231, 0.294] |
| agree | 0.689 [0.661, 0.718] | 0.192 [0.170, 0.217] | 0.192 [0.168, 0.217] | 0.242 [0.223, 0.262] | 0.774 [0.757, 0.791] | 0.135 [0.110, 0.160] | 0.706 [0.678, 0.735] | 0.253 [0.224, 0.282] |

| pair (a − b) | ΔAUROC [95% CI] | DeLong z | p | p (Holm) | supported | ΔECE | Δsel. acc |
|---|---|---|---|---|---|---|---|
| stated_vs_prob | -0.066 [-0.103, -0.029] | -3.58 | 3.40e-04 | 6.80e-04 | yes | -0.040 [-0.046, -0.036] | -0.018 [-0.032, -0.001] |
| stated_vs_agree | -0.103 [-0.141, -0.065] | -5.67 | 1.42e-08 | 4.25e-08 | yes | 0.114 [0.089, 0.135] | -0.033 [-0.048, -0.017] |
| prob_vs_agree | -0.036 [-0.069, -0.004] | -2.22 | 0.0261 | 0.0261 | yes | 0.154 [0.131, 0.176] | -0.015 [-0.032, -0.000] |

### Exploratory (not part of the pre-registered conclusions)

- Majority-vote accuracy (5 CoT samples): 0.639 (Wilson 0.613–0.665)
- AUROC of −entropy of the 5 sample answers: 0.652
- AUROC of rank-average(prob, agree): 0.703
- ECE after 5-fold cross-fitted Platt scaling: stated 0.008, prob 0.010, agree 0.035

| meta_info | n | accuracy | AUROC stated | AUROC prob | AUROC agree | ECE stated | ECE prob | ECE agree |
|---|---|---|---|---|---|---|---|---|
| step1 | 679 | 0.632 | 0.601 | 0.673 | 0.707 | 0.314 | 0.354 | 0.199 |
| step2&3 | 594 | 0.648 | 0.572 | 0.630 | 0.668 | 0.295 | 0.337 | 0.186 |

## Setting: direct (secondary)

Complete-case N used: 1273 of 1273 (dropped 0; missing per signal: {'stated': 0, 'prob': 0, 'agree': 0})

**Validity flags:** none — accuracy = 0.597, greedy_parse_fail_rate = 0.002, median_letter_mass = 1.000, sample_truncation_rate = 0.000

N = 1273; accuracy = 0.597 (Wilson 95% CI 0.570–0.624); selective-accuracy references at k = 1018: random 0.597, oracle 0.747

| signal | AUROC | ECE | adaptive ECE | Brier | mean conf | overconf. gap | sel. acc @80% | AURC |
|---|---|---|---|---|---|---|---|---|
| stated | 0.587 [0.563, 0.611] | 0.282 [0.254, 0.308] | 0.282 [0.254, 0.308] | 0.313 [0.292, 0.333] | 0.879 [0.876, 0.881] | 0.282 [0.254, 0.308] | 0.612 [0.586, 0.641] | 0.328 [0.296, 0.359] |
| prob | 0.718 [0.690, 0.746] | 0.347 [0.320, 0.374] | 0.347 [0.319, 0.373] | 0.349 [0.324, 0.373] | 0.944 [0.937, 0.950] | 0.347 [0.319, 0.373] | 0.651 [0.624, 0.683] | 0.237 [0.210, 0.264] |
| agree | 0.726 [0.697, 0.752] | 0.196 [0.172, 0.221] | 0.196 [0.170, 0.219] | 0.239 [0.220, 0.259] | 0.747 [0.730, 0.764] | 0.150 [0.124, 0.174] | 0.675 [0.646, 0.705] | 0.267 [0.238, 0.296] |

| pair (a − b) | ΔAUROC [95% CI] | DeLong z | p | p (Holm) | supported | ΔECE | Δsel. acc |
|---|---|---|---|---|---|---|---|
| stated_vs_prob | -0.131 [-0.161, -0.100] | -8.49 | 2.03e-17 | 6.10e-17 | yes | -0.065 [-0.073, -0.059] | -0.039 [-0.053, -0.027] |
| stated_vs_agree | -0.139 [-0.172, -0.105] | -8.33 | 8.25e-17 | 1.65e-16 | yes | 0.085 [0.062, 0.107] | -0.063 [-0.075, -0.050] |
| prob_vs_agree | -0.008 [-0.036, 0.021] | -0.59 | 0.5565 | 0.5565 | no | 0.151 [0.129, 0.173] | -0.024 [-0.036, -0.009] |

**Hypotheses (decision rule: Holm-adjusted DeLong p < 0.05 and bootstrap CI excludes 0):**

- H1 (stated AUROC below prob and agree): supported (below prob: True, below agree: True)
- H2 (stated overconfident and highest ECE): not supported (overconfident: True, ECE above prob: False, ECE above agree: True)
- H3 (prob and agree AUROC differ): not supported (observed direction: agree>prob)

### Sensitivity: missing conf_stated imputed with median (0.850; 0 imputed)

N = 1273; accuracy = 0.597 (Wilson 95% CI 0.570–0.624); selective-accuracy references at k = 1018: random 0.597, oracle 0.747

| signal | AUROC | ECE | adaptive ECE | Brier | mean conf | overconf. gap | sel. acc @80% | AURC |
|---|---|---|---|---|---|---|---|---|
| stated | 0.587 [0.563, 0.611] | 0.282 [0.254, 0.308] | 0.282 [0.254, 0.308] | 0.313 [0.292, 0.333] | 0.879 [0.876, 0.881] | 0.282 [0.254, 0.308] | 0.612 [0.586, 0.641] | 0.328 [0.296, 0.359] |
| prob | 0.718 [0.690, 0.746] | 0.347 [0.320, 0.374] | 0.347 [0.319, 0.373] | 0.349 [0.324, 0.373] | 0.944 [0.937, 0.950] | 0.347 [0.319, 0.373] | 0.651 [0.624, 0.683] | 0.237 [0.210, 0.264] |
| agree | 0.726 [0.697, 0.752] | 0.196 [0.172, 0.221] | 0.196 [0.170, 0.219] | 0.239 [0.220, 0.259] | 0.747 [0.730, 0.764] | 0.150 [0.124, 0.174] | 0.675 [0.646, 0.705] | 0.267 [0.238, 0.296] |

| pair (a − b) | ΔAUROC [95% CI] | DeLong z | p | p (Holm) | supported | ΔECE | Δsel. acc |
|---|---|---|---|---|---|---|---|
| stated_vs_prob | -0.131 [-0.161, -0.100] | -8.49 | 2.03e-17 | 6.10e-17 | yes | -0.065 [-0.073, -0.059] | -0.039 [-0.053, -0.027] |
| stated_vs_agree | -0.139 [-0.172, -0.105] | -8.33 | 8.25e-17 | 1.65e-16 | yes | 0.085 [0.062, 0.107] | -0.063 [-0.075, -0.050] |
| prob_vs_agree | -0.008 [-0.036, 0.021] | -0.59 | 0.5565 | 0.5565 | no | 0.151 [0.129, 0.173] | -0.024 [-0.036, -0.009] |

### Exploratory (not part of the pre-registered conclusions)

- Majority-vote accuracy (5 CoT samples): 0.642 (Wilson 0.615–0.668)
- AUROC of −entropy of the 5 sample answers: 0.676
- AUROC of rank-average(prob, agree): 0.757
- ECE after 5-fold cross-fitted Platt scaling: stated 0.051, prob 0.031, agree 0.040

| meta_info | n | accuracy | AUROC stated | AUROC prob | AUROC agree | ECE stated | ECE prob | ECE agree |
|---|---|---|---|---|---|---|---|---|
| step1 | 679 | 0.592 | 0.605 | 0.730 | 0.744 | 0.289 | 0.346 | 0.187 |
| step2&3 | 594 | 0.603 | 0.566 | 0.699 | 0.704 | 0.274 | 0.349 | 0.207 |

