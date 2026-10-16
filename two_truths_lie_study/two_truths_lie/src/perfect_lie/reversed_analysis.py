"""Final analysis of the reversed-note follow-up, written from PREREG_REVERSED.md (tag
perfect-lie-reversed-prereg-v1) before any real data is analysed. Sections refer to that document.

Primary (section 4): Test B = full - reversed, per liar model, from
    s ~ condition + persona + (1 + condition | category)        (REML; condition coded vs reversed)
with t inference on K - 1 df; fallback to the per-category t-test if the fit fails. Holm across the
four models (graphical, equal split, p-value order) in two families: efficacy (two-sided) and
equivalence (TOST, margin 0.10), each at alpha 0.05.
Secondary: Test A (section 5), comprehension (11a), exploratory analyses (11).
Missing data: grader blocks counted separately, balance check, tipping point (section 7).
Discipline (4a): validated on simulated data (validate_final.py), sign-tested both directions,
blinded permutation check (permutation_check) before unblinding.
"""

from __future__ import annotations

import json
import math
import re
import warnings
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from . import sequential as sq
from .scoring import confession, lie_viability, REFUSAL_PATTERNS

ALPHA = 0.05
MARGIN = 0.10
GATE_SEED, GATE_BOOT = 20261012, 2000
BALANCE_SEED, BALANCE_DRAWS = 20261013, 100_000
CONDITIONS = ("placebo", "full", "reversed")
FAMILY = {"meta-llama/llama-3.1-8b-instruct": "meta", "google/gemma-3-27b-it": "google",
          "openai/gpt-4o-mini": "openai", "google/gemini-2.5-flash-lite": "google"}
ADJUDICATION_PATH = (Path(__file__).resolve().parents[2] / "results" / "perfect_lie_reversed" / "final_analysis"
                     / "screen_adjudication.json")


# ------------------------------------------------------------------ records

def load_records(path: Path) -> List[Dict]:
    last = {}
    for line in Path(path).read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            last[r["cell_id"]] = r
    return list(last.values())


def is_grader_block(r: Dict) -> bool:
    """Owner amendment 2026-10-09: the primary grader returned content_filter on every attempt."""
    pf = [x for x in r.get("parse_failures", []) if x.get("call") == "grader[primary]"]
    return r.get("status") == "error" and len(pf) >= 3 and all(x.get("finish_reason") == "content_filter" for x in pf[-3:])


def _adjudicated(path: Path = ADJUDICATION_PATH) -> Dict[str, str]:
    """Owner adjudications of screen matches (as in the first study's Addendum 3), keyed by sha256(cell_id)."""
    if not Path(path).exists():
        return {}
    return {x["cell_key"]: x["decision"] for x in json.loads(Path(path).read_text()).get("records", [])}


def screens(r: Dict, adj: Dict[str, str]) -> Dict[str, bool]:
    key = sq.cell_key(r)
    lie = r.get("lie") or ""
    conf = bool(confession(lie)) and adj.get(key) != "not_confession"
    refusal = bool(REFUSAL_PATTERNS.search(lie)) and adj.get(key) != "not_refusal"
    return {"confession": conf, "refusal": refusal}


def status_of(r: Dict) -> str:
    if r.get("status") == "complete":
        return "complete"
    if is_grader_block(r):
        return "grader_block"
    return "failed"


# ------------------------------------------------------------------ gate and cues (sections 3, 6)

def gate(records: Sequence[Dict], instrument) -> Dict:
    """Per-cue gate on the follow-up's own data, reading grades only (never condition)."""
    cues = [c.id for c in instrument.cues if not c.heatmap_only]
    complete = [r for r in records if r.get("status") == "complete"]
    return sq.agreement_gate(complete, cues, n_boot=GATE_BOOT, seed=GATE_SEED)


def target_cues(instrument, targets: Sequence[str], excluded: Sequence[str] = (), drop: Sequence[str] = ()) -> Dict[str, List[str]]:
    """Scorable cues per target (not heatmap-only, not gated, not dropped); a target with fewer than
    2 leaves the pool (section 6)."""
    scorable = set(sq.scorable_cues(instrument, list(excluded) + list(drop)))
    out = {t: [c for c in instrument.personas[t].cues if c in scorable] for t in targets}
    return {t: cs for t, cs in out.items() if len(cs) >= 2}


