"""Phase 2 Addendum 2: the seeded, stratified 20% subsample graded also by the Google grader (descriptive).

One target per evaluation category: the 32 evaluation categories (category_split.json) in a seeded order are
assigned the five targets in turn, so every category contributes exactly one (category, target) cell (20% of the
160) and every target 6 or 7 cells. The same cells are used for both models, both hypotheses and every graded arm
(stage-2 steered and placebo, the unsteered placebo / full / reversed references, and the method check's steered and
placebo lies, on whichever of its 16 categories are drawn), so the steered-minus-placebo pairs stay intact.

  python subsample.py      -> subsample.json
"""
import json, random
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = 20261028
TARGETS = ["P1", "P2", "P3", "P5", "P6"]


def draw(evaluation, seed=SEED, targets=TARGETS):
    order = random.Random(seed).sample(sorted(evaluation), len(evaluation))
    return {c: targets[i % len(targets)] for i, c in enumerate(order)}


def main():
    split = json.loads((HERE.parent / "probe/category_split.json").read_text())
    cells = draw(split["evaluation"])
    out = {"seed": SEED, "targets": TARGETS, "fraction": len(cells) / (len(split["evaluation"]) * len(TARGETS)),
           "cells": dict(sorted(cells.items()))}
    (HERE / "subsample.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({t: sum(v == t for v in cells.values()) for t in TARGETS}), out["fraction"])


if __name__ == "__main__":
    main()
