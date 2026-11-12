"""Phase 2 stage-2 driver (Addendum 7). Runs from this container; the pod generates.

  python stage2_stage.py pod-up --commit SHA --key-file PATH --cap-usd C [--watchdog-hours H] [--poll-hours H]
  python stage2_stage.py mc-precheck --pod ID --key-file PATH --model M   (before stage 2; coherence only)
  python stage2_stage.py run --pod ID --key-file PATH --model M           (stage 2: generation, coherence, naturalness)
  python stage2_stage.py grade --model M                                  (primary direct route + Google subsample)
  python stage2_stage.py screens                                          (blind screen listing for adjudication)
  python stage2_stage.py permcheck                                        (blinded permutation check: shares only)
  python stage2_stage.py analyse --i-am-unblinding                        (the registered analysis; owner's go only)
  python stage2_stage.py pod-down --pod ID

mc-precheck: the method check's vectors (per target: v_fp,t and its placebo, Addendum 7) are built on the pod and
checked (|cos(placebo, v_fp,t)| <= 1e-6, norm match 1); the exact hook check is run for every method-check kind; then
on the pilot's 8 training categories x 5 targets under the placebo note: unsteered, mc_steered and mc_placebo at
alpha 1, one batch per target with a shared seed; the first 64 tokens scored; the pilot's coherence measures.
Nothing is graded.
"""
import argparse, gzip, json, os, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT))
import probe_stage as PS
import pilot_stage as PL
import pilot2_stage as P2
from src.perfect_lie import phase2_pilot as Q, phase2_gen as G

FILES = {**P2.FILES,
         "pod_server_phase2_stage2.py": "two_truths_lie_study/two_truths_lie/results/phase2/probe/pod_server_phase2_stage2.py"}
STAGE2 = HERE.parent / "stage2"
MC_PLACEBO_SEED = 20261038      # + 10 x model index + target index


def mc_seeds(model):
    mi = G.MODELS.index(model)
    return {t: MC_PLACEBO_SEED + 10 * mi + i for i, t in enumerate(G.TARGETS)}


def pod_up(commit, key_file, gpus, hours, cap, poll_hours=0.0):
    key = Path(key_file).read_text().strip()
    fetch = " && ".join(f"curl -fsSL {PS.REPO_RAW}/{commit}/{src} -o /root/p2/{dst}" for dst, src in FILES.items())
    cmd = (f"(sleep {int(hours * 3600)}; runpodctl remove pod $RUNPOD_POD_ID) >/dev/null 2>&1 & "
           f"mkdir -p /root/p2 && {fetch} && "
           "pip install -q transformers==4.53.2 accelerate "
           "'sae-ethos-pipeline @ git+https://github.com/RandallSPQR/SAE-Ethos-Calibration@v1.1.0' && "
           "cd /root/p2 && HF_HOME=/workspace/hf python pod_server_phase2_stage2.py")
    env = {"POD_KEY": key, **({"HF_TOKEN": os.environ["HF_TOKEN"]} if os.environ.get("HF_TOKEN") else {})}
    body = {"name": "phase2-stage2", "imageName": PS.IMAGE, "gpuTypeIds": list(gpus), "gpuTypePriority": "custom",
            "gpuCount": 1, "cloudType": "SECURE", "dataCenterIds": [PS.DC], "networkVolumeId": PS.VOLUME,
            "volumeMountPath": "/workspace", "containerDiskInGb": 40, "ports": ["8000/http"], "env": env,
            "dockerStartCmd": ["bash", "-c", cmd]}
    deadline = time.time() + poll_hours * 3600
    while True:
        r = PS.pod_api("POST", "/pods", body)
        print(json.dumps({k: r.get(k) for k in ("id", "costPerHr", "desiredStatus", "error") if k in r}), flush=True)
        if r.get("id"):
            if float(r.get("costPerHr") or 0) * hours > cap:
                print(json.dumps({"refused": f"{r['costPerHr']}/h x {hours} h exceeds the ${cap} cap",
                                  "delete": PS.pod_api("DELETE", f"/pods/{r['id']}")}), flush=True)
                raise SystemExit(1)
            return r
        if time.time() >= deadline:
            return r
        time.sleep(300)


