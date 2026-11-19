import pytest
from pydantic import TypeAdapter

from touchstone_llm.scoring.rules import Check, run_checks

CHECKS = TypeAdapter(list[Check])


def _checks(raw: list[dict]) -> list[Check]:
    return CHECKS.validate_python(raw)


def test_item_count_comma() -> None:
    checks = _checks([{"type": "item_count", "n": 3, "separator": "comma"}])
    assert run_checks("aam, kela, seb", checks).passed
    assert not run_checks("aam, kela", checks).passed


def test_item_count_lines_ignores_bullets_and_blanks() -> None:
    checks = _checks([{"type": "item_count", "n": 2, "separator": "line"}])
    assert run_checks("- chai\n\n- samosa\n", checks).passed


def test_word_limits() -> None:
    checks = _checks([{"type": "max_words", "n": 3}, {"type": "min_words", "n": 2}])
    assert run_checks("kal milte hain", checks).passed
    assert not run_checks("haan", checks).passed
    assert not run_checks("kal shaam ko milte hain", checks).passed


def test_contains_all_and_none_case_insensitive() -> None:
    checks = _checks(
        [
            {"type": "contains_all", "terms": ["Chai", "samosa"]},
            {"type": "contains_none", "terms": ["coffee"]},
        ]
    )
    assert run_checks("chai aur SAMOSA", checks).passed
    assert not run_checks("chai aur coffee aur samosa", checks).passed


def test_contains_any() -> None:
    checks = _checks([{"type": "contains_any", "terms": ["meet", "see you"]}])
    assert run_checks("See you later!", checks).passed
    assert run_checks("We will MEET again", checks).passed
    assert not run_checks("I don't know.", checks).passed


@pytest.mark.parametrize(
    "script,text,ok",
    [
        ("latin", "Main ghar ja raha hoon", True),
        ("latin", "मैं घर जा रहा हूँ", False),
        ("devanagari", "मैं घर जा रहा हूँ", True),
        ("devanagari", "मैं ghar जा रहा", False),
    ],
)
def test_script(script: str, text: str, ok: bool) -> None:
    assert run_checks(text, _checks([{"type": "script", "script": script}])).passed is ok


def test_starts_and_ends_with() -> None:
    checks = _checks(
        [{"type": "starts_with", "text": "Namaste"}, {"type": "ends_with", "text": "!"}]
    )
    assert run_checks("  namaste dosto!  ", checks).passed


def test_result_reports_which_checks_failed() -> None:
    checks = _checks([{"type": "max_words", "n": 1}, {"type": "contains_all", "terms": ["x"]}])
    result = run_checks("a b", checks)
    assert not result.passed
    assert result.summary == "0/2 checks passed (failed: max_words, contains_all)"


def test_unknown_check_type_rejected() -> None:
    with pytest.raises(ValueError):
        _checks([{"type": "vibes"}])
