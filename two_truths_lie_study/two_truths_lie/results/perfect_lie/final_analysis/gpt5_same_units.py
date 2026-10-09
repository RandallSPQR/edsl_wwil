"""NOT PRE-REGISTERED, descriptive, written after unblinding. The gpt-5 robustness units are few
(5-13 per model). To tell grader disagreement from subsample noise, score the SAME subsample units
with the primary grader and set the two side by side."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
from src.perfect_lie import sequential as sq
from src.perfect_lie.personas import load_instrument
import numpy as np
RUN = ROOT / "results/perfect_lie/full_interim_r01-15"
last = {}
for line in (RUN / "records.jsonl").read_text().splitlines():
    if line.strip():
        r = json.loads(line); last[r["cell_id"]] = r
recs = list(last.values()); inst = load_instrument()
rep = json.loads((HERE / "final_report.json").read_text())
scorable = sq.scorable_cues(inst, rep["gate"]["excluded"])
sub = [r for r in recs if (r.get("grades") or {}).get("secondary") and (r.get("grades") or {}).get("primary")]
pool = sq.primary_pool(inst, scorable)
out = {}
for g in ("secondary", "primary"):
    ul = sq.unit_lifts(sub, inst, scorable, pool, grader=g)
    by = {}
    for u in ul["units"]:
        by.setdefault(u["model_id"] if "model_id" in u else u["model"], []).append(u["d"])
    out[g] = {m: {"n": len(v), "mean": float(np.mean(v)), "n_pos": int(sum(x > 0 for x in v)),
                  "n_neg": int(sum(x < 0 for x in v)), "n_zero": int(sum(x == 0 for x in v))} for m, v in by.items()}
(HERE / "gpt5_same_units.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
