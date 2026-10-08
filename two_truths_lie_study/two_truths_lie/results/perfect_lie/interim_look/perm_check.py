"""Blinded permutation check on the real interim data (owner instruction, step 1).

Within each unit, the full/placebo labels are swapped at random; for a unit lift d = s(full) -
s(placebo) a swap is d -> -d. Each permuted dataset goes through the real decision code
(sequential.interim_decisions). Reported: only the share of permutations in which each model stops
for efficacy, against the design's nominal interim rate. The unpermuted statistics are never
printed, written, or compared with the permutation distribution.
"""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
from src.perfect_lie import sequential as sq
from src.perfect_lie.personas import load_instrument

RUN = ROOT / "results/perfect_lie/full_interim_r01-15"
MODELS = ["meta-llama/llama-3.1-8b-instruct", "google/gemma-3-27b-it", "openai/gpt-4o-mini", "google/gemini-2.5-flash-lite"]
N_PERM = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
SEED = 20261008

last = {}
for line in (RUN / "records.jsonl").read_text().splitlines():
    if line.strip():
        r = json.loads(line); last[r["cell_id"]] = r
complete = [r for r in last.values() if r.get("status") == "complete"]
inst = load_instrument()
gate = sq.agreement_gate(complete, sq.scorable_cues(inst))
scorable = sq.scorable_cues(inst, gate["excluded"])
units = sq.unit_lifts(complete, inst, scorable, sq.primary_pool(inst, scorable))["units"]

rng = np.random.default_rng(SEED)
d = np.array([u["d"] for u in units])
stops = {m: 0 for m in MODELS}; any_stop = 0
for _ in range(N_PERM):
    flips = rng.choice((-1.0, 1.0), size=len(d))
    perm = [dict(u, d=float(x)) for u, x in zip(units, d * flips)]
    dec = sq.interim_decisions(perm, MODELS)["decisions"]
    hit = [m for m in MODELS if dec[m]["decision"] == "efficacy stop"]
    for m in hit: stops[m] += 1
    any_stop += bool(hit)
a1, _, _ = sq.obf_one_sided(0.0125 / 2)
nominal = 2 * a1
out = {"permutations": N_PERM, "seed": SEED, "units": len(units),
       "nominal_interim_efficacy_rate_per_model_at_local_0.0125": nominal,
       "nominal_upper_if_all_alpha_passed_local_0.05": 2 * sq.obf_one_sided(0.05 / 2)[0],
       "share_of_permutations_stopping_for_efficacy": {m: stops[m] / N_PERM for m in MODELS},
       "share_with_any_model_stopping": any_stop / N_PERM}
(HERE / "perm_check.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
