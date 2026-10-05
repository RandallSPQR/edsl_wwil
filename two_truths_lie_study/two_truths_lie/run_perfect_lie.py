#!/usr/bin/env python3
"""The Perfect Lie: entry point.

    python run_perfect_lie.py --dry-run [--tier tier1|tier2|all]   # cells + cost, no model calls
    python run_perfect_lie.py --refresh-prices                      # verify prices from OpenRouter (no key needed)
    python run_perfect_lie.py --smoke --confirm-spend USD           # liar-only checks, every family x level
    python run_perfect_lie.py --pilot --confirm-spend USD           # Phase 2 pilot, one family at reasoning off
    python run_perfect_lie.py --full  --confirm-spend USD           # Phase 3 (gated)
    python run_perfect_lie.py --resume RUN_DIR --confirm-spend USD  # continue a crashed or capped run
    python run_perfect_lie.py --score RUN_DIR                       # T, p0, co-firing, acceptance, fabricability
    python run_perfect_lie.py --record-fabricability RUN_DIR        # write pilot evidence into prompts.json

Cost guard: a live mode prints its estimate, refuses unless --confirm-spend is at least
the estimate, and stops scheduling new cells once actual spend reaches --confirm-spend.
"""

import argparse
import asyncio
import datetime
import json
import sys
from pathlib import Path

from src.perfect_lie import DATA_DIR
from src.perfect_lie.personas import load_instrument
from src.perfect_lie.pipeline import (
    DEFAULT_REPLICATES, TIERS, enumerate_cells, estimate_cost, format_estimate, load_models, preflight,
    priced_entries, smoke_cells,
)

HERE = Path(__file__).resolve().parent
RESULTS_ROOT = HERE / "results" / "perfect_lie"


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


def refresh_prices(models_path: Path) -> None:
    """Overwrite every price from OpenRouter's public model list. Atomic: nothing is written
    unless every model id exists, and every entry is stamped with price_verified_at."""
    import urllib.request
    models = json.loads(models_path.read_text())
    with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as r:
        live = {m["id"]: m for m in json.load(r)["data"]}
    entries = priced_entries(models)
    missing = sorted({e["id"] for e in entries if e["id"] not in live})
    if missing:
        raise SystemExit(f"not writing {models_path.name}: model ids not on OpenRouter: {missing}. "
                         "Fix models.json and rerun --refresh-prices.")
    now = utc_now()
    for e in entries:
        m = live[e["id"]]
        e["usd_per_1k_input"] = float(m["pricing"]["prompt"]) * 1000
        e["usd_per_1k_output"] = float(m["pricing"]["completion"]) * 1000
        e["price_verified_at"] = now
        e["openrouter_supported_parameters"] = m.get("supported_parameters")
    models["price_fetched_at"] = now
    models["price_source"] = "openrouter.ai/api/v1/models"
    models_path.write_text(json.dumps(models, indent=2) + "\n")
    print(f"prices verified for {len(entries)} entries at {now}")
    for e in entries:
        sp = e.get("openrouter_supported_parameters") or []
        print(f"  {e['id']:40s} in ${e['usd_per_1k_input']:.5f}/1K  out ${e['usd_per_1k_output']:.5f}/1K  "
              f"reasoning={'reasoning' in sp}  temperature={'temperature' in sp}")