def load(base, auth, model):
    PS.curl(auth + ["-X", "POST", f"{base}/load"], {"model": PS.POD_MODEL[model]}, timeout=90)
    while PS.curl(auth + [f"{base}/health"], timeout=30).get("loaded") != PS.POD_MODEL[model]:
        time.sleep(15)
    env = PS.curl(auth + [f"{base}/env"], timeout=30)
    if env.get("n_blocks") != PS.N_BLOCKS[model]:
        raise SystemExit(f"expected {PS.N_BLOCKS[model]} blocks, the pod reports {env.get('n_blocks')}")
    return env


def prepare(base, auth, model, slug, sel):
    p2 = PL.job(base, auth, "/placebo2_prepare", {"slug": slug, "layer": sel, "placebo_seed": P2.PLACEBO2_SEED[model]})
    if abs(p2["cos_v_placebo"]) > P2.COS_TOL or abs(p2["norm_match"] - 1) > P2.NORM_TOL:
        raise SystemExit(f"main placebo fails its construction check: {p2}")
    mc = PL.job(base, auth, "/mc_prepare", {"slug": slug, "layer": sel, "seeds": mc_seeds(model)})
    for t, i in mc["targets"].items():
        if abs(i["cos_placebo_vfp"]) > P2.COS_TOL or abs(i["norm_match"] - 1) > P2.NORM_TOL:
            raise SystemExit(f"method-check placebo for {t} fails its construction check: {i}")
    return p2, mc


def hook_checks(base, auth, slug, item, kinds, coefs):
    out = {}
    for k in kinds:
        c = PL.job(base, auth, "/hook_check", {"slug": slug, "item": PL.pod_item(item), "kind": k, "coef": coefs[k]})
        if not c["passes"]:
            raise SystemExit(f"hook check failed for {k}: {c}")
        out[k] = c
    return out


GEN_RETRIES = 2


def status_of(r):
    """A record's status. Rows written before Addendum 8 carry none; every one of them holds a generated lie."""
    return r.get("status") or ("complete" if "ids" in r else "generation_failed")


def cell_key(r):
    return (r["key"], r["item_id"])


def check_cardinality(recs, jobs, what="records"):
    """Addendum 8: every planned cell has exactly one record (complete or generation_failed); else stop."""
    planned = {(j["key"], it["item_id"]) for j in jobs for it in j["items"]}
    got = [cell_key(r) for r in recs]
    dup = len(got) - len(set(got))
    missing, extra = planned - set(got), set(got) - planned
    if dup or missing or extra:
        raise SystemExit(f"{what}: {len(got)} rows for {len(planned)} planned cells; {dup} duplicated, "
                         f"{len(missing)} missing (e.g. {sorted(missing)[:3]}), {len(extra)} unplanned")
    return {"cells": len(planned), "generation_failed": sum(status_of(r) == "generation_failed" for r in recs)}


