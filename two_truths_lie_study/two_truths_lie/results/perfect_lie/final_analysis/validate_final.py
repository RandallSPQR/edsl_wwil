"""Offline validation of src/perfect_lie/final_analysis.py on simulated data. No real data, no
model calls."""
import json, math, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
from src.perfect_lie import sequential as sq
from src.perfect_lie import final_analysis as fa
from src.perfect_lie.personas import load_instrument
lines = []; out = {}
def say(s=""): print(s, flush=True); lines.append(s)
inst = load_instrument()
MODELS = ["meta-llama/llama-3.1-8b-instruct", "google/gemma-3-27b-it", "openai/gpt-4o-mini", "google/gemini-2.5-flash-lite"]
FAM = {"meta-llama/llama-3.1-8b-instruct": "meta", "google/gemma-3-27b-it": "google", "openai/gpt-4o-mini": "openai",
       "google/gemini-2.5-flash-lite": "google"}

# ---------------- V1: stagewise MUE on two-look data (normal d), stage-1 and stage-2 stops
say("V1. Stagewise median-unbiased estimate and 95% CI, single model at local 0.0125, normal d")
c1, c2 = sq.efficacy_bounds(0.0125)
for theta, sd, upr in ((0.073, 0.45, 10), (0.146, 0.45, 10), (0.0, 0.45, 10)):
    rng = np.random.default_rng(7 + int(theta * 1000)); below = cover = stage1 = n = 0; eq1 = 0
    for _ in range(2000):
        d = theta + sd * rng.standard_normal(35 * upr); n1 = 15 * upr
        z1 = d[:n1].mean() / (d[:n1].std(ddof=1) / math.sqrt(n1))
        if abs(z1) >= c1:
            s = d[:n1].std(ddof=1); r = fa.stagewise_mue(1, z1, n1, None, s, c1); stage1 += 1
            eq1 += abs(r["mue"] - d[:n1].mean()) < 1e-6
        else:
            s = d.std(ddof=1); z2 = d.mean() / (s / math.sqrt(len(d)))
            r = fa.stagewise_mue(2, z2, n1, len(d), s, c1)
        n += 1; below += r["mue"] < theta; cover += r["ci"][0] <= theta <= r["ci"][1]
    res = {"P(mue<theta)": below / n, "coverage95": cover / n, "stage1_stops": stage1, "stage1_mue_equals_naive": eq1}
    out[f"V1 theta {theta}"] = res
    say(f"  theta {theta}: P(MUE < theta) {below/n:.3f} (target 0.5, SE 0.011); CI coverage {cover/n:.3f} (target 0.95, SE 0.005); "
        f"stage-1 stops {stage1}, of which MUE == naive: {eq1}")

# ---------------- V2: conditional MUE removes the winner's curse after an early stop
say("\nV2. Conditional MUE (additional) given a stage-1 stop: median relative to theta")
theta, sd, n1 = 0.146, 0.45, 150
rng = np.random.default_rng(11); naive = []; cond = []
while len(naive) < 1500:
    d = theta + sd * rng.standard_normal(n1); z = d.mean() / (d.std(ddof=1) / math.sqrt(n1))
    if z >= c1:
        naive.append(d.mean()); cond.append(fa.conditional_mue(z, n1, d.std(ddof=1), c1)["mue"])
none = sum(c is None for c in cond)
# a non-identified case corresponds to an unbounded-below estimate: count it as below theta
condv = [(-np.inf if c is None else c) for c in cond]
say(f"  theta {theta}: median naive {np.median(naive):.3f} (inflated); median conditional MUE {np.median(condv):.3f}; "
    f"P(cond MUE < theta) {np.mean([c < theta for c in condv]):.3f} (target 0.5); not identified {none} of {len(cond)}")
out["V2"] = {"median_naive": float(np.median(naive)), "median_conditional_mue": float(np.median(condv)), "theta": theta,
             "p_below": float(np.mean([c < theta for c in condv])), "not_identified": none}

