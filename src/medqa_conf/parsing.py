"""Answer / confidence parsing (PREREGISTRATION.md sections 5-6)."""
from __future__ import annotations

import math
import re

# "Answer", optional "**" before the colon, ":", optional "**", optional "(" or "[", one capital A-D
# that is not followed by another letter. Last match wins.
ANSWER_LINE_RE = re.compile(r"(?i:answer)(?:\s*\*\*)?\s*:\s*(?:\*\*\s*)?[\(\[]?\s*([A-D])(?![A-Za-z])")
ANSWER_IS_RE = re.compile(
    r"(?i:answer\s+is)\s*(?:\*\*\s*)?(?:(?i:option)\s*)?[:\(\[]?\s*(?:\*\*\s*)?([A-D])(?![A-Za-z])")

_NUM = r"(\d+(?:\.\d+)?|\.\d+)"
CONF_RE = re.compile(r"(?i:confidence)(?:\s*\*\*)?\s*:\s*(?:\*\*\s*)?" + _NUM + r"\s*%?")
LEADING_NUM_RE = re.compile(r"^\s*(?:\*\*\s*)?" + _NUM)


def parse_answer(text: str | None) -> tuple[str | None, str]:
    """Return (letter or None, method) with method in {'answer_line', 'answer_is', 'none'}."""
    if not text:
        return None, "none"
    m = list(ANSWER_LINE_RE.finditer(text))
    if m:
        return m[-1].group(1), "answer_line"
    m = list(ANSWER_IS_RE.finditer(text))
    if m:
        return m[-1].group(1), "answer_is"
    return None, "none"


def _to_conf(num: str) -> tuple[float, bool]:
    v = float(num)
    if v <= 1 and "." in num:
        return min(max(v, 0.0), 1.0), True
    return min(max(v / 100.0, 0.0), 1.0), False


def parse_confidence(text: str | None) -> tuple[float, bool]:
    """Last 'Confidence:' number -> (conf in [0,1] or NaN, fraction_flag)."""
    if not text:
        return math.nan, False
    m = list(CONF_RE.finditer(text))
    if not m:
        return math.nan, False
    return _to_conf(m[-1].group(1))


def parse_confidence_continuation(text: str | None) -> tuple[float, bool]:
    """Number at the start of a short generation that follows a 'Confidence:' prefill."""
    if not text:
        return math.nan, False
    m = LEADING_NUM_RE.match(text)
    if not m:
        return math.nan, False
    return _to_conf(m.group(1))
