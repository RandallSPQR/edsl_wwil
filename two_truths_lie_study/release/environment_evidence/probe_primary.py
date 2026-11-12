import json, sys, os, platform
from pathlib import Path
ROOT = Path(sys.argv[1]); sys.path.insert(0, str(ROOT))
from src.perfect_lie import reversed_analysis as A, reversed_run as R
from src.perfect_lie.personas import load_instrument
recs = A.load_records(ROOT / "results/perfect_lie_reversed/full_run/main/records.jsonl")
inst, cfg = load_instrument(), R.load_config()
rep = json.loads((ROOT / "results/perfect_lie_reversed/final_analysis/final_report.json").read_text())
lies = A.lie_table(recs, A.target_cues(inst, cfg["targets"], rep["gate"]["excluded"]))
import numpy, scipy, statsmodels, pandas
res = {}
for m in cfg["liar_models"]:
    f = A.fit_model(lies[lies.model == m])
    res[m.split("/")[1][:6]] = (f.get("method"), round(f["B"], 5), f["B"] == rep["primary"][m]["B"])
print(platform.python_version(), "threads", os.environ.get("OPENBLAS_NUM_THREADS", "default"), numpy.__version__,
      pandas.__version__, scipy.__version__, statsmodels.__version__, res)
