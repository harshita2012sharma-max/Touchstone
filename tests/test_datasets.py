"""Checks on the real dataset files (shipped and pending)."""

from pathlib import Path

import pytest

from kasauti.review import check_pending
from kasauti.scoring.mcq import LETTERS
from kasauti.tasks import available_tasks, get_task
from kasauti.tasks.base import DatasetError
from kasauti.tasks.mcq import MCQSample, MCQTask

PENDING = Path(__file__).resolve().parents[1] / "datasets" / "pending"


def _shipped(name: str) -> list:
    try:
        return get_task(name).load_samples()
    except DatasetError as err:
        if "No data found" in str(err):
            return []
        raise


@pytest.mark.parametrize("name", available_tasks())
def test_shipped_data_is_valid_and_reviewed(name: str) -> None:
    # load_samples enforces license, two independent reviewers and unique ids
    for sample in _shipped(name):
        assert len(sample.reviewers) >= 2


def test_pending_items_are_valid() -> None:
    if PENDING.is_dir():
        check_pending(PENDING)


@pytest.mark.parametrize("name", [n for n in available_tasks() if isinstance(get_task(n), MCQTask)])
def test_mcq_options_resolve_unambiguously(name: str) -> None:
    task = get_task(name)
    for sample in _shipped(name):
        assert isinstance(sample, MCQSample)
        for letter, option in zip(LETTERS, sample.options, strict=False):
            assert task.score(option, sample).parsed == letter, (sample.id, option)
