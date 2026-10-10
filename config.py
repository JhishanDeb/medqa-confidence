"""Pre-registered configuration. Do not change values without amending PREREGISTRATION.md.

Everything that determines model outputs or analysis results lives here. The config hash
(used for resume and logged in run_log.json) covers every field of `Config`.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json

DATASET_ID = "GBaker/MedQA-USMLE-4-options"
TEST_ROWS = 1273
TRAIN_ROWS = 10178
LETTERS = ("A", "B", "C", "D")

DEFAULT_MODELS = (
    "Qwen/Qwen2.5-7B-Instruct",
    "meta-llama/Llama-3.1-8B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
)


@dataclasses.dataclass(frozen=True)
class Config:
    model_id: str = DEFAULT_MODELS[0]
    pilot: bool = False
    dataset_id: str = DATASET_ID
    # generation
    base_seed: int = 12345
    greedy_max_new_tokens: int = 1024
    n_samples: int = 5
    sample_temperature: float = 0.7
    sample_top_p: float = 1.0
    sample_max_new_tokens: int = 1024
    confidence_max_new_tokens: int = 6
    topk_logprobs: int = 20
    dtype: str = "float16"
    max_model_len: int = 4096
    tensor_parallel_size: int = 2
    # pilot
    pilot_n: int = 20
    pilot_split: str = "train"
    max_projected_hours: float = 11.0
    # analysis
    n_bins: int = 15
    coverage: float = 0.8
    n_boot: int = 2000
    boot_seed: int = 2026
    cv_folds: int = 5
    cv_seed: int = 2026
    alpha: float = 0.05
    # validity flags
    flag_min_accuracy: float = 0.40
    flag_max_parse_fail: float = 0.10
    flag_min_median_letter_mass: float = 0.5
    flag_max_truncation: float = 0.10
    # engineering
    checkpoint_every: int = 50
    determinism_n: int = 10

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    def config_hash(self) -> str:
        blob = json.dumps(self.to_dict(), sort_keys=True).encode()
        return hashlib.sha256(blob).hexdigest()[:12]

    @property
    def model_slug(self) -> str:
        slug = self.model_id.split("/")[-1].replace(".", "_").replace("-", "_").lower()
        return slug + ("_pilot" if self.pilot else "")


# Analysis-only settings (used by report.py when recomputing from a CSV).
ANALYSIS_KEYS = ("n_bins", "coverage", "n_boot", "boot_seed", "cv_folds", "cv_seed", "alpha",
                 "flag_min_accuracy", "flag_max_parse_fail", "flag_min_median_letter_mass",
                 "flag_max_truncation")
