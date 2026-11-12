"""Final analysis of the reversed-note follow-up (reversed_analysis.py), offline on synthetic data."""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.perfect_lie import reversed_analysis as A
from src.perfect_lie import reversed_run as R

FA = Path(__file__).resolve().parents[1] / "results/perfect_lie_reversed/final_analysis"
sys.path.insert(0, str(FA))


@pytest.fixture(scope="module")
def instrument():
    from src.perfect_lie.personas import load_instrument
    return load_instrument()


@pytest.fixture(scope="module")
def small_cfg():
    cfg = R.load_config()
    return dict(cfg, categories=cfg["categories"][:16])


def test_holm_is_stepwise_in_p_order():
    a = A.holm({"a": 0.001, "b": 0.02, "c": 0.013, "d": 0.5})
    assert a == {"a": 0.0125, "c": 0.016666666666666666, "b": 0.025, "d": None}
    assert A.holm({"a": 0.02, "b": 0.001}) == {"b": 0.025, "a": 0.05}
    assert A.holm({"a": 0.02, "b": 0.03, "c": 0.04, "d": 0.04}) == {m: None for m in "abcd"}   # first fails -> none


def test_labels_cover_every_registered_outcome():
    assert A.label(0.0125, None, 0.3) == "belief-tracking"
    assert A.label(0.0125, 0.0125, 0.03) == "valence effect present, within ±0.10"
    assert A.label(None, 0.05, 0.0) == "no valence effect beyond ±0.10"
    assert A.label(None, None, 0.05) == "inconclusive"
    assert A.label(0.05, None, -0.3).startswith("fewer named cues under full")
    assert A.label(0.0125, 0.0125, -0.03) == "valence effect present, within ±0.10"   # registered joint label, any sign


def test_tost_and_two_sided_p():
    assert A._p_tost(0.0, 0.02, 71) < 1e-4 and A._p_tost(0.0, 0.2, 71) > 0.3
    assert A._p_tost(0.12, 0.01, 71) > 0.9                      # outside the margin: not equivalent
    assert abs(A._p_two(0.0, 0.05, 71) - 1) < 1e-9


def test_grader_block_and_status():
    block = {"status": "error", "parse_failures": [{"call": "grader[primary]", "finish_reason": "content_filter"}] * 3}
    assert A.is_grader_block(block) and A.status_of(block) == "grader_block"
    parse = {"status": "error", "parse_failures": [{"call": "grader[primary]", "finish_reason": "stop"}] * 3}
    assert not A.is_grader_block(parse) and A.status_of(parse) == "failed"
    assert A.status_of({"status": "complete"}) == "complete"


def test_balance_check_flags_only_imbalance():
    rng = np.random.default_rng(0)
    assert A._multinomial_p([4, 4, 4], rng) == 1.0
    assert A._multinomial_p([12, 0, 0], rng) < 0.001
    assert A._multinomial_p([0, 0, 0], rng) == 1.0


def test_fallback_on_degenerate_data_and_no_data():
    df = pd.DataFrame([{"model": "m", "category": f"c{k}", "persona": f"P{p}", "condition": c, "s": 0.5, "cell_id": ""}
                       for k in range(6) for p in range(5) for c in ("placebo", "full", "reversed")])
    f = A.fit_model(df)          # zero variance everywhere: the mixed model cannot be fitted
    assert f["method"].startswith("per-category") and f["B"] == 0.0
    assert A.fit_model(df.iloc[:0])["method"] == "no data"
    # review 3: the decision stage survives it (no ZeroDivisionError) and labels it untestable
    r = A.decide_all(df, ["m"])["m"]
    assert not r["testable"] and r["label"].startswith("inconclusive (not testable") and r["p_efficacy"] != r["p_efficacy"]


def test_mixed_model_and_fallback_agree_on_balanced_data(instrument, small_cfg):
    import synth
    main = synth.make_main(B=0.3, A=0.0, seed=3, cfg=small_cfg, instrument=instrument, n_fail=0, n_block=0)
    cb = A.target_cues(instrument, small_cfg["targets"])
    lies = A.lie_table(main, cb, adj={})
    for m in small_cfg["liar_models"]:
        d = lies[lies.model == m]
        f, b = A.fit_model(d), A.category_t(d, "full", "reversed")
        assert abs(f["B"] - b["est"]) < 0.002


