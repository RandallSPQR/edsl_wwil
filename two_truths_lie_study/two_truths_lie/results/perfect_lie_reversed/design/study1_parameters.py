"""Parameters for the follow-up's cost estimate and power analysis, read from the first study's
interim records (unblinded after Addendum 3; final analysis at f60ea64). No model calls."""
import json, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
from src.perfect_lie import sequential as sq
from src.perfect_lie.personas import load_instrument
from src.perfect_lie.pipeline import load_models

RUN = ROOT / "results/perfect_lie/full_interim_r01-15"
last = {}
for line in (RUN / "records.jsonl").read_text().splitlines():
    if line.strip():
        r = json.loads(line); last[r["cell_id"]] = r
recs = list(last.values()); inst = load_instrument(); M = load_models()
liar = {m["id"]: m for m in M["classes"]["C1"]["liar_models"]}
tgt = {m["id"]: m for m in M["classes"]["C1"]["target_models"]}
grd = {g["role"]: g for g in M["graders"]}
price = lambda e, u: (u.get("prompt_tokens") or 0) / 1000 * e["usd_per_1k_input"] + (u.get("completion_tokens") or 0) / 1000 * e["usd_per_1k_output"]

# ---- 1. cost per complete cell, by component (usage of the accepted call; parse retries are in `other`)
comp = defaultdict(float); n = 0; total = 0.0
for r in recs:
    if r.get("status") != "complete":
        continue
    n += 1; total += r.get("cost_usd", 0.0)
    comp["liar"] += price(liar[r["model_id"]], r["liar_usage"])
    for t, v in (r.get("targets") or {}).items():
        comp["judges_4"] += price(tgt[t], v["usage"])
    for g, v in (r.get("grades") or {}).items():
        comp[f"grade_{g}"] += price(grd[g], v["usage"])
    if r.get("elicitation"):
        comp["elicitation"] += price(liar[r["model_id"]], r["elicitation"]["usage"])
    for g, v in (r.get("bhat_grades") or {}).items():
        comp[f"bhat_{g}"] += price(grd[g], v["usage"])
comp["other_retries_and_failed_call_bounds"] = total - sum(comp.values())
all_spend = sum(r.get("cost_usd", 0.0) for r in recs)
cost = {"complete_cells": n, "counted_spend_all_cells": all_spend, "billed_spend": 62.09,
        "per_complete_cell": {k: v / n for k, v in comp.items()}, "per_complete_cell_total": total / n}

# ---- 2. lie-level s (share of the target's note-named, placebo-net, scorable cues present; primary grader)
gate_excluded = ["emotional_appeal"]
scorable = sq.scorable_cues(inst, gate_excluded)
pool = sq.primary_pool(inst, scorable)
rows = {r.prompt_id: r for r in inst.design}
lies = []
for r in recs:
    if r.get("status") != "complete" or r.get("target_id") not in pool or sq.is_confession(r):
        continue
    named = sq.note_named(inst, rows[r["prompt_id"]], r["target_id"], scorable)
    if not named or "primary" not in (r.get("grades") or {}):
        continue
    s = sum(bool(r["grades"]["primary"]["cues"][q]) for q in named) / len(named)
    lies.append(dict(model=r["model_id"], prompt=r["prompt_id"], target=r["target_id"], cond=r["condition"],
                     rep=r["replicate"], s=s, k=len(named)))
by = defaultdict(list)
for x in lies:
    by[(x["model"], x["cond"])].append(x["s"])
s_means = {f"{m}|{c}": {"n": len(v), "mean": float(np.mean(v)), "sd": float(np.std(v, ddof=1))} for (m, c), v in sorted(by.items())}

# within-cell (same model, prompt, target, condition) replicate SD of s
cells = defaultdict(list)
for x in lies:
    cells[(x["model"], x["prompt"], x["target"], x["cond"])].append(x["s"])
within = defaultdict(list)
for (m, p, t, c), v in cells.items():
    if len(v) > 1:
        within[m].append(np.var(v, ddof=1))
within_sd = {m: float(np.sqrt(np.mean(v))) for m, v in within.items()}
within_sd_by_cond = {}
for c in ("none", "placebo", "full"):
    vv = [np.var(v, ddof=1) for (m, p, t, cc), v in cells.items() if cc == c and len(v) > 1]
    within_sd_by_cond[c] = float(np.sqrt(np.mean(vv)))

# effect heterogeneity: per (model, prompt, target) cell mean of full minus placebo; spread across cells
eff = defaultdict(dict)
for (m, p, t, c), v in cells.items():
    eff[(m, p, t)][c] = float(np.mean(v))
het = {}
for m in sorted({k[0] for k in eff}):
    d = {(p, t): e["full"] - e["placebo"] for (mm, p, t), e in eff.items() if mm == m and "full" in e and "placebo" in e}
    vals = np.array(list(d.values()))
    nrep = np.mean([len(cells[(m, p, t, "full")]) for (p, t) in d])
    # observed variance of cell effects minus the sampling part (2 * within var / reps)
    samp = 2 * within_sd[m] ** 2 / nrep
    het[m] = {"cells": len(vals), "mean_effect": float(vals.mean()), "sd_cell_effects_observed": float(vals.std(ddof=1)),
              "sampling_sd_of_a_cell_effect": float(np.sqrt(samp)),
              "sd_true_cell_effects": float(np.sqrt(max(vals.var(ddof=1) - samp, 0.0))),
              "by_target": {t: float(np.mean([v for (p, tt), v in d.items() if tt == t])) for t in sorted({t for _, t in d})},
              "by_prompt": {p: float(np.mean([v for (pp, t), v in d.items() if pp == p])) for p in sorted({p for p, _ in d})}}
out = {"source": str(RUN.relative_to(ROOT)), "cost": cost, "lie_level_s": s_means, "within_cell_sd": within_sd,
       "within_cell_sd_by_condition": within_sd_by_cond, "effect_heterogeneity": het,
       "note": "In the first study prompt and target pair are partly confounded (each prompt has two targets and one placebo), so the split of cell-effect heterogeneity into category and persona parts is rough."}
(HERE / "study1_parameters.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
