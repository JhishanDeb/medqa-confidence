import dataclasses
import filecmp
import json
import os
import zipfile

import pytest

from config import Config
from medqa_conf import data, generate, pipeline, report
from medqa_conf.backends import MockBackend, NonFiniteLogprobError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREREG = os.path.join(ROOT, "PREREGISTRATION.md")

EXPECTED = ["per_question.csv", "summary.json", "results_table.md", "sanity_report.md", "run_log.json",
            "raw_examples.md", "raw_generations.jsonl.gz", "checkpoint.jsonl",
            "figures/reliability_cot.png", "figures/reliability_direct.png", "figures/risk_coverage_cot.png",
            "figures/risk_coverage_direct.png", "figures/histograms_cot.png", "figures/histograms_direct.png"]


@pytest.fixture(scope="module")
def mock_run(tmp_path_factory):
    out = tmp_path_factory.mktemp("mock")
    cfg, qs, res = pipeline.run_mock(30, str(out), prereg_path=PREREG, code_dir=os.path.join(ROOT, "src"),
                                     log=lambda *a: None)
    return cfg, qs, res


def test_all_files_and_bundle(mock_run):
    cfg, qs, res = mock_run
    assert res["status"] == "complete"
    for f in EXPECTED:
        assert os.path.exists(os.path.join(res["out_dir"], f)), f
    b = res["bundle"]
    assert os.path.getsize(b) < 5 * 1024 * 1024
    names = zipfile.ZipFile(b).namelist()
    assert "PREREGISTRATION.md" in names and "per_question.csv" in names and "summary.json" in names
    assert not any("raw_generations" in n or "checkpoint" in n for n in names)


def test_per_question_columns(mock_run):
    _, qs, res = mock_run
    df = report.read_csv(res["csv"])
    assert len(df) == 2 * len(qs)
    for c in ["model", "setting", "qid", "meta_info", "gold", "answer", "correct", "p_A", "p_B", "p_C", "p_D",
              "letter_mass", "conf_prob", "conf_stated", "conf_agree", "stated_recovered", "stated_fraction_flag",
              "sample_answers", "majority_answer", "forced_answer", "parsed_vs_argmax_mismatch", "greedy_tokens",
              "greedy_truncated", "n_samples_truncated"]:
        assert c in df.columns, c
    assert df.conf_prob.between(0.25, 1).all()
    assert (df.sample_answers.str.len() == 5).all()
    # the mock exercises the rare paths
    cot = df[df.setting == "cot"]
    assert cot.forced_answer.sum() > 0 or cot.stated_recovered.sum() > 0 or cot.conf_stated.isna().any()
    # the Direct setting shares the CoT samples
    d = df[df.setting == "direct"].set_index("qid").sample_answers
    assert (cot.set_index("qid").sample_answers == d).all()


def test_from_csv_reproduces_summary_exactly(mock_run, tmp_path):
    _, _, res = mock_run
    report.main(["--from-csv", res["csv"], "--out", str(tmp_path), "--no-figures"])
    assert filecmp.cmp(os.path.join(res["out_dir"], "summary.json"), os.path.join(tmp_path, "summary.json"),
                       shallow=False)


def test_summary_contents(mock_run):
    _, _, res = mock_run
    s = json.load(open(os.path.join(res["out_dir"], "summary.json")))
    cot = s["settings"]["cot"]
    assert set(cot["signals"]) == {"stated", "prob", "agree"}
    assert set(cot["pairs"]) == {"stated_vs_prob", "stated_vs_agree", "prob_vs_agree"}
    assert cot["n_complete_case"] + cot["n_dropped"] == cot["n_total"] == 30
    assert cot["references"]["k"] == 24
    for h in ("H1", "H2", "H3"):
        assert "supported" in cot["hypotheses"][h]
    assert "EXPLORATORY" in cot["exploratory"]["label"]


def test_checkpoint_resume(tmp_path):
    over = dict(checkpoint_every=10)
    cfg = dataclasses.replace(Config(), model_id="mock/Mock-7B", **over)
    rows = data.synthetic_rows(30, seed=1)
    qs, info = data.load_questions(cfg, [], rows, expected_test=30, expected_train=None)
    key = {q.question: q.gold for q in qs}
    quiet = lambda *a: None
    first = tmp_path / "session1" / cfg.model_slug
    r1 = pipeline.run(cfg, MockBackend(key), qs, info, str(first), model_revision="mock", time_budget_s=0.0, log=quiet)
    assert r1["status"] == "incomplete" and r1["n_done"] == 10
    second = tmp_path / "session2" / cfg.model_slug
    r2 = pipeline.run(cfg, MockBackend(key), qs, info, str(second), model_revision="mock",
                      resume_roots=[str(tmp_path / "session1")], log=quiet)
    assert r2["status"] == "complete"
    log = json.load(open(second / "run_log.json"))
    assert log["generation"]["n_resumed"] == 10 and log["generation"]["n_generated"] == 20
    straight = tmp_path / "straight" / cfg.model_slug
    pipeline.run(cfg, MockBackend(key), qs, info, str(straight), model_revision="mock", log=quiet)
    assert filecmp.cmp(second / "per_question.csv", straight / "per_question.csv", shallow=False)
    # mismatched revision refuses to resume
    with pytest.raises(generate.ResumeMismatchError):
        pipeline.run(cfg, MockBackend(key), qs, info, str(tmp_path / "s3" / cfg.model_slug), model_revision="other",
                     resume_roots=[str(tmp_path / "session1")], log=quiet)


