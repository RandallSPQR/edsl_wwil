"""Phase 2 identity check, part 2: behavioral equivalence, pod vs API (rules: RULES.md, item 2).

Steps (each a subcommand; all committed before any pod lie exists):
  draw      36 categories, seeded (SEED), from the frozen final_72 -> behavioral_categories.json
  generate  unsteered placebo / full / reversed lies on the pod for both models, on the drawn
            categories x the 5 targets, one per cell (540 per model). The exact messages the API
            models received in the reversed-note run (replay export); temperature 0.6, top_p 0.9,
            max tokens as in the run; batched, seed SEED + batch index. Llama rendered without the
            template's date header (as CoreWeave renders it); Gemma with its standard template.
            -> pod_run/records.jsonl in the runner's record format, stage_done = liar
  grade     the frozen runner's own grader stage (FollowupRun, stages liar -> graders, liar already
            done), primary grader only (anthropic/claude-sonnet-4.5 via OpenRouter, rubric v0.6),
            namespace pod_identity, spend cap CAP_USD
  analyse   s per lie with the reversed-note run's registered gate (historical_anchor and
            emotional_appeal excluded) and confession screen; per model and category, the persona
            mean of s per condition and of B = full - reversed; d_k = pod - API, paired by category;
            TOST at +/-0.10 (90% CI on K - 1 df) on d for B and for each condition's s.
            Pass for a model = all four TOSTs pass. -> behavioral_result.json / .md

  python behavioral.py draw
  python behavioral.py generate --pod POD_ID --key-file PATH
  python behavioral.py grade
  python behavioral.py analyse
"""
import argparse, asyncio, json, random, sys, time
from dataclasses import asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))

SEED, K, MARGIN, CAP_USD = 20261022, 36, 0.10, 25.0
MODELS = ["meta-llama/llama-3.1-8b-instruct", "google/gemma-3-27b-it"]
BATCH = {"meta-llama/llama-3.1-8b-instruct": 24, "google/gemma-3-27b-it": 12}
NAMESPACE = "pod_identity"
POD_RUN = HERE / "pod_run"
REGISTERED_GATE_EXCLUDED = ["historical_anchor", "emotional_appeal"]   # reversed-note run, final_report.json


def draw():
    from src.perfect_lie import reversed_run as R
    cats = random.Random(SEED).sample(sorted(R.load_config()["categories"]), K)
    (HERE / "behavioral_categories.json").write_text(json.dumps({"seed": SEED, "k": K, "categories": sorted(cats)}, indent=1) + "\n")
    print(sorted(cats))


def cells():
    from src.perfect_lie import reversed_run as R
    cats = set(json.loads((HERE / "behavioral_categories.json").read_text())["categories"])
    return [c for c in R.main_cells() if c.model_id in MODELS and c.category in cats]


def generate(pod, key_file):
    import diagnostic as D
    from diagnostic_tf import get, POD_MODEL
    from src.perfect_lie import reversed as rv
    from src.perfect_lie.runner import cell_id
    from src.perfect_lie.personas import load_instrument
    inst = load_instrument()
    key = Path(key_file).read_text().strip()
    base, auth = f"https://{pod}-8000.proxy.runpod.net", {"Authorization": f"Bearer {key}"}
    replay = {r["cell_id"]: r for r in map(json.loads, D.REPLAY.open())}
    POD_RUN.mkdir(exist_ok=True)
    out = POD_RUN / "records.jsonl"
    done = {json.loads(l)["cell_id"] for l in out.open()} if out.exists() else set()
    for m in MODELS:
        todo = [c for c in cells() if c.model_id == m and cell_id(c, NAMESPACE) not in done]
        if not todo:
            continue
        D.post(f"{base}/load", {"model": POD_MODEL[m]}, auth, timeout=90)
        while get(f"{base}/health", auth).get("loaded") != POD_MODEL[m]:
            time.sleep(15)
        for b in range(0, len(todo), BATCH[m]):
            chunk = todo[b:b + BATCH[m]]
            items = [{"messages": replay[cell_id(c, "rev_full")]["messages"], "strip_llama_date": m.startswith("meta-llama")}
                     for c in chunk]
            seed = SEED + MODELS.index(m) * 100_000 + b
            jid = D.post(f"{base}/generate_batch", {"items": items, "max_tokens": chunk[0].max_output_tokens,
                                                    "temperature": chunk[0].temperature, "top_p": chunk[0].top_p,
                                                    "seed": seed}, auth, timeout=60).get("job")
            while True:
                time.sleep(10)
                j = get(f"{base}/job/{jid}", auth)
                if j.get("status") in ("done", "error"):
                    break
            if j["status"] != "done":
                raise SystemExit(f"batch {b} of {m} failed: {j.get('error')}")
            with out.open("a") as f:
                for c, res in zip(chunk, j["results"]):
                    rec = asdict(c)
                    lp = rv.liar_prompts(c, inst)
                    rec.update(cell_id=cell_id(c, NAMESPACE), run_namespace=NAMESPACE, mode="pod_identity",
                               status="in_progress", stage_done="liar", cost_usd=0.0, errors=[],
                               lie=res["text"], user_prompt=lp["user_prompt"], liar_system_prompt=lp["system_prompt"],
                               lie_words=len(res["text"].split()), liar_finish_reason=res["finish"],
                               liar_completion_tokens=len(res["ids"]), liar_prompt_tokens=res["prompt_count"],
                               liar_served_provider="pod", pod_seed=seed, api_cell_id=cell_id(c, "rev_full"),
                               liar_delivered_messages=replay[cell_id(c, "rev_full")]["messages"],
                               pod_render={"strip_llama_date": m.startswith("meta-llama")})
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"{m}: {b + len(chunk)}/{len(todo)}", flush=True)


