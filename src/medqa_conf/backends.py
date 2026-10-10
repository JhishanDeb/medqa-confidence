"""Model backends behind one interface: vLLM (preferred), transformers (fallback), Mock (CPU tests).

Interface
---------
render(user_msg) -> str                       chat-template prompt (no system message, generation prompt added)
generate(list[GenRequest]) -> list[list[GenOutput]]
next_token_logprobs(list[str]) -> list[dict[token_id, logprob]]   restricted to letter-variant ids that are
                                              available (top-k for vLLM, full softmax for HF). Raises on NaN/inf.
letter_variants: dict[letter, list[token_id]] ; letter_variant_strings: dict[token_id, str]
info() -> dict
"""
from __future__ import annotations

import dataclasses
import hashlib
import math
import re

LETTERS = ("A", "B", "C", "D")


class NonFiniteLogprobError(RuntimeError):
    pass


@dataclasses.dataclass
class GenRequest:
    prompt: str
    max_new_tokens: int
    temperature: float = 0.0
    top_p: float = 1.0
    n: int = 1
    seed: int | None = None


@dataclasses.dataclass
class GenOutput:
    text: str
    n_tokens: int
    finish_reason: str  # "stop" | "length"


def check_finite(values, where: str) -> None:
    for v in values:
        if not math.isfinite(v):
            raise NonFiniteLogprobError(f"non-finite logprob ({v}) in {where}")


def find_letter_variants(tokenizer) -> tuple[dict, dict]:
    """Single-token ids for 'L' and ' L' (byte-level 'ĠL' or sentencepiece '▁L')."""
    vocab = tokenizer.get_vocab()
    variants, strings = {}, {}
    for L in LETTERS:
        ids = []
        for cand in (L, "Ġ" + L, "▁" + L):
            tid = vocab.get(cand)
            if tid is None or tid in ids:
                continue
            dec = tokenizer.decode([tid])
            if dec.strip() == L:
                ids.append(tid)
                strings[tid] = dec
        if not ids:
            raise RuntimeError(f"no single-token variant found for letter {L}")
        variants[L] = ids
    return variants, strings


def render_chat(tokenizer, user_msg: str) -> str:
    msgs = [{"role": "user", "content": user_msg}]
    try:
        return tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True,
                                             enable_thinking=False)
    except TypeError:
        return tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


def eos_token_ids(model_path: str, tokenizer) -> list[int]:
    ids = []
    try:
        from transformers import GenerationConfig
        e = GenerationConfig.from_pretrained(model_path).eos_token_id
        ids += list(e) if isinstance(e, (list, tuple)) else ([e] if e is not None else [])
    except Exception:
        pass
    if tokenizer.eos_token_id is not None:
        ids.append(tokenizer.eos_token_id)
    return sorted(set(int(i) for i in ids))


def download_model(model_id: str, cache_dir: str, revision: str | None = None, token: str | None = None):
    """Resolve the exact commit hash and download weights (safetensors shards only). -> (path, sha)."""
    from huggingface_hub import HfApi, snapshot_download
    sha = HfApi(token=token).model_info(model_id, revision=revision).sha
    path = snapshot_download(model_id, revision=sha, cache_dir=cache_dir, token=token,
                             allow_patterns=["*.json", "model*.safetensors", "*.model", "tokenizer*",
                                             "*.txt", "*.jinja", "*.tiktoken"])
    return path, sha


class Backend:
    name = "base"
    topk: int | None = None
    letter_variants: dict
    letter_variant_strings: dict

    def render(self, user_msg: str) -> str:
        return render_chat(self.tokenizer, user_msg)

    def all_letter_ids(self) -> list[int]:
        return [i for L in LETTERS for i in self.letter_variants[L]]

    def info(self) -> dict:
        return {"backend": self.name, "topk": self.topk,
                "letter_variants": {L: [[i, self.letter_variant_strings[i]] for i in ids]
                                    for L, ids in self.letter_variants.items()}}


