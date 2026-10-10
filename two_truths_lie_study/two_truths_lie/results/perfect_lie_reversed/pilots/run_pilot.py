"""Follow-up pilots (rules: PILOT_RULES.md). Live model calls; spend-capped and killed on breach.

  python run_pilot.py degeneration --cap 3
  python run_pilot.py fabricability --temperature 0.8 --cap 10
"""
import argparse, asyncio, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
from src.perfect_lie import DATA_DIR
from src.perfect_lie import reversed as rv
from src.perfect_lie.personas import load_instrument
from src.perfect_lie.pipeline import load_models, select_class

TOP_P = 0.9


def cells_for(kind, temperature, liars, design, cats):
    targets, pmap = design["targets"], design["placebo_for_target"]
    out = []
    for m_i, m in enumerate(liars):
        for i, cat in enumerate(cats):
            if kind == "degeneration":
                tl = [targets[i % len(targets)]]
            else:
                skip = targets[(i + m_i) % len(targets)]
                tl = [t for t in targets if t != skip]
            for t in tl:
                out.append(rv.make_cell(category=cat, target_id=t, condition="placebo", model=m, replicate=1,
                                        temperature=temperature, top_p=TOP_P, placebo_id=pmap[t]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=("degeneration", "fabricability", "pilot4"))
    ap.add_argument("--temperature", type=float)
    ap.add_argument("--cap", type=float, required=True)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--categories", nargs="*", help="pilot4: categories for 4a (default: the pending three)")
    ap.add_argument("--set", choices=("first", "second", "third"), default="first",
                    help="first: the 24 first-round categories (Pilot 2); second: drawn 48 + 3 replacements (Pilot 3)")
    a = ap.parse_args()
    inst = load_instrument(); models = select_class(load_models(), "C1")
    design, cats = rv.load_design(), rv.load_categories()
    if a.set == "first":
        cats = cats["original"] + cats["new"]
    elif a.set == "second":
        cats = cats["drawn_48"] + cats["replacements_for_failed"]
    else:
        cats = list(a.categories or cats["replacements_for_pilot3_failed"])
    if a.kind == "pilot4":
        if a.cap > 3:
            raise SystemExit("pilot 4 cap is $3")
        from src.perfect_lie import comprehension as C
        allc = rv.load_categories()
        p72 = allc["proposed_72"]
        cats72 = p72["first_round_passed"] + p72["replacements_for_failed"] + p72["drawn_passed"] + p72["pending_pilot"]
        fab_cats = list(a.categories or allc["replacements_for_pilot3_failed"])
        fab = cells_for("fabricability", 0.6, models["liar_models"], design, fab_cats)
        comp = []
        for m in models["liar_models"]:
            for t in design["targets"]:
                for cond in ("full", "reversed", "placebo"):
                    for k in (1, 2):
                        comp.append(rv.make_cell(category=C.seeded_category(cats72, m["id"], t, cond, k), target_id=t,
                                                 condition=cond, model=m, replicate=k, temperature=0.6, top_p=TOP_P,
                                                 placebo_id=design["placebo_for_target"][t]))
        from src.edsl_adapter import PerfectLieAdapter
        from src.perfect_lie.transport import TransportRetryAdapter
        from run_perfect_lie import openrouter_billed_usd
        spent = 0.0
        for name, cells, stages, mdl, RunCls in (
                ("fabricability_t0.6_set3", fab, ("liar", "graders"),
                 dict(models, graders=[g for g in models["graders"] if g["role"] == "primary"]), rv.make_run_class()),
                ("comprehension_pilot", comp, ("liar",), dict(models, graders=[]), C.make_run_class())):
            ns = "rev_pilot_fabricability_t0.6_set3" if name.startswith("fab") else "rev_pilot_comprehension"
            run = RunCls(namespace=ns, run_dir=HERE / name, cells=cells, instrument=inst, models=mdl,
                         adapter=TransportRetryAdapter(PerfectLieAdapter(service_name=models.get("service", "open_router"))),
                         spend_cap_usd=a.cap - spent, concurrency=a.concurrency, models_path=DATA_DIR / "models.json",
                         stages=stages, trace_probe_locked=True, billing_probe=openrouter_billed_usd, elicitation=False,
                         retry_failed="transport")
            print(f"{name}: {len(cells)} cells, remaining cap ${a.cap - spent:.2f}", flush=True)
            mf = asyncio.run(run.run())
            spent += mf["spend_usd"]
            print(f"{name}: {mf['n_complete']}/{mf['n_cells_planned']} complete, {mf['n_error']} error, "
                  f"spend ${mf['spend_usd']:.2f}; pilot total ${spent:.2f}", flush=True)
            if mf["spend_cap_reached"]:
                raise SystemExit("cap reached: stopped")
        return
    if a.kind == "degeneration":
        if a.cap > 3:
            raise SystemExit("degeneration pilot cap is $3")
        # Cell ids do not carry temperature, so each temperature is its own run (and namespace).
        plans = [(f"degeneration_t{t}", cells_for("degeneration", t, models["liar_models"], design, cats))
                 for t in (0.6, 0.8)]
        stages = ("liar",)
        models = dict(models, graders=[])
    else:
        limit = 10 if a.set == "first" else 12
        if a.cap > limit or a.temperature is None:
            raise SystemExit(f"fabricability pilot needs --temperature and a cap of at most ${limit}")
        plans = [(f"fabricability_t{a.temperature}" + ("" if a.set == "first" else "_set2"),
                  cells_for("fabricability", a.temperature, models["liar_models"], design, cats))]
        stages = ("liar", "graders")
        models = dict(models, graders=[g for g in models["graders"] if g["role"] == "primary"])
    from src.edsl_adapter import PerfectLieAdapter
    from src.perfect_lie.transport import TransportRetryAdapter
    from run_perfect_lie import openrouter_billed_usd
    Run = rv.make_run_class()
    spent = 0.0
    for name, cells in plans:
        run = Run(namespace=f"rev_pilot_{name}", run_dir=HERE / name, cells=cells, instrument=inst, models=models,
                  adapter=TransportRetryAdapter(PerfectLieAdapter(service_name=models.get("service", "open_router"))),
                  spend_cap_usd=a.cap - spent, concurrency=a.concurrency, models_path=DATA_DIR / "models.json",
                  stages=stages, trace_probe_locked=True, billing_probe=openrouter_billed_usd, elicitation=False,
                  retry_failed="transport")
        print(f"{name}: {len(cells)} cells, remaining cap ${a.cap - spent:.2f}", flush=True)
        mf = asyncio.run(run.run())
        spent += mf["spend_usd"]
        print(f"{name}: {mf['n_complete']}/{mf['n_cells_planned']} complete, {mf['n_error']} error, "
              f"spend ${mf['spend_usd']:.2f} (counted {mf['spend_counted_usd']:.2f}, billed delta "
              f"{mf['openrouter_billed_delta_usd']}); pilot total ${spent:.2f}", flush=True)
        if mf["spend_cap_reached"]:
            raise SystemExit("cap reached: stopped")


if __name__ == "__main__":
    main()