def test_nan_logprob_stops_run(tmp_path):
    cfg = dataclasses.replace(Config(), model_id="mock/Mock-7B")
    rows = data.synthetic_rows(5, seed=1)
    qs, info = data.load_questions(cfg, [], rows, expected_test=5, expected_train=None)
    key = {q.question: q.gold for q in qs}
    with pytest.raises(NonFiniteLogprobError):
        pipeline.run(cfg, MockBackend(key, nan_question=qs[2].question), qs, info, str(tmp_path / "x"),
                     log=lambda *a: None)


def test_dataset_validation_fails_loudly():
    cfg = Config()
    rows = data.synthetic_rows(10)
    with pytest.raises(data.DataValidationError):
        data.load_questions(cfg, [], rows)  # expects exactly 1273 test rows
    bad = data.synthetic_rows(10)
    del bad[3]["options"]["D"]
    with pytest.raises(data.DataValidationError):
        data.load_questions(cfg, [], bad, expected_test=10)
    bad = data.synthetic_rows(10)
    bad[4]["answer_idx"] = "E"
    with pytest.raises(data.DataValidationError):
        data.load_questions(cfg, [], bad, expected_test=10)


def test_cleaning_counts():
    assert data.clean_option('Benzodiazepine intoxication\n"') == "Benzodiazepine intoxication"
    assert data.clean_option('"Wait and see"') == '"Wait and see"'
    qs, st = data.build_questions(data.synthetic_rows(14))
    assert st["n_options_cleaned"] == 2  # rows 0 and 7
    assert all(not q.options["C"].endswith('"') for q in qs)


def test_pilot_uses_train_and_reports(tmp_path):
    cfg, qs, res = pipeline.run_mock(30, str(tmp_path), pilot=True, log=lambda *a: None)
    assert cfg.pilot and len(qs) == 20 and res["status"] == "complete"
    assert os.path.exists(os.path.join(res["out_dir"], "pilot_report.md"))
    assert res["out_dir"].endswith("_pilot")
    log = json.load(open(os.path.join(res["out_dir"], "run_log.json")))
    assert log["data"]["used_split"] == "train"
    assert "projected_full_hours" in log["pilot_projection"]
    pipeline.check_pilot(res)  # mock is fast -> no abort
    res["projection"]["abort"] = True
    with pytest.raises(pipeline.PilotAbort):
        pipeline.check_pilot(res)


def test_combine_two_models(tmp_path):
    for mid, acc in (("mock/Mock-A", 0.6), ("mock/Mock-B", 0.7)):
        pipeline.run_mock(30, str(tmp_path / "runs"), model_id=mid, accuracy=acc, log=lambda *a: None)
    c = report.combine([str(tmp_path / "runs")], str(tmp_path / "combined"), prereg_path=PREREG)
    assert c["models"] == ["mock/Mock-A", "mock/Mock-B"]
    assert os.path.exists(c["bundle"]) and os.path.getsize(c["bundle"]) < 5 * 1024 * 1024
    cot = c["settings"]["cot"]
    n_ok = 2 - len(cot["excluded_flagged_models"])
    assert cot["holm_family_size"] == 3 * n_ok


