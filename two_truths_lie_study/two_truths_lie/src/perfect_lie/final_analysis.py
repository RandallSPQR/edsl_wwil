"""Pre-registered final analysis (PREREG revision 3, sections 3-10; brief §8 items 29-31; owner
instruction of 2026-10-08).

Unblinded. Every function here reports estimates; nothing in this module is used by the blinded
interim. Run only after the owner confirms the code is registered (OSF Addendum 2 references the
commit that holds this file).

Contents
- primary(): per-model decision, direction, naive mean, SE, 95% CI, repeated CI, Z.
- stagewise_mue(): median-unbiased estimate and 95% CI under stagewise ordering.
- conditional_mue(): additional, not pre-registered. Median-unbiased given the observed stopping
  stage, as a check on winner's-curse inflation after an early stop.
- mixed_model(): d ~ 1 + (1 | prompt), REML, per model (robustness, PREREG section 4).
- sensitivity analyses: flagged cues dropped (PREREG 6), pooled gate (PREREG 6), non-viable lies
  excluded (item 29, "added post-registration, before data").
- tipping_point(): for the failed cells, how adverse the missing units must be to reverse each
  decision (owner instruction).
- gpt5_robustness(): agreement with the primary grader, and the primary test on gpt-5 annotations
  (PREREG 8).
- p4_secondary(): PREREG 7.
- secondaries(): PREREG 10 items 1-6 on the balanced replicates 1-15.
- empty_cue_breakdown(): the units dropped for an empty placebo-net cue set, by persona x model.
"""

from __future__ import annotations

import math
import random
from collections import Counter, defaultdict
from typing import Dict, Iterable, List, Optional, Sequence

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm

from . import sequential as sq
from .scoring import confession, degenerate_tail, tailoring_score

BALANCED = range(1, 16)
SEED = 20261006


# ------------------------------------------------------------------ small helpers

def _summ(d: Sequence[float]) -> Dict:
    d = np.asarray(d, float)
    n = len(d)
    if n < 2:
        return {"n": n, "mean": float(d.mean()) if n else None, "se": None, "ci95": None, "z": None}
    m, sd = float(d.mean()), float(d.std(ddof=1))
    se = sd / math.sqrt(n)
    return {"n": n, "mean": m, "sd": sd, "se": se, "ci95": [m - 1.96 * se, m + 1.96 * se],
            "z": (m / se) if se > 0 else None}


def _boot_ci(fn, idx: Sequence, n_boot: int = 2000, seed: int = SEED) -> Optional[List[float]]:
    rng = np.random.default_rng(seed)
    idx = list(idx)
    vals = []
    for _ in range(n_boot):
        s = [idx[i] for i in rng.integers(0, len(idx), len(idx))]
        v = fn(s)
        if v is not None and np.isfinite(v):
            vals.append(v)
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))] if len(vals) > 50 else None


def _by_model(units: List[Dict], models: Sequence[str]) -> Dict[str, List[float]]:
    return {m: [u["d"] for u in units if u["model_id"] == m] for m in models}


# ------------------------------------------------------------------ stagewise inference

def _bounds(alpha: float):
    return sq.efficacy_bounds(alpha)


def _p_stagewise(theta: float, stage: int, z_obs: float, i1: float, i2: Optional[float], c1: float) -> float:
    """P_theta(outcome at least as large as observed) under stagewise ordering, two-sided interim
    boundary +/- c1. Larger = stop at stage 1 high, then stage-2 outcomes by Z2, then stop low."""
    mu1 = theta * math.sqrt(i1)
    if stage == 1:
        return float(norm.sf(z_obs - mu1))
    mu2 = theta * math.sqrt(i2)
    r = math.sqrt(i1 / i2)
    from scipy.stats import multivariate_normal
    mvn = multivariate_normal(mean=[mu1, mu2], cov=[[1, r], [r, 1]])
    p_high = norm.sf(c1 - mu1)
    # P(-c1 < Z1 < c1, Z2 >= z_obs)
    p_mid = (norm.cdf(c1 - mu1) - norm.cdf(-c1 - mu1)) - (mvn.cdf([c1, z_obs]) - mvn.cdf([-c1, z_obs]))
    return float(p_high + p_mid)


