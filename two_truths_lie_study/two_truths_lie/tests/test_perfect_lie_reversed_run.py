"""Follow-up full-run code (reversed_run.py), offline: fake adapter, no model calls, no spend."""
import asyncio, json, shutil
from collections import Counter
from pathlib import Path
import pytest

from src.perfect_lie import reversed_run as R
from src.perfect_lie.runner import cell_id


@pytest.fixture(scope="module")
def instrument():
    from src.perfect_lie.personas import load_instrument
    return load_instrument()


@pytest.fixture(scope="module")
def cfg():
    return R.load_config()


def test_main_cells_match_the_registration(cfg):
    cells = R.main_cells(cfg)
    assert len(cells) == 4320 and len({cell_id(c, R.MAIN_NAMESPACE) for c in cells}) == 4320
    assert Counter((c.model_id, c.condition) for c in cells) == {(m, k): 360 for m in cfg["liar_models"] for k in cfg["conditions"]}
    assert {c.category for c in cells} == set(cfg["categories"]) and len(cfg["categories"]) == 72
    assert all(c.temperature == 0.6 and c.top_p == 0.9 and c.replicate == 1 and c.prompt_version == "v3" for c in cells)
    assert all(c.placebo_id == cfg["placebo_for_target"][c.target_id] for c in cells)


def test_comprehension_cells(cfg):
    cells = R.comprehension_cells(cfg)
    assert len(cells) == 500 and len({cell_id(c, "rev_full_comprehension") for c in cells}) == 500
    n = Counter((c.model_id, c.target_id, c.condition) for c in cells)
    assert set(n.values()) == {10, 5} and all(v == 5 for (m, t, k), v in n.items() if k == "placebo")


def test_gpt5_subsample_uses_the_registered_seed_and_strata(cfg):
    from src.perfect_lie.pipeline import subsample_cell_ids
    models = R.run_models(cfg)
    sec = next(g for g in models["graders"] if g["role"] == "secondary")
    assert sec["subsample"]["seed"] == 20261009 and sec["subsample"]["fraction"] == 0.25
    cells = R.main_cells(cfg, models)
    chosen = subsample_cell_ids(cells, 0.25, 20261009, R.MAIN_NAMESPACE)
    by = Counter((c.model_id, c.condition) for c in cells if cell_id(c, R.MAIN_NAMESPACE) in chosen)
    assert set(by.values()) == {90} and len(by) == 12
    # and the first study's file is untouched
    assert json.loads((R.DATA_DIR / "models.json").read_text())["graders"][1]["subsample"]["seed"] == 20261006


def test_preflight_frozen_hashes_and_lock(tmp_path):
    assert R.check_frozen() == []                                  # the tree matches the registration
    locked = tmp_path / "locks.json"
    locked.write_text(json.dumps({R.LOCK_KEY: {"locked": True}, "trace_probe": {"locked": True}}))
    assert any("LOCKED" in p for p in R.preflight(locks_path=locked))
    unlocked = tmp_path / "unlocked.json"
    unlocked.write_text(json.dumps({R.LOCK_KEY: {"locked": False}, "trace_probe": {"locked": True}}))
    assert R.preflight(locks_path=unlocked) == []
    # a changed frozen file is refused
    fake_root = tmp_path / "root"
    for rel, _ in R.frozen_hashes():
        (fake_root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(R.ROOT / rel, fake_root / rel)
    (fake_root / "data/perfect_lie_reversed/reversed_notes.json").write_text("{}")
    assert any("reversed_notes.json" in p for p in R.check_frozen(root=fake_root))


def test_real_lock_is_set():
    assert any("LOCKED" in p for p in R.preflight())


def test_end_to_end_with_fake_adapter(instrument, tmp_path, cfg, monkeypatch):
    from tests.test_perfect_lie_invariants import FakeAdapter
    fake = FakeAdapter(instrument)
    small = dict(cfg, categories=cfg["categories"][:2])
    main, comp = R.make_runs(run_dir=tmp_path, instrument=instrument, adapter=fake, cap_usd=5.0, concurrency=4, cfg=small)
    mf = asyncio.run(main.run())
    assert mf["mode"] == "full" and mf["run_namespace"] == R.MAIN_NAMESPACE
    assert mf["n_cells_planned"] == 2 * 5 * 3 * 4 and mf["n_complete"] == mf["n_cells_planned"]
    recs = [json.loads(l) for l in (tmp_path / "main/records.jsonl").read_text().splitlines()]
    last = {r["cell_id"]: r for r in recs}
    assert all(set(r["targets"]) == set(cfg["liar_models"]) for r in last.values())          # 4x4 judges
    assert all({"primary", "google"} <= set(r["grades"]) for r in last.values())
    liar_calls = [c for c in fake.calls if c["role"] == "liar"]
    assert all(c["temperature"] == 0.6 and c["top_p"] == 0.9 for c in liar_calls)
    assert all("suspect when it has these qualities" in c["system_prompt"]
               for c in liar_calls if "Distrusts" in c["system_prompt"] or "less believable" in c["system_prompt"])
    cr = comp(5.0 - mf["spend_usd"])
    mc = asyncio.run(cr.run())
    assert mc["mode"] == "full" and mc["n_cells_planned"] == 500 and mc["n_complete"] == 500
    crecs = {json.loads(l)["cell_id"]: json.loads(l) for l in (tmp_path / "comprehension/records.jsonl").read_text().splitlines()}
    assert all(r["kind"] == "comprehension" and "variant" in r for r in crecs.values())
    assert not any("Now tell your story:" in c["user_prompt"] for c in fake.calls[-500:])


def test_dry_run_cli_makes_no_calls(capsys):
    import run_perfect_lie_reversed as cli
    assert cli.main(["--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "4320 lies" in out and "500 calls" in out and "REFUSES" in out and "LOCKED" in out
    assert cli.main(["--go", "--cap", "125"]) == 4                 # refused while locked
