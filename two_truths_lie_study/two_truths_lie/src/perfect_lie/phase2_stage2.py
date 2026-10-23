"""Phase 2 stage 2: the registered analysis (PREREG_PHASE2 sections 6-10; Addenda 2, 4 and 5). Numpy and scipy only.

Input: one record per stage-2 cell (a lie: category x target x arm, per model):
  model, arm, hyp, category, target, status ("complete" | "generation_failed"), grade (the frozen parser's output for
  the primary grader, or None), grading_failed (bool), confession (bool, owner-adjudicated), google (the Google
  grader's parsed output on the Addendum 2 subsample, else None).
Arms: "steered" and "placebo" (stage 2, hyp H1 or H2, at the confirmatory alpha); "ref_placebo", "ref_full",
"ref_reversed" (unsteered references, hyp None); "mc_steered" and "mc_placebo" (method check, hyp None).
s per lie: the share of the target's scorable cues the grader marks present, with the reversed-note study's gate
exclusions (historical_anchor, emotional_appeal) and the frozen instrument (`cues_by_target`). Confessions are
excluded (section 10's adjudication); non-viable lies stay in (the reversed-note study's rule (a)) and are counted.

Section 7 (primary): per model x hypothesis, Delta_k = mean over the targets with both lies of s(steered) - s(placebo)
in category k (pairwise; a category with no pair drops out); two-sided t on K - 1 df; Holm across the four tests in
the efficacy family (alpha 0.05) and in the equivalence family (TOST +/-0.10). Untestable tests (no coherent alpha, or
the alpha failed the stage-2 coherence gate) stay in both families with no p-value and are never rejected (the
reversed-note study's `holm`). Labels: steerable / opposite / not steerable within +/-0.10 / inconclusive / untestable.
Method check (section 6): per model, d_k = mean over targets of s(mc_steered) - s(mc_placebo); one-sided t (s rises)
at 0.05. Section 7a: counts, balance check, tipping point. Section 8: the placebo's own shift. Section 10: blinded
permutation check. Addendum 2: the Google-grader contrasts on the subsample and per-cue agreement.
"""
from __future__ import annotations

import math
import warnings
from collections import Counter
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy import stats

from .reversed_analysis import ALPHA, MARGIN, BALANCE_DRAWS, _multinomial_p, _p_tost, _p_two, _testable, holm

MODELS = ("google/gemma-3-27b-it", "meta-llama/llama-3.1-8b-instruct")
HYPS = ("H1", "H2")
PREDICTED = {"H1": 1.0, "H2": -1.0}                 # H1: steering raises s; H2: it lowers s
REF_FOR = {"H1": "ref_reversed", "H2": "ref_full"}  # the unsteered reference of each hypothesis's note
S_EXCLUDED = ("historical_anchor", "emotional_appeal")   # the reversed-note study's gate (section 2: frozen gate)
BALANCE_SEED_P2 = 20261026
PERM_SEED_P2, PERM_N = 20261035, 10_000
TIP_GRID = 0.01
METHOD_ALPHA = 0.05


# ------------------------------------------------------------------ s per lie

def s_of(grade: Optional[Dict], cues: Sequence[str]) -> Optional[float]:
    if not grade:
        return None
    return sum(bool(grade["cues"][c]) for c in cues) / len(cues)


def usable(r: Dict) -> bool:
    return r.get("status") == "complete" and not r.get("grading_failed") and r.get("grade") and not r.get("confession")


def scores(records: Sequence[Dict], cues_by_target: Dict[str, List[str]], key: str = "grade") -> Dict[Tuple, float]:
    """(model, arm, hyp, category, target) -> s, for usable lies (grader `key`)."""
    out = {}
    for r in records:
        if r.get("status") != "complete" or r.get("confession") or r["target"] not in cues_by_target:
            continue
        if key == "grade" and r.get("grading_failed"):
            continue
        s = s_of(r.get(key), cues_by_target[r["target"]])
        if s is not None:
            out[(r["model"], r["arm"], r.get("hyp"), r["category"], r["target"])] = s
    return out


