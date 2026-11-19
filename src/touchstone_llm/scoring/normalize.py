"""Text clean-up shared by all scorers (works for Devanagari and Roman script)."""

from __future__ import annotations

import re
import unicodedata

DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

_THINK_BLOCK = re.compile(r"<think>.*?(?:</think>|$)", re.DOTALL | re.IGNORECASE)
_MARKDOWN = re.compile(r"[*_`#]+")
_SPACES = re.compile(r"\s+")


def strip_thinking(text: str) -> str:
    """Remove ``<think>…</think>`` reasoning blocks that some models print first."""
    return _THINK_BLOCK.sub(" ", text)


def clean_output(text: str) -> str:
    """NFC-normalise, drop thinking blocks and markdown marks, convert Devanagari digits."""
    text = unicodedata.normalize("NFC", text)
    text = strip_thinking(text)
    text = _MARKDOWN.sub("", text)
    return text.translate(DEVANAGARI_DIGITS).strip()


def is_word_char(ch: str) -> bool:
    """Return True for letters, combining marks (e.g. Devanagari vowel signs) and digits."""
    return unicodedata.category(ch)[0] in "LMN"


def normalize_text(text: str) -> str:
    """Lower-case, remove punctuation (including ``।``) and collapse spaces, for comparisons."""
    text = clean_output(text).casefold()
    text = "".join(" " if unicodedata.category(ch).startswith("P") else ch for ch in text)
    return _SPACES.sub(" ", text).strip()
