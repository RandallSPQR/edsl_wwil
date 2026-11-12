"""Tier 1 (API, re-measurement): re-grade released lies with the primary grader and compare with the released grades.

Same lies, same frozen rubric (v0.6), same grader model id; only the grader call is new. It measures grader stability,
not the experiment: Tier 0 already reproduces every number from the released grades.

  python release/tiers/tier1_regrade.py --study reversed --fraction 0.10            dry run: sample and cost only
  python release/tiers/tier1_regrade.py --study reversed --fraction 0.10 --go --cap-usd 10
Run from two_truths_lie_study/. Needs PL_GRADER_KEY (an Anthropic API key; never printed) for --go. Writes
build/tier1/<study>/regrades.jsonl (one row per lie, resumable) and agreement.json (per-cue and pooled kappa against
the released primary grades, and the change in s per lie).

Route: the direct Anthropic API with the strict forced tool (src/perfect_lie/grader_direct.py, the Phase 2 route).
Study 1 and the reversed note were graded through OpenRouter; the Phase 2 route check found kappa 0.915 between the
two (results/phase2/grading_route/regrade_direct.json).
Caveats (README "Tiers"): the model id `claude-sonnet-4-5` may be served by a newer snapshot or retired; grades are
not deterministic even at temperature 0; prices change (--price-in/--price-out, USD per million tokens).
"""
import argparse, gzip, json, random, sys
from pathlib import Path

REL = Path(__file__).resolve().parents[1]
STUDY = REL.parent
TTL = STUDY / "two_truths_lie"
sys.path.insert(0, str(TTL))
SOURCES = {"study1": TTL / "results/perfect_lie/full_interim_r01-15/records.jsonl.gz",
           "reversed": TTL / "results/perfect_lie_reversed/full_run/main/records.jsonl.gz",
           "phase2": [TTL / f"results/phase2/stage2/{s}/graded.jsonl.gz" for s in ("gemma-3-27b-it", "llama-3.1-8b-instruct")]}


def lies(study):
    if study == "phase2":
        rows = [json.loads(l) for p in SOURCES["phase2"] for l in gzip.open(p, "rt")]
        out = []
        for r in rows:
            if r.get("status") == "complete" and (r.get("grade") or {}).get("cues"):
                out.append({"id": f"{r['model']}|{r['key']}|{r['item_id']}", "user_prompt": r["user_prompt"],
                            "lie": r["text"], "released": r["grade"]["cues"],
                            "usage": (r.get("primary") or {}).get("usage") or {}})
        return out
    last = {}
    for l in gzip.open(SOURCES[study], "rt"):
        r = json.loads(l); last[r["cell_id"]] = r
    out = []
    for r in last.values():
        p = (r.get("grades") or {}).get("primary") or {}
        if r.get("status") == "complete" and p.get("cues"):
            u = p.get("usage") or {}
            out.append({"id": r["cell_id"], "user_prompt": r["user_prompt"], "lie": r["lie"], "released": p["cues"],
                        "usage": {"input_tokens": u.get("prompt_tokens", u.get("input_tokens", 0)),
                                  "output_tokens": u.get("completion_tokens", u.get("output_tokens", 0))}})
    return out


def kappa(a, b):
    n = len(a)
    if not n:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return None if pe == 1 else (po - pe) / (1 - pe)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", choices=list(SOURCES), required=True)
    ap.add_argument("--fraction", type=float, default=0.10)
    ap.add_argument("--seed", type=int, default=20261029)
    ap.add_argument("--price-in", type=float, default=3.0, help="USD per million input tokens")
    ap.add_argument("--price-out", type=float, default=15.0, help="USD per million output tokens")
    ap.add_argument("--go", action="store_true")
    ap.add_argument("--cap-usd", type=float)
    a = ap.parse_args()
    pool = sorted(lies(a.study), key=lambda x: x["id"])
    sample = random.Random(a.seed).sample(pool, max(1, round(a.fraction * len(pool))))
    est_in = sum(x["usage"].get("input_tokens", 0) for x in sample)
    est_out = sum(x["usage"].get("output_tokens", 0) for x in sample)
    est = est_in * a.price_in / 1e6 + est_out * a.price_out / 1e6
    print(json.dumps({"study": a.study, "graded_lies": len(pool), "sample": len(sample), "seed": a.seed,
                      "estimate_usd": round(est, 2), "basis": "the released grading calls' own token usage"}, indent=1))
    if not a.go:
        print("dry run: nothing sent. Add --go --cap-usd C to grade.")
        return
    if a.cap_usd is None or a.cap_usd < est:
        raise SystemExit(f"refusing: --cap-usd must be at least the estimate (${est:.2f})")
    from src.perfect_lie import grader_direct
    from src.perfect_lie.grader import build_grader_input
    from src.perfect_lie.personas import load_instrument
    cues = load_instrument().cues
    order = [c.id for c in cues]
    out = STUDY / "build" / "tier1" / a.study
    out.mkdir(parents=True, exist_ok=True)
    rp = out / "regrades.jsonl"
    done = {json.loads(l)["id"]: json.loads(l) for l in rp.open()} if rp.exists() else {}
    spent = sum(r["usd"] for r in done.values())
    with rp.open("a") as f:
        for x in sample:
            if x["id"] in done:
                continue
            if spent >= a.cap_usd:
                print(f"cap reached (${spent:.2f}); stopping"); break
            g = grader_direct.grade(build_grader_input(x["user_prompt"], x["lie"], cues), order)
            usd = g["usage"]["input_tokens"] * a.price_in / 1e6 + g["usage"]["output_tokens"] * a.price_out / 1e6
            spent += usd
            row = {"id": x["id"], "released": x["released"], "regrade": (g["parsed"] or {}).get("cues"),
                   "models_returned": g["models_returned"], "error": g["error"], "usd": usd}
            f.write(json.dumps(row) + "\n"); f.flush()
            done[x["id"]] = row
    ok = [r for r in done.values() if r["regrade"]]
    per = {c: kappa([bool(r["released"][c]) for r in ok], [bool(r["regrade"][c]) for r in ok]) for c in order}
    a_all = [bool(r["released"][c]) for r in ok for c in order]; b_all = [bool(r["regrade"][c]) for r in ok for c in order]
    rep = {"study": a.study, "regraded": len(ok), "failed": len(done) - len(ok), "spent_usd": round(spent, 2),
           "models_returned": sorted({m for r in done.values() for m in r["models_returned"]}),
           "pooled_kappa": kappa(a_all, b_all), "pooled_agreement": sum(p == q for p, q in zip(a_all, b_all)) / len(a_all) if a_all else None,
           "per_cue_kappa": per}
    (out / "agreement.json").write_text(json.dumps(rep, indent=1) + "\n")
    print(json.dumps({k: rep[k] for k in ("regraded", "failed", "spent_usd", "models_returned", "pooled_kappa")}, indent=1))


if __name__ == "__main__":
    main()
