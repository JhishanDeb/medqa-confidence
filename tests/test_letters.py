import math

import pytest

from medqa_conf.backends import find_letter_variants
from medqa_conf.generate import letter_distribution

VAR = {"A": [1, 11], "B": [2, 12], "C": [3, 13], "D": [4, 14]}


def lp(d):
    return {k: math.log(v) for k, v in d.items()}


def test_sum_of_variants_and_renormalisation():
    d = letter_distribution(lp({1: 0.1, 11: 0.3, 2: 0.05, 12: 0.05, 3: 0.2, 14: 0.1, 99: 0.2}), VAR)
    assert d["letter_mass"] == pytest.approx(0.8)
    assert d["p"]["A"] == pytest.approx(0.4 / 0.8)
    assert d["p"]["B"] == pytest.approx(0.1 / 0.8)
    assert d["p"]["C"] == pytest.approx(0.2 / 0.8)
    assert d["p"]["D"] == pytest.approx(0.1 / 0.8)
    assert sum(d["p"].values()) == pytest.approx(1.0)
    assert d["argmax"] == "A" and d["missing_letters"] == []


def test_missing_letter_contributes_zero():
    d = letter_distribution(lp({11: 0.6, 12: 0.2, 13: 0.1}), VAR)
    assert d["missing_letters"] == ["D"]
    assert d["p"]["D"] == 0.0
    assert d["letter_mass"] == pytest.approx(0.9)
    assert d["p"]["A"] == pytest.approx(0.6 / 0.9)


def test_space_vs_nospace_variant_only():
    d = letter_distribution(lp({3: 0.5, 14: 0.5}), VAR)  # "C" (no space) and " D"
    assert d["p"]["C"] == pytest.approx(0.5) and d["p"]["D"] == pytest.approx(0.5)
    assert d["argmax"] == "C"  # tie -> alphabetical


def test_zero_mass_uniform():
    d = letter_distribution({99: 0.0}, VAR)
    assert d["letter_mass"] == 0 and d["p"] == {L: 0.25 for L in "ABCD"} and d["argmax"] == "A"
    assert d["missing_letters"] == list("ABCD")


class _Tok:
    def __init__(self, vocab):
        self.vocab = vocab

    def get_vocab(self):
        return self.vocab

    def decode(self, ids):
        inv = {v: k for k, v in self.vocab.items()}
        return inv[ids[0]].replace("Ġ", " ").replace("▁", " ")


def test_find_variants_byte_level_and_sentencepiece():
    bl = _Tok({"A": 0, "B": 1, "C": 2, "D": 3, "ĠA": 10, "ĠB": 11, "ĠC": 12, "ĠD": 13, "x": 5})
    v, s = find_letter_variants(bl)
    assert v == {"A": [0, 10], "B": [1, 11], "C": [2, 12], "D": [3, 13]}
    assert s[10] == " A"
    sp = _Tok({"A": 0, "B": 1, "C": 2, "D": 3, "▁A": 20, "▁B": 21, "▁C": 22, "▁D": 23})
    v, _ = find_letter_variants(sp)
    assert v["D"] == [3, 23]
    with pytest.raises(RuntimeError):
        find_letter_variants(_Tok({"A": 0, "B": 1, "C": 2}))