def generate_jobs(base, auth, slug, jobs, recp, coef_of, extra=lambda j: {}):
    """One durable record per planned cell. A job counts as done only when all its cells are on file; partial rows
    (an interrupted write) are dropped and the job regenerated. A pod error or a result list of the wrong length is
    retried GEN_RETRIES times; then every cell of the job is recorded as generation_failed with the reason (the pod
    returns results by position, so a short list cannot be matched to its items)."""
    rows = [json.loads(l) for l in recp.open()] if recp.exists() else []
    want = {j["key"]: {it["item_id"] for it in j["items"]} for j in jobs}
    have = {}
    for r in rows:
        have.setdefault(r["key"], set()).add(r["item_id"])
    partial = {k for k, v in have.items() if k in want and v != want[k]}
    if partial:
        recp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows if r["key"] not in partial))
        print(f"{slug}: dropped partial rows of {len(partial)} job(s), regenerating", flush=True)
    done = {k for k, v in have.items() if k in want and v == want[k]}
    for j in jobs:
        if j["key"] in done:
            continue
        results, reason = None, None
        for _ in range(1 + GEN_RETRIES):
            try:
                r = PL.job(base, auth, "/generate_steered",
                           {"items": [PL.pod_item(it) for it in j["items"]], "max_tokens": Q.SAMPLING["max_tokens"],
                            "temperature": Q.SAMPLING["temperature"], "top_p": Q.SAMPLING["top_p"], "seed": j["seed"],
                            "slug": slug, "kind": j["kind"], "coef": coef_of(j)})
            except SystemExit as e:
                reason = f"pod job failed: {str(e)[:200]}"
                continue
            got = r.get("results") or []
            if len(got) == len(j["items"]):
                results = got
                break
            reason = f"pod returned {len(got)} of {len(j['items'])} results; positions cannot be matched"
        ident = lambda it: {"key": j["key"], "arm": j["arm"], "hyp": j["hyp"], "alpha": j["alpha"], "target": it["target"],
                            "category": it["category"], "condition": it["condition"], "item_id": it["item_id"],
                            "seed": j["seed"], **extra(it)}
        if results is None:
            lines = [{**ident(it), "status": "generation_failed", "failure": reason, "attempts": 1 + GEN_RETRIES}
                     for it in j["items"]]
        else:
            lines = [{**ident(it), "status": "complete", "text": x["text"], "ids": x["ids"], "finish": x["finish"],
                      "prompt_count": x["prompt_count"]} for it, x in zip(j["items"], results)]
        with recp.open("a") as f:
            f.write("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in lines))
            f.flush()
        print(f"{slug} {j['key']}: {'done' if results is not None else 'GENERATION FAILED: ' + reason}", flush=True)


def score_nll(base, auth, recp, by_id):
    recs = [json.loads(l) for l in recp.open()]
    todo = [k for k, r in enumerate(recs) if "nll" not in r and status_of(r) == "complete"]
    for s in range(0, len(todo), 40):
        ks = todo[s:s + 40]
        j = PL.job(base, auth, "/nll", {"items": [PL.pod_item(by_id[recs[k]["item_id"]]) for k in ks],
                                        "conts": [recs[k]["ids"][:Q.NLL_TOKENS] for k in ks]}, every=5)
        for k, n in zip(ks, j["nll"]):
            recs[k]["nll"] = n
        recp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs))
    return recs


def mc_precheck(pod, key_file, model):
    slug = PS.slug(model)
    out = PL.OUT / slug; out.mkdir(parents=True, exist_ok=True)
    recp = out / "mc_precheck_records.jsonl"
    base, auth = PS.base_auth(pod, key_file)
    sel = json.loads((HERE / slug / "probe_result.json").read_text())["selected_layer"]
    env = load(base, auth, model)
    p2, mc = prepare(base, auth, model, slug, sel)
    print(json.dumps({"method_check_vectors": mc["targets"]}), flush=True)
    vfp = {t: i["vfp_norm"] for t, i in mc["targets"].items()}
    items_all = [json.loads(l) for l in gzip.open(HERE / "probe_items.jsonl.gz", "rt")]
    cats = Q.pilot_categories(json.loads((HERE / "category_split.json").read_text())["training"])
    first = G.items_for(items_all, model, cats, "placebo")[0]
    kinds = [f"{a}:{t}" for t in G.TARGETS for a in ("mc_steered", "mc_placebo")]
    checks = hook_checks(base, auth, slug, first, kinds, {k: vfp[k.split(":")[1]] for k in kinds})
    mi, jobs = G.MODELS.index(model), []
    for ti, t in enumerate(G.TARGETS):
        its = G.items_for(items_all, model, cats, "placebo", [t])
        seed = G._seed(mi, 4, ti * 100)
        for arm, kind in (("none", "none"), ("mc_steered", f"mc_steered:{t}"), ("mc_placebo", f"mc_placebo:{t}")):
            jobs.append({"arm": arm, "hyp": None, "kind": kind, "alpha": 0.0 if arm == "none" else G.MC_ALPHA, "sign": 1.0,
                         "target": t, "items": its, "seed": seed, "key": f"{arm}|{t}"})
    (out / "mc_precheck_setup.json").write_text(json.dumps({"model": model, "layer": sel, "env": env, "main_placebo": p2,
                                                            "method_check_vectors": mc, "hook_check": checks,
                                                            "categories": cats}, indent=1) + "\n")
    generate_jobs(base, auth, slug, jobs, recp, lambda j: 0.0 if j["kind"] == "none" else G.MC_ALPHA * vfp[j["target"]])
    check_cardinality([json.loads(l) for l in recp.open()], jobs, f"{slug} method-check pre-check")
    by_id = {it["item_id"]: it for j in jobs for it in j["items"]}
    recs = score_nll(base, auth, recp, by_id)
    mc_analyse(model, recs)