# --------------------------------------------------------------------------------------------- vLLM
class VLLMBackend(Backend):
    name = "vllm"

    def __init__(self, model_path: str, cfg, gpu_memory_utilization: float = 0.90):
        from transformers import AutoTokenizer
        from vllm import LLM

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.eos_ids = eos_token_ids(model_path, self.tokenizer)
        self.letter_variants, self.letter_variant_strings = find_letter_variants(self.tokenizer)
        self.topk = cfg.topk_logprobs
        kw = dict(model=model_path, tokenizer=model_path, tensor_parallel_size=cfg.tensor_parallel_size,
                  dtype=cfg.dtype, max_model_len=cfg.max_model_len, seed=cfg.base_seed,
                  gpu_memory_utilization=gpu_memory_utilization, disable_custom_all_reduce=True,
                  max_logprobs=max(20, cfg.topk_logprobs), generation_config="vllm")
        try:
            self.llm = LLM(**kw)
        except TypeError as e:  # older vLLM without `generation_config`
            if "generation_config" not in str(e):
                raise
            kw.pop("generation_config")
            self.llm = LLM(**kw)

    def _ids(self, prompt: str) -> dict:
        return {"prompt_token_ids": self.tokenizer.encode(prompt, add_special_tokens=False)}

    def generate(self, reqs):
        from vllm import SamplingParams
        sps = [SamplingParams(n=r.n, temperature=r.temperature, top_p=r.top_p, max_tokens=r.max_new_tokens,
                              seed=r.seed, stop_token_ids=self.eos_ids, repetition_penalty=1.0,
                              skip_special_tokens=True) for r in reqs]
        outs = self.llm.generate([self._ids(r.prompt) for r in reqs], sps, use_tqdm=False)
        res = []
        for o in outs:
            comps = sorted(o.outputs, key=lambda c: c.index)
            res.append([GenOutput(text=c.text, n_tokens=len(c.token_ids),
                                  finish_reason="length" if c.finish_reason == "length" else "stop")
                        for c in comps])
        return res

    def next_token_logprobs(self, prompts):
        from vllm import SamplingParams
        sp = SamplingParams(max_tokens=1, temperature=0.0, logprobs=self.topk)
        outs = self.llm.generate([self._ids(p) for p in prompts], sp, use_tqdm=False)
        wanted = set(self.all_letter_ids())
        res = []
        for o in outs:
            lp = o.outputs[0].logprobs[0]  # dict token_id -> Logprob (top-k, plus sampled token)
            vals = {int(t): float(v.logprob) for t, v in lp.items()}
            check_finite(vals.values(), "vLLM top-k logprobs")
            res.append({t: v for t, v in vals.items() if t in wanted})
        return res

    def info(self):
        import vllm
        d = super().info()
        d.update(vllm_version=vllm.__version__, eos_ids=self.eos_ids)
        return d


