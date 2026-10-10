import math

import pytest

from medqa_conf import parsing, prompts

ANSWER_CASES = [
    ("Answer: C\nConfidence: 80", "C", "answer_line"),
    ("**Answer:** C", "C", "answer_line"),
    ("**Answer: C**", "C", "answer_line"),
    ("**Answer**: B", "B", "answer_line"),
    ("Answer: (B)", "B", "answer_line"),
    ("Answer: [D]", "D", "answer_line"),
    ("Answer: C. Confidence: 85%", "C", "answer_line"),
    ("Answer:A", "A", "answer_line"),
    ("Final Answer: D) Hypertension", "D", "answer_line"),
    ("answer: b", None, "none"),  # lower-case letter is not accepted
    ("Answer: A\n...on reflection...\nAnswer: B\nConfidence: 70", "B", "answer_line"),  # last wins
    ("The answer is D", "D", "answer_is"),
    ("So the answer is (A).", "A", "answer_is"),
    ("Therefore the answer is **C**", "C", "answer_is"),
    ("The answer is option B.", "B", "answer_is"),
    ("I think it's probably the second one.", None, "none"),
    ("", None, "none"),
    ("Answer: <A, B, C or D>", None, "none"),  # template echo is not an answer
    ("Answer: Acute kidney injury", None, "none"),  # A followed by a letter
    ("Answer: A\nConfidence: 90\nAnswer: <A, B, C or D>", "A", "answer_line"),
    ("Step 1 ... the answer is B.\nAnswer: C", "C", "answer_line"),  # Answer line beats fallback
]


@pytest.mark.parametrize("text,letter,method", ANSWER_CASES)
def test_parse_answer(text, letter, method):
    assert parsing.parse_answer(text) == (letter, method)


CONF_CASES = [
    ("Confidence: 85", 0.85, False),
    ("Confidence: 85%", 0.85, False),
    ("**Confidence:** 90%", 0.90, False),
    ("**Confidence: 75**", 0.75, False),
    ("Confidence:   60 %", 0.60, False),
    ("Confidence: 0.9", 0.9, True),
    ("Confidence: .7", 0.7, True),
    ("Confidence: 1.0", 1.0, True),
    ("Confidence: 1", 0.01, False),  # integer 1 means 1 %
    ("Confidence: 150", 1.0, False),  # clipped
    ("Confidence: 85.5", 0.855, False),
    ("Answer: C. Confidence: 85%", 0.85, False),
    ("Confidence: 40\n...\nConfidence: 70", 0.70, False),  # last wins
]


@pytest.mark.parametrize("text,val,frac", CONF_CASES)
def test_parse_confidence(text, val, frac):
    v, f = parsing.parse_confidence(text)
    assert v == pytest.approx(val) and f == frac


@pytest.mark.parametrize("text", ["", "no number here", "Confidence: high", None])
def test_parse_confidence_missing(text):
    v, f = parsing.parse_confidence(text)
    assert math.isnan(v) and f is False


@pytest.mark.parametrize("text,val,frac", [(" 85", 0.85, False), (" 85%", 0.85, False), ("**90**", 0.9, False),
                                           (" 0.8", 0.8, True), ("\n70", 0.7, False)])
def test_parse_confidence_continuation(text, val, frac):
    v, f = parsing.parse_confidence_continuation(text)
    assert v == pytest.approx(val) and f == frac


def test_parse_confidence_continuation_missing():
    assert math.isnan(parsing.parse_confidence_continuation(" unsure")[0])


def test_cot_letter_prefix():
    g = "Reasoning. Answer: A maybe.\nMore.\nAnswer: C\nConfidence: 80"
    pre, forced = prompts.cot_letter_prefix(g)
    assert pre == "Reasoning. Answer: A maybe.\nMore.\nAnswer:" and not forced
    pre, forced = prompts.cot_letter_prefix("No final line here.  \n")
    assert pre == "No final line here.\nAnswer:" and forced
    assert prompts.cot_recovery_prefill("x Answer:", "B") == "x Answer: B\nConfidence:"
    assert prompts.direct_conf_prefill("D") == "Answer: D\nConfidence:"


def test_prompts_verbatim():
    class Q:
        question = "Q?"
        options = {"A": "a", "B": "b", "C": "c", "D": "d"}
    m = prompts.cot_message(Q)
    assert m.startswith("The following is a multiple-choice question from the US Medical Licensing Examination "
                        "(USMLE). Choose the single best answer.\n\nQuestion: Q?\nA. a\nB. b\nC. c\nD. d\n\n"
                        "Think through the problem step by step.")
    assert m.endswith("Answer: <A, B, C or D>\nConfidence: <a number from 0 to 100: the probability that your "
                      "answer is correct>")
    assert "Reply with exactly these two lines and nothing else:\n" in prompts.direct_message(Q)