def mc_analyse(model, recs=None):
    slug = PS.slug(model)
    out = PL.OUT / slug
    recs = recs or [json.loads(l) for l in (out / "mc_precheck_records.jsonl").open()]
    if len(recs) != 3 * Q.N_PILOT * 5 or any("nll" not in r for r in recs):
        raise SystemExit(f"{model}: {len(recs)} records of {3 * Q.N_PILOT * 5}, or NLL missing")
    ref = {(r["category"], r["target"]): r for r in recs if r["arm"] == "none"}
    rep = {"model": model, "alpha": G.MC_ALPHA,
           "unsteered": Q.cell_metrics([r for r in recs if r["arm"] == "none"], ref),
           **{a: Q.cell_metrics([r for r in recs if r["arm"] == a], ref) for a in ("mc_steered", "mc_placebo")}}
    rep["coherent"] = rep["mc_steered"]["passes"] and rep["mc_placebo"]["passes"]
    (out / "mc_precheck.json").write_text(json.dumps(rep, indent=1) + "\n")
    setup = json.loads((out / "mc_precheck_setup.json").read_text())
    f = lambda x, k=3: "-" if x is None or x != x else f"{x:.{k}f}"
    L = [f"# Method-check coherence pre-check (alpha 1, placebo note, pilot categories): {model}", "",
         f"**Coherent (steered and placebo both pass): {'yes' if rep['coherent'] else 'no'}**", "",
         "| vector | viable (>= 0.95) | median ppl ratio (<= 2.0) | mean rep4 (<= 0.25) | median words | passes |",
         "|---|---|---|---|---|---|"]
    for a in ("unsteered", "mc_steered", "mc_placebo"):
        c = rep[a]
        L.append(f"| {a} | {f(c['viable_share'], 2)} | {f(c['ppl_ratio_median'], 2)} | {f(c['rep4_mean'])} | "
                 f"{f(c['words_median'], 0)} | {'yes' if c['passes'] else 'no'} |")
    L += ["", "Method-check vectors at the selected layer (per target):", "",
          "| target | ||v_fp,t|| / ||v|| | cos(v_fp,t, v) | cos(placebo_fp,t, v_fp,t) | before projection | norm match | cos with main placebo |",
          "|---|---|---|---|---|---|---|"]
    for t, i in setup["method_check_vectors"]["targets"].items():
        L.append(f"| {t} | {f(i['vfp_over_v'])} | {f(i['cos_vfp_v'])} | {i['cos_placebo_vfp']:.1e} | "
                 f"{f(i['cos_placebo_vfp_before_projection'])} | {i['norm_match']:.12f} | {f(i['cos_with_main_placebo'])} |")
    (out / "MC_PRECHECK.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


# ------------------------------------------------------------------ stage 2 (owner's go only)

def stage2_items():
    return [json.loads(l) for l in gzip.open(HERE / "stage2_items.jsonl.gz", "rt")]


def alphas():
    return json.loads((HERE.parent / "pilot" / "confirmatory_alphas.json").read_text())["confirmatory_alpha"]


def run(pod, key_file, model):
    slug = PS.slug(model)
    out = STAGE2 / slug; out.mkdir(parents=True, exist_ok=True)
    recp = out / "records.jsonl"
    base, auth = PS.base_auth(pod, key_file)
    sel = json.loads((HERE / slug / "probe_result.json").read_text())["selected_layer"]
    env = load(base, auth, model)
    p2, mc = prepare(base, auth, model, slug, sel)
    vfp = {t: i["vfp_norm"] for t, i in mc["targets"].items()}
    ev = json.loads((HERE / "category_split.json").read_text())["evaluation"]
    items = stage2_items()
    a = alphas()[slug]
    jobs = G.plan(items, model, a, ev, Q.BATCH[model])
    kinds = ["steered", "placebo"] + [f"{x}:{t}" for t in G.TARGETS for x in ("mc_steered", "mc_placebo")]
    coefs = {"steered": p2["v_norm"], "placebo": p2["v_norm"], **{k: vfp[k.split(":")[1]] for k in kinds[2:]}}
    checks = hook_checks(base, auth, slug, G.items_for(items, model, ev, "reversed")[0], kinds, coefs)
    (out / "setup.json").write_text(json.dumps({"model": model, "layer": sel, "env": env, "alphas": a, "main_placebo": p2,
                                                "method_check_vectors": mc, "hook_check": checks,
                                                "mc_categories": G.mc_categories(ev)}, indent=1) + "\n")
    generate_jobs(base, auth, slug, jobs, recp, lambda j: G.coef(j, p2["v_norm"], vfp),
                  extra=lambda it: {"user_prompt": it["user_prompt"], "model": model})
    card = check_cardinality([json.loads(l) for l in recp.open()], jobs, f"{slug} stage-2 records")
    print(json.dumps({"cardinality": card}), flush=True)
    by_id = {it["item_id"]: it for it in items}
    recs = score_nll(base, auth, recp, by_id)
    full, rev = (G.items_for(items, model, ev, c) for c in ("full", "reversed"))
    first = {(r["category"], r["target"], r["arm"]): r["ids"][:1] for r in recs
             if r["arm"] in ("ref_full", "ref_reversed") and status_of(r) == "complete"}
    nat = PL.job(base, auth, "/natural", {"slug": slug, "layer": sel, "full": [PL.pod_item(i) for i in full],
                                          "reversed": [PL.pod_item(i) for i in rev],
                                          "first_full": [first.get((i["category"], i["target"], "ref_full"), []) for i in full],
                                          "first_reversed": [first.get((i["category"], i["target"], "ref_reversed"), []) for i in rev]})
    (out / "natural.json").write_text(json.dumps(nat, indent=1) + "\n")
    coh = G.coherence(recs, a)
    (out / "coherence.json").write_text(json.dumps(coh, indent=1) + "\n")
    print(json.dumps({h: {"testable": coh[h]["testable"], "reason": coh[h]["reason"]} for h in ("H1", "H2")}), flush=True)


# ------------------------------------------------------------------ grading, screens, permutation check, analysis

GRADED = "graded.jsonl"
SCREENS = STAGE2 / "screen_matches.json"              # blind: no arm, hypothesis or alpha
SCREEN_KEY = STAGE2 / "screen_matches_key.json"       # id -> cell, read only to apply the adjudication
ADJUDICATION = STAGE2 / "screen_adjudication.json"    # the owner's: id -> "confession" | "not a confession"


def cell_id(r):
    return f"{r['model']}|{r['key']}|{r['item_id']}"


def grade(model):
    from src.perfect_lie import phase2_grading as PG
    from src.perfect_lie.personas import load_instrument
    out = STAGE2 / PS.slug(model)
    recs = [json.loads(l) for l in (out / "records.jsonl").open()]
    check_cardinality(recs, planned_jobs(model), f"{PS.slug(model)} stage-2 records")
    gp = out / GRADED
    done = {cell_id(r) for r in map(json.loads, gp.open())} if gp.exists() else set()
    sub = json.loads((HERE.parent / "grader_robustness" / "subsample.json").read_text())["cells"]
    todo = [{**r, "status": status_of(r), "lie": r.get("text")} for r in recs if cell_id(r) not in done]
    state = {"strict": True}
    with gp.open("a") as f:
        for r in (r for r in todo if r["status"] != "complete"):     # failed cells pass through, ungraded
            f.write(json.dumps(r, ensure_ascii=False) + "\n"); f.flush()
        PG.grade_records([r for r in todo if r["status"] == "complete"], load_instrument().cues, sub,
                         on_graded=lambda r: (f.write(json.dumps(r, ensure_ascii=False) + "\n"), f.flush()), state=state)
    allg = [json.loads(l) for l in gp.open()]
    summ = PG.summary(allg, state)
    (out / "grading_summary.json").write_text(json.dumps(summ, indent=1) + "\n")
    print(json.dumps(summ))


def planned_jobs(model):
    ev = json.loads((HERE / "category_split.json").read_text())["evaluation"]
    return G.plan(stage2_items(), model, alphas()[PS.slug(model)], ev, Q.BATCH[model])


def graded_all(check=True):
    """Every graded row of both models; with `check`, each model's file must hold exactly its planned cells."""
    out = []
    for m in G.MODELS:
        p = STAGE2 / PS.slug(m) / GRADED
        rows = [json.loads(l) for l in p.open()] if p.exists() else []
        if check:
            check_cardinality(rows, planned_jobs(m), f"{PS.slug(m)} graded rows")
        out += rows
    return out


def screens():
    """Section 10: every lie matching the frozen confession or refusal screen, listed blind (shuffled, seeded)."""
    import hashlib, random
    from src.perfect_lie import scoring
    rows, key = [], {}
    for r in graded_all():
        if status_of(r) != "complete":
            continue
        c, ref = scoring.confession(r["text"]), scoring.REFUSAL_PATTERNS.search(r["text"])
        if c or ref:
            i = hashlib.sha256(cell_id(r).encode()).hexdigest()[:12]
            rows.append({"id": i, "confession_match": c, "refusal_match": ref.group(0) if ref else None, "lie": r["text"]})
            key[i] = cell_id(r)
    random.Random(20261039).shuffle(rows)
    SCREENS.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
    SCREEN_KEY.write_text(json.dumps(key, indent=1) + "\n")
    print(f"{len(rows)} screen matches listed blind in {SCREENS.name}; adjudication goes in {ADJUDICATION.name}")


def analysis_records():
    import hashlib
    adj = json.loads(ADJUDICATION.read_text()) if ADJUDICATION.exists() else None
    if adj is None and SCREENS.exists() and json.loads(SCREENS.read_text()):
        raise SystemExit("screen matches are not adjudicated yet")
    out = []
    for r in graded_all():
        i = hashlib.sha256(cell_id(r).encode()).hexdigest()[:12]
        st = status_of(r)
        out.append({"model": r["model"], "arm": r["arm"], "hyp": r["hyp"], "category": r["category"], "target": r["target"],
                    "status": st, "grade": r.get("grade") if st == "complete" else None,
                    "grading_failed": bool(r.get("grading_failed")) if st == "complete" else False,
                    "google": r.get("google") if st == "complete" else None, "confession": (adj or {}).get(i) == "confession",
                    "nonviable": ([x for x in Q.viability(r["text"], r["finish"]) if x.split("(")[0] in Q.NONVIABLE]
                                  if st == "complete" else [])})
    return out


def context():
    from src.perfect_lie import reversed_analysis as RA, phase2_stage2 as A
    from src.perfect_lie.personas import load_instrument
    inst = load_instrument()
    ev = json.loads((HERE / "category_split.json").read_text())["evaluation"]
    cues = RA.target_cues(inst, list(G.TARGETS), A.S_EXCLUDED)
    testable = {}
    for m in G.MODELS:
        coh = json.loads((STAGE2 / PS.slug(m) / "coherence.json").read_text())
        for h in ("H1", "H2"):
            testable[(m, h)] = bool(coh[h]["testable"])
    return inst, ev, cues, testable


def permcheck():
    """Section 10, before unblinding: decision shares under within-cell label swaps; nothing else is printed."""
    from src.perfect_lie import phase2_stage2 as A
    inst, ev, cues, testable = context()
    recs = analysis_records()
    S = A.scores(recs, cues)
    mc = G.mc_categories(ev)
    method = {m: A.method_check(S, m, mc, list(G.TARGETS))["passed"] for m in G.MODELS}
    mats = {(m, h): A.pair_matrix(S, m, "steered", "placebo", h, h, ev, list(G.TARGETS)) for m in G.MODELS for h in ("H1", "H2")}
    rep = A.permutation_check(mats, testable, method)
    shares = {k: {x: round(v[x], 4) for x in ("efficacy", "equivalence") if x in v} for k, v in rep["shares"].items()}
    (STAGE2 / "permutation_check.json").write_text(json.dumps({"n": rep["n"], "seed": rep["seed"], "shares": shares}, indent=1) + "\n")
    print(json.dumps(shares, indent=1))


def analyse_all():
    from src.perfect_lie import phase2_stage2 as A
    inst, ev, cues, testable = context()
    recs = analysis_records()
    rep = A.analyse(recs, cues, ev, G.mc_categories(ev), testable, list(G.TARGETS))
    rep["naturalness"] = {m: json.loads((STAGE2 / PS.slug(m) / "natural.json").read_text()) for m in G.MODELS}
    sub = json.loads((HERE.parent / "grader_robustness" / "subsample.json").read_text())["cells"]
    rep["google_subsample"] = A.google_report(recs, cues, sub, ev, list(G.TARGETS), [c.id for c in inst.cues], rep["primary"])
    (STAGE2 / "stage2_result.json").write_text(json.dumps(rep, indent=1, default=float) + "\n")
    lines = ["# Phase 2 stage 2: primary analysis (section 7)", "",
             "| test | label | Delta | 95% CI | K | p | method check |", "|---|---|---|---|---|---|---|"]
    for k, d in rep["primary"].items():
        ci = d["ci95"]
        lines.append(f"| {k} | **{d['label']}** | {d['est']:+.3f} | {'[%+.3f, %+.3f]' % tuple(ci) if ci else '-'} | {d['K']} | "
                     f"{d['p_efficacy']:.4g} | {d['method_check_passed']} |")
    (STAGE2 / "STAGE2.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("pod-up"); a.add_argument("--commit", required=True); a.add_argument("--key-file", required=True)
    a.add_argument("--gpus", default=",".join(PS.GPUS)); a.add_argument("--watchdog-hours", type=float, default=0.8)
    a.add_argument("--cap-usd", type=float, required=True); a.add_argument("--poll-hours", type=float, default=0.0)
    for name in ("mc-precheck", "run"):
        b = sub.add_parser(name); b.add_argument("--pod", required=True); b.add_argument("--key-file", required=True)
        b.add_argument("--model", required=True, choices=list(G.MODELS))
    c = sub.add_parser("mc-analyse"); c.add_argument("--model", required=True, choices=list(G.MODELS))
    g = sub.add_parser("grade"); g.add_argument("--model", required=True, choices=list(G.MODELS))
    sub.add_parser("screens"); sub.add_parser("permcheck")
    u = sub.add_parser("analyse"); u.add_argument("--i-am-unblinding", action="store_true")
    d = sub.add_parser("pod-down"); d.add_argument("--pod", required=True)
    x = ap.parse_args()
    if x.cmd == "pod-up":
        pod_up(x.commit, x.key_file, x.gpus.split(","), x.watchdog_hours, x.cap_usd, x.poll_hours)
    elif x.cmd == "mc-precheck":
        mc_precheck(x.pod, x.key_file, x.model)
    elif x.cmd == "mc-analyse":
        mc_analyse(x.model)
    elif x.cmd == "run":
        run(x.pod, x.key_file, x.model)
    elif x.cmd == "grade":
        grade(x.model)
    elif x.cmd == "screens":
        screens()
    elif x.cmd == "permcheck":
        permcheck()
    elif x.cmd == "analyse":
        if not x.i_am_unblinding:
            raise SystemExit("refusing: the analysis unblinds; pass --i-am-unblinding (owner's go only)")
        analyse_all()
    else:
        print(json.dumps(PS.pod_api("DELETE", f"/pods/{x.pod}")))


if __name__ == "__main__":
    main()
