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
