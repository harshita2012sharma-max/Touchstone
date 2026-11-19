"""Sentence-level chrF (character n-gram F-score), dependency-free.

Matches sacreBLEU 2.x ``CHRF()`` defaults: character n-grams of order 1-6,
whitespace removed, beta = 2, no word n-grams. Precision and recall are
averaged over the orders that exist in both texts, then combined into
F-beta. With several references, the best-scoring one is used.
Equality with sacreBLEU is checked in ``tests/scoring/test_chrf.py``.

Reference: Popović (2015), "chrF: character n-gram F-score for automatic
MT evaluation", WMT.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

CHAR_ORDER = 6
BETA = 2.0


def _char_ngrams(text: str, order: int) -> list[Counter[str]]:
    text = "".join(text.split())
    return [Counter(text[i : i + n] for i in range(len(text) - n + 1)) for n in range(1, order + 1)]


def _f_score(hyp: list[Counter[str]], ref: list[Counter[str]]) -> float:
    factor = BETA**2
    avg_prec = avg_rec = 0.0
    effective = 0
    for h, r in zip(hyp, ref, strict=True):
        n_hyp = sum(h.values()) if r else 0
        n_ref = sum(r.values())
        if n_hyp == 0 or n_ref == 0:
            continue
        n_match = sum(min(count, r[gram]) for gram, count in h.items() if gram in r)
        avg_prec += n_match / n_hyp
        avg_rec += n_match / n_ref
        effective += 1
    if effective == 0:
        return 0.0
    avg_prec /= effective
    avg_rec /= effective
    if avg_prec + avg_rec == 0:
        return 0.0
    return (1 + factor) * avg_prec * avg_rec / (factor * avg_prec + avg_rec)


def chrf(hypothesis: str, references: Sequence[str]) -> float:
    """Return chrF between 0 and 1 against the best of ``references``."""
    if not references:
        raise ValueError("chrf needs at least one reference")
    hyp = _char_ngrams(hypothesis, CHAR_ORDER)
    return max(_f_score(hyp, _char_ngrams(ref, CHAR_ORDER)) for ref in references)
