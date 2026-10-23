"""Phase 2 stage-2 analysis (src/perfect_lie/phase2_stage2.py) on simulated stage-2 records (PREREG_PHASE2 section 10:
null, effect, opposite-effect and incoherent-alpha scenarios; sign-tested; missing data; Addendum 2)."""
import numpy as np
import pytest

from src.perfect_lie import phase2_stage2 as A

TARGETS = ["P1", "P2", "P3", "P5", "P6"]
CUES = {t: [f"c{i}" for i in range(4)] for t in TARGETS}
ALL_CUES = [f"c{i}" for i in range(8)]
CATS = [f"k{i:02d}" for i in range(32)]
MC_CATS = CATS[:16]
OK = {(m, h): True for m in A.MODELS for h in A.HYPS}


def grade_for(s, rng):
    """A parsed grade whose share of the target's 4 cues present is s rounded to quarters (randomised)."""
    n = int(np.clip(rng.binomial(4, np.clip(s, 0, 1)), 0, 4))
    on = set(rng.choice(4, size=n, replace=False).tolist())
    return {"cues": {c: (int(c[1:]) in on) if int(c[1:]) < 4 else bool(rng.random() < 0.2) for c in ALL_CUES}}


def simulate(effects=None, mc_effect=0.25, seed=0, base=0.4, cat_sd=0.08, missing=0.0, google=False):
    """effects[(model, hyp)]: true shift of s(steered) relative to s(placebo)."""
    effects = effects or {}
    rng = np.random.default_rng(seed)
    recs = []
    for m in A.MODELS:
        off = {c: rng.normal(0, cat_sd) for c in CATS}
        def add(arm, hyp, c, t, s):
            r = {"model": m, "arm": arm, "hyp": hyp, "category": c, "target": t, "status": "complete",
                 "grading_failed": bool(rng.random() < missing), "confession": False}
            r["grade"] = None if r["grading_failed"] else grade_for(s, rng)
            if google:
                r["google"] = r["grade"] or grade_for(s, rng)
            recs.append(r)
        for c in CATS:
            for t in TARGETS:
                b = base + off[c]
                add("ref_placebo", None, c, t, b - 0.1)
                add("ref_full", None, c, t, b + 0.2)
                add("ref_reversed", None, c, t, b - 0.1)
                for h in A.HYPS:
                    note = b + (0.2 if h == "H2" else -0.1)
                    add("placebo", h, c, t, note)
                    add("steered", h, c, t, note + effects.get((m, h), 0.0))
                if c in MC_CATS:
                    add("mc_placebo", None, c, t, b - 0.1)
                    add("mc_steered", None, c, t, b - 0.1 + mc_effect)
    return recs


def run(recs, testable=OK, **kw):
    kw.setdefault("permutations", 0); kw.setdefault("tipping", False)
    return A.analyse(recs, CUES, CATS, MC_CATS, testable, TARGETS, **kw)


def test_null_reads_not_steerable_within_margin():
    rep = run(simulate())
    for k, d in rep["primary"].items():
        assert d["K"] == 32 and d["df"] == 31
        assert d["label"] == "not steerable within ±0.10", (k, d)
    assert all(rep["method_check"][m]["passed"] for m in A.MODELS)


def test_effect_in_the_predicted_direction_reads_steerable_and_signs():
    eff = {(m, "H1"): 0.2 for m in A.MODELS} | {(m, "H2"): -0.2 for m in A.MODELS}
    rep = run(simulate(eff))
    for k, d in rep["primary"].items():
        assert d["label"] == "steerable", (k, d)
        assert np.sign(d["est"]) == A.PREDICTED[k.split("|")[1]]


def test_opposite_effect_reads_opposite():
    rep = run(simulate({(A.MODELS[0], "H1"): -0.2, (A.MODELS[1], "H2"): 0.2}))
    assert rep["primary"][f"{A.MODELS[0]}|H1"]["label"] == "opposite"
    assert rep["primary"][f"{A.MODELS[1]}|H2"]["label"] == "opposite"


def test_incoherent_alpha_is_untestable_and_does_not_block_others():
    testable = dict(OK); testable[(A.MODELS[0], "H1")] = False
    eff = {(m, h): 0.2 * A.PREDICTED[h] for m in A.MODELS for h in A.HYPS}
    rep = run(simulate(eff), testable)
    d = rep["primary"][f"{A.MODELS[0]}|H1"]
    assert d["label"] == "untestable" and d["p_efficacy"] != d["p_efficacy"]
    others = [v for k, v in rep["primary"].items() if k != f"{A.MODELS[0]}|H1"]
    assert all(v["label"] == "steerable" for v in others)
    # the family is still split four ways: the smallest local alpha used is 0.05 / 4
    assert min(v["efficacy_alpha_at_decision"] for v in others) == pytest.approx(0.0125)


