import csv
import json
from pathlib import Path
from typing import Any

import pytest

from touchstone_llm.review import check_pending, export_csv, import_csv, promote
from touchstone_llm.tasks.base import DatasetError


def _item(n: int, **extra: Any) -> dict[str, Any]:
    return {
        "id": f"hindi_reasoning-{n:03d}",
        "author": "writer",
        "license": "CC-BY-4.0",
        "reviewers": [],
        "question": f"{n} + 1 कितना होता है?",
        "answer": n + 1,
        **extra,
    }


def _write_jsonl(path: Path, items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items), "utf-8")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]


@pytest.fixture
def dirs(tmp_path: Path) -> tuple[Path, Path]:
    pending, shipped = tmp_path / "pending", tmp_path / "shipped"
    _write_jsonl(pending / "hindi_reasoning.jsonl", [_item(1), _item(2)])
    return pending, shipped


def test_check_pending_counts_items(dirs: tuple[Path, Path]) -> None:
    assert check_pending(dirs[0]) == {"hindi_reasoning": 2}


def test_check_pending_reports_bad_item(dirs: tuple[Path, Path]) -> None:
    _write_jsonl(dirs[0] / "hindi_reasoning.jsonl", [_item(1, answer="not a number")])
    with pytest.raises(DatasetError, match="hindi_reasoning-001"):
        check_pending(dirs[0])


def test_check_pending_rejects_unknown_task_file(dirs: tuple[Path, Path]) -> None:
    _write_jsonl(dirs[0] / "nope.jsonl", [_item(1)])
    with pytest.raises(DatasetError, match="nope"):
        check_pending(dirs[0])


def test_export_csv_has_prompt_and_expected(dirs: tuple[Path, Path], tmp_path: Path) -> None:
    out = tmp_path / "review.csv"
    assert export_csv(dirs[0], out) == 2
    raw = out.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")  # BOM so Excel shows Hindi correctly
    rows = list(csv.DictReader(out.open(encoding="utf-8-sig")))
    assert rows[0]["id"] == "hindi_reasoning-001"
    assert "1 + 1 कितना होता है?" in rows[0]["prompt"]
    assert rows[0]["expected"] == "2"
    assert rows[0]["verdict"] == ""


def _fill(path: Path, verdicts: dict[str, tuple[str, str]]) -> None:
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    for row in rows:
        row["verdict"], row["comment"] = verdicts.get(row["id"], ("", ""))
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_import_records_approvals_and_feedback(dirs: tuple[Path, Path], tmp_path: Path) -> None:
    sheet = tmp_path / "r.csv"
    export_csv(dirs[0], sheet)
    _fill(sheet, {"hindi_reasoning-001": ("OK", ""), "hindi_reasoning-002": ("fix", "typo")})
    summary = import_csv(dirs[0], sheet, reviewer="rev1")
    assert summary.approved == ["hindi_reasoning-001"]
    assert summary.feedback == [("hindi_reasoning-002", "fix", "typo")]
    items = _read_jsonl(dirs[0] / "hindi_reasoning.jsonl")
    assert items[0]["reviewers"] == ["rev1"]
    assert items[1]["reviewers"] == []


def test_import_is_idempotent_and_blocks_self_review(
    dirs: tuple[Path, Path], tmp_path: Path
) -> None:
    sheet = tmp_path / "r.csv"
    export_csv(dirs[0], sheet)
    _fill(sheet, {"hindi_reasoning-001": ("ok", "")})
    import_csv(dirs[0], sheet, reviewer="rev1")
    import_csv(dirs[0], sheet, reviewer="rev1")
    assert _read_jsonl(dirs[0] / "hindi_reasoning.jsonl")[0]["reviewers"] == ["rev1"]
    with pytest.raises(DatasetError, match="author"):
        import_csv(dirs[0], sheet, reviewer="writer")


def test_import_rejects_unknown_verdict(dirs: tuple[Path, Path], tmp_path: Path) -> None:
    sheet = tmp_path / "r.csv"
    export_csv(dirs[0], sheet)
    _fill(sheet, {"hindi_reasoning-001": ("maybe", "")})
    with pytest.raises(DatasetError, match="maybe"):
        import_csv(dirs[0], sheet, reviewer="rev1")


def test_promote_moves_only_fully_reviewed(dirs: tuple[Path, Path]) -> None:
    pending, shipped = dirs
    _write_jsonl(
        pending / "hindi_reasoning.jsonl",
        [_item(1, reviewers=["rev1", "rev2"]), _item(2, reviewers=["rev1"])],
    )
    assert promote(pending, shipped) == {"hindi_reasoning": 1}
    assert [i["id"] for i in _read_jsonl(shipped / "hindi_reasoning.jsonl")] == [
        "hindi_reasoning-001"
    ]
    assert [i["id"] for i in _read_jsonl(pending / "hindi_reasoning.jsonl")] == [
        "hindi_reasoning-002"
    ]


def test_promote_refuses_duplicate_ids(dirs: tuple[Path, Path]) -> None:
    pending, shipped = dirs
    _write_jsonl(shipped / "hindi_reasoning.jsonl", [_item(1, reviewers=["a", "b"])])
    _write_jsonl(pending / "hindi_reasoning.jsonl", [_item(1, reviewers=["rev1", "rev2"])])
    with pytest.raises(DatasetError, match="already shipped"):
        promote(pending, shipped)
