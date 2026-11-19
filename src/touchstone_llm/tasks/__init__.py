"""Task registry.

Built-in tasks are listed below. Third-party packages can add tasks through
the ``touchstone_llm.tasks`` entry point group; each entry point must load a
:class:`~touchstone_llm.tasks.base.Task` subclass.
"""

from __future__ import annotations

from importlib.metadata import entry_points
from typing import Any

from touchstone_llm.errors import TouchstoneError
from touchstone_llm.tasks.base import Task
from touchstone_llm.tasks.instructions import CodemixedInstructions
from touchstone_llm.tasks.mcq import CulturalContext, HindiComprehension, HinglishUnderstanding
from touchstone_llm.tasks.numeric import HindiReasoning
from touchstone_llm.tasks.translation import TranslationHiEn

__all__ = ["Task", "available_tasks", "get_task"]

_BUILTINS: dict[str, type[Task[Any]]] = {
    cls.name: cls
    for cls in (
        HindiComprehension,
        HinglishUnderstanding,
        TranslationHiEn,
        CodemixedInstructions,
        HindiReasoning,
        CulturalContext,
    )
}


def _plugins() -> dict[str, type[Task[Any]]]:
    return {
        ep.name: ep.load()
        for ep in entry_points(group="touchstone_llm.tasks")
        if ep.name not in _BUILTINS
    }


def available_tasks() -> list[str]:
    """Names of built-in tasks (in their standard order) followed by plugin tasks."""
    plugins = sorted(ep.name for ep in entry_points(group="touchstone_llm.tasks"))
    return list(_BUILTINS) + [p for p in plugins if p not in _BUILTINS]


def get_task(name: str, **kwargs: Any) -> Task[Any]:
    """Create the task called ``name``.

    Raises:
        TouchstoneError: unknown task (the message lists known ones).

    """
    cls = _BUILTINS.get(name) or _plugins().get(name)
    if cls is None:
        raise TouchstoneError(
            f"Unknown task '{name}'. Available tasks: {', '.join(available_tasks())}."
        )
    return cls(**kwargs)
