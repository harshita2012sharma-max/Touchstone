"""Find which option letter a model chose in a multiple-choice answer.

Models answer in many styles: ``B``, ``(b)``, ``Option B``, ``Answer: B``,
``उत्तर: B``, ``**B**``, or by writing the option text. :func:`parse_choice`
accepts all of these. When the answer is missing or names two different
options, it returns ``None`` and the item is scored as "unparsed" (wrong),
so formatting failures stay visible in reports instead of being guessed.

Order of evidence, strongest first:
1. Explicit answer markers ("Answer:", "उत्तर", "सही जवाब", ...).
2. Option markers ("Option B", "विकल्प B").
3. The whole reply is a single letter (``B``, ``(b)``, ``B.``).
4. Stand-alone capital letters anywhere, combined with option text found
   in the reply; these must all agree.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from touchstone_llm.scoring.normalize import clean_output, is_word_char, normalize_text

LETTERS = "ABCDEFGH"

# A choice letter: bracketed (any case), a capital not touching other Latin
# letters, or a lower-case letter followed by end/punctuation (so the English
# article "a" in "a big city" is not read as option A).
_LETTER = (
    r"(?:[\(\[]\s*(?P<br>[A-Ha-h])\s*[\)\]]"
    r"|(?P<up>[A-H])(?![A-Za-z])"
    r"|(?P<lo>[a-h])(?=\s*(?:$|[.\)\]:,।!])))"
)
_EN_DASH = chr(0x2013)
_SEP = r"(?:\s*(?:is|है|:|-|" + _EN_DASH + r"|=)\s*)*\s*"
_ANSWER = re.compile(
    r"(?:correct\s+answer|final\s+answer|answer|ans|सही\s+उत्तर|सही\s+जवाब|उत्तर|जवाब)"
    + _SEP
    + _LETTER,
    re.IGNORECASE,
)
_OPTION = re.compile(r"(?:option|choice|विकल्प)" + _SEP + _LETTER, re.IGNORECASE)
_WHOLE = re.compile(r"^\s*" + _LETTER + r"\s*[.।:)\]]?\s*$")
_BARE = re.compile(r"(?<![A-Za-z])" + _LETTER)


def _letters(pattern: re.Pattern[str], text: str, valid: str) -> set[str]:
    found = set()
    for m in pattern.finditer(text):
        letter = (m.group("br") or m.group("up") or m.group("lo")).upper()
        if letter in valid:
            found.add(letter)
    return found


def _contains_phrase(haystack: str, needle: str) -> bool:
    """Whole-word substring test that also respects Devanagari vowel signs."""
    start = haystack.find(needle)
    while start != -1:
        end = start + len(needle)
        before_ok = start == 0 or not is_word_char(haystack[start - 1])
        after_ok = end == len(haystack) or not is_word_char(haystack[end])
        if before_ok and after_ok:
            return True
        start = haystack.find(needle, start + 1)
    return False


def _letters_by_text(text: str, options: Sequence[str], valid: str) -> set[str]:
    reply = normalize_text(text)
    normalized = [normalize_text(o) for o in options]
    for letter, opt in zip(valid, normalized, strict=True):
        if opt and reply == opt:
            return {letter}
    hits = {
        letter: opt
        for letter, opt in zip(valid, normalized, strict=True)
        if opt and _contains_phrase(reply, opt)
    }
    # If "राम" and "राम और श्याम" both match, keep only the longer option.
    return {
        letter
        for letter, opt in hits.items()
        if not any(opt != other and opt in other for other in hits.values())
    }


def parse_choice(text: str, options: Sequence[str]) -> str | None:
    """Return the chosen option letter (``"A"``, ``"B"``, ...) or ``None`` if unclear."""
    if not 2 <= len(options) <= len(LETTERS):
        raise ValueError(f"MCQ needs 2-{len(LETTERS)} options, got {len(options)}")
    valid = LETTERS[: len(options)]
    reply = clean_output(text)
    if not reply:
        return None

    for pattern in (_ANSWER, _OPTION):
        found = _letters(pattern, reply, valid)
        if found:
            return found.pop() if len(found) == 1 else None

    found = _letters(_WHOLE, reply, valid)
    if found:
        return found.pop()

    found = _letters(_BARE, reply, valid) | _letters_by_text(reply, options, valid)
    return found.pop() if len(found) == 1 else None