def test_confession_excluded_unless_adjudicated(instrument, small_cfg):
    import synth
    main = synth.make_main(B=0.0, seed=4, cfg=small_cfg, instrument=instrument, n_fail=0, n_block=0)
    main[0] = {**main[0], "lie": main[0]["lie"] + " I made the whole thing up."}
    cb = A.target_cues(instrument, small_cfg["targets"])
    assert len(A.lie_table(main, cb, adj={})) == len(main) - 1
    from src.perfect_lie import sequential as sq
    assert len(A.lie_table(main, cb, adj={sq.cell_key(main[0]): "not_confession"})) == len(main)


def test_comprehension_reading_rules(instrument):
    import synth
    comp = synth.make_comprehension(acc_full=0.98, acc_rev=0.98)
    models = R.load_config()["liar_models"]
    dec = {m: {"B": 0.3, "efficacy_alpha_at_decision": 0.0125, "equivalence_alpha_at_decision": None} for m in models}
    assert all(v["reading"].startswith("belief use confirmed") for v in A.comprehension(comp, dec, models).values())
    null = {m: {"B": 0.0, "efficacy_alpha_at_decision": None, "equivalence_alpha_at_decision": 0.0125} for m in models}
    assert all(v["reading"] == "priming despite comprehension" for v in A.comprehension(comp, null, models).values())
    lean = synth.make_comprehension(acc_full=0.3, acc_rev=1.0)   # says "suspicious" to everything
    assert all(v["reading"].startswith("inconclusive") and not v["check_valid"] for v in A.comprehension(lean, null, models).values())


def test_runner_refuses_the_real_run_without_the_unblinding_flag():
    import run_final
    with pytest.raises(SystemExit, match="refusing"):
        run_final.main(["--run-dir", str(run_final.REAL)])
    with pytest.raises(SystemExit):
        run_final.main(["--real"])


# ---------------------------------------------------------------- regression tests from the independent review

def test_review1_fit_diagnostics_use_the_final_estimate_only():
    from types import SimpleNamespace as NS
    good_h = -np.eye(3)
    model = lambda h: NS(hessian=lambda p: (h, False))
    ok = NS(converged=True, cov_re=np.diag([0.005, 0.02, 0.02]), scale=0.05, model=model(good_h), params_object=None)
    assert A.fit_diagnostics(ok) is None                        # small but non-singular variance: not a failure
    assert A.fit_diagnostics(NS(**{**ok.__dict__, "converged": False})) == "did not converge"
    sing = NS(**{**ok.__dict__, "cov_re": np.diag([1e-12, 0.02, 0.02])})
    assert A.fit_diagnostics(sing).startswith("singular fit")
    indef = NS(**{**ok.__dict__, "model": model(np.array([[-1.0, 0, 0], [0, -1.0, 0], [0, 0, 0.5]]))})
    assert A.fit_diagnostics(indef) == "final Hessian not positive definite"   # diagonal sign alone would miss off-diagonal cases too


def test_review2_fallback_pairs_within_persona_and_test_A_has_its_own_K():
    rows = [{"model": "m", "category": f"c{k}", "persona": p, "condition": c, "s": v, "cell_id": ""}
            for k in range(20) for p, v in (("A", 0.1), ("B", 0.8)) for c in ("placebo", "full", "reversed")]
    df = pd.DataFrame(rows)
    d2 = df[~((df.persona == "A") & (df.condition == "full"))]
    assert A.category_t(d2, "full", "reversed")["est"] == 0.0   # was 0.35 before the fix
    d3 = df[~(df.category.isin(["c0", "c1", "c2"]) & (df.condition == "placebo"))]
    assert A.category_t(d3, "full", "reversed")["K"] == 20 and A.category_t(d3, "reversed", "placebo")["K"] == 17


def test_review3_untestable_model_stays_in_family_but_never_blocks():
    a = A.holm({"a": float("nan"), "b": 0.001, "c": 0.002, "d": 0.003})
    assert a == {"a": None, "b": 0.0125, "c": 0.016666666666666666, "d": 0.025}
    assert A._p_two(0.1, 0.0, 71) != A._p_two(0.1, 0.0, 71) and A._p_tost(0.0, float("nan"), 71) != A._p_tost(0.0, float("nan"), 71)