# ---------------- V3: synthetic records end to end
say("\nV3. run_final on synthetic graded records (known effects)")
def synth(effects, seed=3, fail_rate=0.02):
    rng = np.random.default_rng(seed); recs = []; cue_ids = [c.id for c in inst.cues]
    for m in MODELS:
        for row in inst.design:
            for t in row.targets:
                named = set(inst.personas[t].cues)
                for rep in range(1, 16):
                    for cond in ("none", "placebo", "full"):
                        cid = f"{m}|{row.prompt_id}|{t}|{cond}|{rep}"
                        if rng.random() < fail_rate:
                            recs.append({"cell_id": cid, "model_id": m, "model_family": FAM[m], "prompt_id": row.prompt_id,
                                         "category": row.prompt_id, "target_id": t, "j1": row.j1, "j2": row.j2,
                                         "placebo_id": row.placebo, "condition": cond, "replicate": rep, "status": "error"})
                            continue
                        p = np.full(len(cue_ids), 0.3)
                        if cond == "full":
                            p = np.array([0.3 + effects[m] if c in named else 0.3 for c in cue_ids])
                        prim = dict(zip(cue_ids, map(bool, rng.random(len(cue_ids)) < p)))
                        goog = {c: (v if rng.random() > 0.08 else not v) for c, v in prim.items()}
                        bhat = {c: (v if rng.random() > 0.3 else not v) for c, v in prim.items()}
                        grades = {"primary": {"cues": prim}, "google": {"cues": goog}}
                        if rng.random() < 0.25:
                            grades["secondary"] = {"cues": {c: (v if rng.random() > 0.1 else not v) for c, v in prim.items()}}
                        nc = sum(prim[c] for c in named)
                        targets = {j: {"accept": bool(rng.random() < 0.4 + 0.05 * nc), "family": FAM[j]} for j in MODELS}
                        recs.append({"cell_id": cid, "model_id": m, "model_family": FAM[m], "prompt_id": row.prompt_id,
                                     "category": row.prompt_id, "target_id": t, "j1": row.j1, "j2": row.j2,
                                     "placebo_id": row.placebo, "condition": cond, "replicate": rep, "status": "complete",
                                     "lie": " ".join(["word"] * (350 if rng.random() > 0.03 else 150)),
                                     "lie_word_range": [300, 400], "grades": grades,
                                     "bhat_grades": {"primary": {"cues": bhat}}, "targets": targets,
                                     "elicitation": {"flags": {"echo": False, "refusal": False, "breakdown": False}}})
    return recs
eff = {MODELS[0]: 0.25, MODELS[1]: 0.10, MODELS[2]: 0.0, MODELS[3]: -0.15}
recs = synth(eff)
res = fa.run_final(recs, inst, MODELS)
for m in MODELS:
    r = res["primary"]["models"][m]
    say(f"  {m:34s} true {eff[m]:+.2f}-scaled | decision {r['decision']:15s} dir {str(r['direction']):8s} "
        f"mean {r['mean_lift']:+.3f} MUE {(r.get('stagewise') or {}).get('mue', float('nan')):+.3f} n {r['n_units']}")
ok_eq = all(abs(res["primary"]["models"][m]["stagewise"]["mue"] - res["primary"]["models"][m]["mean_lift"]) < 1e-6
            for m in MODELS if "stagewise" in res["primary"]["models"][m])
say(f"  stage-1 MUE equals naive mean for every model stopped at the interim: {ok_eq}")
say(f"  empty-cue exclusions: breakdown total {res['empty_cue_exclusions']['total']} vs unit_lifts count {res['units_excluded']['empty_cue_set']}")
tp = res["tipping_point"]
say(f"  tipping point: missing units {tp['missing_units_total']}")
for m, t in tp["models"].items():
    if "at_decision_boundary" in t:
        a = t["at_decision_boundary"]; say(f"    {m}: {t['missing_units']} missing; delta to reverse {a['delta']} (reversible {a['reversible']}); "
                                           f"z with all missing at worst {a['z_if_all_missing_at_worst']:.2f} vs boundary {a['boundary']:.2f}")
# self-consistency: plugging delta gives Z == boundary
for m, t in tp["models"].items():
    a = t.get("at_decision_boundary")
    if a and a["reversible"]:
        d = np.array([u["d"] for u in sq.unit_lifts([r for r in recs if r["status"] == "complete"], inst, res["scorable_cues"], res["primary_pool"])["units"] if u["model_id"] == m])
        x = np.concatenate([d, np.full(t["missing_units"], a["delta"])]); z = x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))
        say(f"    check {m}: |Z| at delta {abs(z):.4f} == boundary {a['boundary']:.4f}")
