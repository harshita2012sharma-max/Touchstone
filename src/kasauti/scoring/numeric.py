"""Extract the final number from a model's answer to a word problem.

Rule: if the reply has an answer marker ("Answer", "उत्तर", "जवाब"), take
the first number after the last marker; otherwise take the last number.
Devanagari digits and Indian digit grouping (1,00,000) are supported.
"""

from __future__ import annotations

import math
import re

from kasauti.scoring.normalize import clean_output

_NUMBER = re.compile(r"(?<!\d)-?\d+(?:,\d{2,3})*(?:\.\d+)?")
_MARKER = re.compile(r"answer|ans\b|उत्तर|जवाब", re.IGNORECASE)


def _to_float(token: str) -> float:
    return float(token.replace(",", ""))


def parse_number(text: str) -> float | None:
    """Return the answer number in ``text``, or ``None`` if there is none."""
    reply = clean_output(text)
    markers = list(_MARKER.finditer(reply))
    if markers:
        after = _NUMBER.search(reply, markers[-1].end())
        if after:
            return _to_float(after.group())
    numbers = _NUMBER.findall(reply)
    return _to_float(numbers[-1]) if numbers else None


def numbers_match(got: float, expected: float) -> bool:
    """Equal up to floating-point noise (absolute tolerance 1e-6)."""
    return math.isclose(got, expected, rel_tol=1e-9, abs_tol=1e-6)
