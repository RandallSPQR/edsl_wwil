"""Pilot 2 report: fabricability of the 24 categories under placebo (rules: PILOT_RULES.md)."""
import json, sys
from collections import defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
from src.perfect_lie.scoring import degenerate_tail, confession, lie_viability, REFUSAL_PATTERNS
from src.perfect_lie.stage1 import wilson
from src.perfect_lie.runner import load_records
from src.perfect_lie.personas import load_instrument
from src.perfect_lie import reversed as rv
from src.perfect_lie import sequential as sq

T = sys.argv[1] if len(sys.argv) > 1 else "0.6"
SET = sys.argv[2] if len(sys.argv) > 2 else "first"
RUN = HERE / (f"fabricability_t{T}" + ("" if SET == "first" else "_set2"))
OUT = "fabricability_report" + ("" if SET == "first" else "_set2")
inst = load_instrument(); cats = rv.load_categories()
allcats = cats["original"] + cats["new"] if SET == "first" else cats["drawn_48"] + cats["replacements_for_failed"]
NEW = set(cats["new"]) if SET == "first" else set(cats["drawn_48"])


def grader_block(r):
    """Owner amendment 2026-10-09: the primary grader returned content_filter on every attempt."""
    pf = [x for x in r.get("parse_failures", []) if x.get("call") == "grader[primary]"]
    return r.get("status") == "error" and len(pf) >= 3 and all(x.get("finish_reason") == "content_filter" for x in pf[-3:])
scorable = sq.scorable_cues(inst)  # pre-gate scorable (heatmap-only cues exempt, as Stage 1 A)
recs = load_records(RUN); mf = json.loads((RUN / "manifest.json").read_text())
NAME = {"meta-llama/llama-3.1-8b-instruct": "Llama", "google/gemma-3-27b-it": "Gemma",
        "openai/gpt-4o-mini": "gpt-4o-mini", "google/gemini-2.5-flash-lite": "Gemini"}

cat_rep, model_rep, matches = {}, {}, []
for cat in allcats:
    rs = [r for r in recs if r["category"] == cat]
    lies = [r for r in rs if r.get("lie")]
    blocks = sum(grader_block(r) for r in rs)
    failed = sum(r.get("status") == "error" and not grader_block(r) for r in rs)
    refus = [r for r in lies if REFUSAL_PATTERNS.search(r["lie"])]
    conf = [r for r in lies if confession(r["lie"])]
    for r in refus + conf:
        matches.append({"category": cat, "model": NAME[r["model_id"]], "screen": "refusal" if r in refus else "confession",
                        "match": (REFUSAL_PATTERNS.search(r["lie"]).group(0) if r in refus else confession(r["lie"]))})
    nonv = [r for r in lies if [x for x in lie_viability(r) if not x.startswith("refusal")]]
    # A: P(cue | placebo) for cues not named in that lie's placebo note, pooled over models
    graded = [r for r in lies if (r.get("grades") or {}).get("primary")]
    A = {}
    for c in scorable:
        pool = [r for r in graded if c not in inst.personas[r["placebo_id"]].cues]
        k = sum(bool(r["grades"]["primary"]["cues"][c]) for r in pool)
        if pool:
            A[c] = {"k": k, "n": len(pool), "rate": k / len(pool), "wilson_lb": wilson(k, len(pool))[0]}
    a_fail = {c: v for c, v in A.items() if v["wilson_lb"] > 0.5}
    # headroom: placebo share of the TARGET's scorable cues (descriptive)
    sh = [sum(bool(r["grades"]["primary"]["cues"][c]) for c in inst.personas[r["target_id"]].cues if c in scorable)
          / len([c for c in inst.personas[r["target_id"]].cues if c in scorable]) for r in graded]
    v_fail = bool(refus) or bool(conf) or len(nonv) > 1
    cat_rep[cat] = {"lies": len(lies), "graded": len(graded), "failed_cells": failed, "grader_blocks": blocks, "refusal_matches": len(refus),
                    "confession_matches": len(conf), "non_viable": len(nonv),
                    "non_viable_detail": [(NAME[r["model_id"]], lie_viability(r)) for r in nonv],
                    "A_fail": a_fail, "A_max": max(A.items(), key=lambda kv: kv[1]["rate"]) if A else None,
                    "placebo_target_share_mean": sum(sh) / len(sh) if sh else None,
                    "placebo_target_share_zero": sum(x == 0 for x in sh) / len(sh) if sh else None,
                    "V_fail_before_reading_matches": v_fail, "D_fail": failed > 1,
                    "new": cat in NEW}
    cat_rep[cat]["pass_before_reading_matches"] = not (v_fail or a_fail or failed > 1)