@pytest.fixture(scope="module")
def tiny_hf(tmp_path_factory):
    torch = pytest.importorskip("torch")
    pytest.importorskip("transformers")
    from tokenizers import Tokenizer, models, pre_tokenizers
    try:
        from transformers import LlamaConfig, LlamaForCausalLM, PreTrainedTokenizerFast
    except Exception as e:  # e.g. transformers too new for the installed torch
        pytest.skip(f"transformers models unavailable: {e}")
    from medqa_conf.backends import HFBackend

    path = tmp_path_factory.mktemp("tiny")
    words = ["<pad>", "<s>", "</s>", "A", "B", "C", "D", "Answer:", "Confidence:", "Question:", "<unk>"]
    words += [f"w{i}" for i in range(50)]
    tk = Tokenizer(models.WordLevel({w: i for i, w in enumerate(words)}, unk_token="<unk>"))
    tk.pre_tokenizer = pre_tokenizers.WhitespaceSplit()
    tok = PreTrainedTokenizerFast(tokenizer_object=tk, bos_token="<s>", eos_token="</s>", pad_token="<pad>",
                                  unk_token="<unk>")
    tok.chat_template = "{% for m in messages %}<s> {{ m['content'] }} {% endfor %}{% if add_generation_prompt %} w0 {% endif %}"
    tok.save_pretrained(path)
    torch.manual_seed(0)
    model = LlamaForCausalLM(LlamaConfig(vocab_size=len(words), hidden_size=32, intermediate_size=64,
                                         num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=2,
                                         max_position_embeddings=512, bos_token_id=1, eos_token_id=2,
                                         pad_token_id=0))
    model.save_pretrained(path)
    cfg = dataclasses.replace(Config(), model_id="tiny/random", greedy_max_new_tokens=6, sample_max_new_tokens=6)
    be = HFBackend(str(path), cfg, batch_size=2, sample_batch_questions=2, device_map=None, dtype=torch.float32)
    return torch, be, cfg, path


def test_hf_backend_pipeline(tiny_hf, tmp_path):
    torch, be, cfg, _ = tiny_hf
    assert be.letter_variants == {"A": [3], "B": [4], "C": [5], "D": [6]}
    rows = data.synthetic_rows(3, seed=1)
    qs, info = data.load_questions(cfg, [], rows, expected_test=3, expected_train=None)
    res = pipeline.run(cfg, be, qs, info, str(tmp_path / "out"), model_revision="tiny", log=lambda *a: None)
    assert res["status"] == "complete"
    df = report.read_csv(res["csv"])
    assert df.letter_mass.between(0, 1).all() and (df.n_letters_missing_topk == 0).all()
    log = json.load(open(tmp_path / "out" / "run_log.json"))
    assert log["determinism"]["identical"] == 3


def test_hf_decode_matches_generate_and_padding(tiny_hf):
    from medqa_conf.backends import GenRequest
    torch, be, cfg, _ = tiny_hf
    short, long_ = "<s> w1 w2", "<s> w3 w4 w5 w6 w7 w8 w9 Answer:"
    # greedy loop == transformers generate (no padding)
    for p in (short, long_):
        ids = torch.tensor([be.tokenizer.encode(p, add_special_tokens=False)])
        ref = be.model.generate(input_ids=ids, attention_mask=torch.ones_like(ids), max_new_tokens=8,
                                do_sample=False, eos_token_id=be.eos_ids, pad_token_id=be.pad_id)
        ref_toks = [t for t in ref[0, ids.shape[1]:].tolist() if t not in be.eos_ids][:8]
        out = be._decode([p], 8, 0.0, 1.0, [0])[0]
        assert be.tokenizer.encode(out.text, add_special_tokens=False) == ref_toks and out.n_tokens == len(ref_toks)
    # left padding does not change results
    alone = be._decode([short], 8, 0.0, 1.0, [0])[0].text
    padded = be._decode([long_, short], 8, 0.0, 1.0, [0, 0])[1].text
    assert alone == padded
    lp_alone = be.next_token_logprobs([short])[0]
    lp_pad = be.next_token_logprobs([long_, short])[1]
    for k in lp_alone:
        assert lp_alone[k] == pytest.approx(lp_pad[k], abs=1e-4)
    # a question's samples do not depend on the other questions in the batch
    r1 = GenRequest(short, 8, temperature=0.7, n=5, seed=101)
    r2 = GenRequest(long_, 8, temperature=0.7, n=5, seed=202)
    a = [o.text for o in be.generate([r1])[0]]
    b = [o.text for o in be.generate([r2, r1])[1]]
    assert a == b
    assert len(set(a)) > 1  # actually sampling


def test_notebooks_inline_current_sources():
    nbformat = pytest.importorskip("nbformat")
    for name in ("generate_and_analyze.ipynb", "combine_models.ipynb"):
        nb = nbformat.read(os.path.join(ROOT, "kaggle", name), as_version=4)
        written = {}
        for c in nb.cells:
            if c.cell_type == "code" and c.source.startswith("%%writefile "):
                head, body = c.source.split("\n", 1)
                written[head.split(" ", 1)[1].strip()] = body
        assert "medqa_src/config.py" in written and "medqa_src/PREREGISTRATION.md" in written
        for rel, body in written.items():
            local = rel.replace("medqa_src/", "", 1)
            local = os.path.join(ROOT, local if not local.startswith("medqa_conf/") else "src/" + local)
            with open(local, encoding="utf-8") as f:
                assert f.read() == body, f"{name}: {rel} is stale; run tools/build_kaggle_notebook.py"
