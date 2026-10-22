"""Phase 2 probe stage analysis (PREREG_PHASE2 section 4; Addendum 1). Numpy only, plus the sae-ethos-pipeline
v1.1.0 transfer rule and logistic probe, used as a library.

Input, per model: `acts[L]` an (N, d) float array of block-L outputs at the last prompt token (0-based block index),
and `meta`, N dicts with category, target, condition (full / reversed / placebo) and wording (frozen / A / B / C).

Per candidate layer L:
  v_L      mean over (category, target) of h_full - h_reversed, frozen wording.
  (a)      held-out personas: for each target t, v from the other four targets; t's frozen full vs reversed items
           scored by projection; scores pooled over the five folds; AUROC (full = 1).
  (b)      held-out wordings: v_L from the frozen wording; AUROC on each paraphrase set's full vs reversed items.
  pass     the pipeline's transfer rule (probe/transfer.py): AUROC >= 0.70 and the 95% cluster-bootstrap lower bound
           > 0.50 (clusters = categories, 2,000 resamples), for (a) and for each of the three sets in (b).
  control  c_L = mean(h over frozen full and reversed) - mean(h over placebo); AUROC of full vs reversed projected on
           c_L; its 90% cluster-bootstrap interval must lie inside [0.40, 0.60]. cos(v_L, c_L) reported.
  logistic pipeline fit_logistic on z-scored activations, C by the pipeline's 5-fold cv_score over {0.01, 0.1, 1, 10}
           on all frozen full/reversed items; the same (a) and (b) AUROCs. Reported, never used for steering.
Layer rule: among candidates passing (a) and all of (b), the highest mean held-out-wording AUROC; ties to the lower
layer. No candidate passes -> the model fails the gate (no transferable valence direction): no pilot, no steering.
"""
from __future__ import annotations

from typing import Dict, List, Sequence

import numpy as np

SETS = ("A", "B", "C")
C_GRID = (0.01, 0.1, 1.0, 10.0)
CONTROL_BAND = (0.40, 0.60)
BOOT_SEED, N_BOOT = 20261027, 2000


def _pipeline():
    import sae_ethos_pipeline  # noqa: F401  (puts the pipeline's import root on sys.path)
    from probe.transfer import auroc, cluster_boot, verdict, AUROC_MIN, LOWER_MIN
    from probe.train import fit_logistic, cv_score
    return dict(auroc=auroc, cluster_boot=cluster_boot, verdict=verdict, AUROC_MIN=AUROC_MIN, LOWER_MIN=LOWER_MIN,
                fit_logistic=fit_logistic, cv_score=cv_score)


def cluster_interval(score, y, clusters, n_boot, seed, q):
    """Percentile interval (q, 1 - q) of the cluster-bootstrap AUROC, resampling as the pipeline's cluster_boot does."""
    auroc = _pipeline()["auroc"]
    rng = np.random.default_rng(seed)
    ids = np.unique(clusters); idx = {c: np.where(clusters == c)[0] for c in ids}
    out = []
    for _ in range(n_boot):
        take = np.concatenate([idx[c] for c in rng.choice(ids, size=len(ids), replace=True)])
        a = auroc(score[take], y[take])
        if a == a:
            out.append(a)
    return float(np.percentile(out, 100 * q)), float(np.percentile(out, 100 * (1 - q)))


class Index:
    def __init__(self, meta: Sequence[Dict]):
        self.meta = list(meta)
        self.cat = np.array([m["category"] for m in meta])
        self.tgt = np.array([m["target"] for m in meta])
        self.cond = np.array([m["condition"] for m in meta])
        self.word = np.array([m["wording"] for m in meta])
        self.targets = sorted(set(self.tgt))

    def sel(self, cond, wording, targets=None):
        m = (self.cond == cond) & (self.word == wording)
        if targets is not None:
            m &= np.isin(self.tgt, list(targets))
        return np.where(m)[0]

    def pairs(self, wording, targets=None):
        """Aligned (full, reversed) indices, paired by (category, target)."""
        f, r = self.sel("full", wording, targets), self.sel("reversed", wording, targets)
        rk = {(self.cat[i], self.tgt[i]): i for i in r}
        fk = [(self.cat[i], self.tgt[i]) for i in f]
        if len(rk) != len(r) or len(set(fk)) != len(fk) or set(fk) != set(rk):
            raise ValueError("full and reversed items do not pair one to one")
        return np.array(f), np.array([rk[(self.cat[i], self.tgt[i])] for i in f])


def direction(X, ix: Index, wording="frozen", targets=None):
    f, r = ix.pairs(wording, targets)
    return (X[f] - X[r]).mean(0)


def scored(X, ix: Index, w, wording, targets=None):
    f, r = ix.pairs(wording, targets)
    idx = np.concatenate([f, r])
    return X[idx] @ w, np.r_[np.ones(len(f), int), np.zeros(len(r), int)], ix.cat[idx]


