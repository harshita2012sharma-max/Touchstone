import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from kasauti.errors import KasautiError
from kasauti.tasks import available_tasks, get_task
from kasauti.tasks.base import DatasetError, ItemMeta
from kasauti.tasks.instructions import CodemixedInstructions
from kasauti.tasks.mcq import HindiComprehension, MCQSample
from kasauti.tasks.numeric import HindiReasoning
from kasauti.tasks.translation import TranslationHiEn

META = {"author": "writer1", "license": "CC-BY-4.0", "reviewers": ["rev1", "rev2"]}

BUILTINS = {
    "hindi_comprehension",
    "hinglish_understanding",
    "translation_hi_en",
    "codemixed_instructions",
    "hindi_reasoning",
    "cultural_context",
}


def _write(path: Path, items: list[dict[str, Any]]) -> Path:
    path.write_text(
        "\n".join(json.dumps(i, ensure_ascii=False) for i in items) + "\n", encoding="utf-8"
    )
    return path


def _mcq(n: int, **extra: Any) -> dict[str, Any]:
    return {
        "id": f"hindi_comprehension-{n:03d}",
        **META,
        "passage": "सीता रोज़ सुबह बगीचे में पानी देती है।",
        "question": "सीता बगीचे में कब पानी देती है?",
        "options": ["सुबह", "दोपहर", "शाम", "रात"],
        "answer": "A",
        **extra,
    }


def test_builtin_tasks_registered() -> None:
    assert set(available_tasks()) >= BUILTINS


def test_unknown_task_lists_known() -> None:
    with pytest.raises(KasautiError, match="hindi_comprehension"):
        get_task("nope")


# --- review gate -------------------------------------------------------------


def test_item_needs_two_reviewers() -> None:
    with pytest.raises(ValidationError, match="2 reviewers"):
        ItemMeta(id="x-001", author="a", license="CC-BY-4.0", reviewers=["r1"])


def test_author_cannot_review_own_item() -> None:
    with pytest.raises(ValidationError, match="author"):
        ItemMeta(id="x-001", author="a", license="CC-BY-4.0", reviewers=["a", "r1"])


def test_duplicate_reviewers_rejected() -> None:
    with pytest.raises(ValidationError):
        ItemMeta(id="x-001", author="a", license="CC-BY-4.0", reviewers=["r1", "r1"])


def test_only_open_license_allowed() -> None:
    with pytest.raises(ValidationError):
        ItemMeta(id="x-001", author="a", license="CC-BY-NC-4.0", reviewers=["r1", "r2"])


# --- loading -----------------------------------------------------------------


def test_load_samples_with_limit(tmp_path: Path) -> None:
    path = _write(tmp_path / "d.jsonl", [_mcq(1), _mcq(2), _mcq(3)])
    samples = HindiComprehension(data_path=path).load_samples(limit=2)
    assert [s.id for s in samples] == ["hindi_comprehension-001", "hindi_comprehension-002"]


def test_load_reports_line_number(tmp_path: Path) -> None:
    bad = _mcq(2)
    del bad["question"]
    path = _write(tmp_path / "d.jsonl", [_mcq(1), bad])
    with pytest.raises(DatasetError, match="line 2"):
        HindiComprehension(data_path=path).load_samples()


def test_duplicate_ids_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path / "d.jsonl", [_mcq(1), _mcq(1)])
    with pytest.raises(DatasetError, match="duplicate"):
        HindiComprehension(data_path=path).load_samples()


def test_id_must_start_with_task_name(tmp_path: Path) -> None:
    path = _write(tmp_path / "d.jsonl", [_mcq(1, id="other_task-001")])
    with pytest.raises(DatasetError, match="hindi_comprehension-"):
        HindiComprehension(data_path=path).load_samples()


def test_missing_data_file_is_clear(tmp_path: Path) -> None:
    with pytest.raises(DatasetError, match="No data"):
        HindiComprehension(data_path=tmp_path / "missing.jsonl").load_samples()


