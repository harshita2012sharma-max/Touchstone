"""Hindi to English translation, scored with chrF against reference translations."""

from __future__ import annotations

import re

from pydantic import Field

from kasauti.scoring.chrf import chrf
from kasauti.scoring.normalize import clean_output
from kasauti.tasks.base import ItemMeta, ScoredOutput, Task

TRANSLATION_TEMPLATE = (
    "Translate the following Hindi text into English. "
    "Reply with only the English translation.\n\n"
    "Hindi: {source}\nEnglish:"
)

_LABEL = re.compile(r"^\s*(?:english\s*(?:translation)?\s*:)\s*", re.IGNORECASE)


class TranslationSample(ItemMeta):
    """A Hindi sentence and one or more acceptable English translations."""

    source: str = Field(min_length=1)
    references: list[str] = Field(min_length=1)


class TranslationHiEn(Task[TranslationSample]):
    """Translate Hindi sentences into English."""

    name = "translation_hi_en"
    version = "1"
    description = "Translate Hindi into English; chrF against reference translations (rough)."
    sample_type = TranslationSample
    prompt_template = TRANSLATION_TEMPLATE

    def build_prompt(self, sample: TranslationSample) -> str:
        """Insert the Hindi source into the template."""
        return self.prompt_template.format(source=sample.source)

    def score(self, output: str, sample: TranslationSample) -> ScoredOutput:
        """Return chrF (0-1) of the reply, after removing a leading "English:" label."""
        reply = _LABEL.sub("", clean_output(output)).strip()
        if not reply:
            return ScoredOutput(score=0.0, unparsed=True)
        return ScoredOutput(score=chrf(reply, sample.references))

    def expected(self, sample: TranslationSample) -> list[str]:
        """Return the reference translations."""
        return sample.references