def stagewise_mue(stage: int, z_obs: float, n1: int, n2: Optional[int], sd: float, c1: float,
                  conf: float = 0.95) -> Dict:
    """Median-unbiased estimate and CI (in units of mean d) under stagewise ordering. sd is the
    plug-in SD of d at the analysis look. For a stop at the first look this equals the naive
    estimate and the fixed-sample CI."""
    i1 = n1 / sd ** 2
    i2 = (n2 / sd ** 2) if n2 else None
    f = lambda th, target: _p_stagewise(th, stage, z_obs, i1, i2, c1) - target
    se_last = sd / math.sqrt(n2 if stage == 2 else n1)
    lo, hi = -50 * se_last + (z_obs * se_last), 50 * se_last + (z_obs * se_last)
    a = (1 - conf) / 2
    est = brentq(lambda t: f(t, 0.5), lo, hi)
    l = brentq(lambda t: f(t, a), lo, hi)
    u = brentq(lambda t: f(t, 1 - a), lo, hi)
    return {"mue": est, "ci": [l, u]}


def conditional_mue(z_obs: float, n1: int, sd: float, c1: float, conf: float = 0.95) -> Dict:
    """ADDITIONAL, not pre-registered. Median-unbiased given the trial stopped at the interim in the
    observed direction: solves P_mu(Z1 >= |z| | Z1 >= c1) = 0.5 on the z scale (log survival
    functions avoid underflow), then converts mu to the d scale."""
    sgn = 1.0 if z_obs > 0 else -1.0
    z = abs(z_obs)
    i1 = n1 / sd ** 2

    def g(mu, target):
        return math.exp(norm.logsf(z - mu) - norm.logsf(c1 - mu)) - target
    lo, hi = -60.0, z + 60.0
    a = (1 - conf) / 2
    try:
        est = brentq(lambda m: g(m, 0.5), lo, hi)
        l = brentq(lambda m: g(m, a), lo, hi)
        u = brentq(lambda m: g(m, 1 - a), lo, hi)
    except ValueError:
        # Z only just past the boundary: P(Z1 >= z | stop) stays near 1 for every effect size, so
        # no conditional median exists (the lower bound is unbounded). Reported, not hidden.
        return {"mue": None, "ci": None, "note": "not identified: observed Z too close to the stopping boundary"}
    to_d = lambda m: sgn * m / math.sqrt(i1)
    return {"mue": to_d(est), "ci": sorted([to_d(l), to_d(u)])}


# ------------------------------------------------------------------ primary

def primary(units: List[Dict], models: Sequence[str]) -> Dict:
    fa = sq.final_analysis(units, models)
    out = {}
    for m in models:
        r = dict(fa["models"][m])
        has_extension = any(u["model_id"] == m and u["replicate"] not in sq.INTERIM_REPLICATES for u in units)
        if r["interim_decision"] == "extend" and not has_extension:
            # The rules say extend, but no extension data exist: no final look is taken.
            d = [u["d"] for u in units if u["model_id"] == m]
            s = _summ(d)
            out[m] = {"decision": "extend (extension not run)", "direction": None, "look": "interim",
                      "n_units": s["n"], "mean_lift": s["mean"], "sd": s.get("sd"), "se": s["se"], "z": s["z"],
                      "ci95_naive": s["ci95"], "interim_decision": "extend",
                      "note": "descriptive only; no stopping decision is made without the extension"}
            continue
        d = [u["d"] for u in units if u["model_id"] == m]
        if r["look"] == "final":
            d1 = [u["d"] for u in units if u["model_id"] == m and u["replicate"] in sq.INTERIM_REPLICATES]
            n1, n2 = len(d1), len(d)
        else:
            n1, n2 = len(d), None
        alpha_used = _alpha_at_decision(units, models, m)
        c1, c2 = _bounds(alpha_used)
        se, mean, sd = r["se"], r["mean_lift"], r["sd"]
        r["ci95_naive"] = [mean - 1.96 * se, mean + 1.96 * se]
        cbound = c1 if r["look"] == "interim" else c2
        r["repeated_ci"] = {"local_alpha": alpha_used, "multiplier": cbound,
                            "ci": [mean - cbound * se, mean + cbound * se]}
        r["boundary_at_decision"] = cbound
        stage = 1 if r["look"] == "interim" else 2
        z_for_order = r["z"] if stage == 1 else mean / se
        r["stagewise"] = stagewise_mue(stage, z_for_order, n1, n2, sd, c1)
        r["conditional_mue_additional"] = conditional_mue(r["z"], n1, sd, c1) if stage == 1 else None
        out[m] = r
    return {"models": out, "alpha_after_interim": fa["alpha_after_interim"], "alpha_final": fa["alpha_final"]}


