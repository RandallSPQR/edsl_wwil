"""Steering-scale report (src/perfect_lie/phase2_scale.py) on simulated activations."""
import numpy as np
import pytest

from src.perfect_lie import phase2_probe as P
from src.perfect_lie import phase2_scale as S

TARGETS = ["P1", "P2", "P3", "P5", "P6"]
DIM = 20


def make_meta(n_cat=8):
    return [{"category": f"c{k}", "target": t, "condition": cond, "wording": "frozen"}
            for k in range(n_cat) for t in TARGETS for cond in ("full", "reversed")]


def test_gap_and_norm_per_persona():
    gap = dict(zip(TARGETS, (1.0, 2.0, 3.0, 4.0, 6.0)))
    base = dict(zip(TARGETS, (10.0, 10.0, 20.0, 20.0, 30.0)))
    meta = make_meta(); ix = P.Index(meta)
    e0, e1 = np.eye(DIM)[0], np.eye(DIM)[1]
    X = np.stack([base[m["target"]] * e1 + (gap[m["target"]] / 2 if m["condition"] == "full" else -gap[m["target"]] / 2) * e0
                  for m in meta])
    v = P.direction(X, ix)
    rep = S.persona_scale(X, ix, v)
    for t in TARGETS:
        p = rep["personas"][t]
        assert p["gap"]["mean"] == pytest.approx(gap[t]) and p["shift_norm"] == pytest.approx(gap[t])
        assert p["shift_cos_v"] == pytest.approx(1.0)
        assert p["level"]["full"] - p["level"]["reversed"] == pytest.approx(gap[t])
        assert p["residual_norm"]["median"] == pytest.approx(np.hypot(base[t], gap[t] / 2))
    assert rep["v_norm"] == pytest.approx(np.mean(list(gap.values())))
    assert rep["max_min_ratio"]["gap_mean"] == pytest.approx(6.0)
    assert rep["max_min_ratio"]["residual_norm_median"] == pytest.approx(np.hypot(30, 3) / np.hypot(10, 0.5))
    assert rep["personas"]["all"]["n_pairs"] == 8 * len(TARGETS)


def test_scale_report_layers():
    meta = make_meta(); ix = P.Index(meta)
    X = np.random.default_rng(0).normal(size=(len(meta), DIM))
    V = np.stack([P.direction(X, ix)] * 3)
    rep = S.scale_report({1: X, 2: X}, meta, [1, 2], V)
    assert set(rep["layers"]) == {"1", "2"}
