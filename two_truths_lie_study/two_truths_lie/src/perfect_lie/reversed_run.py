"""Full run of the reversed-note follow-up (PREREG_REVERSED.md, tag perfect-lie-reversed-prereg-v1).

Written after the freeze; it imports the frozen modules (reversed.py, comprehension.py, runner.py)
and changes none of them. Everything the run varies is read from the frozen run_config.json:
  * main run: 72 categories x 5 targets x {placebo, full, reversed} x 4 liars x 1 replicate = 4,320
    lies; stages liar -> 4 judges -> graders (primary + Google on all; gpt-5 on a seeded, stratified
    25% subsample, seed 20261009 per the registration, not models.json's first-study 20261006);
  * comprehension check: 4 liars x 5 targets x {full, reversed} x 10 + placebo x 5 = 500 calls.
preflight() refuses to start when any file hashed in PREREG_REVERSED.md differs from its frozen
hash, or when the owner's run lock is set.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import DATA_DIR
from . import reversed as rv
from . import comprehension as C
from .pipeline import Cell, load_models, select_class

ROOT = DATA_DIR.parents[1]                       # two_truths_lie/
STUDY_DIR = ROOT.parent                          # two_truths_lie_study/
PREREG = STUDY_DIR / "PREREG_REVERSED.md"
CONFIG_PATH = rv.REV_DIR / "run_config.json"
LOCKS_PATH = DATA_DIR / "run_locks.json"
LOCK_KEY = "reversed_followup_full_run"
MAIN_NAMESPACE = "rev_full"


def load_config() -> Dict:
    return json.loads(CONFIG_PATH.read_text())


def frozen_hashes(prereg: Path = PREREG) -> List[Tuple[str, str]]:
    """(path under two_truths_lie/, sha256) rows of the registration's frozen-file table."""
    return re.findall(r"\| `([^`]+)` \| `([0-9a-f]{64})` \|", prereg.read_text())


def check_frozen(root: Path = ROOT, prereg: Path = PREREG) -> List[str]:
    problems = []
    rows = frozen_hashes(prereg)
    if len(rows) < 16:
        problems.append(f"registration lists {len(rows)} frozen files, expected 16")
    for rel, h in rows:
        p = root / rel
        if not p.exists():
            problems.append(f"frozen file missing: {rel}")
        elif hashlib.sha256(p.read_bytes()).hexdigest() != h:
            problems.append(f"frozen file changed since the registration: {rel}")
    from .grader import RUBRIC_PREAMBLE, RUBRIC_OUTPUT
    m = re.search(r"grader rubric \(RUBRIC_PREAMBLE \+ RUBRIC_OUTPUT\) \| `([0-9a-f]{64})`", prereg.read_text())
    if not m or hashlib.sha256((RUBRIC_PREAMBLE + RUBRIC_OUTPUT).encode()).hexdigest() != m.group(1):
        problems.append("grader rubric differs from the registration")
    return problems


def preflight(locks_path: Path = LOCKS_PATH, root: Path = ROOT, prereg: Path = PREREG) -> List[str]:
    problems = check_frozen(root, prereg)
    locks = json.loads(Path(locks_path).read_text())
    if locks.get(LOCK_KEY, {}).get("locked", True):
        problems.insert(0, f"full run is LOCKED by the owner ({Path(locks_path).name}: {LOCK_KEY})")
    if locks.get("trace_probe", {}).get("locked", True) is not True:
        problems.append("trace probe must stay locked")
    return problems


