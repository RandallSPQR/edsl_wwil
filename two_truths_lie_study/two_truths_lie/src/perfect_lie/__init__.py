"""The Perfect Lie: target-conditioned strategic adaptation study.

See ../../../PERFECT_LIE.md for the brief. This package holds only what the
existing TTAL harness does not already provide (personas, conditions, blind
grader input, cell enumeration). Gameplay orchestration reuses
src.edsl_adapter and src.prompts.storyteller.FibberPrompt unchanged.
"""

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "perfect_lie"

CONDITIONS = ("none", "placebo", "partial", "full")