def test_review4_permutation_swaps_singleton_cells_too():
    lies = pd.DataFrame([{"model": "m", "category": "c0", "persona": "P1", "condition": "full", "s": 1.0, "cell_id": "x"},
                         {"model": "m", "category": "c0", "persona": "P1", "condition": "placebo", "s": 0.0, "cell_id": "y"},
                         {"model": "m", "category": "c1", "persona": "P1", "condition": "full", "s": 1.0, "cell_id": "z"},
                         {"model": "m", "category": "c1", "persona": "P1", "condition": "reversed", "s": 0.0, "cell_id": "w"}])
    A._perm_init(lies, ["m"])
    assert sorted(len(c) for c in A._PERM["cells"]) == [1, 2]   # the singleton full lie is a swappable cell


def test_review5_preservation_is_reported_per_family():
    dec = {"B": 0.05, "efficacy_alpha_at_decision": 0.0125, "equivalence_alpha_at_decision": 0.0125}
    assert A.holds(dec, 0.12, 0.01, 71) == {"efficacy_holds": True, "equivalence_holds": False,
                                            "all_primary_rejections_preserved": False}
    assert A.holds(dec, 0.05, 0.01, 71)["all_primary_rejections_preserved"] is True
    none = {"B": 0.0, "efficacy_alpha_at_decision": None, "equivalence_alpha_at_decision": None}
    assert A.holds(none, 0.0, 0.01, 71)["all_primary_rejections_preserved"] is None
    assert A.m1_intercepts(pd.DataFrame(columns=["model", "category", "persona", "condition", "s", "cell_id"])).get("error")


# ------------------------------------------------------------------ second review

def test_review2_5_nonconverged_robustness_fit_makes_no_preservation_claim():
    dec = {"B": 0.05, "efficacy_alpha_at_decision": 0.0125, "equivalence_alpha_at_decision": None}
    h = A.holds(dec, 0.05, 0.01, 71, converged=False)
    assert h["all_primary_rejections_preserved"] is None and "efficacy_holds" not in h


def test_review2_4_exploratory_breakdowns_survive_a_missing_condition(instrument, small_cfg):
    lies = pd.DataFrame([{"model": "m", "category": "c0", "persona": "P1", "condition": "full", "s": 1.0, "cell_id": "x"},
                         {"model": "m", "category": "c1", "persona": "P1", "condition": "full", "s": 0.5, "cell_id": "y"}])
    out = A.exploratory([], lies, {"P1": []}, instrument, ["m"], {})
    assert out["breakdowns"]["m"]["by_category"]["c0"]["B"]["n"] == 0


def test_review2_3_per_line_accuracy_counts_unparsed_and_failed_samples(instrument):
    from src.perfect_lie import comprehension as C
    lines = C.note_lines(instrument.personas["P1"], instrument.personas["P2"], "full")
    good = json.dumps([{"quality": l, "judge_finds": "convincing"} for l in lines])
    recs = [{"model_id": "m", "target_id": "P1", "placebo_id": "P2", "condition": "full", "status": "complete",
             "answer": good, "note_lines": lines},
            {"model_id": "m", "target_id": "P1", "placebo_id": "P2", "condition": "full", "status": "complete",
             "answer": "no json here", "note_lines": lines},
            {"model_id": "m", "target_id": "P1", "condition": "full", "status": "error"}]   # failed: lines rebuilt
    dec = {"m": {"B": 0.0, "efficacy_alpha_at_decision": None}}
    out = A.comprehension(recs, dec, ["m"], instrument, {"P1": "P2"})["m"]
    for ln in lines:
        assert out["per_line_accuracy"]["full"][ln] == {"accuracy": 1 / 3, "n": 3}
        assert out["per_line_accuracy_given_parse"]["full"][ln] == {"accuracy": 1.0, "n": 1}
    assert out["per_line_samples_without_lines"] == 0 and out["failed_calls"] == 1


def test_review2_2_tipping_point_reports_a_detected_crossing_not_a_guarantee():
    src = Path(A.__file__).read_text()
    assert "not reversible within" not in src and "first crossing detected by the" in src
