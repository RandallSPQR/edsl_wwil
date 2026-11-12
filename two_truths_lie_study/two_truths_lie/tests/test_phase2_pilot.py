"""Phase 2 stage 1 pilot logic (src/perfect_lie/phase2_pilot.py): draw, items, conditions, coherence gate, alpha rule."""
import gzip
import json
import math
from pathlib import Path

import pytest

from src.perfect_lie import phase2_pilot as Q

PROBE = Path(__file__).resolve().parents[1] / "results/phase2/probe"
TARGETS = ["P1", "P2", "P3", "P5", "P6"]
PROSE = ("The old mill stood at the edge of the river and the miller kept a ledger of every sack that came in from the "
         "farms, and on the morning of the flood he wrote that the water had reached the third step of the stair. ")


def lie(words=350, degenerate=False):
    w = (PROSE * 40).split()[:words]
    if degenerate:
        w = w[:words - 150] + ["granite", "violet", "harbor", "cobalt", "tundra", "lantern"] * 25
    return " ".join(w)


def rec(hyp, kind, alpha, cat, tgt, text=None, ids=None, nll=None, finish="stop"):
    return {"hyp": hyp, "kind": kind, "alpha": alpha, "category": cat, "target": tgt, "text": text or lie(),
            "ids": ids if ids is not None else list(range(300)), "nll": nll if nll is not None else [1.0] * 64,
            "finish": finish}


def test_pilot_categories_are_eight_training_categories_and_seeded():
    split = json.loads((PROBE / "category_split.json").read_text())
    c = Q.pilot_categories(split["training"])
    assert len(c) == 8 and set(c) <= set(split["training"]) and c == Q.pilot_categories(split["training"])
    assert c == ['business', 'electricity', 'film', 'kites', 'knots', 'mathematics', 'mining', 'music']


def test_pilot_items_use_the_hypothesis_note_in_the_frozen_wording():
    items = [json.loads(l) for l in gzip.open(PROBE / "probe_items.jsonl.gz", "rt")]
    cats = Q.pilot_categories(json.loads((PROBE / "category_split.json").read_text())["training"])
    for m in Q.PLACEBO_SEED:
        for h, note in (("H1", "reversed"), ("H2", "full")):
            its = Q.pilot_items(items, m, cats, h)
            assert len(its) == 40 and {it["condition"] for it in its} == {note}
            assert {it["wording"] for it in its} == {"frozen"} and {it["model_id"] for it in its} == {m}


def test_conditions_and_size():
    c = Q.conditions()
    assert len(c) == 2 + 2 * 5 * 2
    assert sum(1 for x in c if x["kind"] != "none") * 40 == 800          # the registered 800 lies per model
    assert {x["alpha"] for x in c if x["kind"] != "none"} == set(Q.ALPHAS)


def test_seeds_shared_within_hypothesis_and_coef_signs():
    assert Q.batch_seed(0, "H1", 12) == Q.batch_seed(0, "H1", 12) != Q.batch_seed(0, "H2", 12)
    assert Q.batch_seed(0, "H1", 0) != Q.batch_seed(1, "H1", 0)
    assert Q.coef("H1", "steered", 2.0, 3.0) == 6.0 and Q.coef("H2", "placebo", 2.0, 3.0) == -6.0
    assert Q.coef("H1", "none", 4.0, 3.0) == 0.0


def test_rep4_and_ppl_ratio():
    assert Q.rep4_share([1, 2, 3, 4, 1, 2, 3, 4]) == pytest.approx(1 / 5)   # 5 four-grams, (1, 2, 3, 4) repeats once
    assert Q.rep4_share([7] * 10) == pytest.approx(6 / 7)
    assert Q.rep4_share([1, 2, 3]) == 0.0
    assert Q.ppl_ratio([2.0] * 4, [1.0] * 4) == pytest.approx(math.e)


def test_viability_counts_word_range_truncation_and_degeneration_not_refusal():
    assert Q.viability(lie(350), "stop") == []
    assert any(x.startswith("too_short") for x in Q.viability(lie(100), "stop"))
    assert any(x.startswith("too_long") for x in Q.viability(lie(600), "stop"))
    assert "truncated_by_output_cap" in Q.viability(lie(350), "length")
    assert "degenerate_text" in Q.viability(lie(350, degenerate=True), "stop")


def grid_records(bad=lambda h, k, a: None):
    """Every pilot lie of one model; `bad(h, k, a)` returns None (coherent) or one of 'short', 'ppl', 'rep'."""
    out = []
    for h in Q.HYPOTHESES:
        for i, (cat, t) in enumerate((c, t) for c in "abcdefgh" for t in TARGETS):
            out.append(rec(h, "none", 0.0, cat, t))
            for a in Q.ALPHAS:
                for k in Q.KINDS:
                    how = bad(h, k, a)
                    r = rec(h, k, a, cat, t)
                    if how == "short" and i % 10 == 0:          # 4 of 40 too short: 90% viable
                        r["text"] = lie(100)
                    if how == "ppl":
                        r["nll"] = [1.8] * 64                    # exp(0.8) = 2.23
                    if how == "rep":
                        r["ids"] = [1, 2, 3, 4] * 75
                    out.append(r)
    return out


def test_all_coherent_picks_the_largest_alpha():
    rep = Q.analyse(grid_records())
    for h in Q.HYPOTHESES:
        assert rep[h]["confirmatory_alpha"] == 4.0 and rep[h]["status"] == "alpha chosen"
        assert rep[h]["grid"]["1.0"]["steered"]["ppl_ratio_median"] == pytest.approx(1.0)


@pytest.mark.parametrize("how", ["short", "ppl", "rep"])
def test_each_criterion_can_fail_an_alpha(how):
    rep = Q.analyse(grid_records(lambda h, k, a: how if a >= 2.0 and k == "steered" else None))
    for h in Q.HYPOTHESES:
        assert rep[h]["confirmatory_alpha"] == 1.0
        assert not rep[h]["grid"]["2.0"]["coherent"] and rep[h]["grid"]["2.0"]["placebo"]["passes"]


def test_placebo_failure_also_fails_the_alpha_and_none_means_untestable():
    rep = Q.analyse(grid_records(lambda h, k, a: "ppl" if (k == "placebo" and a == 4.0) or h == "H2" else None))
    assert rep["H1"]["confirmatory_alpha"] == 2.0
    assert rep["H2"]["confirmatory_alpha"] is None and rep["H2"]["status"].startswith("untestable")


def test_largest_coherent_alpha_even_when_a_smaller_one_fails():
    rep = Q.analyse(grid_records(lambda h, k, a: "rep" if a == 0.5 else None))
    assert all(rep[h]["confirmatory_alpha"] == 4.0 for h in Q.HYPOTHESES)