def _alpha_at_decision(units: List[Dict], models: Sequence[str], target: str) -> float:
    """Local efficacy alpha at which `target` was decided, replaying the Holm sequence."""
    d = {m: [u["d"] for u in units if u["model_id"] == m and u["replicate"] in sq.INTERIM_REPLICATES] for m in models}
    st = sq.new_state(models)
    eff = st["eff_alpha"]
    changed = True
    while changed:
        changed = False
        for m in models:
            if st["decision"].get(m) == "belief-tracking":
                continue
            if abs(sq._z(d[m])) >= sq.efficacy_bounds(eff[m])[0]:
                st["decision"][m] = "belief-tracking"
                if m == target:
                    return eff[m]
                sq._split(eff, m, [x for x in eff if st["decision"].get(x) is None])
                changed = True
    return eff[target]


# ------------------------------------------------------------------ mixed model

def mixed_model(units: List[Dict], models: Sequence[str]) -> Dict:
    import pandas as pd
    import statsmodels.formula.api as smf
    import warnings
    out = {}
    for m in models:
        df = pd.DataFrame([{"d": u["d"], "prompt": u["prompt_id"]} for u in units if u["model_id"] == m])
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fit = smf.mixedlm("d ~ 1", df, groups=df["prompt"]).fit(reml=True)
            b, se = float(fit.params["Intercept"]), float(fit.bse["Intercept"])
            out[m] = {"n": len(df), "intercept": b, "se": se, "z": b / se, "ci95": [b - 1.96 * se, b + 1.96 * se],
                      "prompt_variance": float(fit.cov_re.iloc[0, 0]), "converged": bool(fit.converged)}
        except Exception as e:  # reported, not hidden
            out[m] = {"n": len(df), "error": f"{type(e).__name__}: {e}"}
    return out


# ------------------------------------------------------------------ sensitivity analyses

def pooled_kappa(records: Iterable[Dict], cues: Sequence[str]) -> float:
    a, b = [], []
    for r in records:
        g = r.get("grades") or {}
        if g.get("primary") and g.get("google"):
            for c in cues:
                a.append(bool(g["primary"]["cues"][c])); b.append(bool(g["google"]["cues"][c]))
    return sq._kappa(np.array(a), np.array(b))


def sensitivity(records: List[Dict], inst, gate: Dict, models: Sequence[str], base_scorable: Sequence[str]) -> Dict:
    out = {}
    # S1: drop flagged (<30 positives) cues
    flagged = gate["flagged"]
    if flagged:
        sc = [c for c in base_scorable if c not in flagged]
        ul = sq.unit_lifts(records, inst, sc, sq.primary_pool(inst, sc))
        out["drop_flagged_cues"] = {"dropped": flagged, "models": {m: _summ(v) for m, v in _by_model(ul["units"], models).items()}}
    else:
        out["drop_flagged_cues"] = {"dropped": [], "note": "no cue was flagged at the interim; identical to the primary analysis"}
    # S2: all scorable cues under a pooled gate
    all_sc = sq.scorable_cues(inst)
    pk = pooled_kappa(records, all_sc)
    s2 = {"pooled_kappa": pk, "threshold": 0.70}
    if pk >= 0.70:
        ul = sq.unit_lifts(records, inst, all_sc, sq.primary_pool(inst, all_sc))
        s2["cues"] = all_sc
        s2["pool"] = sq.primary_pool(inst, all_sc)
        s2["models"] = {m: _summ(v) for m, v in _by_model(ul["units"], models).items()}
    else:
        s2["note"] = "pooled kappa below 0.70: the pooled-gate analysis keeps no cue set"
    out["pooled_gate_all_scorable"] = s2
    # S3: non-viable lies excluded (added post-registration, before data)
    pool = sq.primary_pool(inst, base_scorable)
    ul = sq.unit_lifts(records, inst, base_scorable, pool, exclude_nonviable=True)
    out["nonviable_excluded_added_post_registration_before_data"] = {
        "units_dropped": ul["excluded"]["nonviable"],
        "models": {m: _summ(v) for m, v in _by_model(ul["units"], models).items()}}
    out["nonviable_counts_by_condition"] = sq.nonviable_counts(records)
    return out


