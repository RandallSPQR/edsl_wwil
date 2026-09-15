#!/usr/bin/env python3
"""The Perfect Lie: entry point.

    python run_perfect_lie.py --dry-run             # cell count + cost estimate, no model calls
    python run_perfect_lie.py --dry-run --json out.json
    python run_perfect_lie.py --pilot               # Phase 2: 1 model x 1 replicate (not yet implemented)
    python run_perfect_lie.py --full --confirm-spend N   # Phase 3 (gated; not yet implemented)
    python run_perfect_lie.py --refresh-prices      # overwrite prices in models.json from OpenRouter

Cost guard: any mode that would call a model refuses to start unless the
estimate has been printed and --confirm-spend USD is at least the estimate.
"""

import argparse
import json
import sys
from pathlib import Path

from src.perfect_lie import DATA_DIR
from src.perfect_lie.personas import load_instrument
from src.perfect_lie.pipeline import (
    DEFAULT_REPLICATES, REASONING_LEVELS, TIERS, enumerate_cells, estimate_cost, format_estimate, load_models, preflight,
)


def refresh_prices(models_path: Path) -> None:
    import datetime
    import urllib.request
    models = json.loads(models_path.read_text())
    with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as r:
        live = {m["id"]: m for m in json.load(r)["data"]}
    entries = list(models["liar_models"]) + [models["target_model"]] + list(models["graders"]) + ([models["trace_probe"]] if models.get("trace_probe") else [])
    missing = []
    for e in entries:
        m = live.get(e["id"])
        if m is None:
            missing.append(e["id"])
            continue
        e["usd_per_1k_input"] = float(m["pricing"]["prompt"]) * 1000
        e["usd_per_1k_output"] = float(m["pricing"]["completion"]) * 1000
    models["price_fetched_at"] = datetime.datetime.utcnow().isoformat() + "Z"
    models["price_source"] = "openrouter.ai/api/v1/models"
    models_path.write_text(json.dumps(models, indent=2) + "\n")
    print(f"prices refreshed; missing ids: {missing or 'none'}")
    if missing:
        raise SystemExit("some model ids do not exist on OpenRouter; fix models.json before Phase 2")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="print cell count and cost estimate; no model calls")
    ap.add_argument("--pilot", action="store_true", help="Phase 2 pilot: 1 model x 1 replicate")
    ap.add_argument("--tier", choices=sorted(TIERS), default="all", help="tier1 = reasoning off only (primary test); tier2 = low+high; all = both")
    ap.add_argument("--full", action="store_true", help="Phase 3 full run (gated: verified prices and pilot-verified prompts)")
    ap.add_argument("--refresh-prices", action="store_true", help="fetch live prices into models.json")
    ap.add_argument("--models", nargs="*", help="restrict liar models by id")
    ap.add_argument("--replicates", nargs="*", type=int, help="replicate ids (default 1..5); independent draws, not provider seeds")
    ap.add_argument("--json", type=Path, help="also write the estimate as JSON")
    ap.add_argument("--confirm-spend", type=float, default=None, help="USD ceiling you approve for a live run")
    args = ap.parse_args(argv)

    models_path = DATA_DIR / "models.json"
    if args.refresh_prices:
        refresh_prices(models_path)
        return 0

    instrument = load_instrument()
    models = load_models(models_path)
    replicates = tuple(args.replicates) if args.replicates else DEFAULT_REPLICATES
    liar_ids = args.models or [m["id"] for m in models["liar_models"]]
    levels = TIERS[args.tier]
    if args.pilot:
        replicates = (replicates[0],)
        liar_ids = liar_ids[:1]
        levels = ("off",)

    cells = list(enumerate_cells(instrument, models, replicates=replicates, liar_model_ids=liar_ids, levels=levels))
    est = estimate_cost(instrument, models, cells)

    print("instrument hashes:")
    for k, v in instrument.hashes.items():
        print(f"  {k:9s} {v}")
    print()
    print(format_estimate(est, replicates, liar_ids, levels))
    if args.json:
        args.json.write_text(json.dumps({"hashes": instrument.hashes, "estimate": est.to_dict()}, indent=2))
        print(f"\nwrote {args.json}")

    if args.dry_run or not (args.pilot or args.full):
        return 0

    mode = "full" if args.full else "pilot"
    problems = preflight(models, json.loads((DATA_DIR / "prompts.json").read_text()), mode)
    if problems:
        print(f"\nrefusing to run ({mode}):", file=sys.stderr)
        for pr in problems:
            print(f"  - {pr}", file=sys.stderr)
        return 4

    if args.confirm_spend is None or args.confirm_spend < est.total_usd:
        print(f"\nrefusing to run: pass --confirm-spend >= {est.total_usd:.2f} to approve this spend", file=sys.stderr)
        return 2
    print(f"\n--{mode} execution is implemented in Phase 2/3; nothing was run.", file=sys.stderr)
    return 3


if __name__ == "__main__":
    sys.exit(main())
