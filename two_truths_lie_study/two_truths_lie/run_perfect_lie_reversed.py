"""Reversed-note follow-up: full run CLI (PREREG_REVERSED.md).

  python run_perfect_lie_reversed.py --dry-run           counts, cost estimate, preflight; no calls
  python run_perfect_lie_reversed.py --go --cap 125      live run (refused while the owner's lock is set)

The cap is the kill cap for the main run and the comprehension check together. Spend is the larger
of the runner's own count and OpenRouter's billed delta; every in-flight call is cancelled on breach.
"""
import argparse, asyncio, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
from src.perfect_lie import reversed_run as R
from src.perfect_lie.personas import load_instrument

RUN_DIR = HERE / "results/perfect_lie_reversed/full_run"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--go", action="store_true")
    ap.add_argument("--cap", type=float, help="kill cap in USD (registered: 125)")
    ap.add_argument("--concurrency", type=int, default=8)
    a = ap.parse_args(argv)
    cfg = R.load_config()
    main_cells, comp_cells = R.main_cells(cfg), R.comprehension_cells(cfg)
    est = R.estimate_usd(len(main_cells), len(comp_cells))
    problems = R.preflight()
    print(f"main run: {len(main_cells)} lies; comprehension: {len(comp_cells)} calls")
    print(f"estimate: main ${est['main']:.2f} + comprehension ${est['comprehension']:.2f} = ${est['total']:.2f} "
          f"(registered: flag at ${cfg['spend']['flag_usd']}, kill cap ${cfg['spend']['kill_cap_usd']})")
    print("preflight: " + ("ok" if not problems else "REFUSES:\n  - " + "\n  - ".join(problems)))
    if a.dry_run:
        return 0
    if problems:
        return 4
    if a.cap is None or a.cap > cfg["spend"]["kill_cap_usd"]:
        print(f"refusing: pass --cap <= {cfg['spend']['kill_cap_usd']}", file=sys.stderr)
        return 2
    from src.edsl_adapter import PerfectLieAdapter
    from src.perfect_lie.transport import TransportRetryAdapter
    from run_perfect_lie import openrouter_billed_usd
    adapter = TransportRetryAdapter(PerfectLieAdapter(service_name="open_router"))
    main_run, comp = R.make_runs(run_dir=RUN_DIR, instrument=load_instrument(), adapter=adapter, cap_usd=a.cap,
                                 concurrency=a.concurrency, billing_probe=openrouter_billed_usd, cfg=cfg)
    mf = asyncio.run(main_run.run())
    print(f"main: {mf['n_complete']}/{mf['n_cells_planned']} complete, {mf['n_error']} failed, ${mf['spend_usd']:.2f}", flush=True)
    if mf["spend_cap_reached"]:
        print("cap reached: stopped", file=sys.stderr)
        return 5
    cr = comp(a.cap - mf["spend_usd"])
    mc = asyncio.run(cr.run())
    print(f"comprehension: {mc['n_complete']}/{mc['n_cells_planned']} complete, {mc['n_error']} failed, ${mc['spend_usd']:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
