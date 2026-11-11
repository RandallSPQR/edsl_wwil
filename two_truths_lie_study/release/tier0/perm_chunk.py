"""Recompute the first N chunks of the reversed-note blinded permutation check (section 4a) with the registered code and
compare their decision counts with the released perm_chunks/chunk_KK.json. Run from two_truths_lie/.

  python ../release/tier0/perm_chunk.py N        (N in 0..20; each chunk is 500 permutations, about 870 s on 4 cores)
"""
import json, os, sys
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/perfect_lie_reversed/final_analysis"))
from src.perfect_lie import reversed_analysis as A, reversed_run as R
from src.perfect_lie.personas import load_instrument
from perm_check_chunked import CHUNK, SEED

n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
if n == 0:
    print("no chunk recomputed (--perm-chunks 0)")
    sys.exit(0)
recs = A.load_records(ROOT / "results/perfect_lie_reversed/full_run/main/records.jsonl")
inst, cfg = load_instrument(), R.load_config()
models = cfg["liar_models"]
g = A.gate(recs, inst)
# adj={}: the check was run (2026-10-17 to 10-19) before the owner's screen adjudication existed (465ae50, 10-20), so
# every confession-screen match was excluded as a confession. lie_table now loads that adjudication by default (15 of
# the 16 matches kept), which would change the permuted data; {} reproduces the check as it was run.
lies = A.lie_table(recs, A.target_cues(inst, cfg["targets"], g["excluded"]), adj={})
bad = 0
for k in range(n):
    ref = json.loads((ROOT / f"results/perfect_lie_reversed/final_analysis/perm_chunks/chunk_{k:02d}.json").read_text())
    r = A.permutation_check(lies, models, n=CHUNK, seed=SEED + k * CHUNK, workers=min(4, os.cpu_count() or 1))
    got = {"efficacy_count": {m: round(r["efficacy_share"][m] * CHUNK) for m in models},
           "equivalence_count": {m: round(r["equivalence_share"][m] * CHUNK) for m in models}}
    same = all(got[x] == ref[x] for x in got)
    bad += not same
    print(json.dumps({"chunk": k, "seeds": ref["seeds"], "identical_counts": same, **got}), flush=True)
sys.exit(1 if bad else 0)
