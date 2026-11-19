from pathlib import Path

from touchstone_llm.drafts import default_drafts_dir
from touchstone_llm.tasks import available_tasks


def test_drafts_found_in_source_checkout() -> None:
    drafts = default_drafts_dir()
    assert drafts is not None
    names = {p.stem for p in Path(drafts).glob("*.jsonl")}
    assert set(available_tasks()) <= names
