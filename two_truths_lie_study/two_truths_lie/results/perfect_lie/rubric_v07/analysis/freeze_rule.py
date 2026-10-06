"""Apply the pre-committed rubric freeze rule (brief §8 item 26), and report v0.7 agreement.

Blind: reads cue labels by cell id and grader only. No condition, persona or target field is
read; no score or lift is computed. Offline; no model calls.
"""
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]  # results/perfect_lie
ALL = ["document_citation", "institutional_authority", "named_expert", "historical_anchor", "official_failure",
       "first_person_witness", "family_provenance", "sensory_detail", "direct_quotation", "mundane_aftermath",
       "mechanism_explanation", "emotional_appeal", "hedged_claim", "self_deprecation", "skeptic_acknowledgment", "humor"]
HEATMAP = {"named_expert", "sensory_detail", "mechanism_explanation"}
SCORABLE = [c for c in ALL if c not in HEATMAP]
BAND = 0.08


def load(d, role):
    out = {}
    for line in (ROOT / d / "regrades.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r["grader"] == role and not r.get("failed"):
            out[r["cell_id"]] = r["cues"]
    return out


def kappa(a, b):
    po = np.mean(a == b); pa, pb = a.mean(), b.mean(); pe = pa * pb + (1 - pa) * (1 - pb)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def ac1(a, b):
    po = np.mean(a == b); pi = (a.mean() + b.mean()) / 2; pe = 2 * pi * (1 - pi)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def boot(a, b, f, n=2000, seed=20261006):
    rng = np.random.default_rng(seed); idx = np.arange(len(a)); v = []
    for _ in range(n):
        s = rng.choice(idx, len(idx)); x, y = a[s], b[s]
        v.append(1.0 if (x.min() == x.max() == y.min() == y.max()) else f(x, y))
    return [float(q) for q in np.percentile(v, [2.5, 97.5])]


def vec(A, B, c, ids):
    return np.array([bool(A[i][c]) for i in ids]), np.array([bool(B[i][c]) for i in ids])


def agreement(A, B):
    ids = sorted(set(A) & set(B)); res = {}
    for c in SCORABLE:
        a, b = vec(A, B, c, ids)
        res[c] = dict(n=len(ids), pos=int((a | b).sum()), kappa=float(kappa(a, b)), kappa_ci=boot(a, b, kappa),
                      ac1=float(ac1(a, b)), ac1_ci=boot(a, b, ac1), prev=[float(a.mean()), float(b.mean())])
        res[c]["at_risk"] = res[c]["kappa_ci"][0] < 0.70 and res[c]["ac1_ci"][0] < 0.70
    return res


def change(A, B, cues=ALL):
    ids = sorted(set(A) & set(B))
    return {c: float(np.mean([bool(A[i][c]) != bool(B[i][c]) for i in ids])) for c in cues}, len(ids)


v06 = {"primary": load("rubric_repair_v06", "primary"), "google": load("rubric_repair_v06", "google")}
v07 = {"primary": load("rubric_v07/primary_google", "primary"), "google": load("rubric_v07/primary_google", "google")}
p_rt = load("rubric_v07/primary_retest", "primary")
g5_07 = load("rubric_v07/gpt5", "secondary")
g5_06 = load("prefreeze_checks/gpt5_v06", "secondary")

out = {"band": BAND}
ag06 = agreement(v06["primary"], v06["google"]); ag07 = agreement(v07["primary"], v07["google"])
out["primary_google_v06"] = ag06; out["primary_google_v07"] = ag07
out["primary_gpt5_v07"] = agreement(v07["primary"], g5_07)
out["primary_gpt5_v06"] = agreement(v06["primary"], g5_06)

e6, e7 = ag06["emotional_appeal"], ag07["emotional_appeal"]
valid_both = len(set(v07["primary"]) & set(v07["google"]))
A = e7["kappa"] > e6["kappa"] and e7["ac1"] > e6["ac1"]
chg = {}; B = True; breaches = []
for g in ("primary", "google"):
    rates, n = change(v06[g], v07[g]); chg[g] = dict(n=n, rates=rates)
    for c, r in rates.items():
        if c != "emotional_appeal" and r > BAND + 1e-12:
            B = False; breaches.append((g, c, r))
manifests = [json.loads((ROOT / "rubric_v07" / d / "manifest.json").read_text()) for d in ("primary_google", "primary_retest", "gpt5")]
cap_ok = not any(m["killed_on_breach"] for m in manifests)
enough = valid_both >= 90
out["change_v06_v07"] = chg
out["primary_retest_v07"] = dict(zip(("rates", "n"), change(v07["primary"], p_rt)))
out["gpt5_change_v06_v07"] = dict(zip(("rates", "n"), change(g5_06, g5_07)))
out["rule"] = dict(A=A, B=B, breaches=breaches, cap_ok=cap_ok, valid_lies_both=valid_both, enough=enough,
                   emotional_v06=[e6["kappa"], e6["ac1"]], emotional_v07=[e7["kappa"], e7["ac1"]],
                   freeze="v0.7" if (A and B and cap_ok and enough) else "v0.6")

print("RULE (brief §8 item 26)")
print(f"  A emotional_appeal primary-Google: v0.6 kappa {e6['kappa']:.4f} AC1 {e6['ac1']:.4f} -> v0.7 kappa {e7['kappa']:.4f} AC1 {e7['ac1']:.4f}: {'MET' if A else 'NOT MET'}")
print(f"  B max change, other cues: primary {max(r for c, r in chg['primary']['rates'].items() if c != 'emotional_appeal'):.3f}, "
      f"google {max(r for c, r in chg['google']['rates'].items() if c != 'emotional_appeal'):.3f} (band {BAND}): {'MET' if B else 'NOT MET ' + str(breaches)}")
print(f"  cap not breached: {cap_ok}; lies valid for both: {valid_both} (need 90)")
print(f"  => FREEZE {out['rule']['freeze']}\n")

print("CHANGE RATES (share of lies whose label differs), heatmap-only marked h")
print(f"  {'cue':26s} {'prim v06->v07':>13s} {'goog v06->v07':>13s} {'prim retest v07':>15s} {'gpt5 v06->v07':>13s}")
for c in ALL:
    flag = lambda r: '!' if (r > BAND and c != 'emotional_appeal') else ' '
    rp, rg = chg['primary']['rates'][c], chg['google']['rates'][c]
    print(f"  {c + (' h' if c in HEATMAP else ''):26s} {rp:12.3f}{flag(rp)} {rg:12.3f}{flag(rg)} "
          f"{out['primary_retest_v07']['rates'][c]:15.3f} {out['gpt5_change_v06_v07']['rates'][c]:13.3f}")

for key, title in (("primary_google_v07", "primary vs Google, v0.7"), ("primary_gpt5_v07", "primary vs gpt-5, v0.7")):
    print(f"\nAGREEMENT {title} (bootstrap over lies, 2,000 resamples, seed 20261006)")
    for c in SCORABLE:
        r = out[key][c]
        print(f"  {c:24s} pos {r['pos']:3d}  kappa {r['kappa']:5.2f} [{r['kappa_ci'][0]:5.2f}, {r['kappa_ci'][1]:5.2f}]  "
              f"AC1 {r['ac1']:5.2f} [{r['ac1_ci'][0]:5.2f}, {r['ac1_ci'][1]:5.2f}]  prev {r['prev'][0]:.2f}/{r['prev'][1]:.2f}  {'AT RISK' if r['at_risk'] else ''}")
json.dump(out, open(Path(__file__).with_suffix(".json"), "w"), indent=1)