def score(run_dir: Path) -> int:
    from src.perfect_lie.runner import load_records, smoke_report
    from src.perfect_lie import scoring
    ins = load_instrument()
    models = load_models()
    mf = json.loads((run_dir / "manifest.json").read_text())
    recs = load_records(run_dir)
    out = {"run_dir": str(run_dir), "mode": mf["mode"], "n_records": len(recs)}
    if mf["mode"] == "smoke":
        out["smoke"] = smoke_report(recs, models)
        for row in out["smoke"]:
            print(f"{row['model_id']:34s} {row['level']:5s} ok {row['n_ok']}/{row['n']}  "
                  f"completion~{row['median_completion_tokens']}  reasoning~{row['median_reasoning_tokens']}  "
                  f"cap {row['cap']}  trace {row['trace_kinds']}  {'; '.join(row['flags']) or 'OK'}")
    else:
        cue_ids = [c.id for c in ins.cues]
        prev = scoring.baseline_prevalence(recs, cue_ids)
        sat = scoring.saturated_cues(prev)
        rows = scoring.unit_scores(recs, ins.personas, exclude=sat)
        out.update(
            baseline_prevalence=prev, saturated=sorted(sat),
            mean_T_by_condition={"|".join(k): v for k, v in scoring.mean_T_by(rows, "condition").items()},
            mean_T_by_family_level_condition={"|".join(k): v for k, v in
                                              scoring.mean_T_by(rows, "model_family", "reasoning_level", "condition").items()},
            acceptance_by_condition={"|".join(k): v for k, v in scoring.acceptance_by(recs, "condition").items()},
            cofiring_top=scoring.cofiring_report(recs, ins.design, ins.personas)[:20],
            fabricability=scoring.fabricability_report(recs, [p.id for p in ins.prompts]),
            units=rows,
        )
        print("baseline prevalence p0(c) under none (saturated if > 0.75):")
        for c, v in prev.items():
            print(f"  {c:24s} {v['p0']:.2f}  n={v['n']}{'  SATURATED' if v['saturated'] else ''}")
        print("\nmean T by condition (saturated cues excluded):")
        for k, v in out["mean_T_by_condition"].items():
            print(f"  {k:8s} n={v['n']:4d}  mean T={v['mean_T']:+.3f}  sd={v['sd_T']:.3f}")
        print("\nfabricability under none:")
        for k, v in out["fabricability"].items():
            print(f"  {k:12s} {v['viable']}/{v['n']} viable" + (f"  failures: {v['failures']}" if v["failures"] else ""))
        print("\ntop cross-pair co-firing (phi):")
        for r in out["cofiring_top"][:8]:
            print(f"  {r['prompt_id']:12s} {r['cue_j1']}/{r['cue_j2']}  phi={r['phi']:.2f}  joint={r['p_joint']:.2f}")
    (run_dir / "score.json").write_text(json.dumps(out, indent=2, default=str) + "\n")
    print(f"\nwrote {run_dir / 'score.json'}")
    return 0