say(f"  mixed model converged: {[res['mixed_model'][m].get('converged') for m in MODELS]}")
say(f"  sensitivity keys: {list(res['sensitivity'].keys())}")
say(f"  gpt-5 subsample lies {res['gpt5_robustness']['lies_in_subsample']}; pooled kappa {res['gpt5_robustness']['pooled']['kappa']:.2f}")
say(f"  P4 cues {res['p4_secondary']['p4_scorable_cues']}")
iv = res["secondaries"]["4_iv_wald"]["models"]
say(f"  IV Wald (acceptance rises with named cues in the simulation, so positive where the first stage is positive): "
    + ", ".join(f"{m.split('/')[1][:10]} {iv[m]['wald']:+.2f}" for m in MODELS if m in iv and iv[m]['wald'] is not None))
man = res["secondaries"]["5_bhat"]["manipulation_check_bhat_full_minus_placebo"]
say("  B-hat manipulation check (simulated B-hat copies story labels with noise, so it tracks the effect): "
    + ", ".join(f"{m.split('/')[1][:10]} {man[m]['mean']:+.3f}" for m in MODELS if m in man))
out["V3"] = {"ok_stage1_equal": ok_eq, "decisions": {m: res["primary"]["models"][m]["decision"] for m in MODELS}}
json.dump(out, open(HERE / "validate_final.json", "w"), indent=1, default=float)
(HERE / "validate_final.log.md").write_text("\n".join(lines) + "\n")

# ---------------- V4: tipping point on a constructed case that can be reversed
say("\nV4. Tipping point on a constructed case near the boundary")
rng = np.random.default_rng(5)
m = MODELS[0]
d = 0.20 + 0.45 * rng.standard_normal(140)
units = [{"model_id": m, "replicate": 1 + (i % 15), "d": float(x), "prompt_id": "science"} for i, x in enumerate(d)]
z = d.mean() / (d.std(ddof=1) / math.sqrt(len(d)))
prim = {"models": {m: {"decision": "belief-tracking", "direction": "positive", "boundary_at_decision": c1, "look": "interim"}}}
tp = fa.tipping_point(units, [{"model_id": m}] * 10, [m], prim)[m]["at_decision_boundary"]
x = np.concatenate([d, np.full(10, tp["delta"])]); z2 = x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))
say(f"  observed Z {z:.3f}; 10 missing units; delta {tp['delta']:+.4f}; Z at delta {z2:.4f} vs boundary {c1:.4f}")
out["V4"] = {"z": float(z), "delta": tp["delta"], "z_at_delta": float(z2), "boundary": c1}

# ---------------- V5: empty-cue breakdown matches unit_lifts when the gate excludes emotional_appeal
say("\nV5. Empty-cue breakdown vs unit_lifts with emotional_appeal excluded (as at the real interim)")
complete = [r for r in recs if r["status"] == "complete"]
sc = sq.scorable_cues(inst, ["emotional_appeal"]); pool = sq.primary_pool(inst, sc)
ul = sq.unit_lifts(complete, inst, sc, pool); eb = fa.empty_cue_breakdown(complete, inst, sc, pool)
say(f"  unit_lifts empty_cue_set {ul['excluded']['empty_cue_set']} vs breakdown total {eb['total']}; by prompt x persona {eb['by_prompt_x_persona']}")
out["V5"] = {"unit_lifts": ul["excluded"]["empty_cue_set"], "breakdown": eb["total"]}
json.dump(out, open(HERE / "validate_final.json", "w"), indent=1, default=float)
(HERE / "validate_final.log.md").write_text("\n".join(lines) + "\n")

# ---------------- V6: dump the synthetic records for a dry run of run_final.py (rendering only)
import os
if os.environ.get("DRY_DIR"):
    dry = Path(os.environ["DRY_DIR"]); dry.mkdir(parents=True, exist_ok=True)
    with open(dry / "records.jsonl", "w") as fh:
        for r in recs: fh.write(json.dumps(r) + "\n")