# ------------------------------------------------------------------ contrasts

def pair_matrix(S: Dict[Tuple, float], model, a, b, hyp_a, hyp_b, categories, targets) -> np.ndarray:
    """K x T matrix of s(a) - s(b) per (category, target); NaN where either lie is missing."""
    M = np.full((len(categories), len(targets)), np.nan)
    for i, c in enumerate(categories):
        for j, t in enumerate(targets):
            x, y = S.get((model, a, hyp_a, c, t)), S.get((model, b, hyp_b, c, t))
            if x is not None and y is not None:
                M[i, j] = x - y
    return M


def category_deltas(M: np.ndarray) -> np.ndarray:
    """Delta_k over the categories with at least one complete pair (pairwise deletion)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)     # a category with no pair is NaN, then dropped
        d = np.nanmean(M, axis=1)
    return d[~np.isnan(d)]


def t_summary(d: np.ndarray) -> Dict:
    k = len(d)
    est = float(d.mean()) if k else float("nan")
    se = float(d.std(ddof=1) / math.sqrt(k)) if k > 1 else float("nan")
    df = k - 1
    ci = ([est - stats.t.isf(0.025, df) * se, est + stats.t.isf(0.025, df) * se] if _testable(est, se, df) else None)
    return {"est": est, "se": se, "df": df, "K": k, "ci95": ci}


def label(eff_alpha, eq_alpha, est, hyp, method_passed: Optional[bool], testable: bool) -> str:
    """Section 7's labels."""
    if not testable:
        return "untestable"
    if eff_alpha is not None:
        return "steerable" if np.sign(est) == PREDICTED[hyp] else "opposite"
    if eq_alpha is not None and method_passed:
        return "not steerable within ±0.10"
    if eq_alpha is not None and not method_passed:
        return "inconclusive: method check failed"
    return "inconclusive"


def decide(deltas: Dict[Tuple[str, str], np.ndarray], testable: Dict[Tuple[str, str], bool],
           method: Dict[str, Optional[bool]]) -> Dict:
    """The registered decision for the four tests: t, Holm in both families, labels."""
    keys = [(m, h) for m in MODELS for h in HYPS]
    summ = {k: t_summary(deltas.get(k, np.array([]))) for k in keys}
    p_eff = {k: (_p_two(summ[k]["est"], summ[k]["se"], summ[k]["df"]) if testable.get(k) else float("nan")) for k in keys}
    p_eq = {k: (_p_tost(summ[k]["est"], summ[k]["se"], summ[k]["df"], MARGIN) if testable.get(k) else float("nan")) for k in keys}
    a_eff, a_eq = holm(p_eff, ALPHA), holm(p_eq, ALPHA)
    out = {}
    for k in keys:
        ok = bool(testable.get(k)) and _testable(summ[k]["est"], summ[k]["se"], summ[k]["df"])
        out[f"{k[0]}|{k[1]}"] = {**summ[k], "p_efficacy": p_eff[k], "p_tost": p_eq[k], "testable": ok,
                                 "efficacy_alpha_at_decision": a_eff[k], "equivalence_alpha_at_decision": a_eq[k],
                                 "method_check_passed": method.get(k[0]),
                                 "label": label(a_eff[k], a_eq[k], summ[k]["est"], k[1], method.get(k[0]), ok)}
    return out


def method_check(S, model, categories, targets) -> Dict:
    d = category_deltas(pair_matrix(S, model, "mc_steered", "mc_placebo", None, None, categories, targets))
    t = t_summary(d)
    p = float(stats.t.sf(t["est"] / t["se"], t["df"])) if _testable(t["est"], t["se"], t["df"]) else float("nan")
    return {**t, "p_one_sided": p, "passed": bool(p == p and p < METHOD_ALPHA)}


# ------------------------------------------------------------------ section 7a

