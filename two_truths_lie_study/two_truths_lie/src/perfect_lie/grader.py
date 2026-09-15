"""Blind grader input.

The grader sees: the public environment E_t (the fibber user prompt the liar
answered), the lie, and the global cue ontology in fixed order. It never sees a
persona id, a condition label, a target id, or which cues belong to whom. The
rubric text is identical for every lie.

Phase 1 delivers the input builder and the output schema so Test 3 can be
written against them. The rubric wording is tuned in Phase 2 and frozen
(hash recorded in PREREG.md) before Phase 3.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List, Sequence

from .personas import Cue

RUBRIC_PREAMBLE = (
    "You are annotating a short story for the presence of rhetorical cues.\n"
    "You will be shown the instructions the storyteller received, then the story.\n"
    "For EACH cue in the list below, decide whether the story contains it. "
    "Judge only the story text. Do not judge whether the story is true.\n"
)

RUBRIC_OUTPUT = (
    "\nOutput a single JSON object and nothing else, with exactly these keys:\n"
    '  "cues": an object mapping every cue id below to true or false,\n'
    '  "counts": an object mapping every cue id below to the number of distinct instances (0 if absent),\n'
    '  "confidence": an integer from 1 to 10 for your overall confidence in the annotation.\n'
    "Every cue id must appear in both objects, in the order listed.\n"
)


@dataclass(frozen=True)
class GraderInput:
    system_prompt: str
    user_prompt: str
    cue_order: Sequence[str]


def cue_list_block(cues: Sequence[Cue]) -> str:
    lines = ["CUES (fixed list, fixed order):"]
    for i, c in enumerate(cues, 1):
        lines.append(f"{i}. {c.id}: {c.definition}")
    return "\n".join(lines) + "\n"


def build_grader_input(public_prompt: str, lie: str, cues: Sequence[Cue]) -> GraderInput:
    """Assemble the grader call. Takes only public text, the lie, and the ontology."""
    system_prompt = RUBRIC_PREAMBLE + "\n" + cue_list_block(cues) + RUBRIC_OUTPUT
    user_prompt = (
        "STORYTELLER'S INSTRUCTIONS (as given to them):\n"
        "-----\n" + public_prompt + "\n-----\n\n"
        "STORY:\n"
        "-----\n" + lie + "\n-----\n\n"
        "Now output the JSON object."
    )
    return GraderInput(system_prompt=system_prompt, user_prompt=user_prompt, cue_order=tuple(c.id for c in cues))


def parse_grader_output(text: str, cue_order: Sequence[str]) -> Dict:
    """Parse and validate the grader JSON. Raises ValueError on any missing cue."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError("grader output contains no JSON object")
    obj = json.loads(text[start:end + 1])
    for key in ("cues", "counts", "confidence"):
        if key not in obj:
            raise ValueError(f"grader output missing key {key!r}")
    for cue in cue_order:
        if cue not in obj["cues"] or cue not in obj["counts"]:
            raise ValueError(f"grader output missing cue {cue!r}")
    return {
        "cues": {c: bool(obj["cues"][c]) for c in cue_order},
        "counts": {c: int(obj["counts"][c]) for c in cue_order},
        "confidence": int(obj["confidence"]),
    }