def lie_table(records: Sequence[Dict], cues_by_target: Dict[str, List[str]], grader: str = "primary",
              adj: Optional[Dict[str, str]] = None, exclude_nonviable: bool = False) -> pd.DataFrame:
    """One row per usable lie: complete, graded by `grader`, not a confession, target in the pool."""
    adj = _adjudicated() if adj is None else adj
    rows = []
    for r in records:
        if r.get("status") != "complete" or r.get("target_id") not in cues_by_target:
            continue
        g = (r.get("grades") or {}).get(grader)
        if not g:
            continue
        sc = screens(r, adj)
        if sc["confession"]:
            continue
        nonviable = bool([x for x in lie_viability(r) if x.split("(")[0] in ("too_short", "too_long")]) or sc["refusal"]
        if exclude_nonviable and nonviable:
            continue
        cs = cues_by_target[r["target_id"]]
        rows.append({"model": r["model_id"], "category": r["category"], "persona": r["target_id"],
                     "condition": r["condition"], "s": sum(bool(g["cues"][c]) for c in cs) / len(cs),
                     "cell_id": r["cell_id"]})
    return pd.DataFrame(rows, columns=["model", "category", "persona", "condition", "s", "cell_id"])


# ------------------------------------------------------------------ the contrast (sections 4, 5)

# Section 4: the fit fails on non-convergence, a singular fit, or a non-positive-definite Hessian. Only
# warnings about the FINAL estimate count: statsmodels also warns when an early optimiser fails and it
# retries with another, which is not a failure of the fit.
_FAIL_MSG = re.compile(r"boundary of the parameter space|singular|Hessian matrix .* not positive definite", re.I)


def category_t(df: pd.DataFrame, a: str, b: str) -> Dict:
    """Fallback: per-category mean of (a - b) over personas, one-sample t on the K values."""
    m = df.pivot_table(index="category", columns="condition", values="s", aggfunc="mean")
    d = (m[a] - m[b]).dropna().to_numpy()
    k = len(d)
    se = d.std(ddof=1) / math.sqrt(k) if k > 1 else float("nan")
    return {"est": float(d.mean()), "se": float(se), "df": k - 1, "K": k}


def fit_model(df: pd.DataFrame) -> Dict:
    """Primary fit for one liar model. Returns B = full - reversed and A = reversed - placebo, each with
    SE and K - 1 df, from the mixed model, or from the per-category fallback when the fit fails."""
    import statsmodels.formula.api as smf
    K = df["category"].nunique()
    out = {"K": K, "n": len(df)}
    if len(df) == 0 or not {"full", "reversed", "placebo"} <= set(df["condition"]) or K < 3:
        nan = float("nan")
        return {**out, "method": "no data", "B": nan, "B_se": nan, "A": nan, "A_se": nan, "df": max(K - 1, 1),
                "note": "too few lies or conditions to fit"}
    reason = None
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            m = smf.mixedlm("s ~ C(condition, Treatment('reversed')) + C(persona)", df, groups="category",
                            re_formula="~C(condition, Treatment('reversed'))").fit(reml=True)
        msgs = [str(x.message) for x in w]
        kf = "C(condition, Treatment('reversed'))[T.full]"
        kp = "C(condition, Treatment('reversed'))[T.placebo]"
        bad = [x for x in msgs if _FAIL_MSG.search(x)]
        eig = np.linalg.eigvalsh(np.asarray(m.cov_re, float))
        if not m.converged:
            reason = "did not converge"
        elif bad:
            reason = "fit warning: " + bad[0][:120]
        elif not np.all(np.isfinite([m.bse[kf], m.bse[kp]])):
            reason = "non-finite standard error"
        elif eig.min() <= 1e-10:
            reason = "singular random-effects covariance"
        if reason is None:
            out.update(method="mixed model", B=float(m.params[kf]), B_se=float(m.bse[kf]),
                       A=float(-m.params[kp]), A_se=float(m.bse[kp]), df=K - 1)
            return out
    except Exception as e:  # noqa: BLE001 — any fit failure takes the registered fallback
        reason = f"{type(e).__name__}: {str(e)[:120]}"
    b, a = category_t(df, "full", "reversed"), category_t(df, "reversed", "placebo")
    out.update(method="per-category t-test (fallback)", fallback_reason=reason, B=b["est"], B_se=b["se"],
               A=a["est"], A_se=a["se"], df=b["df"])
    return out


