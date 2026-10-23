"""Phase 2 stage 1: the dose-finding pilot (PREREG_PHASE2 section 6; Addendum 4). Coherence only: no lie is graded.
Runs locally on what the pod returns (text, token ids, finish reason, per-token NLL).

Design (registered): 8 training categories, seeded (20261025), x 5 targets; both models; both hypotheses; alpha in
{0.25, 0.5, 1, 2, 4}; steered and placebo. H1: the reversed note + alpha v; H2: the full note - alpha v. The added
vector is unit(d) x alpha x ||v_L*|| at the output of block L*, at every prompt and generated position, with d = v
(steered) or the covariance-matched placebo (pipeline `vectors.placebo_cov`, seeded). Addendum 4 adds the unsteered
continuations the perplexity criterion compares against: the same 40 items per hypothesis, alpha = 0, same seeds.

Coherence gate per model x hypothesis x alpha, for the steered AND the placebo lies (40 each):
  viability     >= 95% of lies pass the frozen viability screen: `scoring.lie_viability` with the prompt's word range,
                counting too_short, too_long, truncated_by_output_cap and degenerate_text (word range, not degenerate);
                refusal language is reported, not counted;
  perplexity    median over the 40 lies of exp(mean NLL of the lie's first 64 tokens - mean NLL of the unsteered
                continuation's first 64 tokens for the same item), both teacher-forced under the unsteered model
                (pipeline `probe/coherence.py`, per item instead of pooled): <= 2.0;
  repetition    mean over the 40 lies of the repeated-4-gram share of the lie's generated tokens (pipeline
                `rep4_share`): <= 0.25.
Alpha rule (registered): per model and hypothesis, the confirmatory alpha is the largest grid alpha at which the
steered and the placebo lies both pass; none -> untestable.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Sequence

import numpy as np

from . import scoring

PILOT_SEED, N_PILOT = 20261025, 8
ALPHAS = (0.25, 0.5, 1.0, 2.0, 4.0)
HYPOTHESES = {"H1": {"note": "reversed", "sign": 1.0}, "H2": {"note": "full", "sign": -1.0}}
KINDS = ("steered", "placebo")
PLACEBO_SEED = {"google/gemma-3-27b-it": 20261030, "meta-llama/llama-3.1-8b-instruct": 20261031}
GEN_SEED = 20261032
BATCH = {"meta-llama/llama-3.1-8b-instruct": 24, "google/gemma-3-27b-it": 12}   # the identity check's batches
SAMPLING = {"temperature": 0.6, "top_p": 0.9, "max_tokens": 1500}               # the run's settings
WORD_RANGE = (300, 400)
VIABLE_MIN, PPL_RATIO_MAX, REP4_MAX, NLL_TOKENS = 0.95, 2.0, 0.25, 64
NONVIABLE = ("too_short", "too_long", "truncated_by_output_cap", "degenerate_text")


def pilot_categories(training: Sequence[str], seed=PILOT_SEED, k=N_PILOT) -> List[str]:
    return sorted(random.Random(seed).sample(sorted(training), k))


def pilot_items(items: Sequence[Dict], model: str, categories: Sequence[str], hyp: str) -> List[Dict]:
    """The frozen-wording items of `model` on `categories` under the hypothesis's note, in (category, target) order."""
    note = HYPOTHESES[hyp]["note"]
    out = [it for it in items if it["model_id"] == model and it["wording"] == "frozen" and it["condition"] == note
           and it["category"] in set(categories)]
    out.sort(key=lambda it: (it["category"], it["target"]))
    if len(out) != len(categories) * 5:
        raise ValueError(f"{model} {hyp}: expected {len(categories) * 5} items, found {len(out)}")
    return out


def conditions() -> List[Dict]:
    """Every generation condition of the pilot for one model: unsteered first (alpha 0), then the grid."""
    out = [{"hyp": h, "kind": "none", "alpha": 0.0} for h in HYPOTHESES]
    out += [{"hyp": h, "kind": k, "alpha": a} for h in HYPOTHESES for a in ALPHAS for k in KINDS]
    return out


