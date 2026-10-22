"""Phase 2 probe-stage analysis (src/perfect_lie/phase2_probe.py) on simulated activations, and the item builder."""
import gzip
import json
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("sae_ethos_pipeline")
from src.perfect_lie import phase2_probe as P

TARGETS = ["P1", "P2", "P3", "P5", "P6"]
D = 40


def make_meta(n_cat=12):
    meta = []
    for k in range(n_cat):
        for t in TARGETS:
            for cond in ("full", "reversed", "placebo"):
                for w in (("frozen",) if cond == "placebo" else ("frozen", "A", "B", "C")):
                    meta.append({"category": f"c{k}", "target": t, "condition": cond, "wording": w})
    return meta


def simulate(meta, signal, seed=0, noise=1.0):
    """signal(m) -> d-vector added to Gaussian noise; a per-category offset is shared by all its items."""
    rng = np.random.default_rng(seed)
    cats = {m["category"] for m in meta}
    off = {c: rng.normal(scale=0.5, size=D) for c in cats}
    return np.stack([off[m["category"]] + signal(m) + rng.normal(scale=noise, size=D) for m in meta])


def e(i):
    v = np.zeros(D); v[i] = 1.0
    return v


def valence(m, scale=1.5, axis=0):
    return {"full": scale, "reversed": -scale}.get(m["condition"], 0.0) * e(axis)


def run(X, meta, **kw):
    kw.setdefault("n_boot", 200); kw.setdefault("logistic", False)
    return P.analyse({5: X}, meta, [5], **kw)[0]


def test_null_fails_gate():
    meta = make_meta()
    rep = run(simulate(meta, lambda m: np.zeros(D)), meta)
    assert rep["gate"].startswith("FAIL") and rep["selected_layer"] is None


def test_shared_valence_passes_gate():
    meta = make_meta()
    rep = run(simulate(meta, valence), meta)
    L = rep["per_layer"][5]
    assert rep["gate"] == "PASS" and rep["selected_layer"] == 5
    assert L["held_out_personas"]["auroc"] > 0.9 and all(L["held_out_wordings"][s]["auroc"] > 0.9 for s in P.SETS)


def test_wording_specific_signal_fails_held_out_wordings():
    meta = make_meta()
    rep = run(simulate(meta, lambda m: valence(m) if m["wording"] == "frozen" else np.zeros(D)), meta)
    L = rep["per_layer"][5]
    assert L["held_out_personas"]["verdict"] == "PASS"
    assert all(L["held_out_wordings"][s]["verdict"] == "FAIL" for s in P.SETS) and rep["gate"].startswith("FAIL")


def test_one_failed_wording_fails_gate():
    meta = make_meta()
    rep = run(simulate(meta, lambda m: valence(m) if m["wording"] != "C" else np.zeros(D)), meta)
    L = rep["per_layer"][5]
    assert L["held_out_wordings"]["A"]["verdict"] == "PASS" and L["held_out_wordings"]["C"]["verdict"] == "FAIL"
    assert not L["passes"] and rep["gate"].startswith("FAIL")


def test_persona_specific_signal_fails_held_out_personas():
    meta = make_meta()
    axis = {t: 1 + i for i, t in enumerate(TARGETS)}
    rep = run(simulate(meta, lambda m: valence(m, axis=axis[m["target"]])), meta)
    L = rep["per_layer"][5]
    assert L["held_out_personas"]["verdict"] == "FAIL" and rep["gate"].startswith("FAIL")


def test_sign_full_scores_higher():
    meta = make_meta()
    rep = run(simulate(meta, lambda m: -valence(m)), meta)   # reversed > full along the axis: v flips with it
    assert rep["per_layer"][5]["held_out_wordings"]["A"]["auroc"] > 0.9