def run_models(cfg: Optional[Dict] = None) -> Dict:
    """C1 models with the registration's grader subsample (gpt-5, 25%, strata model x condition,
    seed from run_config.json)."""
    cfg = cfg or load_config()
    models = copy.deepcopy(select_class(load_models(), "C1"))
    want = [m["id"] for m in models["liar_models"]]
    if want != cfg["liar_models"]:
        raise ValueError(f"liar models {want} differ from run_config {cfg['liar_models']}")
    sub = cfg["graders"]["secondary_subsample"]
    for g in models["graders"]:
        if g["role"] == "secondary":
            if g["id"] != sub["model"]:
                raise ValueError(f"secondary grader {g['id']} != run_config {sub['model']}")
            g["subsample"] = dict(g["subsample"], fraction=sub["fraction"], seed=sub["seed"], strata=sub["strata"])
    roles = {g["role"]: g["id"] for g in models["graders"]}
    if roles.get("primary") != cfg["graders"]["primary"] or roles.get("google") != cfg["graders"]["google"]:
        raise ValueError(f"graders {roles} differ from run_config")
    return models


def main_cells(cfg: Optional[Dict] = None, models: Optional[Dict] = None) -> List[Cell]:
    cfg = cfg or load_config()
    models = models or run_models(cfg)
    t, p = cfg["sampling"]["temperature"], cfg["sampling"]["top_p"]
    return [rv.make_cell(category=cat, target_id=tid, condition=cond, model=m, replicate=r, temperature=t, top_p=p,
                         placebo_id=cfg["placebo_for_target"][tid])
            for m in models["liar_models"] for cat in cfg["categories"] for tid in cfg["targets"]
            for cond in cfg["conditions"] for r in cfg["replicates"]]


def comprehension_cells(cfg: Optional[Dict] = None, models: Optional[Dict] = None) -> List[Cell]:
    cfg = cfg or load_config()
    models = models or run_models(cfg)
    cc = cfg["comprehension"]
    t, p = cfg["sampling"]["temperature"], cfg["sampling"]["top_p"]
    n = {c: cc["samples_per_model_target_condition"] for c in cc["conditions"]}
    n["placebo"] = cc["placebo_format_check_samples"]
    return [rv.make_cell(category=C.seeded_category(cfg["categories"], m["id"], tid, cond, k), target_id=tid,
                         condition=cond, model=m, replicate=k, temperature=t, top_p=p,
                         placebo_id=cfg["placebo_for_target"][tid])
            for m in models["liar_models"] for tid in cfg["targets"] for cond in ("full", "reversed", "placebo")
            for k in range(1, n[cond] + 1)]


def estimate_usd(n_main: int, n_comp: int) -> Dict:
    cost = json.loads((ROOT / "results/perfect_lie_reversed/design/cost.json").read_text())
    per_lie = cost["per_cell_total_usd"]
    per_comp = cost["comprehension_check"]["usd_per_call_pilot"]
    return {"main": n_main * per_lie, "comprehension": n_comp * per_comp, "total": n_main * per_lie + n_comp * per_comp,
            "per_lie": per_lie, "per_comprehension_call": per_comp}


def make_runs(*, run_dir: Path, instrument, adapter, cap_usd: float, concurrency: int, billing_probe=None,
              cfg: Optional[Dict] = None):
    """The two runs (main, comprehension), as mode 'full', sharing one spend cap (the comprehension
    run receives what the main run left)."""
    cfg = cfg or load_config()
    models = run_models(cfg)
    Main = rv.make_run_class()
    Comp = C.make_run_class()

    def build(cls, namespace, sub, cells, mdl, stages, cap):
        r = cls(namespace=namespace, run_dir=Path(run_dir) / sub, cells=cells, instrument=instrument, models=mdl,
                adapter=adapter, spend_cap_usd=cap, concurrency=concurrency, models_path=DATA_DIR / "models.json",
                stages=stages, trace_probe_locked=True, billing_probe=billing_probe, elicitation=False,
                retry_failed="transport")
        r.mode = "full"  # FollowupRun is constructed as 'pilot'; this is the registered full run
        return r

    main = build(Main, MAIN_NAMESPACE, "main", main_cells(cfg, models), models, ("liar", "target", "graders"), cap_usd)
    comp_models = dict(models, graders=[])
    comp = lambda cap: build(Comp, cfg["comprehension"]["namespace"], "comprehension", comprehension_cells(cfg, models),
                             comp_models, ("liar",), cap)
    return main, comp