def batch_seed(model_index: int, hyp: str, b: int) -> int:
    """Shared by every condition of a hypothesis (steered, placebo, unsteered, every alpha): common random numbers."""
    return GEN_SEED + model_index * 100_000 + list(HYPOTHESES).index(hyp) * 10_000 + b


def coef(hyp: str, kind: str, alpha: float, v_norm: float) -> float:
    """Signed length of the added vector (its direction is unit v or unit placebo)."""
    return 0.0 if kind == "none" else HYPOTHESES[hyp]["sign"] * float(alpha) * float(v_norm)


def rep4_share(tokens: Sequence[int]) -> float:
    """pipeline probe/coherence.py rep4_share, verbatim."""
    grams = [tuple(tokens[i:i + 4]) for i in range(len(tokens) - 3)]
    if not grams:
        return 0.0
    seen, rep = set(), 0
    for g in grams:
        rep += g in seen; seen.add(g)
    return rep / len(grams)


def viability(text: str, finish: str, word_range=WORD_RANGE) -> List[str]:
    return scoring.lie_viability({"lie": text, "liar_finish_reason": finish, "lie_word_range": list(word_range)})


def ppl_ratio(nll: Sequence[float], nll_ref: Sequence[float]) -> float:
    if not nll or not nll_ref:
        return float("nan")
    return math.exp(float(np.mean(nll)) - float(np.mean(nll_ref)))


def cell_metrics(recs: Sequence[Dict], ref: Dict[tuple, Dict]) -> Dict:
    """recs: the 40 lies of one (hyp, kind, alpha); ref: (category, target) -> the unsteered lie of that hypothesis.
    Each record carries text, ids, finish, nll (first 64 tokens, unsteered model)."""
    reasons = [viability(r["text"], r["finish"]) for r in recs]
    bad = [any(x.split("(")[0] in NONVIABLE for x in rs) for rs in reasons]
    ratios = [ppl_ratio(r["nll"], ref[(r["category"], r["target"])]["nll"]) for r in recs]
    ratios = [x for x in ratios if x == x]
    rep = [rep4_share(r["ids"]) for r in recs]
    out = {"n": len(recs), "viable_share": 1 - float(np.mean(bad)) if recs else float("nan"),
           "nonviable_reasons": {k: sum(any(x.startswith(k) for x in rs) for rs in reasons)
                                 for k in NONVIABLE + ("refusal_or_disclaimer",)},
           "ppl_ratio_median": float(np.median(ratios)) if ratios else float("nan"), "n_ppl": len(ratios),
           "rep4_mean": float(np.mean(rep)) if rep else float("nan"),
           "words_median": float(np.median([len(r["text"].split()) for r in recs])) if recs else float("nan")}
    out["passes"] = bool(out["n"] > 0 and out["viable_share"] >= VIABLE_MIN and out["ppl_ratio_median"] == out["ppl_ratio_median"]
                         and out["ppl_ratio_median"] <= PPL_RATIO_MAX and out["rep4_mean"] <= REP4_MAX)
    return out


def analyse(records: Sequence[Dict]) -> Dict:
    """records: every pilot lie of one model. Returns per hypothesis the per-alpha metrics, the gate and the alpha."""
    out = {}
    for h in HYPOTHESES:
        ref = {(r["category"], r["target"]): r for r in records if r["hyp"] == h and r["kind"] == "none"}
        base = cell_metrics([r for r in records if r["hyp"] == h and r["kind"] == "none"], ref)
        grid = {}
        for a in ALPHAS:
            cells = {k: cell_metrics([r for r in records if r["hyp"] == h and r["kind"] == k and r["alpha"] == a], ref)
                     for k in KINDS}
            grid[str(a)] = {**cells, "coherent": all(cells[k]["passes"] for k in KINDS)}
        ok = [a for a in ALPHAS if grid[str(a)]["coherent"]]
        out[h] = {"unsteered": base, "grid": grid, "confirmatory_alpha": max(ok) if ok else None,
                  "status": "alpha chosen" if ok else "untestable: no coherent alpha"}
    return out
