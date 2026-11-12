"""Blinded interim look (PREREG sections 5-6; brief §8 items 27, 29, 30). Offline, no model calls.

Reports ONLY: per-model decisions (efficacy stop / equivalence stop / extend), the cues the gate
excludes (and flags), cell counts, failures, and spend. No lift, interval, mean or test statistic is
printed or written: `sequential.interim_decisions` computes them internally and returns none.
"""
import collections, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from src.perfect_lie import sequential as sq
from src.perfect_lie.personas import load_instrument
from src.perfect_lie.transport import is_transport_error

RUN = ROOT / "results/perfect_lie/full_interim_r01-15"
MODELS = ["meta-llama/llama-3.1-8b-instruct", "google/gemma-3-27b-it", "openai/gpt-4o-mini", "google/gemini-2.5-flash-lite"]

history = collections.defaultdict(list)
for line in (RUN / "records.jsonl").read_text().splitlines():
    if line.strip():
        r = json.loads(line); history[r["cell_id"]].append(r)
last = {k: v[-1] for k, v in history.items()}
records = list(last.values())
manifest = json.loads((RUN / "manifest.json").read_text())

# ---- cell counts and failures (no outcome data)
status = collections.Counter(r.get("status") for r in records)
by_mc = collections.Counter((r["model_id"], r["condition"], r.get("status")) for r in records)
def cause(r):
    errs = r.get("errors") or []
    e = str(errs[-1].get("error", "")) if errs else ""
    if errs and is_transport_error(e): return "rate limit / timeout / connection"
    pf = (r.get("parse_failures") or [])[-1:] 
    if pf and pf[0].get("finish_reason") == "content_filter": return f"content filter ({pf[0].get('call')})"
    if "no content" in e: return "empty answer at token limit"
    if pf: return f"parse/consistency ({pf[0].get('call')})"
    return "other"
fail_cause = collections.Counter(cause(r) for r in records if r.get("status") == "error")
retried = [k for k, h in history.items() if any(x.get("status") == "error" and x.get("errors") and is_transport_error(x["errors"][-1].get("error", "")) for x in h)]
retried_ok = sum(1 for k in retried if last[k].get("status") == "complete")

# ---- gate (blind: grades only) on all complete interim lies
inst = load_instrument()
complete = [r for r in records if r.get("status") == "complete"]
candidates = sq.scorable_cues(inst)
gate = sq.agreement_gate(complete, candidates)
scorable = sq.scorable_cues(inst, gate["excluded"])
pool = sq.primary_pool(inst, scorable)

# ---- units and blinded decisions
ul = sq.unit_lifts(complete, inst, scorable, pool)
dec = sq.interim_decisions(ul["units"], MODELS)

report = {
    "run": str(RUN.relative_to(ROOT)), "records_through": manifest.get("updated_at"),
    "cells": {"planned": manifest.get("n_cells_planned"), **dict(status)},
    "cells_by_model_condition": {f"{m}|{c}|{s}": n for (m, c, s), n in sorted(by_mc.items())},
    "failed_by_cause": dict(fail_cause),
    "transport_retries": {"cells_retried": len(retried), "completed_after_retry": retried_ok},
    "spend": {"counted_usd": manifest.get("spend_usd"), "cap_usd": 80.0},
    "gate": {"lies": gate["n_lies"], "excluded": gate["excluded"], "flagged_under_30_positives": gate["flagged"]},
    "primary_pool_personas": pool,
    "units_excluded": ul["excluded"],
    "decisions": dec["decisions"],
    "alpha_after_interim": dec["alpha_after_interim"],
}
(HERE / "interim_blind.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
