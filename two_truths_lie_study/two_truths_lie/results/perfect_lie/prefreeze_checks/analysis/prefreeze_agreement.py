"""Pre-freeze checks: gpt-5 under v0.6, and Google test-retest under the old rubric.

Blind: reads cue labels by cell id and grader only. No condition, persona or target field is
read, and no score or lift is computed. Offline; no model calls.
"""
import json, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]  # results/perfect_lie
CUES = ["document_citation", "institutional_authority", "historical_anchor", "official_failure",
        "first_person_witness", "family_provenance", "direct_quotation", "mundane_aftermath",
        "emotional_appeal", "hedged_claim", "self_deprecation", "skeptic_acknowledgment", "humor"]
REVISED = {"hedged_claim", "direct_quotation", "mundane_aftermath"}


def regrades(d):
    out = {}
    for line in (ROOT / d / "regrades.jsonl").read_text().splitlines():
        r = json.loads(line)
        if not r.get("failed"):
            out.setdefault(r["grader"], {})[r["cell_id"]] = r["cues"]
    return out


def stage1():
    out = {}
    for line in (ROOT / "stage1_v3_controls/records.jsonl").read_text().splitlines():
        r = json.loads(line)
        for role, g in (r.get("grades") or {}).items():
            if g and g.get("cues"):
                out.setdefault(role, {})[r["cell_id"]] = g["cues"]
    return out


def kappa(a, b):
    po = np.mean(a == b); pa, pb = a.mean(), b.mean()
    pe = pa * pb + (1 - pa) * (1 - pb)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def ac1(a, b):
    po = np.mean(a == b); pi = (a.mean() + b.mean()) / 2
    pe = 2 * pi * (1 - pi)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def boot(a, b, f, n=2000, seed=20261006):
    rng = np.random.default_rng(seed); idx = np.arange(len(a)); v = []
    for _ in range(n):
        s = rng.choice(idx, len(idx)); x, y = a[s], b[s]
        if x.min() == x.max() and y.min() == y.max() and x[0] == y[0]:
            v.append(1.0); continue
        v.append(f(x, y))
    return np.percentile(v, [2.5, 97.5])


def agreement(A, B, title):
    ids = sorted(set(A) & set(B))
    rows = {}
    print(f"\n{title} ({len(ids)} lies; bootstrap over lies, 2,000 resamples, seed 20261006)")
    print(f"  {'cue':24s} {'pos':>4s}  kappa [95% CI]          AC1 [95% CI]        at risk")
    for c in CUES:
        a = np.array([bool(A[i][c]) for i in ids]); b = np.array([bool(B[i][c]) for i in ids])
        k, g = kappa(a, b), ac1(a, b); kl, ku = boot(a, b, kappa); gl, gu = boot(a, b, ac1)
        risk = kl < 0.70 and gl < 0.70
        rows[c] = dict(pos=int((a | b).sum()), kappa=k, kappa_ci=[kl, ku], ac1=g, ac1_ci=[gl, gu], at_risk=risk,
                       prev=[float(a.mean()), float(b.mean())])
        print(f"  {c + ('*' if c in REVISED else ''):24s} {rows[c]['pos']:4d}  {k:5.2f} [{kl:5.2f}, {ku:5.2f}]   "
              f"{g:5.2f} [{gl:5.2f}, {gu:5.2f}]   {'YES' if risk else ''}")
    print("  at risk:", [c for c in CUES if rows[c]["at_risk"]])
    return rows


def flips(A, B):
    ids = sorted(set(A) & set(B))
    return {c: float(np.mean([bool(A[i][c]) != bool(B[i][c]) for i in ids])) for c in CUES}, len(ids)


s1 = stage1()
v06 = regrades("rubric_repair_v06")
gpt5 = regrades("prefreeze_checks/gpt5_v06")["secondary"]
rt = regrades("prefreeze_checks/retest_google_v05")["google"]
out = {}

out["gpt5_v06_vs_primary_v06"] = agreement(v06["primary"], gpt5, "CHECK 1: primary (v0.6) vs gpt-5 (v0.6)")
out["gpt5_v05_vs_primary_v05"] = agreement(s1["primary"], s1["secondary"], "reference: primary (v0.5) vs gpt-5 (v0.5), Stage 1")
out["primary_v05_vs_google_retest_v05"] = agreement(s1["primary"], rt, "reference: primary (v0.5, Stage 1) vs Google RETEST (v0.5)")

noise, n1 = flips(s1["google"], rt)
rubric, n2 = flips(s1["google"], v06["google"])
rubric_vs_retest, n3 = flips(rt, v06["google"])
p_noise, _ = flips(s1["primary"], v06["primary"])
g5, n4 = flips(s1["secondary"], gpt5)
print(f"\nCHECK 2: Google grader label-change rates (share of lies whose label differs; n = {n1}, {n2}, {n3})")
print(f"  {'cue':24s} {'old run1->old run2':>18s} {'old run1->new':>14s} {'old run2->new':>14s}  "
      f"{'prev old1/old2/new':>20s}")
prev = lambda G, c: np.mean([bool(v[c]) for v in G.values()])
for c in CUES:
    print(f"  {c + ('*' if c in REVISED else ''):24s} {noise[c]:18.2f} {rubric[c]:14.2f} {rubric_vs_retest[c]:14.2f}  "
          f"{prev(s1['google'], c):6.2f}/{prev(rt, c):4.2f}/{prev(v06['google'], c):4.2f}")
print(f"\n  gpt-5 v0.5 -> v0.6 change (n = {n4}; temperature 1.0, so this mixes rubric and sampling):")
print("  " + ", ".join(f"{c} {g5[c]:.2f}" for c in CUES))
out["google_flip_noise_old_vs_old"] = noise
out["google_flip_old_vs_new"] = rubric
out["google_flip_retest_vs_new"] = rubric_vs_retest
out["gpt5_flip_v05_vs_v06"] = g5
json.dump(out, open(Path(__file__).with_suffix(".json"), "w"), indent=1, default=float)