def test_control_inside_band_when_cue_mention_is_shared():
    meta = make_meta(20)
    mention = lambda m: 0.0 if m["condition"] == "placebo" else 1.0
    rep = run(simulate(meta, lambda m: valence(m) + 3.0 * mention(m) * e(7)), meta)
    c = rep["per_layer"][5]["control"]
    assert c["inside_band"] and abs(c["cos_v_c"]) < 0.5


def test_control_flags_valence_confounded_with_mention():
    meta = make_meta(20)
    rep = run(simulate(meta, lambda m: valence(m) + (3.0 * e(0) if m["condition"] == "full" else 0.0)), meta)
    assert not rep["per_layer"][5]["control"]["inside_band"]


def test_layer_rule_highest_mean_wording_auroc_ties_to_lower():
    pl = {21: {"passes": True, "mean_wording_auroc": 0.80}, 22: {"passes": True, "mean_wording_auroc": 0.90},
          23: {"passes": True, "mean_wording_auroc": 0.90}, 24: {"passes": False, "mean_wording_auroc": 0.99}}
    assert P.select_layer(pl) == 22
    assert P.select_layer({21: {"passes": False, "mean_wording_auroc": 0.9}}) is None


def test_multi_layer_selection():
    meta = make_meta()
    X1 = simulate(meta, lambda m: valence(m, 0.6), seed=1)
    X2 = simulate(meta, lambda m: valence(m, 2.0), seed=2)
    rep, vs, cs = P.analyse({21: X1, 22: X2, 23: simulate(meta, lambda m: np.zeros(D), seed=3)}, meta, [21, 22, 23],
                            n_boot=200, logistic=False)
    assert rep["selected_layer"] == 22 and not rep["per_layer"][23]["passes"] and set(vs) == {21, 22, 23}


def test_logistic_is_reported_and_deterministic():
    meta = make_meta(8)
    X = simulate(meta, valence)
    a = run(X, meta, logistic=True)["per_layer"][5]["logistic"]
    b = run(X, meta, logistic=True)["per_layer"][5]["logistic"]
    assert a == b and a["C"] in P.C_GRID and a["held_out_personas"]["auroc"] > 0.8


def test_bootstrap_is_seeded():
    meta = make_meta()
    X = simulate(meta, valence)
    assert run(X, meta) == run(X, meta)


def test_pairing_mismatch_raises():
    meta = make_meta(3)
    meta = [m for m in meta if not (m["category"] == "c0" and m["target"] == "P1" and m["condition"] == "reversed"
                                    and m["wording"] == "frozen")]
    with pytest.raises(ValueError):
        P.direction(np.zeros((len(meta), D)), P.Index(meta))


ITEMS = Path(__file__).resolve().parents[1] / "results/phase2/probe/probe_items.jsonl.gz"


@pytest.mark.skipif(not ITEMS.exists(), reason="probe items not built")
def test_committed_items():
    items = [json.loads(l) for l in gzip.open(ITEMS, "rt")]
    split = json.loads((ITEMS.parent / "category_split.json").read_text())
    assert len(split["training"]) == 40 and len(split["evaluation"]) == 32
    assert not set(split["training"]) & set(split["evaluation"])
    assert {i["category"] for i in items} == set(split["training"])
    assert len(items) == 2 * 40 * 5 * 9 and len({i["item_id"] for i in items}) == len(items)
    for i in items:
        text = json.dumps(i["messages"])
        assert "well- known" not in text and i["belief_block"].startswith("- ")
        assert i["strip_llama_date"] == i["model_id"].startswith("meta-llama")
        assert i["strip_trailing_newline"] == i["model_id"].startswith("google/gemma")
    frozen = {(i["model_id"], i["category"], i["target"], i["condition"]): i for i in items if i["wording"] == "frozen"}
    for i in items:
        if i["wording"] != "frozen":
            f = frozen[(i["model_id"], i["category"], i["target"], i["condition"])]
            assert i["messages"] != f["messages"]
            assert len(i["messages"]) == len(f["messages"])
