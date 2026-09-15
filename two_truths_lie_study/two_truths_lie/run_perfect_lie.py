#!/usr/bin/env python3
"""The Perfect Lie: entry point.

    python run_perfect_lie.py --dry-run             # cell count + cost estimate, no model calls
    python run_perfect_lie.py --dry-run --json out.json
    python run_perfect_lie.py --pilot               # Phase 2: 1 model x 1 seed (not yet implemented)
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
    DEFAULT_SEEDS, enumerate_cells, estimate_cost, format_estimate, load_models,
)


def refresh_prices(models_path: Path) -> None:
    import datetime
    import urllib.request
    models = json.loads(models_path.read_text())
    with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as r:
        live = {m["id"]: m for m in json.load(r)["data"]}
    entries = list(models["liar_models"]) + [models["target_model"], models["grader_model"]]
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="print cell count and cost estimate; no model calls")
    ap.add_argument("--pilot", action="store_true", help="Phase 2 pilot: 1 model x 1 seed")
    ap.add_argument("--refresh-prices", action="store_true", help="fetch live prices into models.json")
    ap.add_argument("--models", nargs="*", help="restrict liar models by id")
    ap.add_argument("--seeds", nargs="*", type=int, help="replicate indices (default 1..5)")
    ap.add_argument("--json", type=Path, help="also write the estimate as JSON")
    ap.add_argument("--confirm-spend", type=float, default=None, help="USD ceiling you approve for a live run")
    args = ap.parse_args(argv)

    models_path = DATA_DIR / "models.json"
    if args.refresh_prices:
        refresh_prices(models_path)
        return 0

    instrument = load_instrument()
    models = load_models(models_path)
    seeds = tuple(args.seeds) if args.seeds else DEFAULT_SEEDS
    liar_ids = args.models or [m["id"] for m in models["liar_models"]]
    if args.pilot:
        seeds = (seeds[0],)
        liar_ids = liar_ids[:1]

    cells = list(enumerate_cells(instrument, models, seeds=seeds, liar_model_ids=liar_ids))
    est = estimate_cost(instrument, models, cells)

    print("instrument hashes:")
    for k, v in instrument.hashes.items():
        print(f"  {k:9s} {v}")
    print()
    print(format_estimate(est, seeds, liar_ids))
    if args.json:
        args.json.write_text(json.dumps({"hashes": instrument.hashes, "estimate": est.to_dict()}, indent=2))
        print(f"\nwrote {args.json}")

    if args.dry_run or not args.pilot:
        return 0

    if args.confirm_spend is None or args.confirm_spend < est.total_usd:
        print(f"\nrefusing to run: pass --confirm-spend >= {est.total_usd:.2f} to approve this spend", file=sys.stderr)
        return 2
    print("\n--pilot execution is implemented in Phase 2; nothing was run.", file=sys.stderr)
    return 3


if __name__ == "__main__":
    sys.exit(main())