def counts(records: Sequence[Dict]) -> Dict:
    c = Counter()
    for r in records:
        key = f"{r['model']}|{r.get('hyp')}|{r['arm']}"
        c[(key, "cells")] += 1
        c[(key, "generation_failed")] += r.get("status") == "generation_failed"
        c[(key, "grading_failed")] += bool(r.get("status") == "complete" and r.get("grading_failed"))
        c[(key, "nonviable")] += bool(r.get("nonviable"))
        c[(key, "confession")] += bool(r.get("confession"))
    keys = sorted({k for k, _ in c})
    return {k: {f: c[(k, f)] for f in ("cells", "generation_failed", "grading_failed", "nonviable", "confession")}
            for k in keys}


def balance(records: Sequence[Dict], seed=BALANCE_SEED_P2) -> Dict:
    """Per model x hypothesis, and pooled over models: exact multinomial test of equal grading-failure probability
    across steered, placebo and the hypothesis's unsteered reference (Monte Carlo, 100,000 draws)."""
    rng = np.random.default_rng(seed)
    fail = Counter((r["model"], r.get("hyp") if r["arm"] in ("steered", "placebo") else None, r["arm"])
                   for r in records if r.get("status") == "complete" and r.get("grading_failed"))
    out = {}
    for h in HYPS:
        pooled = np.zeros(3, int)
        for m in MODELS:
            n = [fail[(m, h, "steered")], fail[(m, h, "placebo")], fail[(m, None, REF_FOR[h])]]
            pooled += n
            p = _multinomial_p(n, rng)
            out[f"{m}|{h}"] = {"failures": dict(zip(("steered", "placebo", REF_FOR[h]), n)), "p": p, "flag": p < 0.05}
        p = _multinomial_p(list(pooled), rng)
        out[f"pooled|{h}"] = {"failures": dict(zip(("steered", "placebo", "reference"), map(int, pooled))), "p": p,
                              "flag": p < 0.05}
    out["draws"] = BALANCE_DRAWS
    return out


def tipping_point(records, S, model, hyp, deltas, testable, method, categories, targets) -> Dict:
    """Impute every missing stage-2 steered / placebo cell (failed generation or grading) at s_arm -/+ delta, against
    the hypothesis (or for it), clipped to [0, 1], over all five targets; the smallest delta that changes this
    test's label with the other three tests held as observed; and the worst case."""
    key = (model, hyp)
    cells = {(c, t) for c in categories for t in targets}
    have = {a: {(c, t) for (m, a2, h, c, t) in S if m == model and a2 == a and h == hyp} for a in ("steered", "placebo")}
    miss = {a: cells - have[a] for a in have}
    n_miss = sum(len(v) for v in miss.values())
    base = decide(deltas, testable, method)[f"{model}|{hyp}"]["label"]
    if n_miss == 0 or not testable.get(key):
        return {"missing": n_miss, "label": base, "note": "no missing cell" if n_miss == 0 else "untestable"}
    obs = {a: float(np.mean([S[(model, a, hyp, c, t)] for (c, t) in have[a]])) for a in have}
    sign = PREDICTED[hyp]

    def label_at(d, against=True):
        s = -sign if against else sign          # against the hypothesis: steered moves opposite to its prediction
        fill = {"steered": min(max(obs["steered"] + s * d, 0.0), 1.0),
                "placebo": min(max(obs["placebo"] - s * d, 0.0), 1.0)}
        S2 = dict(S)
        for a in miss:
            for (c, t) in miss[a]:
                S2[(model, a, hyp, c, t)] = fill[a]
        dl = dict(deltas)
        dl[key] = category_deltas(pair_matrix(S2, model, "steered", "placebo", hyp, hyp, categories, targets))
        return decide(dl, testable, method)[f"{model}|{hyp}"]["label"]

    out = {"missing": n_miss, "missing_steered": len(miss["steered"]), "missing_placebo": len(miss["placebo"]),
           "label": base, "grid": TIP_GRID}
    for name, against in (("against", True), ("for", False)):
        first = None
        for d in np.arange(0.0, 1.0 + TIP_GRID / 2, TIP_GRID):
            if label_at(float(d), against) != base:
                first = float(d); break
        out[f"delta_{name}"] = first
        out[f"label_at_delta_{name}"] = label_at(first, against) if first is not None else None
    worst = dict(S)
    w = {"steered": 0.0 if sign > 0 else 1.0, "placebo": 1.0 if sign > 0 else 0.0}
    for a in miss:
        for (c, t) in miss[a]:
            worst[(model, a, hyp, c, t)] = w[a]
    dl = dict(deltas)
    dl[key] = category_deltas(pair_matrix(worst, model, "steered", "placebo", hyp, hyp, categories, targets))
    out["worst_case_label"] = decide(dl, testable, method)[f"{model}|{hyp}"]["label"]
    return out


