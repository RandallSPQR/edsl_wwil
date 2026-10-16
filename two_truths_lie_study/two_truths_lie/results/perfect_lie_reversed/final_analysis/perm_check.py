"""Blinded permutation check (section 4a), BEFORE unblinding: swap full/reversed labels at random within
each (liar, category, target) cell, 10,000 times, run the real decision code, and output ONLY the share
of efficacy and equivalence decisions per model. No unpermuted statistic is computed or shown.

  python perm_check.py [N] [WORKERS]            real run
  python perm_check.py N WORKERS --run-dir DIR  test data
"""
import json, os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
from src.perfect_lie import reversed_analysis as A, reversed_run as R
from src.perfect_lie.personas import load_instrument

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    n = int(args[0]) if args else 10_000
    workers = int(args[1]) if len(args) > 1 else 4
    run_dir = Path(sys.argv[sys.argv.index("--run-dir") + 1]) if "--run-dir" in sys.argv else ROOT / "results/perfect_lie_reversed/full_run"
    if "--run-dir" in sys.argv:
        args = args[:2]
    recs = A.load_records(run_dir / "main/records.jsonl")
    inst, cfg = load_instrument(), R.load_config()
    g = A.gate(recs, inst)                                    # grades only
    lies = A.lie_table(recs, A.target_cues(inst, cfg["targets"], g["excluded"]))
    t = time.time()
    res = A.permutation_check(lies, cfg["liar_models"], n=n, workers=workers)
    res["seconds"] = round(time.time() - t)
    res["gate_excluded"] = g["excluded"]
    out = HERE / ("perm_check.json" if "--run-dir" not in sys.argv else "perm_check_test.json")
    out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))
