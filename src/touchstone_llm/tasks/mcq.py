"""Multiple-choice tasks: Hindi comprehension, Hinglish understanding, cultural context."""

from __future__ import annotations

from pydantic import Field, model_validator

from touchstone_llm.scoring.mcq import LETTERS, parse_choice
from touchstone_llm.scoring.normalize import normalize_text
from touchstone_llm.tasks.base import ItemMeta, ScoredOutput, Task

MCQ_TEMPLATE = (
    "{context}Question: {question}\n\n{options}\n\n"
    "Reply with only the letter of the correct option ({letters})."
)


class MCQSample(ItemMeta):
    """A question with 2-8 options and one correct letter."""

    passage: str | None = None
    question: str = Field(min_length=1)
    options: list[str] = Field(min_length=2, max_length=len(LETTERS))
    answer: str = Field(pattern=r"^[A-H]$")

    @model_validator(mode="after")
    def _check_options(self) -> MCQSample:
        normalized = [normalize_text(o) for o in self.options]
        if len(set(normalized)) != len(normalized) or not all(normalized):
            raise ValueError("options must be non-empty and distinct")
        if self.answer not in LETTERS[: len(self.options)]:
            raise ValueError(f"answer {self.answer!r} is not one of the option letters")
        return self


def _letters_phrase(n: int) -> str:
    letters = list(LETTERS[:n])
    return ", ".join(letters[:-1]) + f" or {letters[-1]}"


class MCQTask(Task[MCQSample]):
    """Shared prompt and scoring for all multiple-choice tasks."""

    version = "1"
    sample_type = MCQSample
    prompt_template = MCQ_TEMPLATE

    def build_prompt(self, sample: MCQSample) -> str:
        """Format passage (if any), question and lettered options."""
        context = f"Passage:\n{sample.passage}\n\n" if sample.passage else ""
        options = "\n".join(f"{LETTERS[i]}. {opt}" for i, opt in enumerate(sample.options))
        return self.prompt_template.format(
            context=context,
            question=sample.question,
            options=options,
            letters=_letters_phrase(len(sample.options)),
        )

    def score(self, output: str, sample: MCQSample) -> ScoredOutput:
        """1.0 if the parsed letter is correct; unparsed if no single letter is found."""
        letter = parse_choice(output, sample.options)
        return ScoredOutput(
            score=1.0 if letter == sample.answer else 0.0,
            parsed=letter,
            unparsed=letter is None,
        )

    def expected(self, sample: MCQSample) -> str:
        """Return the correct letter."""
        return sample.answer


class HindiComprehension(MCQTask):
    """Read a short Hindi passage and answer a question about it."""

    name = "hindi_comprehension"
    description = "Read a short Hindi passage and answer a multiple-choice question."


class HinglishUnderstanding(MCQTask):
    """Understand Roman-script Hindi-English code-mixed text."""

    name = "hinglish_understanding"
    description = "Understand Roman-script Hinglish (code-mixed) text; multiple choice."


class CulturalContext(MCQTask):
    """Neutral, factual questions about Indian everyday culture."""

    name = "cultural_context"
    description = (
        "Neutral, factual questions on Indian festivals, food, geography and institutions; "
        "multiple choice."
    )


class HindiGrammar(MCQTask):
    """Choose the grammatically correct Hindi form or sentence."""

    name = "hindi_grammar"
    description = (
        "Hindi grammar: gender and number agreement, ने/को and other case markers, "
        "verb forms and correct sentences; multiple choice."
    )


class IdiomsProverbs(MCQTask):
    """Understand Hindi idioms (मुहावरे) and proverbs (लोकोक्तियाँ) in context."""

    name = "idioms_proverbs"
    description = "Meaning of Hindi idioms and proverbs used in context; multiple choice."


class HindiLogic(MCQTask):
    """Logic puzzles written in Hindi."""

    name = "hindi_logic"
    description = (
        "Logic puzzles in Hindi: family relations, seating and order, calendars, "
        "directions and syllogisms; multiple choice."
    )
