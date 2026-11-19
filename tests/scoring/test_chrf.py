import pytest
from sacrebleu.metrics import CHRF

from kasauti.scoring.chrf import chrf

CASES = [
    ("The cat sat on the mat.", ["The cat sat on the mat."]),
    ("The cat is on the mat.", ["The cat sat on the mat."]),
    ("A dog ran.", ["The cat sat on the mat."]),
    ("He goes to school every day.", ["He goes to school daily.", "Every day he goes to school."]),
    ("", ["Something."]),
    ("नमस्ते दुनिया", ["नमस्ते, दुनिया!"]),
    ("ok", ["ok"]),
]


@pytest.mark.parametrize("hyp,refs", CASES)
def test_matches_sacrebleu_sentence_chrf(hyp: str, refs: list[str]) -> None:
    expected = CHRF().sentence_score(hyp, refs).score / 100
    assert chrf(hyp, refs) == pytest.approx(expected, abs=1e-9)


def test_identical_is_one_and_range() -> None:
    assert chrf("same text", ["same text"]) == pytest.approx(1.0)
    assert 0.0 <= chrf("abc", ["xyz"]) <= 1.0


def test_requires_reference() -> None:
    with pytest.raises(ValueError):
        chrf("x", [])