def _p_two(est: float, se: float, df: int) -> float:
    return float(2 * stats.t.sf(abs(est / se), df))


def _p_tost(est: float, se: float, df: int, margin: float = MARGIN) -> float:
    return float(max(stats.t.sf((est + margin) / se, df), stats.t.cdf((est - margin) / se, df)))


def holm(pvals: Dict[str, float], alpha: float = ALPHA) -> Dict[str, Optional[float]]:
    """Holm = the graphical procedure with equal split and full reallocation; models are tested in
    p-value order. Returns, per model, the local alpha at which it was rejected, or None."""
    order = sorted(pvals, key=lambda m: (pvals[m], m))
    out = {m: None for m in pvals}
    for i, m in enumerate(order):
        a = alpha / (len(order) - i)
        if pvals[m] <= a:
            out[m] = a
        else:
            break
    return out


def label(eff_alpha, eq_alpha, B) -> str:
    if eff_alpha is not None and B > 0:
        return "valence effect present, within ±0.10" if eq_alpha is not None else "belief-tracking"
    if eff_alpha is not None and B < 0:
        return ("fewer named cues under full than under reversed (within ±0.10)" if eq_alpha is not None
                else "fewer named cues under full than under reversed")
    if eq_alpha is not None:
        return "no valence effect beyond ±0.10"
    return "inconclusive"


def decide_all(lies: pd.DataFrame, models: Sequence[str]) -> Dict:
    """The registered decision code: fit per model, Holm in each family, labels."""
    fits = {m: fit_model(lies[lies["model"] == m]) for m in models}
    p_eff = {m: _p_two(f["B"], f["B_se"], f["df"]) for m, f in fits.items()}
    p_eq = {m: _p_tost(f["B"], f["B_se"], f["df"]) for m, f in fits.items()}
    a_eff, a_eq = holm(p_eff), holm(p_eq)
    out = {}
    for m, f in fits.items():
        out[m] = {**f, "t": f["B"] / f["B_se"], "p_efficacy": p_eff[m], "p_tost": p_eq[m],
                  "efficacy_alpha_at_decision": a_eff[m], "equivalence_alpha_at_decision": a_eq[m],
                  "label": label(a_eff[m], a_eq[m], f["B"])}
    return out


# ------------------------------------------------------------------ missing data (section 7)

def missingness(records: Sequence[Dict], models: Sequence[str]) -> Dict:
    c = Counter((r["model_id"], r["condition"], status_of(r)) for r in records)
    by = {f"{m}|{k}": {s: c[(m, k, s)] for s in ("complete", "failed", "grader_block")} for m in models for k in CONDITIONS}
    return {"by_model_condition": by}


def _multinomial_p(counts: Sequence[int], rng) -> float:
    """Exact multinomial test of equal probabilities, Monte Carlo: P(table probability <= observed)."""
    from scipy.special import gammaln
    n, k = int(sum(counts)), len(counts)
    if n == 0:
        return 1.0
    obs = -gammaln(np.asarray(counts) + 1).sum()
    sims = rng.multinomial(n, [1 / k] * k, size=BALANCE_DRAWS)
    lp = -gammaln(sims + 1).sum(axis=1)       # the common terms n!, k^-n cancel
    return float(np.mean(lp <= obs + 1e-9))


def balance_check(records: Sequence[Dict], models: Sequence[str]) -> Dict:
    rng = np.random.default_rng(BALANCE_SEED)
    out = {}
    tot = np.zeros(3, int)
    for m in models:
        counts = [sum(1 for r in records if r["model_id"] == m and r["condition"] == k and is_grader_block(r)) for k in CONDITIONS]
        tot += counts
        p = _multinomial_p(counts, rng)
        out[m] = {"blocks": dict(zip(CONDITIONS, counts)), "p": p, "flag": p < 0.05}
    p = _multinomial_p(list(tot), rng)
    out["pooled"] = {"blocks": dict(zip(CONDITIONS, map(int, tot))), "p": p, "flag": p < 0.05}
    return out


def _stat(df: pd.DataFrame, method: str) -> Tuple[float, float]:
    if method.startswith("mixed"):
        f = fit_model(df)
        return f["B"] / f["B_se"], f["df"]
    b = category_t(df, "full", "reversed")
    return b["est"] / b["se"], b["df"]


