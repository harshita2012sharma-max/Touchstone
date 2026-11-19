"""Code-mixed instruction following, scored with rule checks."""

from __future__ import annotations

from pydantic import Field

from touchstone_llm.scoring.rules import Check, run_checks
from touchstone_llm.tasks.base import ItemMeta, ScoredOutput, Task


class InstructionSample(ItemMeta):
    """A Hinglish instruction and the checks a correct reply must pass."""

    instruction: str = Field(min_length=1)
    checks: list[Check] = Field(min_length=1)


class CodemixedInstructions(Task[InstructionSample]):
    """Follow Hinglish instructions with checkable output formats."""

    name = "codemixed_instructions"
    version = "1"
    description = "Follow Hinglish instructions; strict rule checks (all must pass)."
    sample_type = InstructionSample
    prompt_template = "{instruction}"

    def build_prompt(self, sample: InstructionSample) -> str:
        """Return the instruction itself as the prompt."""
        return self.prompt_template.format(instruction=sample.instruction)

    def score(self, output: str, sample: InstructionSample) -> ScoredOutput:
        """1.0 only if every check passes; ``parsed`` records the check summary."""
        result = run_checks(output, sample.checks)
        return ScoredOutput(score=1.0 if result.passed else 0.0, parsed=result.summary)

    def expected(self, sample: InstructionSample) -> str:
        """Describe the checks, for reports."""
        return ", ".join(c.type for c in sample.checks)