# --------------------------------------------------------------------------------------- transformers
class HFBackend(Backend):
    name = "hf"

    def __init__(self, model_path: str, cfg, batch_size: int = 16, device_map="auto", dtype=None):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.tokenizer.padding_side = "left"
        self.eos_ids = eos_token_ids(model_path, self.tokenizer)
        self.pad_id = self.tokenizer.pad_token_id if self.tokenizer.pad_token_id is not None else self.eos_ids[0]
        self.letter_variants, self.letter_variant_strings = find_letter_variants(self.tokenizer)
        self.topk = None  # full distribution
        import transformers
        dtype = dtype or getattr(torch, cfg.dtype)
        major, minor = (int(x) for x in transformers.__version__.split(".")[:2])
        dkey = "dtype" if (major, minor) >= (4, 56) else "torch_dtype"  # kwarg renamed in 4.56
        self.model = AutoModelForCausalLM.from_pretrained(model_path, device_map=device_map, **{dkey: dtype})
        if next(self.model.parameters()).dtype != dtype:
            raise RuntimeError(f"model loaded in {next(self.model.parameters()).dtype}, expected {dtype}")
        self.model.eval()
        # Replace model-provided sampling defaults (top_k, repetition_penalty, ...) with a clean config.
        self.model.generation_config = GenerationConfig(eos_token_id=self.eos_ids, pad_token_id=self.pad_id,
                                                        bos_token_id=self.tokenizer.bos_token_id)
        self.batch_size = batch_size

    def _device(self):
        return next(self.model.parameters()).device

    def _batch(self, prompts):
        enc = [self.tokenizer.encode(p, add_special_tokens=False) for p in prompts]
        L = max(len(e) for e in enc)
        ids = [[self.pad_id] * (L - len(e)) + e for e in enc]
        att = [[0] * (L - len(e)) + [1] * len(e) for e in enc]
        t = self.torch
        return t.tensor(ids, device=self._device()), t.tensor(att, device=self._device())

    def _decode_outputs(self, seqs, prompt_len, max_new):
        outs = []
        for s in seqs.tolist():
            gen = s[prompt_len:]
            n, stopped = len(gen), False
            for j, tid in enumerate(gen):
                if tid in self.eos_ids:
                    n, stopped = j, True
                    break
            gen = gen[:n]
            finish = "stop" if stopped or n < max_new else "length"
            outs.append(GenOutput(self.tokenizer.decode(gen, skip_special_tokens=True), n, finish))
        return outs

    def _gen(self, prompts, r, n):
        t = self.torch
        ids, att = self._batch(prompts)
        kw = dict(max_new_tokens=r.max_new_tokens, num_return_sequences=n,
                  eos_token_id=self.eos_ids, pad_token_id=self.pad_id)
        if r.temperature > 0:
            kw.update(do_sample=True, temperature=r.temperature, top_p=r.top_p, top_k=0)
        else:
            kw.update(do_sample=False)
        with t.no_grad():
            seqs = self.model.generate(input_ids=ids, attention_mask=att, **kw)
        return self._decode_outputs(seqs, ids.shape[1], r.max_new_tokens)

    def generate(self, reqs):
        t = self.torch
        res = [None] * len(reqs)
        greedy = [i for i, r in enumerate(reqs) if r.temperature == 0 and r.n == 1]
        # group greedy requests with the same max_new_tokens into batches
        by_len = {}
        for i in greedy:
            by_len.setdefault(reqs[i].max_new_tokens, []).append(i)
        for _, idxs in by_len.items():
            for b in range(0, len(idxs), self.batch_size):
                chunk = idxs[b:b + self.batch_size]
                outs = self._gen([reqs[i].prompt for i in chunk], reqs[chunk[0]], 1)
                for i, o in zip(chunk, outs):
                    res[i] = [o]
        for i, r in enumerate(reqs):
            if res[i] is not None:
                continue
            if r.seed is not None:  # per-question seed
                t.manual_seed(r.seed)
                if t.cuda.is_available():
                    t.cuda.manual_seed_all(r.seed)
            res[i] = self._gen([r.prompt], r, r.n)
        return res

    def next_token_logprobs(self, prompts):
        t = self.torch
        wanted = self.all_letter_ids()
        res = []
        for b in range(0, len(prompts), self.batch_size):
            ids, att = self._batch(prompts[b:b + self.batch_size])
            with t.no_grad():
                logits = self.model(input_ids=ids, attention_mask=att).logits[:, -1, :].float()
            if not bool(t.isfinite(logits).all()):
                raise NonFiniteLogprobError("non-finite logits in HF next-token forward pass")
            lp = t.log_softmax(logits, dim=-1)
            sel = lp[:, wanted].cpu().tolist()
            for row in sel:
                check_finite(row, "HF letter logprobs")
                res.append(dict(zip(wanted, row)))
        return res

    def info(self):
        import transformers
        d = super().info()
        d.update(transformers_version=transformers.__version__, eos_ids=self.eos_ids)
        return d


# --------------------------------------------------------------------------------------------- Mock
def _u(*parts) -> float:
    """Deterministic uniform(0,1) from a hash of the parts."""
    h = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return int.from_bytes(h[:8], "big") / 2 ** 64


class _MockTokenizer:
    def __init__(self):
        self.vocab = {L: i + 1 for i, L in enumerate(LETTERS)}
        self.vocab.update({"Ġ" + L: i + 11 for i, L in enumerate(LETTERS)})
        self.eos_token_id = 0

    def get_vocab(self):
        return dict(self.vocab)

    def decode(self, ids, **kw):
        inv = {v: k.replace("Ġ", " ") for k, v in self.vocab.items()}
        return "".join(inv.get(i, "?") for i in ids)

    def apply_chat_template(self, msgs, tokenize=False, add_generation_prompt=True, **kw):
        return "<|user|>\n" + msgs[0]["content"] + "\n<|assistant|>\n"