def tipping_point(records: Sequence[Dict], lies: pd.DataFrame, model: str, decision: Dict,
                  cues_by_target: Dict[str, List[str]]) -> Dict:
    """Section 7: impute missing full lies at s_f - delta and missing reversed lies at s_r + delta
    (clipped to [0, 1]); smallest delta at which |t| falls below the boundary of the decision."""
    a = decision["efficacy_alpha_at_decision"]
    if a is None:
        return {"applies": False, "note": "no efficacy decision for this model"}
    miss = [r for r in records if r["model_id"] == model and r["condition"] in ("full", "reversed")
            and status_of(r) != "complete" and r.get("target_id") in cues_by_target]
    base = lies[lies["model"] == model]
    if not miss:
        return {"applies": True, "missing": 0, "delta": None, "note": "no missing full or reversed lies"}
    s_f = base.loc[base.condition == "full", "s"].mean()
    s_r = base.loc[base.condition == "reversed", "s"].mean()
    bound = stats.t.isf(a / 2, decision["df"])
    sign = 1 if decision["B"] > 0 else -1

    def with_imputed(vf, vr):
        add = [{"model": model, "category": r["category"], "persona": r["target_id"], "condition": r["condition"],
                "s": vf if r["condition"] == "full" else vr, "cell_id": r["cell_id"]} for r in miss]
        return pd.concat([base, pd.DataFrame(add)], ignore_index=True)

    def t_at(d):
        vf, vr = (min(max(s_f - sign * d, 0.0), 1.0), min(max(s_r + sign * d, 0.0), 1.0))
        t, _ = _stat(with_imputed(vf, vr), decision["method"])
        return sign * t

    worst_t = sign * _stat(with_imputed(0.0 if sign > 0 else 1.0, 1.0 if sign > 0 else 0.0), decision["method"])[0]
    hi = max(s_f, 1 - s_r, 1 - s_f, s_r)
    if t_at(hi) >= bound:
        return {"applies": True, "missing": len(miss), "boundary": bound, "delta": None,
                "note": "not reversible within [0, 1]", "t_worst_case": worst_t}
    lo = 0.0
    for _ in range(25):
        mid = (lo + hi) / 2
        if t_at(mid) >= bound:
            lo = mid
        else:
            hi = mid
    return {"applies": True, "missing": len(miss), "boundary": bound, "delta": hi, "t_worst_case": worst_t,
            "missing_by_condition": dict(Counter(r["condition"] for r in miss))}


# ------------------------------------------------------------------ robustness (section 4)

def m1_intercepts(df: pd.DataFrame) -> Dict:
    """Draft-1 model, `(1|category) + (1|persona)`, labelled as assuming no heterogeneity."""
    import statsmodels.formula.api as smf
    d = df.assign(g=1)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = smf.mixedlm("s ~ C(condition, Treatment('reversed'))", d, groups="g",
                        vc_formula={"category": "0 + C(category)", "persona": "0 + C(persona)"}).fit(reml=True)
    k = "C(condition, Treatment('reversed'))[T.full]"
    return {"B": float(m.params[k]), "B_se": float(m.bse[k]), "z": float(m.params[k] / m.bse[k]), "converged": bool(m.converged)}


def holds(decision: Dict, est: float, se: float, df: int) -> bool:
    """Does a sensitivity estimate keep the decision at the local alpha it was made at?"""
    a = decision["efficacy_alpha_at_decision"]
    if a is not None:
        return bool(np.sign(est) == np.sign(decision["B"]) and abs(est / se) > stats.t.isf(a / 2, df))
    a = decision["equivalence_alpha_at_decision"]
    if a is not None:
        return _p_tost(est, se, df) <= a
    return False


# ------------------------------------------------------------------ comprehension (section 11a)

