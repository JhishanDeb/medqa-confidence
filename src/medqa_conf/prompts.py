"""Pre-registered prompts (verbatim from PREREGISTRATION.md section 4)."""
from __future__ import annotations

QUESTION_BLOCK = (
    "The following is a multiple-choice question from the US Medical Licensing Examination (USMLE). "
    "Choose the single best answer.\n"
    "\n"
    "Question: {question}\n"
    "A. {A}\n"
    "B. {B}\n"
    "C. {C}\n"
    "D. {D}"
)

COT_SUFFIX = (
    "\n"
    "\n"
    "Think through the problem step by step. Then finish with exactly these two lines:\n"
    "Answer: <A, B, C or D>\n"
    "Confidence: <a number from 0 to 100: the probability that your answer is correct>"
)

DIRECT_SUFFIX = (
    "\n"
    "\n"
    "Reply with exactly these two lines and nothing else:\n"
    "Answer: <A, B, C or D>\n"
    "Confidence: <a number from 0 to 100: the probability that your answer is correct>"
)

ANSWER_ANCHOR = "Answer:"


def question_block(q) -> str:
    return QUESTION_BLOCK.format(question=q.question, **q.options)


def cot_message(q) -> str:
    return question_block(q) + COT_SUFFIX


def direct_message(q) -> str:
    return question_block(q) + DIRECT_SUFFIX


def cot_letter_prefix(greedy_text: str) -> tuple[str, bool]:
    """G up to and including its last 'Answer:'; else G.rstrip() + '\\nAnswer:' (forced)."""
    pos = greedy_text.rfind(ANSWER_ANCHOR)
    if pos >= 0:
        return greedy_text[: pos + len(ANSWER_ANCHOR)], False
    return greedy_text.rstrip() + "\n" + ANSWER_ANCHOR, True


def cot_recovery_prefill(cot_prefix: str, letter: str) -> str:
    return cot_prefix + f" {letter}\nConfidence:"


DIRECT_LETTER_PREFILL = "Answer:"


def direct_conf_prefill(letter: str) -> str:
    return f"Answer: {letter}\nConfidence:"
