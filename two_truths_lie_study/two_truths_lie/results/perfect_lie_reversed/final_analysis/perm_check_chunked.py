"""Resumable driver for the blinded permutation check (section 4a). Identical in result to
perm_check.py: permutation i uses seed 20261016 + i in both; this runs i = 0..9,999 in chunks of 1,000
and saves each chunk's decision COUNTS (perm_chunks/chunk_KK.json), so a container restart loses at most
one chunk. When all chunks exist it writes perm_check.json in perm_check.py's format. Like
perm_check.py it outputs only decision shares under permutation; no unpermuted statistic is computed.

  python perm_check_chunked.py [WORKERS]
"""
import json, os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
from src.perfect_lie import reversed_analysis as A, reversed_run as R
from src.perfect_lie.personas import load_instrument

N, CHUNK, SEED = 10_000, 1_000, 20261016

if __name__ == "__main__":
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    out_dir = HERE / "perm_chunks"; out_dir.mkdir(exist_ok=True)
    recs = A.load_records(ROOT / "results/perfect_lie_reversed/full_run/main/records.jsonl")
    inst, cfg = load_instrument(), R.load_config()
    models = cfg["liar_models"]
    g = A.gate(recs, inst)                                    # grades only
    lies = A.lie_table(recs, A.target_cues(inst, cfg["targets"], g["excluded"]))
    for k in range(N // CHUNK):
        f = out_dir / f"chunk_{k:02d}.json"
        if f.exists():
            continue
        t = time.time()
        r = A.permutation_check(lies, models, n=CHUNK, seed=SEED + k * CHUNK, workers=workers)
        f.write_text(json.dumps({"chunk": k, "seeds": [SEED + k * CHUNK, SEED + (k + 1) * CHUNK - 1], "n": CHUNK,
                                 "efficacy_count": {m: round(r["efficacy_share"][m] * CHUNK) for m in models},
                                 "equivalence_count": {m: round(r["equivalence_share"][m] * CHUNK) for m in models},
                                 "seconds": round(time.time() - t)}) + "\n")
        print(f"chunk {k} done in {round(time.time() - t)} s", flush=True)
    ch = [json.loads((out_dir / f"chunk_{k:02d}.json").read_text()) for k in range(N // CHUNK)]
    res = {"n": N, "efficacy_share": {m: sum(c["efficacy_count"][m] for c in ch) / N for m in models},
           "equivalence_share": {m: sum(c["equivalence_count"][m] for c in ch) / N for m in models},
           "note": "only decision shares are output; no unpermuted statistic is computed",
           "seeds": [SEED, SEED + N - 1], "run_in_chunks_of": CHUNK, "seconds": sum(c["seconds"] for c in ch),
           "gate_excluded": g["excluded"]}
    v = json.loads((HERE / "validate_final.json").read_text())["null_B0"]
    res["design_rates_true_B0_simulated"] = {"efficacy_per_model": v["efficacy_per_model"],
                                             "efficacy_any_model": v["efficacy_any_model"],
                                             "equivalence_per_model": v["equivalence_per_model"],
                                             "source": "validate_final.json (S2, balanced Gaussian)"}
    res["efficacy_any_model_bound"] = "familywise alpha 0.05 (Holm); per model at most 0.05"
    (HERE / "perm_check.json").write_text(json.dumps(res, indent=1) + "\n")
    print("perm_check.json written", flush=True)