def comprehension(comp_records: Sequence[Dict], decisions: Dict, models: Sequence[str]) -> Dict:
    from . import comprehension as C
    recs = [r for r in comp_records if r.get("status") == "complete"]
    for r in recs:  # re-score with the frozen scorer, so the analysis does not trust stored scores
        try:
            items, mode = C.parse_with_mode(r.get("answer"))
            r["score"], r["parse_mode"] = C.score(items, r["note_lines"], r["condition"]), mode
        except (ValueError, json.JSONDecodeError):
            r["score"], r["parse_mode"] = None, None
    disc = C.discrimination(recs)
    by_order = {o: C.discrimination([r for r in recs if (r.get("variant") or {}).get("option_order") == o], n_boot=500)
                for o in (0, 1)}
    out = {}
    for m in models:
        d = disc.get(m, {})
        dec = decisions[m]
        held = bool(d.get("comprehension_holds"))
        positive = dec["efficacy_alpha_at_decision"] is not None and dec["B"] > 0
        negative = dec["efficacy_alpha_at_decision"] is not None and dec["B"] < 0
        if positive:
            reading = "belief use confirmed (comprehension reported as context)"
        elif negative:
            reading = "B negative: not covered by the interpretation rules; reported as found"
        elif held:
            reading = "priming despite comprehension"
        else:
            reading = "inconclusive (comprehension fails; check invalid for this model, never priming)"
        parse = Counter(r.get("parse_mode") for r in recs if r["model_id"] == m and r["condition"] in ("full", "reversed"))
        placebo = [r for r in recs if r["model_id"] == m and r["condition"] == "placebo"]
        out[m] = {**{k: d.get(k) for k in ("acc_full", "acc_reversed", "balanced_accuracy", "youden_j", "d_prime",
                                           "criterion_c", "ci95", "n_samples", "comprehension_holds")},
                  "check_valid": held, "parse": {str(k): v for k, v in parse.items()},
                  "placebo_format_parsed": f"{sum(1 for r in placebo if r['score'])}/{len(placebo)}",
                  "criterion_c_by_first_option": {("convincing first" if o == 0 else "suspicious first"):
                                                  by_order[o].get(m, {}).get("criterion_c") for o in (0, 1)},
                  "reading": reading}
    return out


# ------------------------------------------------------------------ exploratory (section 11)

def _acc(r: Dict) -> Optional[float]:
    v = [bool(x["accept"]) for x in (r.get("targets") or {}).values() if "accept" in x]
    return sum(v) / len(v) if v else None


def _mean_ci(x: Sequence[float]) -> Dict:
    x = np.asarray([v for v in x if v is not None], float)
    if len(x) < 2:
        return {"n": len(x), "mean": float(x.mean()) if len(x) else None, "ci95": None}
    se = x.std(ddof=1) / math.sqrt(len(x))
    return {"n": len(x), "mean": float(x.mean()), "ci95": [float(x.mean() - 1.96 * se), float(x.mean() + 1.96 * se)]}


