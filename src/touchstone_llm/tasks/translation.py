"""Translation tasks, scored with chrF against reference translations.

- ``translation_hi_en``: Hindi to English.
- ``translation_en_hi``: English to Hindi (Devanagari).
- ``hinglish_to_hindi``: rewrite Roman-script Hinglish as standard Hindi in Devanagari.
"""

from __future__ import annotations

import re

from pydantic import Field

from touchstone_llm.scoring.chrf import chrf
from touchstone_llm.scoring.normalize import clean_output
from touchstone_llm.tasks.base import ItemMeta, ScoredOutput, Task

TRANSLATION_TEMPLATE = (
    "Translate the following Hindi text into English. "
    "Reply with only the English translation.\n\n"
    "Hindi: {source}\nEnglish:"
)

_LABEL = re.compile(
    r"^\s*(?:(?:english|hindi)\s*(?:translation)?\s*:|हिंदी\s*:|हिन्दी\s*:)\s*", re.IGNORECASE
)


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


EN_HI_TEMPLATE = (
    "Translate the following English text into Hindi, written in Devanagari script. "
    "Reply with only the Hindi translation.\n\n"
    "English: {source}\nHindi:"
)

HINGLISH_HI_TEMPLATE = (
    "The following text is Hinglish written in Roman script. Rewrite it as natural, "
    "standard Hindi in Devanagari script, keeping the meaning. Use Hindi words in place "
    "of English ones where a common Hindi word exists. Reply with only the Hindi text.\n\n"
    "Hinglish: {source}\nHindi:"
)


class TranslationEnHi(TranslationHiEn):
    """Translate English sentences into Hindi."""

    name = "translation_en_hi"
    description = "Translate English into Hindi (Devanagari); chrF against references (rough)."
    prompt_template = EN_HI_TEMPLATE


class HinglishToHindi(TranslationHiEn):
    """Rewrite Roman-script Hinglish as standard Devanagari Hindi."""

    name = "hinglish_to_hindi"
    description = (
        "Rewrite Roman-script Hinglish as standard Hindi in Devanagari; chrF against references."
    )
    prompt_template = HINGLISH_HI_TEMPLATE
