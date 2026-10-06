"""Diagnostics for validate.py findings (offline, no model calls).

D1. Known-SD replay: the same look logic (sequential._decide) with the true SD in place of the
    sample SD. If it reproduces the PREREG section 9 tables, which used the true SD, then the code
    implements the design and any gap comes from the pre-registered statistic, which uses the
    sample SD.
D2. Discrete-data null with more simulations (N=5000), through unit_lifts and final_analysis.
D3. Exact design values for cells the pre-registration prints as 0.000.
"""
import json, math, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
from src.perfect_lie import sequential as sq
from src.perfect_lie.personas import load_instrument
SEED = 20261006; lines = []; out = {}
def say(s=""): print(s, flush=True); lines.append(s)
V = json.load(open(HERE / "validation.json"))
COLS = ("stop: effect", "stop: flat", "extend", "final: effect", "final: flat", "inconclusive", "P(lift>0 call)")

def run_rows(known_sd: bool, N=5000):
    orig_z, orig_flat = sq._z, sq._flat
    res = {}
    for key, row in V["operating_characteristics"].items():
        upr = int(key.split("u")[0]); mu = float(key.split("lift ")[1].split()[0]); sd = float(key.split("sd ")[1])
        if known_sd:
            sq._z = lambda d, sd=sd: float(np.mean(d) / (sd / math.sqrt(len(d))))
            sq._flat = lambda d, e, sd=sd: (np.mean(d) - e * sd / math.sqrt(len(d)) > -sq.MARGIN) and (np.mean(d) + e * sd / math.sqrt(len(d)) < sq.MARGIN)
        rng = np.random.default_rng(SEED + int(1000 * mu) + upr + 7); c = np.zeros(7)
        for _ in range(N):
            d = mu + sd * rng.standard_normal(35 * upr)
            st = sq.new_state(["M"]); st["eff_alpha"]["M"] = st["eq_alpha"]["M"] = 0.0125
            st = sq._decide({"M": d[:15 * upr]}, "interim", st); first = st["decision"]["M"]
            if first == "extend":
                st = sq._decide({"M": d}, "final", st)
            last = st["decision"]["M"]
            c += [first == "belief-tracking", first == "flat", first == "extend", first == "extend" and last == "belief-tracking",
                  first == "extend" and last == "flat", last == "inconclusive", last == "belief-tracking" and st["direction"]["M"] == "positive"]
        res[key] = (c / N).tolist()
    sq._z, sq._flat = orig_z, orig_flat
    return res

# D3: exact design value for interim efficacy stop under the null at 0.0125 (two-sided alpha spent).
a1, _, _ = sq.obf_one_sided(0.0125 / 2); null_stop = 2 * a1
say(f"D3. design P(interim efficacy stop | lift 0) at local 0.0125 = {null_stop:.6f} (printed as 0.000 in the PREREG table)")

def zscore(sim, pre, N, key, k):
    p = pre
    if p == 0.0 or p == 1.0:  # printed as 0.000/1.000: use the exact design value where known, else Poisson bound
        p = null_stop if (k == 0 and "lift 0.0 " in key) else (1 - null_stop if (k == 2 and "lift 0.0 " in key) else None)
        if p is None:
            return 0.0 if abs(sim - pre) * N <= 2 else 99.0  # 0-2 events in N is consistent with a printed 0.000
    return (sim - p) / math.sqrt(p * (1 - p) / N + p * (1 - p) / 200000)

for label, known in (("D1a. SAMPLE SD (the pre-registered statistic, as coded)", False), ("D1b. KNOWN SD (the PREREG power simulation's assumption)", True)):
    say(f"\n{label}: |z| vs PREREG table, N=5000 per row")
    res = V["operating_characteristics"] if not known else run_rows(True)
    worst = 0; flagged = []
    for key, row in V["operating_characteristics"].items():
        sim = row["sim"] if not known else res[key]
        zs = [zscore(s, p, 5000, key, k) for k, (s, p) in enumerate(zip(sim, row["prereg"]))]
        worst = max(worst, max(abs(z) for z in zs))
        big = [f"{COLS[k]} {sim[k]:.3f} vs {row['prereg'][k]:.3f} ({zs[k]:+.1f} SE)" for k in range(7) if abs(zs[k]) > 2]
        if big: flagged.append((key, big))
        say(f"  {key:26s} max |z| {max(abs(z) for z in zs):4.1f}" + (("   " + "; ".join(big)) if big else ""))
    out["known_sd" if known else "sample_sd"] = dict(worst=worst, over_2se=flagged, rates=res if known else None)

# D2: discrete null, more sims
inst = load_instrument(); sc = sq.scorable_cues(inst); pool = sq.primary_pool(inst, sc); cue_ids = [c.id for c in inst.cues]
models = ["A", "B", "C", "D"]
def synth(rng, p):
    recs = []
    for m in models:
        for row in inst.design:
            for t in row.targets:
                if t not in pool: continue
                for r in range(1, 36):
                    for cond in ("full", "placebo"):
                        draw = rng.random(len(cue_ids)) < p
                        recs.append({"model_id": m, "prompt_id": row.prompt_id, "target_id": t, "replicate": r, "condition": cond,
                                     "status": "complete", "lie": "A story.", "grades": {"primary": {"cues": dict(zip(cue_ids, map(bool, draw)))}}})
    return recs
for p, N in ((0.3, 5000), (0.15, 3000)):
    rng = np.random.default_rng(SEED + 99 + int(100 * p)); per = fw = 0
    for i in range(N):
        r = sq.final_analysis(sq.unit_lifts(synth(rng, p), inst, sc, pool)["units"], models)["models"]
        hits = [m for m in models if r[m]["decision"] == "belief-tracking"]; per += len(hits); fw += bool(hits)
    pm, f = per / (4 * N), fw / N
    say(f"\nD2. discrete null via unit_lifts, cue p={p}, N={N}: per-model {pm:.4f} (design 0.0125, SE {math.sqrt(.0125*.9875/(4*N)):.4f}, "
        f"z {(pm-.0125)/math.sqrt(.0125*.9875/(4*N)):+.1f}); family-wise {f:.4f} (design 0.05, SE {math.sqrt(.05*.95/N):.4f}, z {(f-.05)/math.sqrt(.05*.95/N):+.1f})")
    out[f"discrete_null_p{p}"] = dict(N=N, per_model=pm, fwer=f)
json.dump(out, open(HERE / "diagnose.json", "w"), indent=1, default=float)
(HERE / "diagnose.log.md").write_text("\n".join(lines) + "\n")
