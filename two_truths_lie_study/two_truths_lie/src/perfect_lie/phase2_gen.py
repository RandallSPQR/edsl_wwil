"""Phase 2 stage 2: what is generated, in which batches, with which seeds; and the stage-2 coherence gate (section 6;
Addenda 4, 5, 7). Pure functions; the pod generates (results/phase2/probe/stage2_stage.py).

Per model, on the 32 evaluation categories x 5 targets (frozen messages of the reversed-note run):
  H1 (reversed note): "steered" (+alpha_H1 ||v|| unit v), "placebo" (+alpha_H1 ||v|| unit p, Addendum 5), and the
     unsteered reference "ref_reversed"; one batch order and one seed per batch, shared by the three (common random
     numbers, as in the pilot).
  H2 (full note): "steered" (-alpha_H2 ||v|| unit v), "placebo" (-alpha_H2 ||v|| unit p), "ref_full"; likewise.
  Placebo note: "ref_placebo" on all 32 categories; the method check on its 16 categories (seed 20261036), one
     target at a time (each target has its own direction): "mc_steered" (+||v_fp,t|| unit v_fp,t, alpha 1) and
     "mc_placebo" (+||v_fp,t|| unit p_fp,t), sharing batches and seeds.
A hypothesis with no confirmatory alpha generates no steered or placebo lies (untestable).
Stage-2 coherence gate (section 6, re-applied before any grading): per model x hypothesis, the steered and the placebo
lies against the hypothesis's unsteered reference, with the pilot's measures and thresholds (phase2_pilot.cell_metrics:
the perplexity reference is the reference lie of the same item). A test whose steered or placebo lies fail is
untestable; no other alpha is substituted. The method check's coherence is reported the same way (not a gate).
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional, Sequence

from . import phase2_pilot as Q

MC_SEED, N_MC = 20261036, 16
GEN2_SEED = 20261037
MC_ALPHA = 1.0
TARGETS = ("P1", "P2", "P3", "P5", "P6")
MODELS = ("google/gemma-3-27b-it", "meta-llama/llama-3.1-8b-instruct")
NOTE = {"H1": "reversed", "H2": "full"}
REF = {"H1": "ref_reversed", "H2": "ref_full"}


def mc_categories(evaluation: Sequence[str], seed=MC_SEED, k=N_MC) -> List[str]:
    return sorted(random.Random(seed).sample(sorted(evaluation), k))


def items_for(items: Sequence[Dict], model: str, categories: Sequence[str], condition: str,
              targets: Sequence[str] = TARGETS) -> List[Dict]:
    out = [it for it in items if it["model_id"] == model and it["condition"] == condition
           and it["category"] in set(categories) and it["target"] in set(targets)]
    out.sort(key=lambda it: (it["category"], it["target"]))
    if len(out) != len(categories) * len(targets):
        raise ValueError(f"{model} {condition}: expected {len(categories) * len(targets)} items, found {len(out)}")
    return out


def _seed(model_index: int, group: int, b: int) -> int:
    return GEN2_SEED + model_index * 100_000 + group * 10_000 + b


def plan(items: Sequence[Dict], model: str, alphas: Dict[str, Optional[float]], evaluation: Sequence[str],
         batch: int) -> List[Dict]:
    """Every generation job of stage 2 for one model: {arm, hyp, kind, alpha, sign, target, items, seed, key}."""
    mi = MODELS.index(model)
    jobs = []
    for g, h in enumerate(("H1", "H2"), start=0):
        its = items_for(items, model, evaluation, NOTE[h])
        arms = [(REF[h], None, "none", 0.0)]
        if alphas.get(h) is not None:
            arms += [("steered", h, "steered", alphas[h]), ("placebo", h, "placebo", alphas[h])]
        for b in range(0, len(its), batch):
            seed = _seed(mi, g, b)
            for arm, hyp, kind, a in arms:
                jobs.append({"arm": arm, "hyp": hyp, "kind": kind, "alpha": a, "sign": Q.HYPOTHESES[h]["sign"],
                             "target": None, "items": its[b:b + batch], "seed": seed, "key": f"{arm}|{hyp}|{b}"})
    its = items_for(items, model, evaluation, "placebo")
    for b in range(0, len(its), batch):
        jobs.append({"arm": "ref_placebo", "hyp": None, "kind": "none", "alpha": 0.0, "sign": 1.0, "target": None,
                     "items": its[b:b + batch], "seed": _seed(mi, 2, b), "key": f"ref_placebo|None|{b}"})
    mc = mc_categories(evaluation)
    for ti, t in enumerate(TARGETS):
        its = items_for(items, model, mc, "placebo", [t])
        for b in range(0, len(its), batch):
            seed = _seed(mi, 3, ti * 100 + b)
            for arm in ("mc_steered", "mc_placebo"):
                jobs.append({"arm": arm, "hyp": None, "kind": f"{arm}:{t}", "alpha": MC_ALPHA, "sign": 1.0, "target": t,
                             "items": its[b:b + batch], "seed": seed, "key": f"{arm}|{t}|{b}"})
    return jobs


def coef(job: Dict, v_norm: float, vfp_norm: Dict[str, float]) -> float:
    """Signed length of the added vector: alpha x ||v|| for the main test, alpha x ||v_fp,t|| for the method check."""
    if job["kind"] == "none":
        return 0.0
    if job["arm"].startswith("mc_"):
        return job["sign"] * job["alpha"] * vfp_norm[job["target"]]
    return job["sign"] * job["alpha"] * v_norm


def coherence(records: Sequence[Dict], alphas: Dict[str, Optional[float]]) -> Dict:
    """Section 6 re-applied in stage 2, per hypothesis (steered and placebo vs the hypothesis's reference), and the
    method check reported (mc_steered and mc_placebo vs ref_placebo). Records carry category, target, text, ids,
    finish, nll (first 64 tokens under the unsteered model)."""
    out = {}
    for h in ("H1", "H2"):
        if alphas.get(h) is None:
            out[h] = {"testable": False, "reason": "no coherent alpha in the pilot"}
            continue
        ref = {(r["category"], r["target"]): r for r in records if r["arm"] == REF[h]}
        cells = {k: Q.cell_metrics([r for r in records if r["arm"] == k and r.get("hyp") == h], ref) for k in Q.KINDS}
        ok = all(cells[k]["passes"] for k in Q.KINDS)
        out[h] = {"alpha": alphas[h], **cells, "testable": ok,
                  "reason": None if ok else "confirmatory alpha failed the stage-2 coherence gate"}
    ref = {(r["category"], r["target"]): r for r in records if r["arm"] == "ref_placebo"}
    out["method_check"] = {k: Q.cell_metrics([r for r in records if r["arm"] == k], ref) for k in ("mc_steered", "mc_placebo")}
    return out
