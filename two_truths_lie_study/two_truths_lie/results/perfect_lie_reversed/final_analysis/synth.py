"""Synthetic records in the full run's format, for validating the final analysis. No model calls.

make_main(effect_B, effect_A, ...) builds every (liar, category, target, condition) cell: a lie
text that passes the screens, primary/Google grades (Google agrees per cue with prob `agree`),
gpt-5 grades on ~25%, four judges' verdicts, and a few failed cells and grader blocks.
Each target cue is present with probability p_condition (+ category and persona noise), so the
true B = p_full - p_reversed and A = p_reversed - p_placebo on the share scale.
"""
import json, random, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
import numpy as np
from src.perfect_lie import comprehension as C
from src.perfect_lie import reversed_run as R

LIE = ("The old mill on the river had been quiet for years before the engineers came back to it. " * 19).strip()


def make_main(B=0.3, A=-0.05, base=0.28, sd_cat=0.15, sd_cell=0.1, n_fail=8, n_block=8, agree=0.95,
              seed=1, cfg=None, instrument=None):
    from src.perfect_lie.personas import load_instrument
    cfg = cfg or R.load_config(); inst = instrument or load_instrument()
    rng = np.random.default_rng(seed); pyr = random.Random(seed)
    cues = [c.id for c in inst.cues]
    p_cond = {"placebo": base, "reversed": base + A, "full": base + A + B}
    cat_dev = {c: rng.normal(0, sd_cat, 3) for c in cfg["categories"]}
    recs = []
    for m in cfg["liar_models"]:
        for ci, cat in enumerate(cfg["categories"]):
            for t in cfg["targets"]:
                cell_dev = rng.normal(0, sd_cell)
                for k, cond in enumerate(("placebo", "full", "reversed")):
                    p = float(np.clip(p_cond[cond] + cat_dev[cat][k] * (cond != "placebo") + cell_dev, 0.01, 0.99))
                    tcues = set(inst.personas[t].cues)
                    prim = {c: bool(rng.random() < (p if c in tcues else 0.15)) for c in cues}
                    goog = {c: (v if rng.random() < agree else not v) for c, v in prim.items()}
                    grades = {"primary": {"cues": prim}, "google": {"cues": goog}}
                    if rng.random() < 0.25:
                        grades["secondary"] = {"cues": {c: (v if rng.random() < agree else not v) for c, v in prim.items()}}
                    acc = sum(prim[c] for c in tcues) / 4
                    targets = {j: {"accept": bool(rng.random() < 0.4 + 0.4 * acc), "confidence": 6} for j in cfg["liar_models"]}
                    recs.append({"cell_id": f"rev_full|{cat}|{t}|{cond}|{m}|r1", "model_id": m, "category": cat,
                                 "target_id": t, "condition": cond, "status": "complete", "lie": LIE,
                                 "lie_words": len(LIE.split()), "lie_word_range": [300, 400], "grades": grades,
                                 "targets": targets, "liar_finish_reason": "stop"})
    idx = pyr.sample(range(len(recs)), n_fail + n_block)
    for i in idx[:n_fail]:
        recs[i] = {**recs[i], "status": "error", "grades": None, "errors": [{"error": "ValueError: target: no well-formed answer"}]}
    for i in idx[n_fail:]:
        recs[i] = {**recs[i], "status": "error", "grades": None,
                   "parse_failures": [{"call": "grader[primary]", "finish_reason": "content_filter"}] * 3,
                   "errors": [{"error": "ValueError: grader[primary]: no well-formed answer"}]}
    return recs


def make_comprehension(acc_full=0.95, acc_rev=0.95, seed=2, cfg=None, instrument=None):
    from src.perfect_lie.personas import load_instrument
    cfg = cfg or R.load_config(); inst = instrument or load_instrument()
    rng = random.Random(seed); out = []
    for cell in R.comprehension_cells(cfg):
        lines = C.note_lines(inst.personas[cell.target_id], inst.personas[cell.placebo_id], cell.condition)
        want = C.EXPECTED[cell.condition]
        p = acc_rev if cell.condition == "reversed" else acc_full
        ans = [{"quality": l, "judge_finds": want if rng.random() < p else ("convincing" if want == "suspicious" else "suspicious")} for l in lines]
        out.append({"cell_id": f"c|{cell.model_id}|{cell.target_id}|{cell.condition}|{cell.replicate}", "model_id": cell.model_id,
                    "target_id": cell.target_id, "condition": cell.condition, "status": "complete", "answer": json.dumps(ans),
                    "note_lines": lines, "variant": C.variant(cell.model_id, cell.target_id, cell.condition, cell.replicate)})
    return out
