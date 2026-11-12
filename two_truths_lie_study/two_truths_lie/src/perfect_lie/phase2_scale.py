"""Phase 2, before the pilot: the scale of the steering vector relative to each persona's activations (descriptive).

Section 6 adds unit(v_L*) x alpha x ||v_L*|| at block L*, the same vector for every persona and position (alpha = 1
adds the pooled average full - reversed shift). This reports, per persona, at the selected layer, on the frozen
training items (last prompt token):
  residual_norm     ||h|| over the persona's frozen full and reversed items (quantiles);
  gap               per (category) pair, (h_full - h_reversed) . unit(v) with the registered v (quantiles, mean);
  shift_norm        ||mean over pairs of (h_full - h_reversed)|| and its cosine with v;
  level             mean h . unit(v) per condition (the offsets seen in the within-fold diagnostics);
  v_over_norm       ||v|| / median residual norm, i.e. the alpha = 1 step as a share of the persona's residual norm.
Plus the max / min ratio across personas of the median residual norm, the mean gap and the shift norm.
"""
from __future__ import annotations

from typing import Dict, Sequence

import numpy as np

try:
    from . import phase2_probe as P
except ImportError:      # on the pod, the files sit side by side
    import phase2_probe as P


def _q(x):
    x = np.asarray(x, float)
    return {"mean": float(x.mean()), "q10": float(np.quantile(x, 0.1)), "median": float(np.median(x)),
            "q90": float(np.quantile(x, 0.9)), "min": float(x.min()), "max": float(x.max())}


def persona_scale(X, ix: P.Index, v) -> Dict:
    X = np.asarray(X, np.float64)
    v = np.asarray(v, np.float64)
    u = v / np.linalg.norm(v)
    per = {}
    for t in ix.targets + ["all"]:
        f, r = ix.pairs("frozen", None if t == "all" else [t])
        d = X[f] - X[r]
        m = d.mean(0)
        norms = np.linalg.norm(X[np.concatenate([f, r])], axis=1)
        per[t] = {"n_pairs": int(len(f)), "residual_norm": _q(norms), "gap": _q(d @ u),
                  "shift_norm": float(np.linalg.norm(m)), "shift_cos_v": float(m @ u / np.linalg.norm(m)),
                  "level": {"full": float((X[f] @ u).mean()), "reversed": float((X[r] @ u).mean())},
                  "v_over_norm": float(np.linalg.norm(v) / np.median(norms))}
    ps = [per[t] for t in ix.targets]
    ratio = lambda xs: float(max(xs) / min(xs)) if min(xs) > 0 else float("inf")
    return {"v_norm": float(np.linalg.norm(v)), "personas": per,
            "max_min_ratio": {"residual_norm_median": ratio([p["residual_norm"]["median"] for p in ps]),
                              "gap_mean": ratio([p["gap"]["mean"] for p in ps]),
                              "shift_norm": ratio([p["shift_norm"] for p in ps])}}


def scale_report(acts: Dict[int, np.ndarray], meta: Sequence[Dict], layers: Sequence[int], V: np.ndarray) -> Dict:
    """`V`: the registered v at every layer (vectors.npz 'v', n_layers x d)."""
    ix = P.Index(meta)
    return {"layers": {str(L): persona_scale(acts[L], ix, V[L]) for L in layers}}
