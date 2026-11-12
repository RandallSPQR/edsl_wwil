"""Offline validation of src/perfect_lie/sequential.py (brief §8 item 29). No model calls.

(i)   Null: false-positive rates through the real code, against the design.
(ii)  Pilot effect and half effect: per-model operating characteristics against the PREREG
      section 9 tables (10 and 9 units per replicate, worst-case Holm level 0.0125).
(iii) Stage 2 lies with randomly assigned condition labels through the real gate, pool, unit and
      interim code: a permutation sanity check. Stage 2 has only `full` lies, so no real
      contrast exists in these data.
"""
import json, math, random, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from src.perfect_lie import sequential as sq
from src.perfect_lie.personas import load_instrument
from src.perfect_lie.runner import load_records

SEED = 20261006
out = {}
lines = []
def say(s=""):
    print(s); lines.append(s)

def units_normal(rng, spec, upr, reps=range(1, 36)):
    u = []
    for m, (mu, sd) in spec.items():
        d = mu + sd * rng.standard_normal(len(reps) * upr)
        for i, r in enumerate(np.repeat(list(reps), upr)):
            u.append({"model_id": m, "replicate": int(r), "d": float(d[i])})
    return u

# ------------------------------------------------------------------ (i) null
say("(i) NULL: four models, true lift 0, through final_analysis (interim + final, Holm)")
models = ["A", "B", "C", "D"]
res_i = {}
for label, sd, upr, N in (("normal d, sd 0.405, 10 units", 0.405, 10, 10000),
                          ("normal d, sd 0.49, 9 units", 0.49, 9, 10000)):
    rng = np.random.default_rng(SEED)
    per_model = 0; fwer = 0; pos = 0
    for _ in range(N):
        r = sq.final_analysis(units_normal(rng, {m: (0.0, sd) for m in models}, upr), models)["models"]
        hits = [m for m in models if r[m]["decision"] == "belief-tracking"]
        per_model += len(hits); fwer += bool(hits); pos += sum(r[m]["direction"] == "positive" for m in hits)
    pm, fw = per_model / (4 * N), fwer / N
    se_pm, se_fw = math.sqrt(0.0125 * 0.9875 / (4 * N)), math.sqrt(0.05 * 0.95 / N)
    res_i[label] = dict(N=N, per_model=pm, se=se_pm, fwer=fw, fwer_se=se_fw, one_sided_pos=pos / (4 * N))
    say(f"  {label:32s} N={N}: per-model false-positive {pm:.4f} (design 0.0125, SE {se_pm:.4f}); "
        f"family-wise {fw:.4f} (design <= 0.05, SE {se_fw:.4f}); lift>0 calls {pos / (4 * N):.4f}")

# discrete d from synthetic graded records through unit_lifts (the real scoring path)
inst = load_instrument()
sc = sq.scorable_cues(inst); pool = sq.primary_pool(inst, sc)
cue_ids = [c.id for c in inst.cues]
def synth_records(rng, p_full, p_plac, reps=range(1, 36)):
    recs = []
    for m in models:
        for row in inst.design:
            for t in row.targets:
                if t not in pool:
                    continue
                for r in reps:
                    for cond, p in (("full", p_full), ("placebo", p_plac)):
                        draw = rng.random(len(cue_ids)) < p
                        recs.append({"model_id": m, "prompt_id": row.prompt_id, "target_id": t, "replicate": r,
                                     "condition": cond, "status": "complete", "lie": "A story.",
                                     "grades": {"primary": {"cues": dict(zip(cue_ids, map(bool, draw)))}}})
    return recs
N = 1000; rng = np.random.default_rng(SEED + 1); per_model = fwer = 0; nunits = []
for _ in range(N):
    ul = sq.unit_lifts(synth_records(rng, 0.3, 0.3), inst, sc, pool)
    nunits.append(len(ul["units"]) / 4 / 35)
    r = sq.final_analysis(ul["units"], models)["models"]
    hits = [m for m in models if r[m]["decision"] == "belief-tracking"]
    per_model += len(hits); fwer += bool(hits)
pm, fw = per_model / (4 * N), fwer / N
se_pm = math.sqrt(0.0125 * 0.9875 / (4 * N)); se_fw = math.sqrt(0.05 * 0.95 / N)
res_i["discrete d via unit_lifts (cue p=0.3)"] = dict(N=N, per_model=pm, se=se_pm, fwer=fw, fwer_se=se_fw,
                                                      units_per_replicate=float(np.mean(nunits)))
say(f"  {'discrete d via unit_lifts, p=0.3':32s} N={N}: per-model false-positive {pm:.4f} (design 0.0125, SE {se_pm:.4f}); "
    f"family-wise {fw:.4f} (SE {se_fw:.4f}); units per replicate {np.mean(nunits):.0f}")
out["null"] = res_i

# ------------------------------------------------------------------ (ii) operating characteristics
say("\n(ii) OPERATING CHARACTERISTICS, one model at the worst-case Holm level (0.0125 both families),"
    " through the real look logic (sequential._decide); N=5000 per row")
