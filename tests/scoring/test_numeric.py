import pytest

from touchstone_llm.scoring.numeric import numbers_match, parse_number


@pytest.mark.parametrize(
    "text,expected",
    [
        ("42", 42.0),
        ("उत्तर: ४२", 42.0),
        ("कुल 1,00,000 रुपये", 100000.0),
        ("Answer: 3.5", 3.5),
        ("-7", -7.0),
        ("पहले 10 थे, 3 गए, तो उत्तर 7 है", 7.0),
        ("10 - 3 = 7", 7.0),
        ("Answer: 12 apples (since 4 x 3 = 12)", 12.0),
        ("**उत्तर:** 15", 15.0),
    ],
)
def test_parse_number(text: str, expected: float) -> None:
    assert parse_number(text) == pytest.approx(expected)


@pytest.mark.parametrize("text", ["", "पता नहीं", "<think>5</think>"])
def test_parse_number_none(text: str) -> None:
    assert parse_number(text) is None


def test_numbers_match_tolerance() -> None:
    assert numbers_match(0.1 + 0.2, 0.3)
    assert not numbers_match(7.0, 7.01)
