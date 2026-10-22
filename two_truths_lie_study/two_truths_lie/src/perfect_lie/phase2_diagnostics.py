"""Phase 2 Addendum 3: diagnostics on the stored probe-stage activations. The gate decisions and layer choices of
the probe stage stand as registered; nothing here changes them.

(a) Label-permutation null, at the selected layer and its two neighbours. One permutation: within each target, the
    full and reversed labels of each (category, target) pair are swapped with probability 1/2, and the same swap is
    applied to that pair in every wording (frozen, A, B, C). This is a within-persona shuffle that keeps the
    registered pairing: every pair still has one "full" and one "reversed" item. (A free shuffle of a target's 80
    labels can put both items of a pair on one side; the two share everything but the valence words, so the null
    would then measure item content, not the test. In simulation that biases the wording null upward.)
    The registered tests are then recomputed under the permuted labels:
      held-out personas  for each target, v = mean(h, labelled full) - mean(h, labelled reversed) over the other
                         four targets' frozen items; that target's frozen items scored by projection; pooled; AUROC;
      held-out wordings  v from all five targets' frozen items; AUROC on each set's items.
    With the true labels these equal the registered statistics (balanced, complete pairs: the difference of group
    means is the mean of paired differences); `observed` is recomputed here and checked against the registered value.
    Reported per test: the null distribution (mean, SD, quantiles), the observed AUROC and the permutation
    p = (1 + #{null >= observed}) / (1 + n_perm).
    Stop rule (Addendum 3): if the mean null AUROC of any reported test (model x layer x test) lies outside
    [0.40, 0.60], the pilot is not run.
(b) Within-fold persona AUROC, every candidate layer: for each held-out target, v from the other four (registered
    direction), AUROC of that target's frozen full vs reversed projections only, with the registered cluster
    bootstrap (clusters = categories). Also each fold's mean projection on unit v per class, which shows how the
    folds' score levels line up in the pooled figure. Descriptive.
"""
from __future__ import annotations

from typing import Dict, List, Sequence

import numpy as np

try:
    from . import phase2_probe as P
except ImportError:      # on the pod, the files sit side by side
    import phase2_probe as P

PERM_SEED, N_PERM = 20261029, 1000
NULL_BAND = (0.40, 0.60)
TESTS = ("held_out_personas",) + tuple(P.SETS)


def _auroc(score, y):
    return float(P._pipeline()["auroc"](score, y))


def relabel(ix: P.Index, rng) -> np.ndarray:
    """One permutation of the condition labels (see the module docstring); placebo items keep theirs."""
    f, _ = ix.pairs("frozen")                     # one entry per (category, target), in a fixed order
    swap = {(ix.cat[i], ix.tgt[i]): bool(s) for i, s in zip(f, rng.integers(0, 2, size=len(f)))}
    cond = ix.cond.copy()
    flip = {"full": "reversed", "reversed": "full"}
    for i in np.where(np.isin(ix.cond, ("full", "reversed")))[0]:
        if swap[(ix.cat[i], ix.tgt[i])]:
            cond[i] = flip[ix.cond[i]]
    return cond


def _mask(ix, cond, wording, targets):
    return (ix.word == wording) & np.isin(ix.tgt, list(targets)) & np.isin(cond, ("full", "reversed"))


def _direction(X, ix, cond, targets):
    m = _mask(ix, cond, "frozen", targets)
    return X[m & (cond == "full")].mean(0) - X[m & (cond == "reversed")].mean(0)


def _score(X, ix, cond, w, wording, targets):
    m = np.where(_mask(ix, cond, wording, targets))[0]
    return X[m] @ w, (cond[m] == "full").astype(int)


def tests_under(X, ix: P.Index, cond) -> Dict[str, float]:
    """The registered held-out-persona and held-out-wording AUROCs, computed under the labels `cond`."""
    s, y = [], []
    for t in ix.targets:
        a, b = _score(X, ix, cond, _direction(X, ix, cond, [u for u in ix.targets if u != t]), "frozen", [t])
        s.append(a); y.append(b)
    out = {"held_out_personas": _auroc(np.concatenate(s), np.concatenate(y))}
    v = _direction(X, ix, cond, ix.targets)
    for S in P.SETS:
        out[S] = _auroc(*_score(X, ix, cond, v, S, ix.targets))
    return out