# ------------------------------------------------------------------ section 8, 7 (reported)

def placebo_shift(S, model, hyp, categories, targets) -> Dict:
    """The placebo arm's own shift: s(placebo, hyp) - s(unsteered reference of the hypothesis's note), per category."""
    return t_summary(category_deltas(pair_matrix(S, model, "placebo", REF_FOR[hyp], hyp, None, categories, targets)))


def note_effect(S, model, categories, targets) -> Dict:
    return t_summary(category_deltas(pair_matrix(S, model, "ref_full", "ref_reversed", None, None, categories, targets)))


def cos(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def naturalness(v, first_token_shift, last_token_shift) -> Dict:
    """Section 7: cos(v, mean (h_full - h_reversed) at the first generated token), cos(v, the last-token shift on the
    evaluation categories); the vectors come from the pod."""
    return {"cos_first_generated_token": cos(v, first_token_shift), "cos_last_token_evaluation": cos(v, last_token_shift)}


# ------------------------------------------------------------------ section 10: blinded permutation check

def permutation_check(mats: Dict[Tuple[str, str], np.ndarray], testable, method, n=PERM_N, seed=PERM_SEED_P2) -> Dict:
    """Steered and placebo labels swapped at random within each (category, target) cell (the sign of each pair
    difference), n times; each permuted dataset through the decision code. Only decision shares are returned."""
    rng = np.random.default_rng(seed)
    keys = [(m, h) for m in MODELS for h in HYPS]
    hits = {f"{m}|{h}": Counter() for m, h in keys}
    for _ in range(n):
        dl = {}
        for k in keys:
            M = mats.get(k)
            if M is None:
                continue
            sgn = rng.choice((-1.0, 1.0), size=M.shape)
            dl[k] = category_deltas(M * sgn)
        dec = decide(dl, testable, method)
        for k, d in dec.items():
            hits[k]["efficacy"] += d["efficacy_alpha_at_decision"] is not None
            hits[k]["equivalence"] += d["equivalence_alpha_at_decision"] is not None
            hits[k][d["label"]] += 1
    return {"n": n, "seed": seed, "shares": {k: {x: v / n for x, v in c.items()} for k, c in hits.items()}}


# ------------------------------------------------------------------ Addendum 2: the Google grader (descriptive)

def kappa(a: Sequence[bool], b: Sequence[bool]) -> float:
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    if len(a) == 0:
        return float("nan")
    po = float(np.mean(a == b))
    pe = float(a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean()))
    return float("nan") if pe == 1 else (po - pe) / (1 - pe)


