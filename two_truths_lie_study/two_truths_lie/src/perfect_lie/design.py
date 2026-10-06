"""Generate design.json: the persona-pair rotation and fixed placebo per pair.

Run once, commit the output, never regenerate:

    python -m src.perfect_lie.design            # refuses to overwrite
    python -m src.perfect_lie.design --force    # only if you know why

Construction. Six personas, six prompts, one pair per prompt. Each persona
must appear on exactly two prompts with two different partners, so the pair
graph is 2-regular on six vertices with six edges: a single 6-cycle
P1-P2-P3-P4-P5-P6-P1 (the alternative, two triangles, would give each persona
the same two partners as its triangle-mates and leave four personas never
co-occurring with the other triangle; the cycle spreads partners more evenly).
Placebo for the pair (Pk, Pk+1) is P(k+3 mod 6): never in the pair, and every
persona is the placebo exactly once. The prompt order is a fixed permutation
drawn with the recorded seed so that persona pairs are not aligned with the
prompt file order.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import List

from . import DATA_DIR
from .personas import DesignRow, load_personas, load_prompts, validate_design

DESIGN_SEED = 20260915


def generate_design(seed: int = DESIGN_SEED) -> List[DesignRow]:
    personas = load_personas()
    prompts = load_prompts()
    pids = sorted(personas)  # P1..P6
    n = len(pids)
    pairs = [(pids[k], pids[(k + 1) % n]) for k in range(n)]
    placebos = [pids[(k + 3) % n] for k in range(n)]

    rng = random.Random(seed)
    order = list(range(n))
    rng.shuffle(order)  # which pair goes to which prompt

    rows = []
    for prompt, k in zip(prompts, order):
        j1, j2 = pairs[k]
        rows.append(DesignRow(prompt.id, j1, j2, placebos[k]))
    validate_design(rows, personas, prompts)
    return rows


def write_design(path: Path, rows: List[DesignRow], seed: int) -> None:
    payload = {
        "version": "0.1-phase1",
        "generator": "src/perfect_lie/design.py",
        "seed": seed,
        "status": "Generated once and committed. Do not regenerate.",
        "rows": [{"prompt_id": r.prompt_id, "j1": r.j1, "j2": r.j2, "placebo": r.placebo} for r in rows],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=DATA_DIR / "design.json")
    ap.add_argument("--seed", type=int, default=DESIGN_SEED)
    ap.add_argument("--force", action="store_true", help="overwrite an existing design.json")
    args = ap.parse_args()
    if args.out.exists() and not args.force:
        raise SystemExit(f"{args.out} exists; design.json is generated once and committed. Use --force only deliberately.")
    rows = generate_design(args.seed)
    write_design(args.out, rows, args.seed)
    for r in rows:
        print(f"{r.prompt_id:12s} pair=({r.j1},{r.j2}) placebo={r.placebo}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