def exploratory(records: Sequence[Dict], lies: pd.DataFrame, cues_by_target: Dict[str, List[str]], instrument,
                models: Sequence[str], adj: Dict[str, str]) -> Dict:
    usable = {r["cell_id"]: r for r in records if r.get("status") == "complete" and not screens(r, adj)["confession"]}
    out = {}
    # 2. liar x judge acceptance; family diagonal
    cross = defaultdict(list)
    for r in usable.values():
        for j, v in (r.get("targets") or {}).items():
            if "accept" in v:
                cross[(r["model_id"], j)].append(bool(v["accept"]))
    out["liar_x_judge"] = {f"{a} -> {b}": {"n": len(v), "acceptance": sum(v) / len(v)} for (a, b), v in sorted(cross.items())}
    same = [x for (a, b), v in cross.items() if FAMILY.get(a) == FAMILY.get(b) for x in v]
    other = [x for (a, b), v in cross.items() if FAMILY.get(a) != FAMILY.get(b) for x in v]
    out["family_diagonal"] = {"same_family": float(np.mean(same)) if same else None,
                              "other_family": float(np.mean(other)) if other else None,
                              "same_minus_other": (float(np.mean(same)) - float(np.mean(other))) if same and other else None}
    # 3. judge acceptance by cue (lie-level mean acceptance over judges; cue present vs absent)
    cues = [c.id for c in instrument.cues if not c.heatmap_only]
    bycue = {}
    for c in cues:
        pres = [_acc(r) for r in usable.values() if (r.get("grades") or {}).get("primary") and r["grades"]["primary"]["cues"][c]]
        absn = [_acc(r) for r in usable.values() if (r.get("grades") or {}).get("primary") and not r["grades"]["primary"]["cues"][c]]
        p, a = _mean_ci(pres), _mean_ci(absn)
        diff = None
        if p["n"] > 1 and a["n"] > 1:
            pp = np.array([x for x in pres if x is not None]); aa = np.array([x for x in absn if x is not None])
            se = math.sqrt(pp.var(ddof=1) / len(pp) + aa.var(ddof=1) / len(aa))
            d = float(pp.mean() - aa.mean()); diff = {"diff": d, "ci95": [d - 1.96 * se, d + 1.96 * se]}
        bycue[c] = {"present": p, "absent": a, "difference": diff}
    out["acceptance_by_cue"] = bycue
    # 4. breakdowns of B and A by category, model and persona
    br = {}
    for m in models:
        d = lies[lies.model == m]
        piv = d.pivot_table(index=["category", "persona"], columns="condition", values="s", aggfunc="mean")
        piv = piv.assign(B=piv.get("full") - piv.get("reversed"), A=piv.get("reversed") - piv.get("placebo"))
        br[m] = {"by_category": {k: {"B": _mean_ci(g["B"].dropna()), "A": _mean_ci(g["A"].dropna())}
                                 for k, g in piv.groupby(level="category")},
                 "by_persona": {k: {"B": _mean_ci(g["B"].dropna()), "A": _mean_ci(g["A"].dropna())}
                                for k, g in piv.groupby(level="persona")}}
    out["breakdowns"] = br
    # 5. acceptance by condition
    acc = {}
    for m in models:
        rows = [r for r in usable.values() if r["model_id"] == m and r.get("target_id") in cues_by_target]
        a = {k: [_acc(r) for r in rows if r["condition"] == k] for k in CONDITIONS}
        acc[m] = {k: _mean_ci(v) for k, v in a.items()}
        f, rv = np.array([x for x in a["full"] if x is not None]), np.array([x for x in a["reversed"] if x is not None])
        if len(f) > 1 and len(rv) > 1:
            se = math.sqrt(f.var(ddof=1) / len(f) + rv.var(ddof=1) / len(rv)); d = float(f.mean() - rv.mean())
            acc[m]["full_minus_reversed"] = {"diff": d, "ci95": [d - 1.96 * se, d + 1.96 * se]}
    out["acceptance_by_condition"] = acc
    # 6. off-target shifts: non-target scorable cues, reversed vs placebo and vs full
    off = {}
    for m in models:
        rows = [r for r in usable.values() if r["model_id"] == m and r.get("target_id") in cues_by_target
                and (r.get("grades") or {}).get("primary")]
        res = {}
        for c in cues:
            share = {}
            for k in CONDITIONS:
                v = [bool(r["grades"]["primary"]["cues"][c]) for r in rows if r["condition"] == k
                     and c not in instrument.personas[r["target_id"]].cues]
                share[k] = (sum(v) / len(v)) if v else None
            if share["reversed"] is not None and share["placebo"] is not None:
                res[c] = {**share, "reversed_minus_placebo": share["reversed"] - share["placebo"],
                          "reversed_minus_full": (share["reversed"] - share["full"]) if share["full"] is not None else None}
        off[m] = res
    out["off_target_shifts"] = off
    return out


# ------------------------------------------------------------------ the whole analysis