class MockBackend(Backend):
    """Deterministic fake model with controllable accuracy. Exercises every pipeline code path.

    answer_key maps question text -> gold letter. Outputs depend only on hashes of the question,
    the request seed and `seed`, so runs are reproducible.
    """
    name = "mock"
    _QRE = re.compile(r"Question: (.*?)\nA\. ", re.S)

    def __init__(self, answer_key: dict, accuracy: float = 0.65, seed: int = 0, topk: int = 20,
                 nan_question: str | None = None):
        self.tokenizer = _MockTokenizer()
        self.letter_variants, self.letter_variant_strings = find_letter_variants(self.tokenizer)
        self.answer_key, self.accuracy, self.seed, self.topk = answer_key, accuracy, seed, topk
        self.nan_question = nan_question

    def _latent(self, prompt):
        m = self._QRE.search(prompt)
        q = m.group(1).strip() if m else prompt
        gold = self.answer_key.get(q, "A")
        correct = _u(self.seed, q, "c") < self.accuracy
        wrong = [L for L in LETTERS if L != gold]
        intended = gold if correct else wrong[int(_u(self.seed, q, "w") * 3)]
        s = min(1.0, max(0.0, (0.55 if correct else 0.30) + 0.45 * _u(self.seed, q, "s")))
        return q, intended, s

    def _reasoning(self, q, n_words):
        return " ".join(f"step{i}" for i in range(n_words))

    def _greedy(self, prompt, q, X, s, max_new):
        kind = int(_u(self.seed, q, "kind") * 25)
        conf = int(round((60 + 38 * s) / 5) * 5)
        body = "Let me think step by step. " + self._reasoning(q, 20 + int(80 * _u(self.seed, q, "len")))
        if kind == 0:   # no "Answer:" line, fallback phrase, no confidence -> forced prefix + recovery
            return GenOutput(body + f"\nSo the answer is {X}.", 60, "stop")
        if kind == 1:   # truncated, nothing parsable
            return GenOutput(body, max_new, "length")
        if kind == 2:
            tail = f"\n**Answer:** {X}\n**Confidence:** {conf}%"
        elif kind == 3:
            tail = f"\nAnswer: ({X})\nConfidence: {conf / 100:.2f}"
        elif kind == 4:
            tail = f"\nAnswer: {X}\n"
        else:
            tail = f"\nAnswer: {X}\nConfidence: {conf}"
        return GenOutput(body + tail, 40 + len(body.split()), "stop")

    def _sample(self, q, X, s, seed, j):
        u = _u(self.seed, q, seed, j)
        if u < 0.03:
            return GenOutput(self._reasoning(q, 30), 1024, "length")
        if u < 0.06:
            return GenOutput("I am not sure.", 5, "stop")
        if _u(self.seed, q, seed, j, "agree") < 0.45 + 0.55 * s:
            L = X
        else:
            L = LETTERS[int(_u(self.seed, q, seed, j, "o") * 4)]
        return GenOutput(f"Reasoning.\nAnswer: {L}\nConfidence: {int(50 + 50 * s)}", 30, "stop")

    def generate(self, reqs):
        res = []
        for r in reqs:
            q, X, s = self._latent(r.prompt)
            if r.prompt.rstrip().endswith("Confidence:"):
                txt = f" {int(round(55 + 40 * s))}" if _u(self.seed, q, "cfail") > 0.02 else " unsure"
                res.append([GenOutput(txt, 2, "stop")])
            elif r.temperature == 0:
                res.append([self._greedy(r.prompt, q, X, s, r.max_new_tokens)])
            else:
                res.append([self._sample(q, X, s, r.seed, j) for j in range(r.n)])
        return res

    def next_token_logprobs(self, prompts):
        res = []
        for p in prompts:
            q, X, s = self._latent(p)
            if self.nan_question is not None and q == self.nan_question:
                check_finite([math.nan], "mock logprobs")
            cot = "Think through the problem" in p
            top = X
            if cot and _u(self.seed, q, "mismatch") < 0.05:  # argmax differs from written letter
                top = LETTERS[(LETTERS.index(X) + 1) % 4]
            mass = 0.55 + 0.44 * _u(self.seed, q, "mass", cot)
            ptop = 0.30 + 0.69 * s
            rest = [L for L in LETTERS if L != top]
            w = [_u(self.seed, q, L, cot) + 0.05 for L in rest]
            probs = {top: ptop}
            probs.update({L: (1 - ptop) * wi / sum(w) for L, wi in zip(rest, w)})
            drop = rest[0] if _u(self.seed, q, "drop", cot) < 0.10 else None  # missing from top-k
            out = {}
            for L in LETTERS:
                if L == drop:
                    continue
                sp, nosp = self.letter_variants[L][1], self.letter_variants[L][0]
                out[sp] = math.log(mass * probs[L] * 0.9)
                out[nosp] = math.log(mass * probs[L] * 0.1)
            res.append(out)
        return res
