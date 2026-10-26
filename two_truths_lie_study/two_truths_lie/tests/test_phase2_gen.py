"""Phase 2 stage-2 generation plan (src/perfect_lie/phase2_gen.py) and the stage-2 driver's offline steps
(results/phase2/probe/stage2_stage.py: grade, screens, permcheck, analyse) on simulated generations, stubbed graders."""
import gzip
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pytest

from src.perfect_lie import phase2_gen as G, phase2_pilot as Q

PROBE = Path(__file__).resolve().parents[1] / "results/phase2/probe"
EV = json.loads((PROBE / "category_split.json").read_text())["evaluation"]
ITEMS = [json.loads(l) for l in gzip.open(PROBE / "stage2_items.jsonl.gz", "rt")]
GEMMA, LLAMA = G.MODELS
ALPHAS = {GEMMA: {"H1": 2.0, "H2": 1.0}, LLAMA: {"H1": 4.0, "H2": 4.0}}


def test_items_are_the_evaluation_categories_with_prompts():
    assert len(ITEMS) == 2 * 32 * 5 * 3 and {i["category"] for i in ITEMS} == set(EV)
    assert all(i["user_prompt"] and i["messages"] for i in ITEMS)


def test_mc_categories_seeded_sixteen_of_the_evaluation_categories():
    mc = G.mc_categories(EV)
    assert len(mc) == 16 and set(mc) <= set(EV) and mc == G.mc_categories(EV)


@pytest.mark.parametrize("model,batch", [(GEMMA, 12), (LLAMA, 24)])
def test_plan_sizes_seeds_and_batches(model, batch):
    jobs = G.plan(ITEMS, model, ALPHAS[model], EV, batch)
    n = Counter()
    for j in jobs:
        n[(j["arm"], j["hyp"])] += len(j["items"])
        assert len(j["items"]) <= batch
    assert n == {("ref_reversed", None): 160, ("steered", "H1"): 160, ("placebo", "H1"): 160, ("ref_full", None): 160,
                 ("steered", "H2"): 160, ("placebo", "H2"): 160, ("ref_placebo", None): 160,
                 ("mc_steered", None): 80, ("mc_placebo", None): 80}            # 1,280 per model, as registered
    by_seed = defaultdict(set)
    for j in jobs:
        by_seed[j["seed"]].add(j["arm"])
    groups = {frozenset(v) for v in by_seed.values()}
    assert groups == {frozenset({"ref_reversed", "steered", "placebo"}), frozenset({"ref_full", "steered", "placebo"}),
                      frozenset({"ref_placebo"}), frozenset({"mc_steered", "mc_placebo"})}
    for j in jobs:
        if j["arm"].startswith("mc_"):
            assert {i["target"] for i in j["items"]} == {j["target"]} and j["kind"] == f"{j['arm']}:{j['target']}"
            assert {i["condition"] for i in j["items"]} == {"placebo"} and {i["category"] for i in j["items"]} <= set(G.mc_categories(EV))
        if j["arm"] in ("steered", "placebo"):
            assert {i["condition"] for i in j["items"]} == {G.NOTE[j["hyp"]]}
    assert len({j["key"] for j in jobs}) == len(jobs)


def test_untestable_hypothesis_generates_no_steered_lies():
    jobs = G.plan(ITEMS, GEMMA, {"H1": None, "H2": 1.0}, EV, 12)
    assert not [j for j in jobs if j["hyp"] == "H1"] and [j for j in jobs if j["arm"] == "ref_reversed"]


def test_coef():
    jobs = G.plan(ITEMS, GEMMA, ALPHAS[GEMMA], EV, 12)
    get = lambda arm, hyp=None: next(j for j in jobs if j["arm"] == arm and j["hyp"] == hyp)
    vfp = {t: 10.0 + i for i, t in enumerate(G.TARGETS)}
    assert G.coef(get("steered", "H1"), 3.0, vfp) == 6.0 and G.coef(get("placebo", "H2"), 3.0, vfp) == -3.0
    assert G.coef(get("ref_full"), 3.0, vfp) == 0.0
    mc = get("mc_placebo")
    assert G.coef(mc, 3.0, vfp) == vfp[mc["target"]]


def fake_lie(rng, words=350, rep=False):
    return " ".join(rng.choice(["the", "mill", "river", "and", "ledger", "farm", "of", "flood", "a", "stair"], size=words))


def sim_records(model, seed=0, bad_placebo_h2=False):
    rng = np.random.default_rng(seed)
    out = []
    for j in G.plan(ITEMS, model, ALPHAS[model], EV, Q.BATCH[model]):
        for it in j["items"]:
            nll = [1.0] * 64
            if bad_placebo_h2 and j["arm"] == "placebo" and j["hyp"] == "H2":
                nll = [2.0] * 64
            out.append({"key": j["key"], "arm": j["arm"], "hyp": j["hyp"], "alpha": j["alpha"], "target": it["target"],
                        "category": it["category"], "condition": it["condition"], "item_id": it["item_id"], "seed": j["seed"],
                        "text": fake_lie(rng), "ids": [int(x) for x in rng.integers(0, 5000, 300)], "finish": "stop", "prompt_count": 280,
                        "nll": nll, "user_prompt": it["user_prompt"], "model": model})
    return out


