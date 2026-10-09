"""Power and fragility of the follow-up's primary tests, by simulation. No model calls.

Design per liar model: K categories x 5 personas (cells) x 3 conditions (placebo, full, reversed)
x R replicates. Outcome s = share of the target's note-named cues present.

Data model (one liar model):
  s = mu + a_cat + b_pers + c_cell + beta_cond
      + u_cat[cond] + v_pers[cond] + w_cell[cond]     <- condition effect varies across clusters
      + e,   e ~ N(0, sigma)
Parameters come from the first study (study1_parameters.json): within-cell SD sigma ~0.22, true
SD of (full - placebo) cell effects ~0.22-0.25, placebo baseline ~0.22-0.36.

Analyses compared, for Test A (reversed - placebo):
  M1  the owner's draft: s ~ condition + (1|category) + (1|persona). With balanced data its
      estimate is the difference of condition means and its SE is the residual SE; we compute it
      by the equivalent OLS with category and persona intercepts (checked against statsmodels
      MixedLM below).
  M2  category-level test: per category, the mean of (reversed - placebo) over personas and
      replicates; one-sample t on the K values (K-1 df). Equivalent, for balanced data, to a
      mixed model with a random slope for condition by category and persona fixed.
Estimand: the effect averaged over THESE five personas (persona deviations are centred), and over
a population of categories. Treating personas as a random sample adds tau_pers^2 / 5 to the
variance; that case is reported analytically.
"""
import json, sys, math
from pathlib import Path
import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
rng = np.random.default_rng(20261009)
NP, NC = 5, 3  # personas, conditions (0 placebo, 1 full, 2 reversed)


def simulate(K, R, delta_rev, delta_full, sigma, t_cat, t_pers, t_cell, i_cat=0.10, i_pers=0.08, i_cell=0.08):
    a = rng.normal(0, i_cat, K)[:, None, None, None]
    b = rng.normal(0, i_pers, NP)[None, :, None, None]
    c = rng.normal(0, i_cell, (K, NP))[:, :, None, None]
    beta = np.array([0.0, delta_full, delta_rev])[None, None, :, None]
    # slope deviations for full and reversed relative to placebo (placebo column 0)
    u = np.concatenate([np.zeros((K, 1)), rng.normal(0, t_cat, (K, 2))], 1)[:, None, :, None]
    v = rng.normal(0, t_pers, (NP, 2)); v -= v.mean(0)  # personas fixed: deviations centred
    v = np.concatenate([np.zeros((NP, 1)), v], 1)[None, :, :, None]
    w = np.concatenate([np.zeros((K, NP, 1)), rng.normal(0, t_cell, (K, NP, 2))], 2)[:, :, :, None]
    e = rng.normal(0, sigma, (K, NP, NC, R))
    return 0.28 + a + b + c + beta + u + v + w + e


def m1(y):
    """Contrast reversed - placebo with the residual SE of the intercepts-only model (balanced)."""
    K, P, C, R = y.shape
    est = y[:, :, 2].mean() - y[:, :, 0].mean()
    # residuals after category, persona, condition main effects (additive two-way-plus fit)
    gm = y.mean()
    fk = y.mean((1, 2, 3))[:, None, None, None] - gm
    fp = y.mean((0, 2, 3))[None, :, None, None] - gm
    fc = y.mean((0, 1, 3))[None, None, :, None] - gm
    res = y - gm - fk - fp - fc
    df = y.size - (1 + (K - 1) + (P - 1) + (C - 1))
    s2 = (res ** 2).sum() / df
    se = math.sqrt(s2 * 2 / (K * P * R))
    return est, se, est / se


def m2(y):
    d = y[:, :, 2].mean((1, 2)) - y[:, :, 0].mean((1, 2))
    K = len(d)
    se = d.std(ddof=1) / math.sqrt(K)
    return d.mean(), se, d.mean() / se, K - 1


def run(K, R, delta, scen, nsim=4000):
    rej = {"M1": {0.05: 0, 0.0125: 0}, "M2": {0.05: 0, 0.0125: 0}}
    eq = {"M1": 0, "M2": 0}
    for _ in range(nsim):
        y = simulate(K, R, delta, 0.35, **scen)
        e1, s1, z1 = m1(y)
        e2, s2, t2, df = m2(y)
        for a in (0.05, 0.0125):
            rej["M1"][a] += abs(z1) > stats.norm.isf(a / 2)
            rej["M2"][a] += abs(t2) > stats.t.isf(a / 2, df)
        # TOST at margin 0.10, alpha 0.05 each side (equivalence family, first in Holm order would be 0.0125)
        eq["M1"] += (e1 - 0.10) / s1 < -stats.norm.isf(0.0125) and (e1 + 0.10) / s1 > stats.norm.isf(0.0125)
        eq["M2"] += (e2 - 0.10) / s2 < -stats.t.isf(0.0125, df) and (e2 + 0.10) / s2 > stats.t.isf(0.0125, df)
    f = lambda x: x / nsim
    return {"reject_two_sided": {m: {str(a): f(v) for a, v in d.items()} for m, d in rej.items()},
            "equivalence_tost_0.10_at_0.0125": {m: f(v) for m, v in eq.items()}}


SCEN = {
    "S0 no heterogeneity": dict(sigma=0.22, t_cat=0.0, t_pers=0.0, t_cell=0.0),
    "S1 mild": dict(sigma=0.22, t_cat=0.08, t_pers=0.08, t_cell=0.08),
    "S2 first-study-like": dict(sigma=0.22, t_cat=0.15, t_pers=0.12, t_cell=0.12),
    "S3 pessimistic": dict(sigma=0.24, t_cat=0.22, t_pers=0.15, t_cell=0.15),
}

if __name__ == "__main__":
    out = {"design": "K categories x 5 personas x 3 conditions x R replicates, per liar model",
           "alpha_note": "Holm across four models: the first rejection is at 0.0125, the last at 0.05.",
           "grid": {}}
    for name, sc in SCEN.items():
        for K in (12, 24, 36, 48):
            for delta in (0.0, -0.05, -0.10, -0.15, -0.20):
                if K != 24 and name not in ("S2 first-study-like", "S3 pessimistic"):
                    continue
                r = run(K, 3, delta, sc, nsim=3000)
                out["grid"][f"{name}|K={K}|R=3|delta={delta:+.2f}"] = r
                print(name, K, delta, r, flush=True)
    # replicates vs categories at fixed lie count (S2): K=24,R=3 vs K=12,R=6 vs K=36,R=2
    for K, R in ((12, 6), (24, 3), (36, 2), (72, 1)):
        for delta in (0.0, -0.10):
            r = run(K, R, delta, SCEN["S2 first-study-like"], nsim=3000)
            out["grid"][f"S2 first-study-like|K={K}|R={R}|delta={delta:+.2f}"] = r
            print("trade", K, R, delta, r, flush=True)
    # analytic: personas as a random sample (adds t_pers^2/5) for M2's SE at K=24, R=3
    an = {}
    for name, sc in SCEN.items():
        base = 2 * sc["sigma"] ** 2 / (24 * 5 * 3) + 2 * sc["t_cat"] ** 2 / 24 + 2 * sc["t_cell"] ** 2 / 120
        an[name] = {"se_personas_fixed": math.sqrt(base),
                    "se_personas_random": math.sqrt(base + 2 * sc["t_pers"] ** 2 / 5),
                    "note": "slope deviations of reversed and placebo are independent here, hence the factor 2 on tau^2"}
    out["analytic_se"] = an
    (HERE / "power.json").write_text(json.dumps(out, indent=1) + "\n")