def grade():
    from src.edsl_adapter import PerfectLieAdapter
    from src.perfect_lie.transport import TransportRetryAdapter
    from src.perfect_lie import reversed as rv, reversed_run as R
    from src.perfect_lie.personas import load_instrument
    models = R.run_models()
    models = dict(models, graders=[g for g in models["graders"] if g["role"] == "primary"])
    Run = rv.make_run_class()
    run = Run(namespace=NAMESPACE, run_dir=POD_RUN, cells=cells(), instrument=load_instrument(), models=models,
              adapter=TransportRetryAdapter(PerfectLieAdapter(service_name="open_router")), spend_cap_usd=CAP_USD,
              concurrency=8, models_path=R.DATA_DIR / "models.json", stages=("liar", "graders"),
              trace_probe_locked=True, elicitation=False, retry_failed="transport")
    mf = asyncio.run(run.run())
    print(json.dumps({k: mf.get(k) for k in ("finished", "spent_usd", "counts", "cap_reached") if k in mf}, default=str))


def analyse():
    import numpy as np
    from scipy import stats
    from src.perfect_lie import reversed_analysis as A, reversed_run as R
    from src.perfect_lie.personas import load_instrument
    inst, cfg = load_instrument(), R.load_config()
    cats = set(json.loads((HERE / "behavioral_categories.json").read_text())["categories"])
    cbt = A.target_cues(inst, cfg["targets"], REGISTERED_GATE_EXCLUDED)
    api = A.lie_table([r for r in A.load_records(ROOT / "results/perfect_lie_reversed/full_run/main/records.jsonl")
                       if r["model_id"] in MODELS and r["category"] in cats], cbt)
    pod_recs = A.load_records(POD_RUN / "records.jsonl")
    pod = A.lie_table(pod_recs, cbt, adj={})
    out = {"k": K, "margin": MARGIN, "gate_excluded": REGISTERED_GATE_EXCLUDED,
           "pod_lies_graded": int(sum(1 for r in pod_recs if (r.get("grades") or {}).get("primary"))),
           "pod_confessions_excluded": int(sum(1 for r in pod_recs if r.get("status") == "complete" and A.screens(r, {})["confession"])),
           "models": {}}

    def cat_means(d):
        piv = d.pivot_table(index=["category", "persona"], columns="condition", values="s", aggfunc="mean")
        piv = piv.reindex(columns=["placebo", "full", "reversed"])
        piv["B"] = piv["full"] - piv["reversed"]
        return piv.groupby(level="category").mean()

    for m in MODELS:
        cp, ca = cat_means(pod[pod.model == m]), cat_means(api[api.model == m])
        res = {}
        for q in ("B", "placebo", "full", "reversed"):
            d = (cp[q] - ca[q]).dropna()
            n = len(d)
            mean, se = float(d.mean()), float(d.std(ddof=1) / np.sqrt(n))
            t = stats.t.isf(0.05, n - 1)
            lo, hi = mean - t * se, mean + t * se
            res[q] = {"pod": float(cp[q].mean()), "api": float(ca[q].mean()), "diff": mean, "ci90": [lo, hi],
                      "k": n, "equivalent": bool(-MARGIN < lo and hi < MARGIN)}
        out["models"][m] = {"tests": res, "pass": all(v["equivalent"] for v in res.values())}
    (HERE / "behavioral_result.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["draw", "generate", "grade", "analyse"])
    ap.add_argument("--pod"); ap.add_argument("--key-file")
    a = ap.parse_args()
    {"draw": draw, "grade": grade, "analyse": analyse}.get(a.step, lambda: generate(a.pod, a.key_file))()
