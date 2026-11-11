"""Rebuild results/phase2/grading_route/regrade_direct.json from the per-lie labels it stores. Run from two_truths_lie/.

The route check (regrade_direct.py) called the Anthropic API once (2026-10-22) and kept, per lie, the OpenRouter
primary labels and the direct-route labels. This recomputes everything derived from them with regrade_direct.py's own
functions: the seeded sample (re-drawn from the identity-check records, which must give the same cells), the per-cue
and pooled agreement and kappa, and the decision. The API facts (models returned, token usage, attempts) are carried
over: only Tier 1 can reproduce them.
"""
import json, sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/phase2/grading_route"))
import regrade_direct as RD
from src.perfect_lie.personas import load_instrument

src = json.loads((Path(sys.argv[1]) if len(sys.argv) > 1 else
                  ROOT.parent / "release/tier0/inputs/regrade_direct_rows.json").read_text())
rows = src["rows"]
drawn = [r["cell_id"] for r in RD.sample()]
if drawn != [r["cell_id"] for r in rows]:
    raise SystemExit("the seeded sample no longer draws the stored cells")
inst = load_instrument()
cue_order = [c.id for c in inst.cues]
scorable = {c.id for c in inst.cues if not c.heatmap_only and c.id not in RD.GATED}
ok = [x for x in rows if x["direct"]]
per_cue = {}
for c in cue_order:
    a = [bool(x["openrouter"][c]) for x in ok]; b = [bool(x["direct"][c]) for x in ok]
    per_cue[c] = {"agreement": sum(p == q for p, q in zip(a, b)) / len(a) if a else None, "kappa": RD.kappa(a, b),
                  "positives_openrouter": sum(a), "positives_direct": sum(b), "scorable": c in scorable}


def pooled(cues):
    a = [bool(x["openrouter"][c]) for x in ok for c in cues]; b = [bool(x["direct"][c]) for x in ok for c in cues]
    return {"labels": len(a), "agreement": sum(p == q for p, q in zip(a, b)) / len(a), "kappa": RD.kappa(a, b)}


all_, sc = pooled(cue_order), pooled(sorted(scorable))
decision = (all_["kappa"] is not None and all_["kappa"] >= 0.90) or all_["agreement"] >= 0.97
out = {"model_requested": src["model_requested"], "models_returned": src["models_returned"], "n": len(rows),
       "parsed": len(ok), "failures": [x for x in rows if not x["direct"]], "usage": src["usage"],
       "pooled_all_cues": all_, "pooled_scorable_cues": sc, "per_cue": per_cue,
       "decision": "switch to the direct route" if decision else "stay on OpenRouter", "rows": rows}
(ROOT / "results/phase2/grading_route/regrade_direct.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps({"pooled_all_cues": all_, "decision": out["decision"]}))