# ------------------------------------------------------------------ tipping point

def missing_units(all_records: List[Dict], inst, scorable: Sequence[str], pool: Sequence[str]) -> List[Dict]:
    """Units (liar, prompt, target, replicate) with a non-empty cue set that could not be scored
    because a lie failed or is missing. Confessed units are not counted here."""
    rows = {r.prompt_id: r for r in inst.design}
    cells: Dict[tuple, Dict[str, Dict]] = {}
    for r in all_records:
        if r.get("condition") in ("full", "placebo") and r.get("target_id") in pool:
            cells.setdefault((r["model_id"], r["prompt_id"], r["target_id"], r["replicate"]), {})[r["condition"]] = r
    out = []
    for (m, p, t, rep), pair in cells.items():
        if not sq.note_named(inst, rows[p], t, scorable):
            continue
        ok = all(c in pair and pair[c].get("status") == "complete" and (pair[c].get("grades") or {}).get("primary")
                 for c in ("full", "placebo"))
        if not ok:
            out.append({"model_id": m, "prompt_id": p, "target_id": t, "replicate": rep})
    return out


def tipping_point(units: List[Dict], missing: List[Dict], models: Sequence[str], prim: Dict) -> Dict:
    """For each model decided for efficacy: the common value delta that every missing unit would
    need to take (d is bounded in [-1, 1]) for |Z| to fall below the boundary at which the model
    was decided. Also reports delta for the boundary at the starting local alpha 0.0125."""
    out = {}
    for m in models:
        d = np.array([u["d"] for u in units if u["model_id"] == m], float)
        k = sum(1 for x in missing if x["model_id"] == m)
        r = prim["models"][m]
        res = {"observed_units": len(d), "missing_units": k, "decision": r["decision"], "direction": r.get("direction")}
        if r["decision"] != "belief-tracking" or k == 0:
            res["note"] = "no efficacy decision to reverse" if r["decision"] != "belief-tracking" else "no missing units"
            out[m] = res
            continue
        sgn = 1.0 if r["direction"] == "positive" else -1.0

        def zfill(delta):
            x = np.concatenate([d, np.full(k, delta)])
            return sgn * x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))
        for label, bound in (("at_decision_boundary", r["boundary_at_decision"]),
                             ("at_boundary_local_0.0125", sq.efficacy_bounds(0.0125)[0 if r["look"] == "interim" else 1])):
            worst, best = -sgn * 1.0, sgn * 1.0
            if zfill(best) < bound:
                res[label] = {"boundary": bound, "delta": None, "reversible": None,
                              "note": "Z stays below this boundary even if every missing unit is maximally favourable"}
            elif zfill(worst) >= bound:
                res[label] = {"boundary": bound, "delta": None, "z_if_all_missing_at_worst": float(zfill(worst)),
                              "reversible": False}
            else:
                delta = brentq(lambda t: zfill(t) - bound, worst, best)
                res[label] = {"boundary": bound, "delta": float(delta), "reversible": True,
                              "z_if_all_missing_at_worst": float(zfill(worst))}
        out[m] = res
    return out


# ------------------------------------------------------------------ gpt-5 robustness

