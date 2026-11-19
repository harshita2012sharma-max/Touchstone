import pytest

from kasauti.scoring.mcq import parse_choice

OPTIONS = ["दिल्ली", "मुंबई", "चेन्नई", "कोलकाता"]


@pytest.mark.parametrize(
    "text",
    [
        "B",
        "b",
        "B.",
        "B)",
        "(b)",
        "[B]",
        "Option B",
        "option: b",
        "Answer: B",
        "Ans - B",
        "**B**",
        "उत्तर: B",
        "विकल्प B",
        "सही उत्तर B है",
        "The answer is (B).",
        "  B  \n",
        "B) मुंबई",
        "Answer: **B**",
        "मुंबई",
        "सही जवाब मुंबई है।",
        "<think>maybe A or C</think>Answer: B",
        "Ans " + chr(0x2013) + " B",  # en dash
    ],
)
def test_parses_common_formats_as_b(text: str) -> None:
    assert parse_choice(text, OPTIONS) == "B"


@pytest.mark.parametrize(
    "text",
    [
        "",
        "I am not sure.",
        "A or B",
        "Answer: A. Actually answer: C",
        "E",  # only four options
        "मुंबई या चेन्नई",
    ],
)
def test_ambiguous_or_missing_is_none(text: str) -> None:
    assert parse_choice(text, OPTIONS) is None


def test_explicit_answer_marker_beats_other_letters() -> None:
    text = "Option A is wrong because of X. Answer: D"
    assert parse_choice(text, OPTIONS) == "D"


def test_lowercase_article_a_is_not_a_choice() -> None:
    assert parse_choice("it is a big city in the east, so C", OPTIONS) == "C"


def test_devanagari_danda_and_markdown() -> None:
    assert parse_choice("उत्तर: (c)।", OPTIONS) == "C"


def test_option_text_prefers_exact_over_substring() -> None:
    options = ["राम", "राम और श्याम", "श्याम", "कोई नहीं"]
    assert parse_choice("राम और श्याम", options) == "B"


def test_letter_range_follows_option_count() -> None:
    assert parse_choice("C", ["हाँ", "नहीं"]) is None
    assert parse_choice("B", ["हाँ", "नहीं"]) == "B"