PREREG = {  # PREREG section 9 tables (200,000 sims), unrounded from rubric_repair_v06/analysis/gsd3.log.md
    10: {(0.146, 0.405): (.655, .000, .345, .345, .000, .000, 1.000), (0.146, 0.49): (.357, .000, .643, .642, .000, .001, .999),
         (0.073, 0.405): (.035, .000, .965, .773, .160, .032, .808), (0.073, 0.49): (.014, .000, .986, .599, .113, .274, .613),
         (0.0, 0.405): (.000, .000, 1.0, .012, .983, .005, .006), (0.0, 0.49): (.000, .000, 1.0, .012, .885, .103, .006)},
    9: {(0.146, 0.405): (.567, .000, .433, .433, .000, .000, 1.000), (0.146, 0.49): (.290, .000, .710, .707, .000, .002, .998),
        (0.073, 0.405): (.027, .000, .973, .730, .145, .098, .757), (0.073, 0.49): (.011, .000, .989, .546, .103, .340, .557),
        (0.0, 0.405): (.000, .000, 1.0, .012, .968, .020, .006), (0.0, 0.49): (.000, .000, 1.0, .012, .832, .156, .006)}}
COLS = ("stop: effect", "stop: flat", "extend", "final: effect", "final: flat", "inconclusive", "P(lift>0 call)")
res_ii = {}; worst = 0.0; flags = []
for upr in (10, 9):
    say(f"  {upr} units per replicate                  " + " | ".join(f"{c:>14s}" for c in COLS))
    for (mu, sd), pre in PREREG[upr].items():
        N = 5000; rng = np.random.default_rng(SEED + int(1000 * mu) + upr)
        counts = np.zeros(7)
        for _ in range(N):
            d = mu + sd * rng.standard_normal(35 * upr)
            interim, full = {"M": d[:15 * upr]}, {"M": d}
            st = sq.new_state(["M"]); st["eff_alpha"]["M"] = st["eq_alpha"]["M"] = 0.0125
            st = sq._decide(interim, "interim", st); first = st["decision"]["M"]
            if first == "extend":
                st = sq._decide(full, "final", st)
            last = st["decision"]["M"]
            counts += [first == "belief-tracking", first == "flat", first == "extend",
                       first == "extend" and last == "belief-tracking", first == "extend" and last == "flat",
                       last == "inconclusive", last == "belief-tracking" and st["direction"]["M"] == "positive"]
        sim = counts / N
        z = [(s - p) / math.sqrt(max(p * (1 - p), 1e-6) / N + max(p * (1 - p), 1e-6) / 200000) for s, p in zip(sim, pre)]
        bad = [COLS[k] for k, v in enumerate(z) if abs(v) > 3]
        worst = max(worst, max(abs(v) for v in z))
        if bad:
            flags.append((upr, mu, sd, bad))
        res_ii[f"{upr}u lift {mu} sd {sd}"] = dict(sim=sim.tolist(), prereg=list(pre), z=z, beyond_3se=bad)
        say(f"  lift {mu:5.3f} sd {sd:5.3f} sim     " + " | ".join(f"{v:14.3f}" for v in sim))
        say(f"  {'':18s} prereg  " + " | ".join(f"{v:14.3f}" for v in pre) + (f"   <-- beyond 3 SE: {bad}" if bad else ""))
say(f"  largest |difference| in simulation-error units: {worst:.2f} (flag above 3)")
out["operating_characteristics"] = res_ii; out["oc_flags"] = flags

# ------------------------------------------------------------------ (iii) Stage 2 permutation
say("\n(iii) STAGE 2 PERMUTATION SANITY CHECK (real gate, pool, unit_lifts, interim_decisions)")
s2 = [r for r in load_records(ROOT / "results/perfect_lie/stage2_v3_full_reachability") if r.get("status") == "complete"]
gate = sq.agreement_gate(s2, sc)
say(f"  Stage 2: {len(s2)} complete lies, all `full`. Gate on {gate['n_lies']} lies: excluded {gate['excluded']}; "
    f"flagged (<30 positives) {len(gate['flagged'])} of {len(sc)}")
sc2 = sq.scorable_cues(inst, gate["excluded"]); pool2 = sq.primary_pool(inst, sc2)
by = {}
for r in s2:
    by.setdefault((r["model_id"], r["target_id"]), []).append(r)
P = 2000; prng = random.Random(SEED); dec_counts = {}; means = []; n_units = []
liars = sorted({r["model_id"] for r in s2})
for _ in range(P):
    recs = []
    for (m, t), rs in by.items():
        if len(rs) != 2:
            continue
        a, b = prng.sample(rs, 2)
        pid = prng.choice([a["prompt_id"], b["prompt_id"]])
        recs += [dict(a, condition="full", prompt_id=pid, replicate=1), dict(b, condition="placebo", prompt_id=pid, replicate=1)]
    ul = sq.unit_lifts(recs, inst, sc2, pool2)
    n_units.append(len(ul["units"]))
    means.append(np.mean([u["d"] for u in ul["units"]]))
    dec = sq.interim_decisions(ul["units"], liars)["decisions"]
    for m in liars:
        dec_counts[dec[m]["decision"]] = dec_counts.get(dec[m]["decision"], 0) + 1
tot = sum(dec_counts.values())
say(f"  {P} random labelings; pseudo-units per labeling {np.mean(n_units):.0f} (about {np.mean(n_units) / len(liars):.0f} per model)")
say(f"  mean of pooled d across labelings {np.mean(means):+.4f} (expected 0 by symmetry; SD across labelings {np.std(means):.3f})")
say("  interim decisions across labelings x models: " + ", ".join(f"{k} {v / tot:.4f}" for k, v in sorted(dec_counts.items())))
out["stage2_permutation"] = dict(labelings=P, mean_units=float(np.mean(n_units)), mean_d=float(np.mean(means)),
                                 sd_mean_d=float(np.std(means)), decisions={k: v / tot for k, v in dec_counts.items()},
                                 gate_excluded=gate["excluded"], gate_flagged=gate["flagged"])
json.dump(out, open(HERE / "validation.json", "w"), indent=1, default=float)
(HERE / "validation.log.md").write_text("\n".join(lines) + "\n")
