"""Power and false-positive rate for the PRIMARY test after owner decision 2026-10-09:
Test B = full - reversed (same cue words, flipped valence), per liar model, Holm across four.
Design 72 categories x 1 replicate (24 x 3 shown for comparison). Data model and scenarios as in
power.py (first-study-like heterogeneity S2). No model calls.

M1 = random intercepts only (the earlier draft); M2 = random slope by category, persona fixed,
whose balanced-data equivalent is the per-category t-test (K - 1 df), also the pre-registered
fallback. Equivalence (TOST, margin +/-0.10) is the outcome that would support priming."""
import json, math
from pathlib import Path
import numpy as np
from scipy import stats
import power as P

HERE = Path(__file__).resolve().parent
P.rng = np.random.default_rng(20261011)


def contrast_m1(y, a, b):
    K, Pn, C, R = y.shape
    est = y[:, :, a].mean() - y[:, :, b].mean()
    gm = y.mean()
    res = (y - gm - (y.mean((1, 2, 3))[:, None, None, None] - gm) - (y.mean((0, 2, 3))[None, :, None, None] - gm)
           - (y.mean((0, 1, 3))[None, None, :, None] - gm))
    s2 = (res ** 2).sum() / (y.size - (1 + (K - 1) + (Pn - 1) + (C - 1)))
    se = math.sqrt(s2 * 2 / (K * Pn * R))
    return est, se


def contrast_m2(y, a, b):
    d = y[:, :, a].mean((1, 2)) - y[:, :, b].mean((1, 2))
    return d.mean(), d.std(ddof=1) / math.sqrt(len(d)), len(d) - 1


def run(K, R, delta_B, scen, nsim=3000):
    out = {"M1": {"0.05": 0, "0.0125": 0, "eq": 0}, "M2": {"0.05": 0, "0.0125": 0, "eq": 0}}
    for _ in range(nsim):
        y = P.simulate(K, R, 0.0, delta_B, **scen)  # reversed = placebo + 0; full = placebo + delta_B
        e1, s1 = contrast_m1(y, 1, 2)
        e2, s2, df = contrast_m2(y, 1, 2)
        for a in (0.05, 0.0125):
            out["M1"][str(a)] += abs(e1 / s1) > stats.norm.isf(a / 2)
            out["M2"][str(a)] += abs(e2 / s2) > stats.t.isf(a / 2, df)
        out["M1"]["eq"] += (e1 - .1) / s1 < -stats.norm.isf(.0125) and (e1 + .1) / s1 > stats.norm.isf(.0125)
        out["M2"]["eq"] += (e2 - .1) / s2 < -stats.t.isf(.0125, df) and (e2 + .1) / s2 > stats.t.isf(.0125, df)
    return {m: {k: v / nsim for k, v in d.items()} for m, d in out.items()}


if __name__ == "__main__":
    res = {"note": __doc__, "grid": {}}
    for name, sc in P.SCEN.items():
        for (K, R) in ((72, 1), (24, 3)):
            if (K, R) == (24, 3) and name not in ("S2 first-study-like", "S3 pessimistic"):
                continue
            for d in (0.0, 0.05, 0.10, 0.15, 0.20, 0.30):
                r = run(K, R, d, sc)
                res["grid"][f"{name}|K={K}|R={R}|B={d:.2f}"] = r
                print(name, K, R, d, r, flush=True)
    (HERE / "power_testB.json").write_text(json.dumps(res, indent=1) + "\n")
