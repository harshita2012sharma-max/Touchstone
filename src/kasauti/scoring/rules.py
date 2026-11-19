"""Rule checks for instruction-following items.

Each dataset item lists checks such as "exactly 3 comma-separated items" or
"written in Roman script". An answer passes only if every check passes
(strict, like IFEval's strict accuracy); the summary records which failed.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from kasauti.scoring.normalize import clean_output

_BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s*")
SCRIPT_SHARE = 0.95
"""Share of letters that must be in the required script."""


class ItemCount(BaseModel):
    """Exactly ``n`` items, separated by commas or one per line."""

    type: Literal["item_count"]
    n: int = Field(ge=1)
    separator: Literal["comma", "line"]

    def check(self, text: str) -> bool:
        """Count non-empty items (bullets and numbering ignored for lines)."""
        if self.separator == "comma":
            items = [p.strip() for p in text.split(",")]
        else:
            items = [_BULLET.sub("", line).strip() for line in text.splitlines()]
        return len([i for i in items if i]) == self.n


class MaxWords(BaseModel):
    """At most ``n`` whitespace-separated words."""

    type: Literal["max_words"]
    n: int = Field(ge=1)

    def check(self, text: str) -> bool:
        """Compare the word count with the limit."""
        return len(text.split()) <= self.n


class MinWords(BaseModel):
    """At least ``n`` whitespace-separated words."""

    type: Literal["min_words"]
    n: int = Field(ge=1)

    def check(self, text: str) -> bool:
        """Compare the word count with the limit."""
        return len(text.split()) >= self.n


class ContainsAll(BaseModel):
    """Every term appears (case-insensitive)."""

    type: Literal["contains_all"]
    terms: list[str] = Field(min_length=1)

    def check(self, text: str) -> bool:
        """Case-insensitive substring test for each term."""
        lowered = text.casefold()
        return all(t.casefold() in lowered for t in self.terms)


class ContainsAny(BaseModel):
    """At least one of the terms appears (case-insensitive)."""

    type: Literal["contains_any"]
    terms: list[str] = Field(min_length=1)

    def check(self, text: str) -> bool:
        """Case-insensitive substring test; one hit is enough."""
        lowered = text.casefold()
        return any(t.casefold() in lowered for t in self.terms)


class ContainsNone(BaseModel):
    """No term appears (case-insensitive)."""

    type: Literal["contains_none"]
    terms: list[str] = Field(min_length=1)

    def check(self, text: str) -> bool:
        """Case-insensitive substring test for each term."""
        lowered = text.casefold()
        return not any(t.casefold() in lowered for t in self.terms)


class Script(BaseModel):
    """Nearly all letters are Latin (Roman Hinglish) or Devanagari."""

    type: Literal["script"]
    script: Literal["latin", "devanagari"]

    def check(self, text: str) -> bool:
        """At least ``SCRIPT_SHARE`` of Latin+Devanagari letters are in the required script."""
        latin = devanagari = 0
        for ch in text:
            if unicodedata.category(ch)[0] not in "LM":
                continue
            name = unicodedata.name(ch, "")
            if name.startswith("LATIN"):
                latin += 1
            elif name.startswith("DEVANAGARI"):
                devanagari += 1
        total = latin + devanagari
        wanted = latin if self.script == "latin" else devanagari
        return total > 0 and wanted / total >= SCRIPT_SHARE


class StartsWith(BaseModel):
    """Reply begins with ``text`` (case-insensitive)."""

    type: Literal["starts_with"]
    text: str = Field(min_length=1)

    def check(self, text: str) -> bool:
        """Case-insensitive prefix test."""
        return text.casefold().startswith(self.text.casefold())


class EndsWith(BaseModel):
    """Reply ends with ``text`` (case-insensitive)."""

    type: Literal["ends_with"]
    text: str = Field(min_length=1)

    def check(self, text: str) -> bool:
        """Case-insensitive suffix test."""
        return text.casefold().endswith(self.text.casefold())


Check = Annotated[
    ItemCount
    | MaxWords
    | MinWords
    | ContainsAll
    | ContainsAny
    | ContainsNone
    | Script
    | StartsWith
    | EndsWith,
    Field(discriminator="type"),
]


class CheckResult(BaseModel):
    """Outcome of all checks for one reply."""

    total: int
    failed: list[str]

    @property
    def passed(self) -> bool:
        """True when no check failed."""
        return not self.failed

    @property
    def summary(self) -> str:
        """Human-readable result, e.g. ``"1/2 checks passed (failed: max_words)"``."""
        text = f"{self.total - len(self.failed)}/{self.total} checks passed"
        return f"{text} (failed: {', '.join(self.failed)})" if self.failed else text


def run_checks(text: str, checks: list[Check]) -> CheckResult:
    """Run every check on the cleaned reply."""
    reply = clean_output(text)
    return CheckResult(total=len(checks), failed=[c.type for c in checks if not c.check(reply)])
