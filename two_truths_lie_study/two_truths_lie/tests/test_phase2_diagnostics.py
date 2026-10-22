"""Phase 2 Addendum 3 diagnostics (src/perfect_lie/phase2_diagnostics.py) on simulated activations.

The pipeline's AUROC and cluster bootstrap are replaced by plain implementations, so these tests run without
sae-ethos-pipeline; on the pod the pipeline's own functions are used.
"""
import numpy as np
import pytest
from scipy.stats import rankdata

from src.perfect_lie import phase2_diagnostics as D
from src.perfect_lie import phase2_probe as P

TARGETS = ["P1", "P2", "P3", "P5", "P6"]
DIM = 30


def auroc(score, y):
    score, y = np.asarray(score, float), np.asarray(y, int)
    n1, n0 = int(y.sum()), int(len(y) - y.sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = rankdata(score)
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def cluster_boot(score, y, clusters, n_boot, seed):
    rng = np.random.default_rng(seed)
    ids = np.unique(clusters); idx = {c: np.where(clusters == c)[0] for c in ids}
    out = []
    for _ in range(n_boot):
        take = np.concatenate([idx[c] for c in rng.choice(ids, size=len(ids))])
        a = auroc(score[take], y[take])
        if a == a:
            out.append(a)
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def verdict(a, lo, y):
    return "PASS" if a >= 0.70 and lo > 0.50 else "FAIL"


@pytest.fixture(autouse=True)
def fake_pipeline(monkeypatch):
    monkeypatch.setattr(P, "_pipeline", lambda: {"auroc": auroc, "cluster_boot": cluster_boot, "verdict": verdict})


def make_meta(n_cat=10):
    return [{"category": f"c{k}", "target": t, "condition": cond, "wording": w}
            for k in range(n_cat) for t in TARGETS for cond in ("full", "reversed", "placebo")
            for w in (("frozen",) if cond == "placebo" else ("frozen", "A", "B", "C"))]


def simulate(meta, signal, seed=0):
    rng = np.random.default_rng(seed)
    off = {c: rng.normal(scale=0.5, size=DIM) for c in {m["category"] for m in meta}}
    return np.stack([off[m["category"]] + signal(m) + rng.normal(size=DIM) for m in meta])


def e(i):
    v = np.zeros(DIM); v[i] = 1.0
    return v


def valence(m, scale=1.5):
    return {"full": scale, "reversed": -scale}.get(m["condition"], 0.0) * e(0)


def test_relabel_swaps_whole_pairs_consistently_across_wordings():
    meta = make_meta(); ix = P.Index(meta)
    cond = D.relabel(ix, np.random.default_rng(1))
    assert (cond[ix.cond == "placebo"] == "placebo").all()
    swapped = {}
    for i in np.where(ix.cond != "placebo")[0]:
        k = (ix.cat[i], ix.tgt[i])
        s = cond[i] != ix.cond[i]
        assert swapped.setdefault(k, s) == s          # one decision per pair, in every wording and condition
    for w in ("frozen",) + P.SETS:                    # every pair keeps one full and one reversed item
        for k in swapped:
            m = (ix.cat == k[0]) & (ix.tgt == k[1]) & (ix.word == w) & (ix.cond != "placebo")
            assert sorted(cond[m]) == ["full", "reversed"]
    assert 0 < sum(swapped.values()) < len(swapped)


def test_observed_equals_registered_statistics():
    meta = make_meta(); ix = P.Index(meta)
    X = simulate(meta, valence)
    reg = P.analyse_layer(X, ix, n_boot=50, logistic=False)[0]
    obs = D.tests_under(X, ix, ix.cond)
    assert obs["held_out_personas"] == pytest.approx(reg["held_out_personas"]["auroc"], abs=1e-12)
    for s in P.SETS:
        assert obs[s] == pytest.approx(reg["held_out_wordings"][s]["auroc"], abs=1e-12)


def test_null_centred_on_half_and_signal_far_above_it():
    meta = make_meta(); ix = P.Index(meta)
    X = simulate(meta, valence)
    out = D.permutation_null(X, ix, n_perm=200, seed=3)
    for k in D.TESTS:
        assert 0.40 <= out[k]["null"]["mean"] <= 0.60 and out[k]["inside_band"]
        assert out[k]["observed"] > out[k]["null"]["q975"] and out[k]["p"] < 0.01


def test_null_unbiased_when_pairs_share_strong_content():
    """Each (category, target) pair carries a large component shared by both conditions and every wording (the
    note's content), on top of the valence signal: the null stays centred near 0.5 for every test."""
    meta = make_meta(); ix = P.Index(meta)
    rng = np.random.default_rng(5)
    content = {(m["category"], m["target"]): rng.normal(scale=3.0, size=DIM) for m in meta}
    X = simulate(meta, lambda m: valence(m) + content[(m["category"], m["target"])])
    out = D.permutation_null(X, ix, n_perm=300, seed=4)
    for k in D.TESTS:
        assert abs(out[k]["null"]["mean"] - 0.5) < 0.05, (k, out[k]["null"]["mean"])


def test_pure_noise_observed_inside_null():
    meta = make_meta(); ix = P.Index(meta)
    out = D.permutation_null(simulate(meta, lambda m: np.zeros(DIM)), ix, n_perm=200, seed=3)
    for k in D.TESTS:
        assert out[k]["inside_band"] and out[k]["p"] > 0.01


def test_permutation_seeded():
    meta = make_meta(); ix = P.Index(meta)
    X = simulate(meta, valence)
    a = D.permutation_null(X, ix, n_perm=20, seed=7); b = D.permutation_null(X, ix, n_perm=20, seed=7)
    assert all(a[k]["values"] == b[k]["values"] for k in D.TESTS)


def test_within_fold_high_when_persona_offsets_depress_the_pooled_figure():
    """Each target shifts both its conditions along the valence axis by its own amount: separation is near perfect
    inside every fold, while the pooled figure mixes folds with different score levels."""
    shift = dict(zip(TARGETS, (-6.0, -3.0, 0.0, 3.0, 6.0)))
    meta = make_meta(); ix = P.Index(meta)
    X = simulate(meta, lambda m: valence(m, 2.5) + shift[m["target"]] * e(0))
    wf = D.within_fold(X, ix, n_boot=50, seed=1)
    pooled = P.analyse_layer(X, ix, n_boot=50, logistic=False)[0]["held_out_personas"]["auroc"]
    assert wf["min_auroc"] > 0.95 and pooled < 0.85
    m = [wf["folds"][t]["mean_unit_projection"]["full"] for t in TARGETS]
    assert m == sorted(m)


def test_diagnose_stop_rule_and_registered_check():
    meta = make_meta(); ix = P.Index(meta)
    X = simulate(meta, valence)
    reg_layer = P.analyse_layer(X, ix, n_boot=50, logistic=False)[0]
    registered = {"per_layer": {"5": reg_layer, "6": reg_layer}, "selected_layer": 5}
    rep = D.diagnose({5: X, 6: X}, meta, [5], [5, 6], registered, n_perm=50, seed=2, n_boot=50)
    assert rep["observed_matches_registered"] and rep["stop_rule"]["pilot_may_run"]
    assert set(rep["within_fold"]) == {"5", "6"} and rep["within_fold"]["5"]["pooled_registered"] == reg_layer[
        "held_out_personas"]["auroc"]
    bad = {"per_layer": {"5": dict(reg_layer, held_out_personas=dict(reg_layer["held_out_personas"], auroc=0.1))},
           "selected_layer": 5}
    rep = D.diagnose({5: X}, meta, [5], [5], bad, n_perm=10, seed=2, n_boot=20)
    assert not rep["observed_matches_registered"] and rep["mismatches"]