# --- MCQ -----------------------------------------------------------------------


def test_mcq_answer_must_be_valid_letter() -> None:
    with pytest.raises(ValidationError):
        MCQSample(**_mcq(1, answer="E"))


def test_mcq_options_must_be_unique() -> None:
    with pytest.raises(ValidationError):
        MCQSample(**_mcq(1, options=["सुबह", "सुबह", "शाम"]))


def test_mcq_prompt_and_scoring() -> None:
    task = HindiComprehension()
    sample = MCQSample(**_mcq(1))
    prompt = task.build_prompt(sample)
    assert "Passage:\nसीता" in prompt
    assert "A. सुबह\nB. दोपहर" in prompt
    assert prompt.endswith("Reply with only the letter of the correct option (A, B, C or D).")

    right = task.score("उत्तर: (a)", sample)
    assert (right.score, right.parsed, right.unparsed) == (1.0, "A", False)
    wrong = task.score("B", sample)
    assert (wrong.score, wrong.unparsed) == (0.0, False)
    unclear = task.score("A or B", sample)
    assert (unclear.score, unclear.unparsed) == (0.0, True)
    assert task.expected(sample) == "A"


# --- numeric -------------------------------------------------------------------


def test_numeric_task(tmp_path: Path) -> None:
    item = {
        "id": "hindi_reasoning-001",
        **META,
        "question": "राम के पास 5 आम हैं। उसने 2 आम खा लिए। कितने बचे?",
        "answer": 3,
    }
    task = HindiReasoning(data_path=_write(tmp_path / "d.jsonl", [item]))
    sample = task.load_samples()[0]
    assert "Answer: <number>" in task.build_prompt(sample)
    assert task.score("5 - 2 = 3\nAnswer: 3", sample).score == 1.0
    assert task.score("Answer: 4", sample).score == 0.0
    assert task.score("पता नहीं", sample).unparsed
    assert task.expected(sample) == "3"


# --- translation ---------------------------------------------------------------


def test_translation_task(tmp_path: Path) -> None:
    item = {
        "id": "translation_hi_en-001",
        **META,
        "source": "मैं हर दिन स्कूल जाता हूँ।",
        "references": ["I go to school every day."],
    }
    task = TranslationHiEn(data_path=_write(tmp_path / "d.jsonl", [item]))
    sample = task.load_samples()[0]
    assert "Hindi: मैं हर दिन स्कूल जाता हूँ।" in task.build_prompt(sample)
    assert task.score("English: I go to school every day.", sample).score == pytest.approx(1.0)
    empty = task.score("   ", sample)
    assert (empty.score, empty.unparsed) == (0.0, True)
    assert task.expected(sample) == ["I go to school every day."]


# --- instructions --------------------------------------------------------------


def test_instruction_task(tmp_path: Path) -> None:
    item = {
        "id": "codemixed_instructions-001",
        **META,
        "instruction": (
            "Teen Indian sweets ke naam batao, comma se alag karke, sirf Roman script mein."
        ),
        "checks": [
            {"type": "item_count", "n": 3, "separator": "comma"},
            {"type": "script", "script": "latin"},
        ],
    }
    task = CodemixedInstructions(data_path=_write(tmp_path / "d.jsonl", [item]))
    sample = task.load_samples()[0]
    assert task.build_prompt(sample) == item["instruction"]
    ok = task.score("Gulab jamun, Jalebi, Rasgulla", sample)
    assert (ok.score, ok.parsed) == (1.0, "2/2 checks passed")
    bad = task.score("गुलाब जामुन, जलेबी", sample)
    assert bad.score == 0.0
    assert bad.parsed == "0/2 checks passed (failed: item_count, script)"


def test_every_task_exposes_versioned_template() -> None:
    for name in BUILTINS:
        task = get_task(name)
        assert task.version
        assert task.prompt_template
        assert task.description
