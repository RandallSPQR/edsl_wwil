#!/usr/bin/env python3
"""The Perfect Lie: entry point.

    python run_perfect_lie.py --check-env                           # is the OpenRouter key set up right? (no model calls)
    python run_perfect_lie.py --classes                             # list model classes and their status
    python run_perfect_lie.py --dry-run --class C1 [--tier ...]     # cells + cost, no model calls
    python run_perfect_lie.py --refresh-prices                      # verify prices from OpenRouter (no key needed)
    python run_perfect_lie.py --smoke --confirm-spend USD           # liar-only checks, every family x level
    python run_perfect_lie.py --pilot --confirm-spend USD           # Phase 2 pilot, one family at reasoning off
    python run_perfect_lie.py --full  --confirm-spend USD           # Phase 3 (gated)
    python run_perfect_lie.py --resume RUN_DIR --confirm-spend USD  # continue a crashed or capped run
    python run_perfect_lie.py --score RUN_DIR                       # T, p0, co-firing, acceptance, fabricability
    python run_perfect_lie.py --record-fabricability RUN_DIR        # write pilot evidence into prompts.json
    python run_perfect_lie.py --export-replay RUN_DIR               # open-weight lies + exact messages for pod replay

Every live and dry-run command works on one class (--class, default C1). Pilot and full
runs need the class approved in models.json; a smoke test may run on a proposed class.

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
    priced_entries, select_class, smoke_cells,
)

HERE = Path(__file__).resolve().parent
RESULTS_ROOT = HERE / "results" / "perfect_lie"
ENV_FILE = HERE / ".env"   # the same file src/edsl_adapter.py loads

# Load the key before any gate reads the environment. Without this, a key that exists
# only in .env would be refused by preflight, which runs before EDSL or the adapter
# (both of which load .env themselves) are imported. Existing variables win.
try:
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE, override=False)
except ImportError:
    pass

# EDSL reads its settings once, at import. Its default API timeout (60 s) is shorter than
# a gpt-5 high-effort call, and a timed-out call is retried up to EDSL_MAX_ATTEMPTS times
# while OpenRouter still bills each attempt it completes. Set before EDSL is imported;
# an explicit environment value wins.
import os as _os
_os.environ.setdefault("EDSL_API_TIMEOUT", "900")

LOCKS_PATH = DATA_DIR / "run_locks.json"


def run_locks() -> dict:
    return json.loads(LOCKS_PATH.read_text()) if LOCKS_PATH.exists() else {}


KEY_VAR = "OPEN_ROUTER_API_KEY"
# Names people commonly use for this key that EDSL does NOT read.
KEY_MISNAMES = ("OPENROUTER_API_KEY", "OPENROUTER_KEY", "OPEN_ROUTER_KEY", "OPENROUTER_TOKEN")


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


def refresh_prices(models_path: Path) -> None:
    """Overwrite every price, in every class, from OpenRouter's public model list, and confirm
    each provider pin still has a matching endpoint (bf16 for open weights). Atomic: nothing
    is written unless every id resolves and every pin is servable."""
    import urllib.request
    models = json.loads(models_path.read_text())
    with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as r:
        live = {m["id"]: m for m in json.load(r)["data"]}
    entries = priced_entries(models)
    missing = sorted({e["id"] for e in entries if e["id"] not in live})
    if missing:
        raise SystemExit(f"not writing {models_path.name}: model ids not on OpenRouter: {missing}. "
                         "Fix models.json and rerun --refresh-prices.")
    pin_problems = []
    checked = {}
    for e in entries:
        pin = e.get("provider")
        if not pin or e["id"] in checked:
            continue
        with urllib.request.urlopen(f"https://openrouter.ai/api/v1/models/{e['id']}/endpoints", timeout=30) as r:
            eps = json.load(r)["data"]["endpoints"]
        allowed = {x.lower() for x in (pin.get("only") or pin.get("order") or [])}
        quants = set(pin.get("quantizations") or [])
        ok = [ep for ep in eps if (ep.get("tag", "").split("/")[0].lower() in allowed
                                   or (ep.get("provider_name") or "").lower() in allowed)
              and (not quants or ep.get("quantization") in quants)]
        checked[e["id"]] = [f"{ep.get('provider_name')}:{ep.get('quantization')}" for ep in ok]
        if not ok:
            pin_problems.append(f"{e['id']}: no endpoint matches pin {pin}")
    if pin_problems:
        raise SystemExit("not writing models.json: " + "; ".join(pin_problems))
    now = utc_now()
    for e in entries:
        m = live[e["id"]]
        e["usd_per_1k_input"] = float(m["pricing"]["prompt"]) * 1000
        e["usd_per_1k_output"] = float(m["pricing"]["completion"]) * 1000
        e["price_verified_at"] = now
        e["openrouter_supported_parameters"] = m.get("supported_parameters")
        if e["id"] in checked:
            e["pinned_endpoints_verified"] = checked[e["id"]]
    models["price_fetched_at"] = now
    models["price_source"] = "openrouter.ai/api/v1/models"
    models_path.write_text(json.dumps(models, indent=2) + "\n")
    seen = set()
    print(f"prices verified for {len({e['id'] for e in entries})} model ids at {now}")
    for e in entries:
        if e["id"] in seen:
            continue
        seen.add(e["id"])
        sp = e.get("openrouter_supported_parameters") or []
        pin = f"  pinned {checked[e['id']]}" if e["id"] in checked else ""
        print(f"  {e['id']:40s} in ${e['usd_per_1k_input']:.5f}/1K  out ${e['usd_per_1k_output']:.5f}/1K  "
              f"reasoning={'reasoning' in sp}{pin}")


def list_classes() -> int:
    models = load_models()
    for cid in models["class_design"]["order"]:
        c = models["classes"][cid]
        print(f"{cid}  [{c['status']}]  {c['name']}")
        for m in c["liar_models"]:
            pin = f" pin={m['provider']['only']}/bf16" if m.get("provider") else ""
            sysr = "" if m.get("system_role", True) else " (no system role: folded)"
            print(f"     liar  {m['id']:40s} {m['family']:9s} {m['weights']:6s} {m['released']}{pin}{sysr}")
        extra = [t["id"] for t in c["target_models"] if t["id"] not in {m["id"] for m in c["liar_models"]}]
        print(f"     targets: every liar above{(' + ' + ', '.join(extra)) if extra else ''}")
    print("graders (all classes): " + ", ".join(f"{g['role']}={g['id']}" for g in models["graders"]))
    return 0


def export_replay(run_dir: Path) -> int:
    """Write replay.jsonl: for every open-weight lie, the HF checkpoint, the exact messages the
    model received, and the completion, so the pod can teacher-force the same sequence."""
    from src.perfect_lie.runner import load_records
    models = load_models()
    liars = {m["id"]: m for c in models["classes"].values() for m in c["liar_models"]}
    out, n = run_dir / "replay.jsonl", 0
    with out.open("w") as f:
        for r in load_records(run_dir):
            m = liars.get(r.get("model_id"))
            if not m or m.get("weights") != "open" or not r.get("lie"):
                continue
            f.write(json.dumps({
                "cell_id": r["cell_id"], "hf_checkpoint": m.get("hf_checkpoint"), "openrouter_id": m["id"],
                "served_provider": r.get("liar_served_provider"), "provider_pin": r.get("liar_provider_pin"),
                "messages": r.get("liar_delivered_messages"), "completion": r["lie"],
                "temperature": r.get("temperature"), "max_output_tokens": r.get("max_output_tokens"),
                "condition": r["condition"], "prompt_id": r["prompt_id"], "pair": [r["j1"], r["j2"]],
                "target_persona": r["target_id"], "replicate": r["replicate"],
                "generation_id": r.get("liar_generation_id"),
            }, ensure_ascii=False) + "\n")
            n += 1
    print(f"wrote {n} open-weight lies to {out}")
    return 0


def openrouter_billed_usd() -> float:
    """Total usage billed on this key so far, from OpenRouter's free /api/v1/key endpoint."""
    import os
    import urllib.request
    req = urllib.request.Request("https://openrouter.ai/api/v1/key",
                                 headers={"Authorization": f"Bearer {os.environ[KEY_VAR]}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return float(json.load(r)["data"].get("usage") or 0.0)


def check_env() -> int:
    """Report whether the OpenRouter key is set up the way EDSL reads it. Never prints the key."""
    import os
    import re
    problems, notes = [], []
    if ENV_FILE.exists():
        notes.append(f".env found at {ENV_FILE}")
        raw = ENV_FILE.read_text()
        lines = {}
        for n, line in enumerate(raw.splitlines(), 1):
            m = re.match(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
            if m:
                lines[m.group(1)] = (n, m.group(2))
        if KEY_VAR in lines:
            n, val = lines[KEY_VAR]
            stripped = val.strip()
            if stripped != val.rstrip("\n") or val != val.strip():
                notes.append(f"line {n}: surrounding whitespace (python-dotenv strips it; harmless)")
            if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in "\"'":
                notes.append(f"line {n}: value is quoted (python-dotenv removes matching quotes; harmless)")
            if " #" in stripped:
                notes.append(f"line {n}: an inline comment follows the value; check it is not part of the key")
        for bad in KEY_MISNAMES:
            if bad in lines:
                problems.append(f".env line {lines[bad][0]} sets {bad}; EDSL reads {KEY_VAR}. Rename it.")
    else:
        notes.append(f"no .env at {ENV_FILE}; relying on the process environment")
    for bad in KEY_MISNAMES:
        if os.environ.get(bad) and not os.environ.get(KEY_VAR):
            problems.append(f"environment sets {bad}; EDSL reads {KEY_VAR}. Rename it.")
    key = (os.environ.get(KEY_VAR) or "").strip().strip("\"'")
    if not key:
        problems.append(f"{KEY_VAR} is not set")
    else:
        shape = f"{len(key)} characters, starts with {key[:9]!r}" if key.startswith("sk-or-") else f"{len(key)} characters"
        notes.append(f"{KEY_VAR} is set ({shape})")
        if not key.startswith("sk-or-v1-"):
            problems.append(f"{KEY_VAR} does not start with 'sk-or-v1-'; OpenRouter keys do. Check you copied the whole key.")
        if re.search(r"\s", key):
            problems.append(f"{KEY_VAR} contains whitespace inside the key")
        # Free check: GET /api/v1/key returns the key's limits and usage, no model call, no charge.
        import urllib.request, urllib.error
        req = urllib.request.Request("https://openrouter.ai/api/v1/key", headers={"Authorization": f"Bearer {key}"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.load(r).get("data", {})
            limit = data.get("limit")
            notes.append(f"OpenRouter accepted the key: usage ${data.get('usage', 0):.2f}, "
                         f"limit {'none' if limit is None else f'${limit:.2f}'}, free tier {data.get('is_free_tier')}")
        except urllib.error.HTTPError as e:
            problems.append(f"OpenRouter rejected the key (HTTP {e.code}); it is wrong, revoked, or truncated")
        except Exception as e:
            notes.append(f"could not reach openrouter.ai to validate the key ({type(e).__name__}); format checks only")
    try:
        import subprocess
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", str(ENV_FILE)], capture_output=True, cwd=HERE)
        if tracked.returncode == 0:
            problems.append(f"{ENV_FILE.name} is tracked by git; remove it from the index and rotate the key")
        elif ENV_FILE.exists():
            ignored = subprocess.run(["git", "check-ignore", "-q", str(ENV_FILE)], cwd=HERE).returncode == 0
            notes.append(".env is ignored by git" if ignored else ".env is NOT ignored by git; do not commit it")
    except Exception:
        pass
    for n in notes:
        print(f"  ok    {n}")
    for p in problems:
        print(f"  FIX   {p}")
    print("\nkey set up correctly" if not problems else f"\n{len(problems)} problem(s)")
    return 0 if not problems else 6


def score(run_dir: Path, only_models=None) -> int:
    from src.perfect_lie.runner import load_records, smoke_report
    from src.perfect_lie import scoring
    ins = load_instrument()
    mf = json.loads((run_dir / "manifest.json").read_text())
    models = select_class(load_models(), mf.get("class_id") or "C3")
    recs = load_records(run_dir)
    if only_models:
        recs = [r for r in recs if r["model_id"] in only_models]
    out = {"run_dir": str(run_dir), "mode": mf["mode"], "n_records": len(recs), "liar_models": only_models or "all"}
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
            acceptance_crossing_family=scoring.acceptance_crossing(recs, "family"),
            acceptance_crossing_model=scoring.acceptance_crossing(recs, "model"),
            grader_self_preference=scoring.grader_self_preference(recs, cue_ids, models["graders"]),
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
        cr = out["acceptance_crossing_family"]
        print("\nacceptance, liar family -> target family:")
        for k, v in cr["matrix"].items():
            print(f"  {k:24s} n={v['n']:4d}  accept={v['accept_rate']:.2f}")
        print(f"  same family minus other: {cr['summary']['diagonal_minus_off']}")
        print("\ngrader self-preference (own family marked *):")
        for row in out["grader_self_preference"]:
            print(f"  {row['grader']:9s} on {row['liar_family']:9s}{' *' if row['own_family'] else '  '} "
                  f"cues marked {row['mean_cues_marked']:.2f}  disagreement {row['disagreement_with_others']:.3f}  n={row['n']}")
        print("\ntop cross-pair co-firing (phi):")
        for r in out["cofiring_top"][:8]:
            print(f"  {r['prompt_id']:12s} {r['cue_j1']}/{r['cue_j2']}  phi={r['phi']:.2f}  joint={r['p_joint']:.2f}")
    name = "score.json" if not only_models else "score_" + "_".join(m.split("/")[-1] for m in only_models) + ".json"
    (run_dir / name).write_text(json.dumps(out, indent=2, default=str) + "\n")
    print(f"\nwrote {run_dir / name}")
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
    mode.add_argument("--check-env", action="store_true", help="check the OpenRouter key setup; never prints the key")
    mode.add_argument("--classes", action="store_true", help="list model classes and their status")
    mode.add_argument("--invalidate", type=Path, metavar="RUN_DIR",
                      help="mark cells for regeneration (filter with --conditions, --models, --status); no model calls")
    ap.add_argument("--conditions", nargs="*", help="--pilot/--invalidate: only these conditions")
    ap.add_argument("--prompt-version", help="public prompt version for a new run (prompts.json; default: active)")
    mode.add_argument("--stage1-report", nargs=2, type=Path, metavar=("NEW_RUN_DIR", "REF_RUN_DIR"),
                      help="Stage 1 pass criteria: new-prompt control cells vs original-prompt reference; no model calls")
    ap.add_argument("--status", nargs="*", help="--invalidate: only cells whose current status is one of these")
    ap.add_argument("--reason", default="", help="--invalidate: why, recorded in each record")
    mode.add_argument("--export-replay", type=Path, metavar="RUN_DIR", help="export open-weight lies for pod replay")
    ap.add_argument("--class", dest="class_id", default="C1", help="model class to run (default C1)")
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
    if args.check_env:
        return check_env()
    if args.classes:
        return list_classes()
    if args.export_replay:
        return export_replay(args.export_replay)
    if args.stage1_report:
        from src.perfect_lie.runner import load_records
        from src.perfect_lie.stage1 import evaluate, render_markdown
        from src.perfect_lie.conditions import prompt_word_range
        new_dir, ref_dir = args.stage1_report
        cue_ids = [c.id for c in load_instrument().cues]
        res = evaluate(load_records(new_dir), load_records(ref_dir), cue_ids, prompt_word_range("v2"))
        md = render_markdown(res, cue_ids, str(new_dir), str(ref_dir))
        (new_dir / "stage1_report.md").write_text(md)
        (new_dir / "stage1_report.json").write_text(json.dumps(res, indent=2, default=str) + "\n")
        print(md)
        return 0
    if args.invalidate:
        from src.perfect_lie.runner import invalidate_cells
        if not args.reason:
            raise SystemExit("--invalidate needs --reason")
        pred = lambda r: ((not args.conditions or r["condition"] in args.conditions)
                          and (not args.models or r["model_id"] in args.models)
                          and (not args.status or r.get("status") in args.status))
        n = invalidate_cells(args.invalidate, pred, args.reason)
        print(f"invalidated {n} cells in {args.invalidate}; regenerate with --resume")
        return 0
    if args.refresh_prices:
        refresh_prices(models_path)
        return 0
    if args.score:
        return score(args.score, args.models)
    if args.record_fabricability:
        return record_fabricability(args.record_fabricability)

    instrument = load_instrument()
    all_models = load_models(models_path)
    levels = TIERS[args.tier]

    run_mode = "full"
    run_dir = args.run_dir
    class_id = args.class_id
    if args.resume:
        run_dir = args.resume
        prev = json.loads((run_dir / "manifest.json").read_text())
        run_mode = prev["mode"]
        class_id = prev.get("class_id") or class_id
    elif args.smoke:
        run_mode = "smoke"
    elif args.pilot:
        run_mode = "pilot"
    elif not args.full:
        run_mode = None  # dry run
    models = select_class(all_models, class_id)
    replicates = tuple(args.replicates) if args.replicates else DEFAULT_REPLICATES
    liar_ids = args.models or [m["id"] for m in models["liar_models"]]
    print(f"class {class_id} [{models['class_status']}]: {models['class_name']}")

    if run_mode == "smoke":
        cells = smoke_cells(instrument, models, per_level=args.per_level)
        if args.models:
            cells = [c for c in cells if c.model_id in args.models]
    elif run_mode == "pilot":
        # Every liar in the class, reasoning off, one replicate: the fabricability gate has to
        # hold for each model, and the weakest model is where it is most likely to fail.
        cells = list(enumerate_cells(instrument, models, replicates=(1,), liar_model_ids=liar_ids, levels=("off",),
                                     prompt_version=args.prompt_version,
                                     conditions=tuple(args.conditions) if args.conditions else ("none", "placebo", "partial", "full")))
    else:
        cells = list(enumerate_cells(instrument, models, replicates=replicates, liar_model_ids=liar_ids, levels=levels))

    probe_locked = run_locks().get("trace_probe", {}).get("locked", True)
    est = estimate_cost(instrument, models, cells, liar_only=(run_mode == "smoke"),
                        include_trace_probe=not probe_locked)
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
    locks = run_locks()
    if run_mode == "full" and locks.get("full_run", {}).get("locked", True):
        problems.insert(0, f"full run is LOCKED by the owner ({LOCKS_PATH.name}): {locks.get('full_run', {}).get('reason')}")
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
              spend_cap_usd=args.confirm_spend, concurrency=args.concurrency, models_path=models_path,
              trace_probe_locked=locks.get("trace_probe", {}).get("locked", True),
              billing_probe=openrouter_billed_usd)
    manifest = asyncio.run(run.run())
    print(f"\n{run_mode}: {manifest['n_complete']}/{manifest['n_cells_planned']} complete, "
          f"{manifest['n_error']} error, spend ${manifest['spend_usd']:.2f}"
          f"{' (cap reached)' if manifest['spend_cap_reached'] else ''}\nrun dir: {run_dir}")
    return 0 if manifest["n_complete"] == manifest["n_cells_planned"] else 5


if __name__ == "__main__":
    sys.exit(main())