def transfer_test(score, y, clusters, n_boot, seed):
    P = _pipeline()
    a = P["auroc"](score, y)
    lo, hi = P["cluster_boot"](score, y, clusters, n_boot, seed)
    return {"auroc": a, "ci95": [lo, hi], "verdict": P["verdict"](a, lo, y), "n": int(len(y))}


def held_out_personas(X, ix: Index, make_w):
    s, y, c = [], [], []
    for t in ix.targets:
        w = make_w([u for u in ix.targets if u != t])
        a, b, k = scored(X, ix, w, "frozen", [t])
        s.append(a); y.append(b); c.append(k)
    return np.concatenate(s), np.concatenate(y), np.concatenate(c)


def logistic_maker(X, ix: Index):
    """Returns make_w(targets) -> unit logistic direction in raw units, C fixed by CV on all frozen pairs."""
    P = _pipeline()
    f, r = ix.pairs("frozen")
    idx = np.concatenate([f, r]); y = np.r_[np.ones(len(f)), np.zeros(len(r))]
    Xf = X[idx].astype(np.float64)
    C = max(C_GRID, key=lambda c: P["cv_score"](Xf, y, float(c)))

    def make_w(targets=None):
        ff, rr = ix.pairs("frozen", targets)
        ii = np.concatenate([ff, rr]); yy = np.r_[np.ones(len(ff)), np.zeros(len(rr))]
        Xt = X[ii].astype(np.float64)
        mu, sd = Xt.mean(0), Xt.std(0) + 1e-6
        w, _ = P["fit_logistic"]((Xt - mu) / sd, yy, float(C))
        w = w / sd
        return w / (np.linalg.norm(w) + 1e-12)
    return make_w, float(C)


def cos(a, b):
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def analyse_layer(X, ix: Index, n_boot=N_BOOT, seed=BOOT_SEED, logistic=True):
    X = np.asarray(X, np.float64)
    v = direction(X, ix)
    out = {"v_norm": float(np.linalg.norm(v))}
    out["held_out_personas"] = transfer_test(*held_out_personas(X, ix, lambda ts: direction(X, ix, "frozen", ts)),
                                             n_boot, seed)
    out["held_out_wordings"] = {s: transfer_test(*scored(X, ix, v, s), n_boot, seed) for s in SETS}
    out["in_sample_frozen_auroc"] = _pipeline()["auroc"](*scored(X, ix, v, "frozen")[:2])
    out["passes"] = out["held_out_personas"]["verdict"] == "PASS" and \
        all(out["held_out_wordings"][s]["verdict"] == "PASS" for s in SETS)
    out["mean_wording_auroc"] = float(np.mean([out["held_out_wordings"][s]["auroc"] for s in SETS]))
    # cue-mention control
    f, r = ix.pairs("frozen")
    p = ix.sel("placebo", "frozen")
    c = X[np.concatenate([f, r])].mean(0) - X[p].mean(0)
    sc, y, cl = scored(X, ix, c, "frozen")
    a = _pipeline()["auroc"](sc, y)
    lo, hi = cluster_interval(sc, y, cl, n_boot, seed, 0.05)
    out["control"] = {"auroc": a, "ci90": [lo, hi], "inside_band": CONTROL_BAND[0] <= lo and hi <= CONTROL_BAND[1],
                      "cos_v_c": cos(v, c)}
    if logistic:
        make_w, C = logistic_maker(X, ix)
        w = make_w()
        out["logistic"] = {"C": C, "cos_with_v": cos(w, v),
                           "held_out_personas": transfer_test(*held_out_personas(X, ix, make_w), n_boot, seed),
                           "held_out_wordings": {s: transfer_test(*scored(X, ix, w, s), n_boot, seed) for s in SETS}}
    return out, v, c


def select_layer(per_layer: Dict[int, Dict]):
    """Section 4 layer rule; None if no candidate passes."""
    ok = [L for L in sorted(per_layer) if per_layer[L]["passes"]]
    if not ok:
        return None
    best = max(per_layer[L]["mean_wording_auroc"] for L in ok)
    return min(L for L in ok if per_layer[L]["mean_wording_auroc"] == best)


def analyse(acts: Dict[int, np.ndarray], meta: Sequence[Dict], candidates: Sequence[int], n_boot=N_BOOT,
            seed=BOOT_SEED, logistic=True):
    ix = Index(meta)
    per, vs, cs = {}, {}, {}
    for L in candidates:
        per[L], vs[L], cs[L] = analyse_layer(acts[L], ix, n_boot, seed, logistic)
    sel = select_layer(per)
    return {"candidates": list(candidates), "per_layer": per, "selected_layer": sel,
            "gate": "PASS" if sel is not None else "FAIL: no transferable valence direction",
            "rule": "AUROC >= 0.70 and 95% cluster-bootstrap lower bound > 0.50 for held-out personas and each of "
                    "the three held-out wordings; layer = highest mean held-out-wording AUROC, ties to the lower",
            "n_boot": n_boot, "seed": seed}, vs, cs