def gpt5_robustness(records: List[Dict], inst, scorable: Sequence[str], models: Sequence[str]) -> Dict:
    sub = [r for r in records if (r.get("grades") or {}).get("secondary") and (r.get("grades") or {}).get("primary")]
    agree = {}
    for c in sq.scorable_cues(inst):
        a = np.array([bool(r["grades"]["primary"]["cues"][c]) for r in sub])
        b = np.array([bool(r["grades"]["secondary"]["cues"][c]) for r in sub])
        agree[c] = {"kappa": sq._kappa(a, b), "ac1": sq._ac1(a, b), "positives": int((a | b).sum())}
    a = np.array([bool(r["grades"]["primary"]["cues"][c]) for r in sub for c in scorable])
    b = np.array([bool(r["grades"]["secondary"]["cues"][c]) for r in sub for c in scorable])
    ul = sq.unit_lifts(records, inst, scorable, sq.primary_pool(inst, scorable), grader="secondary")
    return {"lies_in_subsample": len(sub), "agreement_per_cue": agree,
            "pooled": {"kappa": sq._kappa(a, b), "ac1": sq._ac1(a, b)},
            "primary_test_on_gpt5_annotations": {m: _summ(v) for m, v in _by_model(ul["units"], models).items()},
            "note": "low-powered by design (about 1 unit in 16); read for sign and rough size only"}


# ------------------------------------------------------------------ P4

def p4_secondary(records: List[Dict], inst, scorable: Sequence[str], models: Sequence[str]) -> Dict:
    ul = sq.unit_lifts(records, inst, scorable, ["P4"], personas_override=["P4"])
    p4_cues = [c for c in inst.personas["P4"].cues if c in set(scorable)]
    return {"p4_scorable_cues": p4_cues, "excluded": ul["excluded"],
            "models": {m: _summ(v) for m, v in _by_model(ul["units"], models).items()}}


# ------------------------------------------------------------------ secondaries (balanced replicates 1-15)

def _acc(r: Dict) -> Optional[float]:
    t = r.get("targets") or {}
    v = [bool(x["accept"]) for x in t.values() if "accept" in x]
    return sum(v) / len(v) if v else None


def _pairs(records: List[Dict], pool: Sequence[str], conds=("full", "placebo")) -> Dict[tuple, Dict[str, Dict]]:
    cells: Dict[tuple, Dict[str, Dict]] = {}
    for r in records:
        if r.get("status") == "complete" and r.get("condition") in conds and r.get("target_id") in pool \
                and r.get("replicate") in BALANCED and not confession(r.get("lie") or ""):
            cells.setdefault((r["model_id"], r["prompt_id"], r["target_id"], r["replicate"]), {})[r["condition"]] = r
    return cells


def _share(cues: Dict, named: Sequence[str]) -> float:
    return sum(bool(cues[c]) for c in named) / len(named)


