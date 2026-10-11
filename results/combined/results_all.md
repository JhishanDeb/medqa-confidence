# Combined results across models

Recomputed from each model's `per_question.csv`. Holm correction across all pairs × non-flagged models within a setting. **The primary family is the CoT setting.**

## Setting: cot (primary)

Holm family size: 9; flagged models excluded: none

| model | N | accuracy | AUROC stated | AUROC prob | AUROC agree | ECE stated | ECE prob | ECE agree |
|---|---|---|---|---|---|---|---|---|
| Qwen/Qwen2.5-7B-Instruct | 1273 | 0.639 | 0.587 [0.563, 0.612] | 0.653 [0.621, 0.683] | 0.689 [0.661, 0.718] | 0.306 [0.279, 0.331] | 0.346 [0.320, 0.373] | 0.192 [0.170, 0.217] |
| meta-llama/Llama-3.1-8B-Instruct | 1273 | 0.690 | 0.653 [0.624, 0.682] | 0.696 [0.666, 0.725] | 0.807 [0.781, 0.832] | 0.166 [0.143, 0.192] | 0.287 [0.262, 0.313] | 0.083 [0.065, 0.105] |
| mistralai/Mistral-7B-Instruct-v0.3 | 1273 | 0.513 | 0.515 [0.493, 0.539] | 0.652 [0.621, 0.678] | 0.539 [0.522, 0.556] | 0.443 [0.415, 0.470] | 0.423 [0.397, 0.451] | 0.447 [0.421, 0.476] |

| model | pair | ΔAUROC [95% CI] | p | p (Holm, across models) | supported |
|---|---|---|---|---|---|
| Qwen/Qwen2.5-7B-Instruct | stated_vs_prob | -0.066 [-0.103, -0.029] | 3.40e-04 | 0.0014 | yes |
| Qwen/Qwen2.5-7B-Instruct | stated_vs_agree | -0.103 [-0.141, -0.065] | 1.42e-08 | 7.08e-08 | yes |
| Qwen/Qwen2.5-7B-Instruct | prob_vs_agree | -0.036 [-0.069, -0.004] | 0.0261 | 0.0522 | no |
| meta-llama/Llama-3.1-8B-Instruct | stated_vs_prob | -0.043 [-0.078, -0.009] | 0.0166 | 0.0498 | yes |
| meta-llama/Llama-3.1-8B-Instruct | stated_vs_agree | -0.155 [-0.190, -0.122] | 3.37e-18 | 3.03e-17 | yes |
| meta-llama/Llama-3.1-8B-Instruct | prob_vs_agree | -0.112 [-0.144, -0.079] | 3.11e-11 | 1.87e-10 | yes |
| mistralai/Mistral-7B-Instruct-v0.3 | stated_vs_prob | -0.136 [-0.169, -0.099] | 9.19e-14 | 6.43e-13 | yes |
| mistralai/Mistral-7B-Instruct-v0.3 | stated_vs_agree | -0.023 [-0.053, 0.007] | 0.1348 | 0.1348 | no |
| mistralai/Mistral-7B-Instruct-v0.3 | prob_vs_agree | 0.113 [0.088, 0.138] | 5.35e-18 | 4.28e-17 | yes |

| model | H1 | H2 | H3 |
|---|---|---|---|
| Qwen/Qwen2.5-7B-Instruct | True | False | False (agree>prob) |
| meta-llama/Llama-3.1-8B-Instruct | True | False | True (agree>prob) |
| mistralai/Mistral-7B-Instruct-v0.3 | False | False | True (prob>agree) |

## Setting: direct (secondary)

Holm family size: 9; flagged models excluded: none

| model | N | accuracy | AUROC stated | AUROC prob | AUROC agree | ECE stated | ECE prob | ECE agree |
|---|---|---|---|---|---|---|---|---|
| Qwen/Qwen2.5-7B-Instruct | 1273 | 0.597 | 0.587 [0.563, 0.611] | 0.718 [0.690, 0.746] | 0.726 [0.697, 0.752] | 0.282 [0.254, 0.308] | 0.347 [0.320, 0.374] | 0.196 [0.172, 0.221] |
| meta-llama/Llama-3.1-8B-Instruct | 1273 | 0.606 | 0.564 [0.545, 0.581] | 0.756 [0.727, 0.783] | 0.862 [0.842, 0.883] | 0.209 [0.184, 0.237] | 0.223 [0.200, 0.249] | 0.080 [0.063, 0.102] |
| mistralai/Mistral-7B-Instruct-v0.3 | 1273 | 0.491 | 0.526 [0.501, 0.553] | 0.661 [0.632, 0.691] | 0.579 [0.558, 0.600] | 0.465 [0.438, 0.491] | 0.426 [0.399, 0.453] | 0.425 [0.398, 0.452] |

| model | pair | ΔAUROC [95% CI] | p | p (Holm, across models) | supported |
|---|---|---|---|---|---|
| Qwen/Qwen2.5-7B-Instruct | stated_vs_prob | -0.131 [-0.161, -0.100] | 2.03e-17 | 1.42e-16 | yes |
| Qwen/Qwen2.5-7B-Instruct | stated_vs_agree | -0.139 [-0.172, -0.105] | 8.25e-17 | 4.95e-16 | yes |
| Qwen/Qwen2.5-7B-Instruct | prob_vs_agree | -0.008 [-0.036, 0.021] | 0.5565 | 0.5565 | no |
| meta-llama/Llama-3.1-8B-Instruct | stated_vs_prob | -0.192 [-0.220, -0.163] | 1.51e-40 | 1.21e-39 | yes |
| meta-llama/Llama-3.1-8B-Instruct | stated_vs_agree | -0.299 [-0.324, -0.273] | 1.00e-110 | 9.03e-110 | yes |
| meta-llama/Llama-3.1-8B-Instruct | prob_vs_agree | -0.106 [-0.134, -0.080] | 1.54e-15 | 7.71e-15 | yes |
| mistralai/Mistral-7B-Instruct-v0.3 | stated_vs_prob | -0.135 [-0.167, -0.098] | 7.64e-14 | 3.05e-13 | yes |
| mistralai/Mistral-7B-Instruct-v0.3 | stated_vs_agree | -0.053 [-0.085, -0.021] | 0.0019 | 0.0038 | yes |
| mistralai/Mistral-7B-Instruct-v0.3 | prob_vs_agree | 0.082 [0.055, 0.107] | 2.14e-09 | 6.43e-09 | yes |

| model | H1 | H2 | H3 |
|---|---|---|---|
| Qwen/Qwen2.5-7B-Instruct | True | False | False (agree>prob) |
| meta-llama/Llama-3.1-8B-Instruct | True | False | True (agree>prob) |
| mistralai/Mistral-7B-Instruct-v0.3 | True | True | True (prob>agree) |

