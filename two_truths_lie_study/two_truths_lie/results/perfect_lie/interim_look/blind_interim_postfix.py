"""Blinded re-run of the interim decisions after the review fixes and the screen adjudication
(owner instruction, before the Addendum 3 hash). Uses the frozen gate from interim_blind.json and
all records. Outputs ONLY per-model decisions, unit counts and the family / local alpha / look at
which each was decided. No mean, interval or statistic is printed or written."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
from src.perfect_lie import sequential as sq
from src.perfect_lie.personas import load_instrument

RUN = ROOT / "results/perfect_lie/full_interim_r01-15"
MODELS = ["meta-llama/llama-3.1-8b-instruct", "google/gemma-3-27b-it", "openai/gpt-4o-mini", "google/gemini-2.5-flash-lite"]
last = {}
for line in (RUN / "records.jsonl").read_text().splitlines():
    if line.strip():
        r = json.loads(line); last[r["cell_id"]] = r
inst = load_instrument()
frozen = json.loads((HERE / "interim_blind.json").read_text())["gate"]
scorable = sq.scorable_cues(inst, frozen["excluded"])
ul = sq.unit_lifts(list(last.values()), inst, scorable, sq.primary_pool(inst, scorable))
dec = sq.interim_decisions(ul["units"], MODELS)["decisions"]
out = {"gate_excluded_frozen": frozen["excluded"], "units_excluded": ul["excluded"],
       "decisions": {m: {"decision": v["decision"], "n_units": v["n_units"], "decided_at": v["decided_at"]} for m, v in dec.items()}}
(HERE / "interim_blind_postfix.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
