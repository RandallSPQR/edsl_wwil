"""Validation of the final-analysis decision code on simulated data (PREREG_REVERSED section 4a).
No model calls, no real data. Data model and scenario S2 (first-study-like heterogeneity) from
design/power.py; each simulated study has four liar models, each 72 categories x 5 personas x 3
conditions x 1 replicate, run through reversed_analysis.decide_all (the registered decision code,
mixed model with fallback, Holm in both families).

Reports, per scenario: false-positive rate of the efficacy family under B = 0 (any model and per
model), equivalence rate under B = 0, power at B = 0.10, coverage of the 95% CI for B and the
median of (estimate - truth) at B = 0.30, and how often the fallback was used.
"""
import json, os, sys
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "results/perfect_lie_reversed/design")); sys.path.insert(0, str(HERE))
import numpy as np, pandas as pd
from scipy import stats
import power as P
from src.perfect_lie import reversed_analysis as A

MODELS = ["m1", "m2", "m3", "m4"]
SCEN = P.SCEN["S2 first-study-like"]


def one(args):
    B, seed = args[:2]
    Bs = args[2] if len(args) > 2 else {m: B for m in MODELS}     # per-model truth (mixed configurations)
    P.rng = np.random.default_rng(seed)
    rows = []
    for m in MODELS:
        y = P.simulate(72, 1, 0.0, Bs[m], **SCEN)      # reversed = placebo + 0; full = placebo + B
        idx = np.indices(y.shape).reshape(4, -1).T
        for (k, p, c, r), v in zip(idx, y.ravel()):
            rows.append({"model": m, "category": f"c{k}", "persona": f"P{p}", "condition": ("placebo", "full", "reversed")[c],
                         "s": float(v), "cell_id": f"{m}|{k}|{p}|{c}"})
    res = A.decide_all(pd.DataFrame(rows), MODELS)
    out = {}
    for m, d in res.items():
        q = stats.t.isf(0.025, d["df"])
        tb = Bs[m]
        out[m] = {"B": d["B"], "truth": tb, "covered": d["B"] - q * d["B_se"] <= tb <= d["B"] + q * d["B_se"],
                  "eff": d["efficacy_alpha_at_decision"] is not None, "eq": d["equivalence_alpha_at_decision"] is not None,
                  "fallback": d["method"] != "mixed model", "label": d["label"]}
    return out


def run(B, n, seed0, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        sims = list(ex.map(one, [(B, seed0 + i) for i in range(n)]))
    per = [x[m] for x in sims for m in MODELS]
    return {"B_true": B, "n_studies": n, "n_model_fits": len(per),
            "efficacy_any_model": float(np.mean([any(x[m]["eff"] for m in MODELS) for x in sims])),
            "efficacy_per_model": float(np.mean([p["eff"] for p in per])),
            "equivalence_per_model": float(np.mean([p["eq"] for p in per])),
            "ci_coverage": float(np.mean([p["covered"] for p in per])),
            "median_error": float(np.median([p["B"] - p["truth"] for p in per])),
            "share_below_truth": float(np.mean([p["B"] < p["truth"] for p in per])),
            "fallback_share": float(np.mean([p["fallback"] for p in per])),
            "labels": {k: v for k, v in pd.Series([p["label"] for p in per]).value_counts().items()}}


def mixed(n, seed0, workers):
    """Two models with B = 0.30, two null: false positives among the nulls under Holm."""
    Bs = {"m1": 0.30, "m2": 0.30, "m3": 0.0, "m4": 0.0}
    with ProcessPoolExecutor(max_workers=workers) as ex:
        sims = list(ex.map(one, [(None, seed0 + i, Bs) for i in range(n)]))
    return {"truth": Bs, "n_studies": n,
            "null_models_efficacy_any": float(np.mean([sims_i["m3"]["eff"] or sims_i["m4"]["eff"] for sims_i in sims])),
            "null_models_efficacy_per_model": float(np.mean([s[m]["eff"] for s in sims for m in ("m3", "m4")])),
            "effect_models_power": float(np.mean([s[m]["eff"] for s in sims for m in ("m1", "m2")]))}


def pipeline_one(seed):
    """Discrete, bounded synthetic records through the real gate, lie table and decision code, with
    asymmetric missingness: 30% of full lies for personas P1 and P5 fail (B = 0)."""
    import random
    import synth
    from src.perfect_lie import reversed_run as R
    from src.perfect_lie.personas import load_instrument
    inst, cfg = load_instrument(), R.load_config()
    recs = synth.make_main(B=0.0, A=0.0, seed=seed, n_fail=0, n_block=0, cfg=cfg, instrument=inst)
    rng = random.Random(seed)
    for i, r in enumerate(recs):
        if r["condition"] == "full" and r["target_id"] in ("P1", "P5") and rng.random() < 0.30:
            recs[i] = {**r, "status": "error", "grades": None, "errors": [{"error": "ValueError: simulated"}]}
    g = A.gate(recs, inst)
    lies = A.lie_table(recs, A.target_cues(inst, cfg["targets"], g["excluded"]), adj={})
    res = A.decide_all(lies, cfg["liar_models"])
    return {m: {"eff": d["efficacy_alpha_at_decision"] is not None, "B": d["B"], "fallback": d["method"] != "mixed model"}
            for m, d in res.items()}


def pipeline(n, seed0, workers):
    with ProcessPoolExecutor(max_workers=workers) as ex:
        sims = list(ex.map(pipeline_one, [seed0 + i for i in range(n)]))
    per = [v for s in sims for v in s.values()]
    return {"design": "synth.make_main, B = 0, discrete cues, 30% of full lies for P1 and P5 failed", "n_studies": n,
            "efficacy_any_model": float(np.mean([any(v["eff"] for v in s.values()) for s in sims])),
            "efficacy_per_model": float(np.mean([v["eff"] for v in per])),
            "median_B": float(np.median([v["B"] for v in per])), "fallback_share": float(np.mean([v["fallback"] for v in per]))}


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    out = {"scenario": "S2 first-study-like (power.py)", "design": "72 categories x 5 personas x 3 conditions x 1 replicate, 4 models",
           "null_B0": run(0.0, n, 1000, workers), "B010": run(0.10, n // 2, 50000, workers), "B030": run(0.30, n // 2, 90000, workers),
           "B_minus010_equivalence_boundary": run(-0.10, n // 2, 130000, workers),
           "mixed_two_effects_two_nulls": mixed(n // 2, 170000, workers),
           "pipeline_discrete_asymmetric_missingness": pipeline(n // 3, 210000, workers)}
    (HERE / "validate_final.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