def test_stage2_coherence_gate():
    recs = sim_records(GEMMA)
    c = G.coherence(recs, ALPHAS[GEMMA])
    assert c["H1"]["testable"] and c["H2"]["testable"] and c["method_check"]["mc_steered"]["n"] == 80
    c = G.coherence(sim_records(GEMMA, bad_placebo_h2=True), ALPHAS[GEMMA])
    assert c["H1"]["testable"] and not c["H2"]["testable"] and c["H2"]["reason"].startswith("confirmatory alpha failed")
    assert G.coherence(recs, {"H1": None, "H2": 1.0})["H1"]["testable"] is False


def test_driver_offline_end_to_end(tmp_path, monkeypatch):
    """Simulated generations for both models -> grade (stubbed graders) -> screens -> permcheck -> analyse."""
    sys.path.insert(0, str(PROBE))
    import stage2_stage as SS
    from src.perfect_lie import phase2_grading as PG
    from src.perfect_lie.personas import load_instrument
    cues = [c.id for c in load_instrument().cues]
    monkeypatch.setattr(SS, "STAGE2", tmp_path)
    monkeypatch.setattr(SS, "SCREENS", tmp_path / "screen_matches.json")
    monkeypatch.setattr(SS, "SCREEN_KEY", tmp_path / "screen_matches_key.json")
    monkeypatch.setattr(SS, "ADJUDICATION", tmp_path / "screen_adjudication.json")
    rng = np.random.default_rng(1)
    prob = {"steered": 0.6, "placebo": 0.4}

    def primary(gi, order, strict=True):
        p = prob.get(gi.user_prompt.split("ARM:")[-1].strip()[:8].strip(), 0.4) if "ARM:" in gi.user_prompt else 0.45
        on = {c: bool(rng.random() < p) for c in order}
        return {"parsed": {"cues": on, "counts": {c: int(v) for c, v in on.items()}, "confidence": 5}, "error": None,
                "usage": {"input_tokens": 1, "output_tokens": 1}}

    def google(gi, order):
        return primary(gi, order)
    real = PG.grade_records
    monkeypatch.setattr(PG, "grade_records", lambda *a, **k: real(*a, primary=primary, google=google, **k))
    for m in G.MODELS:
        d = tmp_path / SS.PS.slug(m); d.mkdir()
        recs = sim_records(m, seed=G.MODELS.index(m))
        for r in recs:
            r["user_prompt"] = r["user_prompt"] + f"\nARM: {r['arm']}"     # lets the stub grade by arm
        recs[0]["text"] = "I just made this up. " + recs[0]["text"]  # one confession-screen match
        (d / "records.jsonl").write_text("".join(json.dumps(r) + "\n" for r in recs))
        (d / "coherence.json").write_text(json.dumps(G.coherence(recs, ALPHAS[m])))
        (d / "natural.json").write_text(json.dumps({"cos_first_generated_token": 0.5, "cos_last_token_evaluation": 0.9}))
        SS.grade(m)
        graded = [json.loads(l) for l in (d / SS.GRADED).open()]
        assert len(graded) == 1280 and sum("google" in r for r in graded) == 256
        SS.grade(m)                                                        # resume: nothing re-graded
        assert len((d / SS.GRADED).read_text().splitlines()) == 1280
    SS.screens()
    rows = json.loads(SS.SCREENS.read_text())
    assert len(rows) >= 1 and all(set(r) == {"id", "confession_match", "refusal_match", "lie"} for r in rows)
    with pytest.raises(SystemExit):
        SS.analysis_records()                                              # not adjudicated yet
    SS.ADJUDICATION.write_text(json.dumps({r["id"]: "confession" if r["confession_match"] else "not a confession" for r in rows}))
    assert sum(r["confession"] for r in SS.analysis_records()) >= 1
    SS.permcheck()
    pc = json.loads((tmp_path / "permutation_check.json").read_text())
    assert pc["n"] == 10_000 and set(pc["shares"]) == {f"{m}|{h}" for m in G.MODELS for h in ("H1", "H2")}
    SS.analyse_all()
    rep = json.loads((tmp_path / "stage2_result.json").read_text())
    assert rep["primary"][f"{GEMMA}|H1"]["K"] == 32 and rep["primary"][f"{GEMMA}|H1"]["est"] > 0.05
    assert rep["primary"][f"{GEMMA}|H2"]["est"] > 0.05                      # simulated steering raised s under H2 too
    assert rep["primary"][f"{GEMMA}|H2"]["label"] in ("opposite", "inconclusive")
    assert rep["google_subsample"]["cells"] == 32 and "naturalness" in rep and (tmp_path / "STAGE2.md").exists()
