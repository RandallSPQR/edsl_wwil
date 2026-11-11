"""Rebuild the stage-2 coherence gate (coherence.json) and grading summaries (grading_summary.json) per model from the
released records, with the functions stage2_stage.py used during the pod and grading sessions:
  coherence.json        phase2_gen.coherence(records with their per-token NLL, the model's confirmatory alphas)
  grading_summary.json  phase2_grading.summary(graded rows, {"strict": True}); token counts come from each row's
                        stored API usage.
Run from two_truths_lie/.
"""
import json, sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/phase2/probe"))
import stage2_stage as SS
from src.perfect_lie import phase2_gen as G, phase2_grading as PG

for m in G.MODELS:
    out = SS.STAGE2 / SS.PS.slug(m)
    recs = [json.loads(l) for l in (out / "records.jsonl").open()]
    SS.check_cardinality(recs, SS.planned_jobs(m), f"{out.name} stage-2 records")
    coh = G.coherence(recs, SS.alphas()[SS.PS.slug(m)])
    (out / "coherence.json").write_text(json.dumps(coh, indent=1) + "\n")
    rows = [json.loads(l) for l in (out / SS.GRADED).open()]
    summ = PG.summary(rows, {"strict": True})
    (out / "grading_summary.json").write_text(json.dumps(summ, indent=1) + "\n")
    print(json.dumps({"model": m, "testable": {h: coh[h]["testable"] for h in ("H1", "H2")}, **summ}))
