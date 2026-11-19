"""Hindi reasoning: word problems with a single numeric answer."""

from __future__ import annotations

from pydantic import Field

from touchstone_llm.scoring.numeric import numbers_match, parse_number
from touchstone_llm.tasks.base import ItemMeta, ScoredOutput, Task

NUMERIC_TEMPLATE = (
    "{question}\n\n"
    "Solve step by step if needed, then give the final answer on the last line as: "
    "Answer: <number>"
)


class NumericSample(ItemMeta):
    """A word problem and its numeric answer."""

    question: str = Field(min_length=1)
    answer: float


def _format_number(value: float) -> str:
    return str(int(value)) if value.is_integer() else str(value)


class HindiReasoning(Task[NumericSample]):
    """Arithmetic and logic word problems written in Hindi."""

    name = "hindi_reasoning"
    version = "1"
    description = "Arithmetic and logic word problems in Hindi; numeric exact match."
    sample_type = NumericSample
    prompt_template = NUMERIC_TEMPLATE

    def build_prompt(self, sample: NumericSample) -> str:
        """Insert the question into the template."""
        return self.prompt_template.format(question=sample.question)

    def score(self, output: str, sample: NumericSample) -> ScoredOutput:
        """1.0 if the extracted number equals the answer."""
        got = parse_number(output)
        return ScoredOutput(
            score=1.0 if got is not None and numbers_match(got, sample.answer) else 0.0,
            parsed=None if got is None else _format_number(got),
            unparsed=got is None,
        )

    def expected(self, sample: NumericSample) -> str:
        """Return the answer as text."""
        return _format_number(sample.answer)
