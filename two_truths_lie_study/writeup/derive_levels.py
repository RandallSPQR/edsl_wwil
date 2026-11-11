"""Descriptive s levels for figures 2 and 3 (post hoc, descriptive: the registered analyses report contrasts, not
levels). Derived from the committed lie-level records with each study's registered scoring code; no new test.

  Reversed note (figure 2): per model x condition, the registered lie table (reversed_analysis.lie_table: complete,
      graded, not a confession, the registered gate's cue pool) -> per category, the mean s over the personas present
      -> mean and 95% t interval over the categories (df = K - 1).
  Phase 2 stage 2 (figure 3): per model x arm (x hypothesis), the registered analysis records (stage2_stage.
      analysis_records: owner adjudication applied) scored by phase2_stage2.scores -> per category, the mean s over the
      targets present -> mean and 95% t interval over the categories.

  python derive_levels.py            -> derived/levels.json
"""
import gzip, hashlib, json, math, sys
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
TTL = HERE.parent / "two_truths_lie"
sys.path.insert(0, str(TTL)); sys.path.insert(0, str(TTL / "results/phase2/probe"))

REV_RECORDS = "results/perfect_lie_reversed/full_run/main/records.jsonl.gz"
REV_REPORT = "results/perfect_lie_reversed/final_analysis/final_report.json"
P2_GRADED = {"google/gemma-3-27b-it": "results/phase2/stage2/gemma-3-27b-it/graded.jsonl.gz",
             "meta-llama/llama-3.1-8b-instruct": "results/phase2/stage2/llama-3.1-8b-instruct/graded.jsonl.gz"}
P2_ADJ = "results/phase2/stage2/screen_adjudication.json"
OUT = HERE / "derived" / "levels.json"


def sha(rel):
    return hashlib.sha256((TTL / rel).read_bytes()).hexdigest()


def summary(cat_means):
    x = np.asarray(cat_means, float)
    k = len(x)
    m, se = float(x.mean()), float(x.std(ddof=1) / math.sqrt(k))
    h = float(stats.t.isf(0.025, k - 1)) * se
    return {"mean": m, "ci95": [m - h, m + h], "K": k}


def by_category(rows):
    """rows: (category, value) -> per category mean."""
    acc = {}
    for c, v in rows:
        acc.setdefault(c, []).append(v)
    return [float(np.mean(v)) for _, v in sorted(acc.items())]


def reversed_levels():
    from src.perfect_lie import reversed_analysis as A
    from src.perfect_lie.personas import load_instrument
    last = {}
    with gzip.open(TTL / REV_RECORDS, "rt") as f:            # reversed_analysis.load_records, from the .gz
        for line in f:
            if line.strip():
                r = json.loads(line); last[r["cell_id"]] = r
    recs = list(last.values())
    rep = json.loads((TTL / REV_REPORT).read_text())
    cues = A.target_cues(load_instrument(), rep["pool"], rep["gate"]["excluded"])
    lies = A.lie_table(recs, cues)
    out = {}
    for m in sorted(lies["model"].unique()):
        out[m] = {}
        for cond in ("placebo", "reversed", "full"):
            d = lies[(lies.model == m) & (lies.condition == cond)]
            out[m][cond] = {**summary(by_category(zip(d["category"], d["s"]))), "n_lies": int(len(d))}
    return {"n_lies_analysed": int(len(lies)), "levels": out}


def stage2_levels():
    import stage2_stage as SS
    from src.perfect_lie import phase2_stage2 as P2
    rows = []
    for m, rel in P2_GRADED.items():
        with gzip.open(TTL / rel, "rt") as f:
            rows += [json.loads(l) for l in f]
    SS.ADJUDICATION = TTL / P2_ADJ
    SS.graded_all = lambda check=True: rows               # the committed graded files, not the working copies
    recs = SS.analysis_records()
    _, ev, cues, _ = SS.context()
    S = P2.scores(recs, cues)
    out = {}
    for (m, arm, hyp) in sorted({(k[0], k[1], k[2]) for k in S}, key=str):
        vals = [(c, v) for (mm, a, h, c, t), v in S.items() if (mm, a, h) == (m, arm, hyp)]
        out.setdefault(m, {})[f"{arm}|{hyp}"] = {**summary(by_category(vals)), "n_lies": len(vals)}
    return {"levels": out}


def derive():
    return {"note": "post hoc, descriptive: s levels with 95% t intervals over categories (per-category means over "
                    "personas/targets present); figure inputs only",
            "inputs": {rel: sha(rel) for rel in [REV_RECORDS, REV_REPORT, P2_ADJ, *P2_GRADED.values()]},
            "reversed_note": reversed_levels(), "phase2_stage2": stage2_levels()}


def main():
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(derive(), indent=1, sort_keys=True) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