def secondaries(records: List[Dict], inst, scorable: Sequence[str], models: Sequence[str]) -> Dict:
    recs = [r for r in records if r.get("status") == "complete" and r.get("replicate") in BALANCED]
    pool = sq.primary_pool(inst, scorable)
    rows = {r.prompt_id: r for r in inst.design}
    cat = {p.id: p.category for p in inst.prompts}
    out: Dict = {"window": "replicates 1-15, all four models (balanced)"}

    # 1. lift by category
    ul = sq.unit_lifts(recs, inst, scorable, pool)["units"]
    by = defaultdict(list); pooled = defaultdict(list)
    for u in ul:
        by[(u["model_id"], cat[u["prompt_id"]])].append(u["d"]); pooled[cat[u["prompt_id"]]].append(u["d"])
    out["1_lift_by_category"] = {"by_model": {f"{m}|{c}": _summ(v) for (m, c), v in sorted(by.items())},
                                 "pooled_over_models": {c: _summ(v) for c, v in sorted(pooled.items())}}

    # 2. judge acceptance by cue (lie-level acceptance = mean over the four judges)
    acc_rows = [(r, _acc(r)) for r in recs if _acc(r) is not None and r["grades"].get("primary")]
    cue_acc = {}
    for c in sq.scorable_cues(inst):
        on = [a for r, a in acc_rows if r["grades"]["primary"]["cues"][c]]
        off = [a for r, a in acc_rows if not r["grades"]["primary"]["cues"][c]]
        if len(on) > 1 and len(off) > 1:
            diff = float(np.mean(on) - np.mean(off))
            se = math.sqrt(np.var(on, ddof=1) / len(on) + np.var(off, ddof=1) / len(off))
            cue_acc[c] = {"n_present": len(on), "n_absent": len(off), "acc_present": float(np.mean(on)),
                          "acc_absent": float(np.mean(off)), "diff": diff, "ci95": [diff - 1.96 * se, diff + 1.96 * se]}
    out["2_acceptance_by_cue"] = cue_acc

    # 3. liar x judge 4 x 4 and the family diagonal
    mat = defaultdict(list)
    fam = {}
    for r in recs:
        fam[r["model_id"]] = r["model_family"]
        for jid, t in (r.get("targets") or {}).items():
            mat[(r["model_id"], jid)].append(bool(t["accept"]))
            fam.setdefault(jid, t.get("family"))
    m4 = {f"{a} -> {b}": {"n": len(v), "accept_rate": sum(v) / len(v)} for (a, b), v in sorted(mat.items())}
    same = [x for (a, b), v in mat.items() if fam.get(a) == fam.get(b) for x in v]
    other = [x for (a, b), v in mat.items() if fam.get(a) != fam.get(b) for x in v]
    same_model = [x for (a, b), v in mat.items() if a == b for x in v]
    other_model = [x for (a, b), v in mat.items() if a != b for x in v]
    out["3_liar_x_judge"] = {"matrix": m4,
                             "same_family_minus_other": (np.mean(same) - np.mean(other)) if same and other else None,
                             "same_model_minus_other": (np.mean(same_model) - np.mean(other_model)) if same_model and other_model else None,
                             "n_same_family": len(same), "n_other_family": len(other)}

    # 4. IV (Wald ratio): note -> cue use -> acceptance, per model, bootstrap over units
    pairs = _pairs(recs, pool)
    unit_rows = defaultdict(list)
    for (m, p, t, rep), pr in pairs.items():
        if "full" in pr and "placebo" in pr:
            named = sq.note_named(inst, rows[p], t, scorable)
            if not named:
                continue
            af, ap = _acc(pr["full"]), _acc(pr["placebo"])
            if af is None or ap is None:
                continue
            ds = _share(pr["full"]["grades"]["primary"]["cues"], named) - _share(pr["placebo"]["grades"]["primary"]["cues"], named)
            unit_rows[m].append((ds, af - ap))
    iv = {}
    for m in models:
        rr = unit_rows[m]
        if not rr:
            continue
        def wald(s):
            num = np.mean([rr[i][1] for i in s]); den = np.mean([rr[i][0] for i in s])
            return num / den if abs(den) > 1e-9 else None
        est = wald(range(len(rr)))
        iv[m] = {"n_units": len(rr), "first_stage_mean_ds": float(np.mean([x[0] for x in rr])),
                 "reduced_form_mean_dacc": float(np.mean([x[1] for x in rr])), "wald": est,
                 "ci95_bootstrap": _boot_ci(wald, range(len(rr)))}
    out["4_iv_wald"] = {"models": iv, "caveat": "exclusion restriction (the note changes acceptance only through the named cues) is doubtful"}

    # 5. stated B-hat
    out["5_bhat"] = _bhat(recs, pairs, inst, rows, scorable, models)

    # 6. directional T by condition, and none-vs-placebo
    out["6_T_and_none_vs_placebo"] = _t_and_none(recs, inst, rows, scorable, pool, models)
    return out