for m in NAME:
    rs = [r for r in recs if r["model_id"] == m]
    lies = [r for r in rs if r.get("lie")]
    model_rep[m] = {"lies": len(lies), "failed": sum(r.get("status") == "error" and not grader_block(r) for r in rs),
                    "grader_blocks": sum(grader_block(r) for r in rs),
                    "degenerate": sum(degenerate_tail(r["lie"]) for r in lies),
                    "B_pass": sum(degenerate_tail(r["lie"]) for r in lies) < 0.05 * max(len(lies), 1),
                    "D_pass": sum(r.get("status") == "error" and not grader_block(r) for r in rs) <= 1,
                    "words_median": sorted(r["lie_words"] for r in lies)[len(lies) // 2] if lies else None}
out = {"run": str(RUN.relative_to(ROOT)), "temperature": float(T), "top_p": 0.9, "spend_usd": mf["spend_usd"],
       "cells": mf["n_cells_planned"], "complete": mf["n_complete"], "error": mf["n_error"],
       "categories": cat_rep, "models": model_rep, "screen_matches_to_read": matches}
(HERE / f"{OUT}.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
L = [f"# Pilot {'2' if SET == 'first' else '3'}: fabricability (placebo, 16 lies per category, T={T}, top_p 0.9)", "",
     "Criterion D as amended 2026-10-09: grader content-filter blocks are counted separately, not as failures.", "",
     f"Spend ${mf['spend_usd']:.2f} (cap ${10 if SET == 'first' else 12}). Cells {mf['n_complete']}/{mf['n_cells_planned']} complete, {mf['n_error']} failed.", "",
     "| category | new | lies | failed | grader blocks | refusal / confession matches | non-viable | A: highest unnamed cue rate (Wilson LB) | placebo share of target cues (share of lies at 0) | verdict |",
     "|---|---|---|---|---|---|---|---|---|---|"]
for cat, x in cat_rep.items():
    am = x["A_max"]
    L.append(f"| {cat} | {'yes' if x['new'] else ''} | {x['lies']} | {x['failed_cells']} | {x['grader_blocks']} | {x['refusal_matches']} / {x['confession_matches']} | "
             f"{x['non_viable']} | {am[0]} {am[1]['k']}/{am[1]['n']} ({am[1]['wilson_lb']:.2f}) | "
             f"{x['placebo_target_share_mean']:.2f} ({x['placebo_target_share_zero']:.0%}) | "
             f"{'PASS' if x['pass_before_reading_matches'] else 'FAIL: ' + ', '.join(k for k, v in (('V', x['V_fail_before_reading_matches']), ('A', bool(x['A_fail'])), ('D', x['D_fail'])) if v)} |")
L += ["", "| model | lies | failed | grader blocks | degenerate | B (<5%) | D (<=1 failed) | median words |", "|---|---|---|---|---|---|---|---|"]
for m, x in model_rep.items():
    L.append(f"| {NAME[m]} | {x['lies']} | {x['failed']} | {x['grader_blocks']} | {x['degenerate']} | {'pass' if x['B_pass'] else 'FAIL'} | {'pass' if x['D_pass'] else 'FAIL'} | {x['words_median']} |")
L += ["", f"Screen matches (read by hand before any category is failed on V): {len(matches)}."]
for x in matches:
    L.append(f"- {x['category']} / {x['model']} / {x['screen']}: \"{x['match']}\"")
(HERE / f"{OUT}.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