def permutation_null(X, ix: P.Index, n_perm=N_PERM, seed=PERM_SEED) -> Dict:
    X = np.asarray(X, np.float64)
    obs = tests_under(X, ix, ix.cond)
    rng = np.random.default_rng(seed)
    null = {k: [] for k in TESTS}
    for _ in range(n_perm):
        r = tests_under(X, ix, relabel(ix, rng))
        for k in TESTS:
            null[k].append(r[k])
    out = {}
    for k in TESTS:
        z = np.array(null[k])
        out[k] = {"observed": obs[k], "p": float((1 + np.sum(z >= obs[k])) / (1 + n_perm)),
                  "null": {"mean": float(z.mean()), "sd": float(z.std(ddof=1)), "min": float(z.min()),
                           "q025": float(np.quantile(z, 0.025)), "q50": float(np.quantile(z, 0.5)),
                           "q975": float(np.quantile(z, 0.975)), "max": float(z.max())},
                  "inside_band": bool(NULL_BAND[0] <= z.mean() <= NULL_BAND[1]),
                  "values": [float(a) for a in z]}
    return out


def within_fold(X, ix: P.Index, n_boot=P.N_BOOT, seed=P.BOOT_SEED) -> Dict:
    X = np.asarray(X, np.float64)
    folds = {}
    for t in ix.targets:
        v = P.direction(X, ix, "frozen", [u for u in ix.targets if u != t])
        sc, y, cl = P.scored(X, ix, v, "frozen", [t])
        lo, hi = P._pipeline()["cluster_boot"](sc, y, cl, n_boot, seed)
        u = sc / (np.linalg.norm(v) + 1e-12)
        folds[t] = {"auroc": _auroc(sc, y), "ci95": [float(lo), float(hi)], "n": int(len(y)),
                    "mean_unit_projection": {"full": float(u[y == 1].mean()), "reversed": float(u[y == 0].mean())}}
    a = [f["auroc"] for f in folds.values()]
    return {"folds": folds, "mean_auroc": float(np.mean(a)), "min_auroc": float(np.min(a))}


def diagnose(acts: Dict[int, np.ndarray], meta: Sequence[Dict], perm_layers: Sequence[int], candidates: Sequence[int],
             registered: Dict, n_perm=N_PERM, seed=PERM_SEED, n_boot=P.N_BOOT, boot_seed=P.BOOT_SEED) -> Dict:
    """`registered`: the probe stage's probe_result.json, for the side-by-side figures and the identity check."""
    ix = P.Index(meta)
    reg = registered["per_layer"]
    perm, outside, mismatch = {}, [], []
    for L in perm_layers:
        perm[L] = permutation_null(acts[L], ix, n_perm, seed)
        r = reg[str(L)]
        for k in TESTS:
            rv = r["held_out_personas"]["auroc"] if k == "held_out_personas" else r["held_out_wordings"][k]["auroc"]
            perm[L][k]["registered"] = rv
            if abs(perm[L][k]["observed"] - rv) > 1e-6:
                mismatch.append(f"layer {L} {k}: {perm[L][k]['observed']} vs registered {rv}")
            if not perm[L][k]["inside_band"]:
                outside.append(f"layer {L} {k}: mean null {perm[L][k]['null']['mean']:.3f}")
    wf = {}
    for L in candidates:
        wf[L] = within_fold(acts[L], ix, n_boot, boot_seed)
        wf[L]["pooled_registered"] = reg[str(L)]["held_out_personas"]["auroc"]
    return {"permutation": {str(k): v for k, v in perm.items()}, "within_fold": {str(k): v for k, v in wf.items()},
            "stop_rule": {"band": list(NULL_BAND), "outside": outside, "pilot_may_run": not outside},
            "observed_matches_registered": not mismatch, "mismatches": mismatch,
            "perm_layers": list(perm_layers), "candidates": list(candidates), "selected_layer": registered["selected_layer"],
            "n_perm": n_perm, "seed": seed, "n_boot": n_boot, "boot_seed": boot_seed}