def _bhat(recs, pairs, inst, rows, scorable, models) -> Dict:
    out = {}
    # manipulation check: B-hat share of note-named cues, full minus placebo, per unit
    man = defaultdict(list)
    med = defaultdict(list)  # (unit, dB, dS) for mediation
    for (m, p, t, rep), pr in pairs.items():
        if "full" in pr and "placebo" in pr and all((pr[c].get("bhat_grades") or {}).get("primary") for c in pr):
            named = sq.note_named(inst, rows[p], t, scorable)
            if not named:
                continue
            bf = _share(pr["full"]["bhat_grades"]["primary"]["cues"], named)
            bp = _share(pr["placebo"]["bhat_grades"]["primary"]["cues"], named)
            sf = _share(pr["full"]["grades"]["primary"]["cues"], named)
            sp = _share(pr["placebo"]["grades"]["primary"]["cues"], named)
            man[m].append(bf - bp)
            med[m].append((bf - bp, sf - sp, bf, bp, sf, sp))
    out["manipulation_check_bhat_full_minus_placebo"] = {m: _summ(v) for m, v in man.items()}

    # tracking: per-lie Jaccard between B-hat and story cue sets (scorable cues), vs shuffled pairs
    track = {}
    rng = random.Random(SEED)
    for m in models:
        for cond in ("none", "placebo", "full"):
            lies = [r for r in recs if r["model_id"] == m and r["condition"] == cond
                    and (r.get("bhat_grades") or {}).get("primary") and r["grades"].get("primary")]
            if len(lies) < 3:
                continue
            def jac(b, s):
                B = {c for c in scorable if b[c]}; S = {c for c in scorable if s[c]}
                return len(B & S) / len(B | S) if (B | S) else 0.0
            obs = [jac(r["bhat_grades"]["primary"]["cues"], r["grades"]["primary"]["cues"]) for r in lies]
            perm = lies[:]; rng.shuffle(perm)
            base = [jac(a["bhat_grades"]["primary"]["cues"], b["grades"]["primary"]["cues"]) for a, b in zip(lies, perm)]
            diff = [o - b for o, b in zip(obs, base)]
            track[f"{m}|{cond}"] = {"n": len(lies), "observed_jaccard": float(np.mean(obs)),
                                    "shuffled_baseline": float(np.mean(base)), "difference": _summ(diff)}
    out["tracking_bhat_vs_story_cue_overlap"] = track

    # mediation: note -> B-hat -> cue use, unit level. a = mean dB; b = slope of story share on
    # B-hat share within unit (unit fixed effects) controlling for condition; indirect = a*b.
    medi = {}
    for m, rows_ in med.items():
        if len(rows_) < 10:
            continue
        def ind(s):
            sub = [rows_[i] for i in s]
            a = np.mean([x[0] for x in sub])
            # within-unit: dS = tau + b*dB  (differencing removes the unit effect)
            dB = np.array([x[0] for x in sub]); dS = np.array([x[1] for x in sub])
            X = np.column_stack([np.ones_like(dB), dB])
            coef, *_ = np.linalg.lstsq(X, dS, rcond=None)
            return a * coef[1]
        idx = range(len(rows_))
        dB = np.array([x[0] for x in rows_]); dS = np.array([x[1] for x in rows_])
        coef, *_ = np.linalg.lstsq(np.column_stack([np.ones_like(dB), dB]), dS, rcond=None)
        medi[m] = {"n_units": len(rows_), "a_note_to_bhat": float(dB.mean()), "b_bhat_to_story": float(coef[1]),
                   "direct_tau": float(coef[0]), "indirect": float(dB.mean() * coef[1]),
                   "indirect_ci95_bootstrap": _boot_ci(ind, idx)}
    out["mediation"] = {"models": medi, "caveat": "the stated B-hat follows the story and may rationalize it"}

    # echo / refusal / breakdown by model x condition
    flags = defaultdict(Counter)
    for r in recs:
        f = (r.get("elicitation") or {}).get("flags") or {}
        k = f"{r['model_id']}|{r['condition']}"
        flags[k]["n"] += 1
        for x in ("echo", "refusal", "breakdown"):
            flags[k][x] += bool(f.get(x))
    out["elicitation_flags"] = {k: dict(v) for k, v in sorted(flags.items())}
    return out