def google_report(records, cues_by_target, subsample: Dict[str, str], categories, targets, all_cues: Sequence[str],
                  primary_deltas: Dict[Tuple[str, str], Dict]) -> Dict:
    """Addendum 2: on the subsample cells (one target per category), the steered - placebo contrast under the Google
    grader beside the primary grader's on the same cells and the primary Delta on all cells; the method check and the
    references the same way; per-cue kappa (all cues, and the cues that enter s), by model."""
    sub = [r for r in records if subsample.get(r["category"]) == r["target"]]
    Sg, Sp = scores(sub, cues_by_target, "google"), scores(sub, cues_by_target, "grade")
    out = {"cells": len(subsample), "contrasts": {}, "agreement": {}}

    def both(m, a, b, ha, hb):
        g = t_summary(category_deltas(pair_matrix(Sg, m, a, b, ha, hb, categories, targets)))
        p = t_summary(category_deltas(pair_matrix(Sp, m, a, b, ha, hb, categories, targets)))
        return {"google": g, "primary_same_cells": p}
    for m in MODELS:
        for h in HYPS:
            out["contrasts"][f"{m}|{h}|steered-placebo"] = {**both(m, "steered", "placebo", h, h),
                                                            "primary_all_cells": primary_deltas.get(f"{m}|{h}")}
            for a in ("steered", "placebo"):
                out["contrasts"][f"{m}|{h}|{a}-ref_placebo"] = both(m, a, "ref_placebo", h, None)
        out["contrasts"][f"{m}|method_check"] = both(m, "mc_steered", "mc_placebo", None, None)
        out["contrasts"][f"{m}|ref_full-ref_reversed"] = both(m, "ref_full", "ref_reversed", None, None)
        pa, ga, ps, gs = [], [], [], []
        for r in sub:
            if r["model"] != m or not usable(r) or not r.get("google"):
                continue
            for c in all_cues:
                pa.append(bool(r["grade"]["cues"][c])); ga.append(bool(r["google"]["cues"][c]))
            for c in cues_by_target.get(r["target"], []):
                ps.append(bool(r["grade"]["cues"][c])); gs.append(bool(r["google"]["cues"][c]))
        out["agreement"][m] = {"kappa_all_cues": kappa(pa, ga), "n_labels_all": len(pa),
                               "kappa_cues_in_s": kappa(ps, gs), "n_labels_in_s": len(ps),
                               "google_failed": sum(1 for r in sub if r["model"] == m and r.get("status") == "complete"
                                                    and not r.get("google"))}
    return out


# ------------------------------------------------------------------ everything

def analyse(records: Sequence[Dict], cues_by_target: Dict[str, List[str]], categories: Sequence[str],
            mc_categories: Sequence[str], testable: Dict[Tuple[str, str], bool], targets: Sequence[str],
            permutations: int = PERM_N, tipping: bool = True) -> Dict:
    """The registered analysis on stage-2 records (primary grader). `testable[(model, hyp)]` is False for a test
    with no coherent alpha or whose alpha failed the stage-2 coherence gate."""
    S = scores(records, cues_by_target)
    mc = {m: method_check(S, m, mc_categories, targets) for m in MODELS}
    method = {m: mc[m]["passed"] for m in MODELS}
    mats = {(m, h): pair_matrix(S, m, "steered", "placebo", h, h, categories, targets) for m in MODELS for h in HYPS}
    deltas = {k: category_deltas(M) for k, M in mats.items()}
    dec = decide(deltas, testable, method)
    out = {"primary": dec, "method_check": mc, "counts": counts(records), "balance": balance(records)}
    if tipping:
        out["tipping_point"] = {f"{m}|{h}": tipping_point(records, S, m, h, deltas, testable, method, categories, targets)
                                for m in MODELS for h in HYPS}
    out["placebo_shift"] = {f"{m}|{h}": placebo_shift(S, m, h, categories, targets) for m in MODELS for h in HYPS}
    out["note_effect"] = {m: note_effect(S, m, categories, targets) for m in MODELS}
    out["effect_relative_to_note"] = {
        f"{m}|{h}": (dec[f"{m}|{h}"]["est"] / out["note_effect"][m]["est"]
                     if out["note_effect"][m]["est"] not in (0, None) and out["note_effect"][m]["est"] == out["note_effect"][m]["est"]
                     else float("nan")) for m in MODELS for h in HYPS}
    out["per_category_sd"] = {f"{m}|{h}": float(np.std(deltas[(m, h)], ddof=1)) if len(deltas[(m, h)]) > 1 else float("nan")
                              for m in MODELS for h in HYPS}
    if permutations:
        out["permutation_check"] = permutation_check(mats, testable, method, n=permutations)
    return out