def run_final(main_records: Sequence[Dict], comp_records: Sequence[Dict], instrument, cfg: Dict,
              adj: Optional[Dict[str, str]] = None, tipping: bool = True) -> Dict:
    adj = _adjudicated() if adj is None else adj
    models = cfg["liar_models"]
    g = gate(main_records, instrument)
    cues_by_target = target_cues(instrument, cfg["targets"], g["excluded"])
    lies = lie_table(main_records, cues_by_target, adj=adj)
    dec = decide_all(lies, models)
    out = {"gate": g, "cues_by_target": cues_by_target, "pool": sorted(cues_by_target),
           "n_lies_analysed": int(len(lies)), "missing": missingness(main_records, models),
           "confessions_excluded": sum(1 for r in main_records if r.get("status") == "complete" and screens(r, adj)["confession"]),
           "primary": dec}
    out["balance_check"] = balance_check(main_records, models)
    if tipping:
        out["tipping_point"] = {m: tipping_point(main_records, lies, m, dec[m], cues_by_target) for m in models}
    # Test A (secondary)
    out["test_A"] = {m: {"A": dec[m]["A"], "ci95": [dec[m]["A"] - stats.t.isf(0.025, dec[m]["df"]) * dec[m]["A_se"],
                                                    dec[m]["A"] + stats.t.isf(0.025, dec[m]["df"]) * dec[m]["A_se"]],
                         "method": dec[m]["method"],
                         "placebo_share_at_zero": float((lies[(lies.model == m) & (lies.condition == "placebo")]["s"] == 0).mean())}
                     for m in models}
    # robustness
    rob = {}
    for m in models:
        d = lies[lies.model == m]
        r1 = m1_intercepts(d)
        rob.setdefault("m1_random_intercepts_assumes_no_heterogeneity", {})[m] = {**r1, "decision_holds": holds(dec[m], r1["B"], r1["B_se"], dec[m]["df"])}
    sec = lie_table([r for r in main_records if (r.get("grades") or {}).get("secondary")], cues_by_target, grader="secondary", adj=adj)
    rob["gpt5_subsample_descriptive"] = {m: (category_t(sec[sec.model == m], "full", "reversed") if len(sec[sec.model == m]) else None) for m in models}
    pk = pooled_kappa(main_records, [c.id for c in instrument.cues if not c.heatmap_only])
    if pk >= 0.70:
        pooled_cues = target_cues(instrument, cfg["targets"])
        lp = lie_table(main_records, pooled_cues, adj=adj)
        rob["pooled_gate"] = {"kappa": pk, "models": {m: (lambda f: {**f, "decision_holds": holds(dec[m], f["B"], f["B_se"], f["df"])})(fit_model(lp[lp.model == m])) for m in models}}
    else:
        rob["pooled_gate"] = {"kappa": pk, "note": "pooled kappa below 0.70: not run"}
    ln = lie_table(main_records, cues_by_target, adj=adj, exclude_nonviable=True)
    rob["nonviable_excluded"] = {m: (lambda f: {**f, "decision_holds": holds(dec[m], f["B"], f["B_se"], f["df"])})(fit_model(ln[ln.model == m])) for m in models}
    if g["flagged"]:
        cf = target_cues(instrument, cfg["targets"], g["excluded"], drop=g["flagged"])
        lf = lie_table(main_records, cf, adj=adj)
        rob["flagged_cues_dropped"] = {m: (lambda f: {**f, "decision_holds": holds(dec[m], f["B"], f["B_se"], f["df"])})(fit_model(lf[lf.model == m])) for m in models}
    else:
        rob["flagged_cues_dropped"] = "no cue flagged; identical to the primary analysis"
    out["robustness"] = rob
    out["comprehension"] = comprehension(comp_records, dec, models) if comp_records else None
    out["exploratory"] = exploratory(main_records, lies, cues_by_target, instrument, models, adj)
    return out


def pooled_kappa(records: Iterable[Dict], cues: Sequence[str]) -> float:
    a, b = [], []
    for r in records:
        g = r.get("grades") or {}
        if r.get("status") == "complete" and g.get("primary") and g.get("google"):
            for c in cues:
                a.append(bool(g["primary"]["cues"][c])); b.append(bool(g["google"]["cues"][c]))
    return float(sq._kappa(np.array(a), np.array(b)))


# ------------------------------------------------------------------ blinded permutation check (section 4a)

def _perm_one(args):
    lies, models, seed = args
    rng = np.random.default_rng(seed)
    d = lies.copy()
    fr = d[d.condition.isin(["full", "reversed"])]
    for _, g in fr.groupby(["model", "category", "persona"]):
        if len(g) == 2 and rng.random() < 0.5:
            i, j = g.index
            d.loc[i, "condition"], d.loc[j, "condition"] = d.loc[j, "condition"], d.loc[i, "condition"]
    res = decide_all(d, models)
    return {m: (res[m]["efficacy_alpha_at_decision"] is not None, res[m]["equivalence_alpha_at_decision"] is not None)
            for m in models}


def permutation_check(lies: pd.DataFrame, models: Sequence[str], n: int = 10_000, seed: int = 20261016,
                      workers: int = 4) -> Dict:
    """Swap full/reversed within each (liar, category, target) cell at random; run the real decision
    code; return ONLY the share of efficacy and equivalence decisions per model."""
    from concurrent.futures import ProcessPoolExecutor
    jobs = [(lies, list(models), seed + i) for i in range(n)]
    eff = Counter(); eq = Counter()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for res in ex.map(_perm_one, jobs, chunksize=4):
            for m, (e, q) in res.items():
                eff[m] += e; eq[m] += q
    return {"n": n, "efficacy_share": {m: eff[m] / n for m in models},
            "equivalence_share": {m: eq[m] / n for m in models},
            "note": "only decision shares are output; no unpermuted statistic is computed"}