def _t_and_none(recs, inst, rows, scorable, pool, models) -> Dict:
    # T per (model, prompt, condition, replicate), across the pair's two targets
    by = defaultdict(dict)
    for r in recs:
        if not confession(r.get("lie") or "") and r["grades"].get("primary"):
            by[(r["model_id"], r["prompt_id"], r["condition"], r["replicate"])][r["target_id"]] = r
    T = defaultdict(list)
    excl = {c.id for c in inst.cues if c.id not in set(scorable)}
    for (m, p, cond, rep), pair in by.items():
        row = rows[p]
        if row.j1 in pair and row.j2 in pair:
            t, _ = tailoring_score(pair[row.j1]["grades"]["primary"]["cues"], pair[row.j2]["grades"]["primary"]["cues"],
                                   inst.personas[row.j1].cues, inst.personas[row.j2].cues, excl)
            T[(m, cond)].append(t)
    t_out = {f"{m}|{c}": _summ(v) for (m, c), v in sorted(T.items())}
    # none vs placebo: s(placebo) - s(none) on the target's placebo-net note-named cues
    cells = _pairs(recs, pool, conds=("none", "placebo"))
    npd = defaultdict(list)
    for (m, p, t, rep), pr in cells.items():
        if "none" in pr and "placebo" in pr:
            named = sq.note_named(inst, rows[p], t, scorable)
            if named:
                npd[m].append(_share(pr["placebo"]["grades"]["primary"]["cues"], named)
                              - _share(pr["none"]["grades"]["primary"]["cues"], named))
    return {"T_by_model_condition": t_out, "placebo_minus_none": {m: _summ(v) for m, v in npd.items()}}


# ------------------------------------------------------------------ bookkeeping

def empty_cue_breakdown(records: List[Dict], inst, scorable: Sequence[str], pool: Sequence[str]) -> Dict:
    rows = {r.prompt_id: r for r in inst.design}
    seen = set(); c = Counter(); detail = Counter()
    for r in records:
        if r.get("condition") in ("full", "placebo") and r.get("target_id") in pool:
            key = (r["model_id"], r["prompt_id"], r["target_id"], r["replicate"])
            if key in seen:
                continue
            seen.add(key)
            if not sq.note_named(inst, rows[r["prompt_id"]], r["target_id"], scorable):
                c[f"{r['target_id']}|{r['model_id']}"] += 1
                detail[f"{r['prompt_id']}|{r['target_id']}"] += 1
    return {"by_persona_x_model": dict(sorted(c.items())), "by_prompt_x_persona": dict(sorted(detail.items())),
            "total": sum(c.values())}


def failure_tables(all_records: List[Dict]) -> Dict:
    by = Counter((r["model_id"], r["condition"]) for r in all_records if r.get("status") == "error")
    deg = Counter(r["condition"] for r in all_records if r.get("status") == "complete" and degenerate_tail(r.get("lie") or ""))
    conf = Counter(r["condition"] for r in all_records if r.get("status") == "complete" and confession(r.get("lie") or ""))
    return {"failed_by_model_condition": {f"{m}|{c}": n for (m, c), n in sorted(by.items())},
            "degenerate_by_condition": dict(deg), "confessed_by_condition": dict(conf)}


def run_final(all_records: List[Dict], inst, models: Sequence[str]) -> Dict:
    complete = [r for r in all_records if r.get("status") == "complete"]
    gate = sq.agreement_gate(complete, sq.scorable_cues(inst))
    scorable = sq.scorable_cues(inst, gate["excluded"])
    pool = sq.primary_pool(inst, scorable)
    ul = sq.unit_lifts(complete, inst, scorable, pool)
    units = ul["units"]
    prim = primary(units, models)
    miss = missing_units(all_records, inst, scorable, pool)
    return {
        "gate": {"excluded": gate["excluded"], "flagged": gate["flagged"], "per_cue": gate["per_cue"], "lies": gate["n_lies"]},
        "scorable_cues": scorable, "primary_pool": pool, "units_excluded": ul["excluded"],
        "primary": prim,
        "mixed_model": mixed_model(units, models),
        "sensitivity": sensitivity(complete, inst, gate, models, scorable),
        "tipping_point": {"missing_units_total": len(miss), "models": tipping_point(units, miss, models, prim)},
        "gpt5_robustness": gpt5_robustness(complete, inst, scorable, models),
        "p4_secondary": p4_secondary(complete, inst, scorable, models),
        "secondaries": secondaries(complete, inst, scorable, models),
        "empty_cue_exclusions": empty_cue_breakdown(complete, inst, scorable, pool),
        "failures": failure_tables(all_records),
    }