def record_fabricability(run_dir: Path) -> int:
    from src.perfect_lie.runner import load_records
    from src.perfect_lie import scoring
    mf = json.loads((run_dir / "manifest.json").read_text())
    if mf["mode"] != "pilot":
        raise SystemExit("fabricability evidence must come from a --pilot run")
    ins = load_instrument()
    rep = scoring.fabricability_report(load_records(run_dir), [p.id for p in ins.prompts])
    path = DATA_DIR / "prompts.json"
    prompts = json.loads(path.read_text())
    for p in prompts["prompts"]:
        r = rep.get(p["id"], {"n": 0, "viable": 0, "failures": []})
        evidence = (f"{run_dir.name}: {r['viable']}/{r['n']} viable lies under `none` "
                    f"({', '.join(mf['liar_models'])}, git {mf['git_sha'][:8]})")
        if r["n"] > 0 and r["viable"] == r["n"]:
            p["fabricability"] = {"status": "verified_in_pilot", "evidence": evidence}
        else:
            p["fabricability"] = {"status": "failed_in_pilot", "evidence": evidence, "failures": r["failures"]}
        print(f"{p['id']:12s} {p['fabricability']['status']:18s} {evidence}")
    path.write_text(json.dumps(prompts, indent=2) + "\n")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="print cell count and cost estimate; no model calls")
    mode.add_argument("--smoke", action="store_true", help="liar-only checks on every family x reasoning level")
    mode.add_argument("--pilot", action="store_true", help="Phase 2 pilot: pilot liar at reasoning off, 1 replicate")
    mode.add_argument("--full", action="store_true", help="Phase 3 full run (gated)")
    mode.add_argument("--resume", type=Path, metavar="RUN_DIR", help="continue an existing run directory")
    mode.add_argument("--score", type=Path, metavar="RUN_DIR", help="score a run directory; no model calls")
    mode.add_argument("--record-fabricability", type=Path, metavar="RUN_DIR", help="write pilot evidence into prompts.json")
    mode.add_argument("--refresh-prices", action="store_true", help="verify prices from OpenRouter into models.json")
    ap.add_argument("--tier", choices=sorted(TIERS), default="all", help="tier1 = reasoning off only; tier2 = low+high")
    ap.add_argument("--models", nargs="*", help="restrict liar models by id")
    ap.add_argument("--replicates", nargs="*", type=int, help="replicate ids (default 1..5); independent draws, not seeds")
    ap.add_argument("--per-level", type=int, default=4, help="smoke: liar cells per family x level")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--run-dir", type=Path, help="output directory for a new live run")
    ap.add_argument("--json", type=Path, help="also write the estimate as JSON")
    ap.add_argument("--confirm-spend", type=float, default=None, help="USD you approve; also the runtime hard cap")
    args = ap.parse_args(argv)

    models_path = DATA_DIR / "models.json"
    if args.refresh_prices:
        refresh_prices(models_path)
        return 0
    if args.score:
        return score(args.score)
    if args.record_fabricability:
        return record_fabricability(args.record_fabricability)

    instrument = load_instrument()
    models = load_models(models_path)
    replicates = tuple(args.replicates) if args.replicates else DEFAULT_REPLICATES
    liar_ids = args.models or [m["id"] for m in models["liar_models"]]
    levels = TIERS[args.tier]

    run_mode = "full"
    run_dir = args.run_dir
    if args.resume:
        run_dir = args.resume
        run_mode = json.loads((run_dir / "manifest.json").read_text())["mode"]
    elif args.smoke:
        run_mode = "smoke"
    elif args.pilot:
        run_mode = "pilot"
    elif not args.full:
        run_mode = None  # dry run

    if run_mode == "smoke":
        cells = smoke_cells(instrument, models, per_level=args.per_level)
        if args.models:
            cells = [c for c in cells if c.model_id in args.models]
    elif run_mode == "pilot":
        pl = models["pilot_liar"]
        cells = list(enumerate_cells(instrument, models, replicates=(1,), liar_model_ids=[pl["id"]], levels=(pl["level"],)))
    else:
        cells = list(enumerate_cells(instrument, models, replicates=replicates, liar_model_ids=liar_ids, levels=levels))

    est = estimate_cost(instrument, models, cells, liar_only=(run_mode == "smoke"))
    print("instrument hashes:")
    for k, v in instrument.hashes.items():
        print(f"  {k:9s} {v}")
    print()
    print(format_estimate(est, sorted({c.replicate for c in cells}), sorted({c.model_id for c in cells}),
                          sorted({c.reasoning_level for c in cells})))
    if args.json:
        args.json.write_text(json.dumps({"hashes": instrument.hashes, "estimate": est.to_dict()}, indent=2))
        print(f"\nwrote {args.json}")
    if run_mode is None:
        return 0

    problems = preflight(models, json.loads((DATA_DIR / "prompts.json").read_text()), run_mode)
    if problems:
        print(f"\nrefusing to run ({run_mode}):", file=sys.stderr)
        for pr in problems:
            print(f"  - {pr}", file=sys.stderr)
        return 4
    if args.confirm_spend is None or args.confirm_spend < est.total_usd:
        print(f"\nrefusing to run: pass --confirm-spend >= {est.total_usd:.2f} to approve this spend", file=sys.stderr)
        return 2

    from src.edsl_adapter import PerfectLieAdapter
    from src.perfect_lie.runner import Run
    if run_dir is None:
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_dir = RESULTS_ROOT / f"{run_mode}_{stamp}"
    run = Run(mode=run_mode, run_dir=run_dir, cells=cells, instrument=instrument, models=models,
              adapter=PerfectLieAdapter(service_name=models.get("service", "open_router")),
              spend_cap_usd=args.confirm_spend, concurrency=args.concurrency, models_path=models_path)
    manifest = asyncio.run(run.run())
    print(f"\n{run_mode}: {manifest['n_complete']}/{manifest['n_cells_planned']} complete, "
          f"{manifest['n_error']} error, spend ${manifest['spend_usd']:.2f}"
          f"{' (cap reached)' if manifest['spend_cap_reached'] else ''}\nrun dir: {run_dir}")
    return 0 if manifest["n_complete"] == manifest["n_cells_planned"] else 5


if __name__ == "__main__":
    sys.exit(main())
