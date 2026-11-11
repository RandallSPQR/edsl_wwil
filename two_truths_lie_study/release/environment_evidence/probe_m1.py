import json, sys, os
from pathlib import Path
ROOT = Path(sys.argv[1]); sys.path.insert(0, str(ROOT))
from src.perfect_lie import reversed_analysis as A, reversed_run as R
from src.perfect_lie.personas import load_instrument
recs = A.load_records(ROOT / "results/perfect_lie_reversed/full_run/main/records.jsonl")
inst, cfg = load_instrument(), R.load_config()
rep = json.loads((ROOT / "results/perfect_lie_reversed/final_analysis/final_report.json").read_text())
lies = A.lie_table(recs, A.target_cues(inst, cfg["targets"], rep["gate"]["excluded"]))
import numpy, scipy, statsmodels, pandas
out = {}
for m in cfg["liar_models"]:
    r = A.m1_intercepts(lies[lies.model == m])
    rel = rep["robustness"]["m1_random_intercepts_assumes_no_heterogeneity"][m]
    out[m.split("/")[1][:6]] = (r["converged"], r["B"] == rel["B"], rel["converged"])
print(os.environ.get("OPENBLAS_NUM_THREADS","default"), numpy.__version__, pandas.__version__, scipy.__version__, statsmodels.__version__, "| (converged, B bit-equal, released converged):", out)