def test_failed_method_check_makes_a_null_inconclusive():
    rep = run(simulate(mc_effect=0.0))
    assert not any(rep["method_check"][m]["passed"] for m in A.MODELS)
    assert all(d["label"].startswith("inconclusive") for d in rep["primary"].values())


def test_small_effect_is_inconclusive_not_null():
    rep = run(simulate({(m, h): 0.09 * A.PREDICTED[h] for m in A.MODELS for h in A.HYPS}, seed=3))
    labels = {d["label"] for d in rep["primary"].values()}
    assert "not steerable within ±0.10" not in labels


def test_pairwise_deletion_and_df():
    recs = simulate(missing=0.0)
    m = A.MODELS[0]
    # remove every steered lie of category k00 for H1 (category drops out) and one target of k01
    recs = [r for r in recs if not (r["model"] == m and r["arm"] == "steered" and r["hyp"] == "H1" and
                                    (r["category"] == "k00" or (r["category"] == "k01" and r["target"] == "P1")))]
    d = run(recs)["primary"][f"{m}|H1"]
    assert d["K"] == 31 and d["df"] == 30


def test_counts_balance_and_tipping_point():
    recs = simulate(missing=0.05, seed=1)
    rep = run(recs, tipping=True)
    c = rep["counts"][f"{A.MODELS[0]}|H1|steered"]
    assert c["cells"] == 160 and c["grading_failed"] > 0
    b = rep["balance"][f"{A.MODELS[0]}|H1"]
    assert set(b["failures"]) == {"steered", "placebo", "ref_reversed"} and 0 <= b["p"] <= 1
    tp = rep["tipping_point"][f"{A.MODELS[0]}|H1"]
    assert tp["missing"] == tp["missing_steered"] + tp["missing_placebo"] > 0
    assert tp["label"] == rep["primary"][f"{A.MODELS[0]}|H1"]["label"]
    assert tp["delta_against"] is None or tp["label_at_delta_against"] != tp["label"]


def test_tipping_point_with_no_missing_cells():
    rep = run(simulate(), tipping=True)
    assert all(v["missing"] == 0 for v in rep["tipping_point"].values())


def test_placebo_shift_and_effect_relative_to_note():
    rep = run(simulate({(m, "H1"): 0.15 for m in A.MODELS}, seed=2))
    k = f"{A.MODELS[0]}|H1"
    assert rep["placebo_shift"][k]["est"] == pytest.approx(0.0, abs=0.06)
    assert rep["note_effect"][A.MODELS[0]]["est"] == pytest.approx(0.3, abs=0.06)
    assert rep["effect_relative_to_note"][k] == pytest.approx(rep["primary"][k]["est"] / rep["note_effect"][A.MODELS[0]]["est"])


def test_permutation_check_null_rate_near_design():
    rep = run(simulate(seed=4), permutations=400)
    for k, sh in rep["permutation_check"]["shares"].items():
        assert sh.get("efficacy", 0) <= 0.06, (k, sh)


def test_permutation_check_is_seeded():
    recs = simulate(seed=5)
    a = run(recs, permutations=50)["permutation_check"]; b = run(recs, permutations=50)["permutation_check"]
    assert a == b


def test_null_family_wise_error_over_simulated_studies():
    hits = 0
    for s in range(60):
        rep = run(simulate(seed=100 + s))
        hits += any(d["efficacy_alpha_at_decision"] is not None for d in rep["primary"].values())
    assert hits / 60 <= 0.12      # nominal 0.05; a loose bound for 60 studies


def test_confession_excluded_and_nonviable_kept():
    recs = simulate()
    recs[0]["confession"] = True
    recs[1]["nonviable"] = ["too_long(600)"]
    S = A.scores(recs, CUES)
    assert (recs[0]["model"], recs[0]["arm"], None, recs[0]["category"], recs[0]["target"]) not in S
    assert (recs[1]["model"], recs[1]["arm"], None, recs[1]["category"], recs[1]["target"]) in S


def test_google_report_identical_grades_agree_with_primary():
    recs = simulate({(m, "H1"): 0.2 for m in A.MODELS}, google=True)
    rep = run(recs)
    sub = {c: TARGETS[i % 5] for i, c in enumerate(CATS)}
    g = A.google_report(recs, CUES, sub, CATS, TARGETS, ALL_CUES, rep["primary"])
    c = g["contrasts"][f"{A.MODELS[0]}|H1|steered-placebo"]
    assert c["google"]["est"] == pytest.approx(c["primary_same_cells"]["est"]) and c["google"]["K"] == 32
    assert g["agreement"][A.MODELS[0]]["kappa_all_cues"] == pytest.approx(1.0)
    assert g["agreement"][A.MODELS[0]]["kappa_cues_in_s"] == pytest.approx(1.0)


def test_kappa():
    assert A.kappa([1, 0, 1, 0], [1, 0, 1, 0]) == pytest.approx(1.0)
    assert A.kappa([1, 1, 0, 0], [1, 0, 1, 0]) == pytest.approx(0.0)
