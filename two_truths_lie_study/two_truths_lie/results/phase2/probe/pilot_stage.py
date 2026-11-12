"""Phase 2 stage 1 driver: the dose-finding pilot (section 6; Addendum 4). Runs from this container; the pod generates.

  python pilot_stage.py pod-up --commit SHA --key-file PATH [--watchdog-hours H] [--cap-usd C] [--poll-hours H]
  python pilot_stage.py run --pod ID --key-file PATH --model M   -> ../pilot/<slug>/records.jsonl, pilot_result.json, PILOT.md
  python pilot_stage.py analyse --model M                        (re-run the analysis on the saved records)
  python pilot_stage.py pod-down --pod ID

`run` loads the model, prepares the steering direction and the placebo on the pod, checks the steering hook, generates
every condition in batches (resumable: a batch already in records.jsonl is skipped), scores the first 64 tokens of
every lie under the unsteered model, and applies the coherence gate and the alpha rule (src/perfect_lie/phase2_pilot.py)
here. No lie is graded and no cue is scored.
"""
import argparse, gzip, json, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT))
import probe_stage as PS
import scale_stage as SS
from src.perfect_lie import phase2_pilot as Q

FILES = {**SS.FILES,
         "pod_server_phase2_pilot.py": "two_truths_lie_study/two_truths_lie/results/phase2/probe/pod_server_phase2_pilot.py"}
OUT = HERE.parent / "pilot"
CAP_USD = 8.0
MODELS = ["google/gemma-3-27b-it", "meta-llama/llama-3.1-8b-instruct"]


def pod_up(commit, key_file, gpus, hours, cap, poll_hours=0.0):
    import os
    key = Path(key_file).read_text().strip()
    fetch = " && ".join(f"curl -fsSL {PS.REPO_RAW}/{commit}/{src} -o /root/p2/{dst}" for dst, src in FILES.items())
    cmd = (f"(sleep {int(hours * 3600)}; runpodctl remove pod $RUNPOD_POD_ID) >/dev/null 2>&1 & "
           f"mkdir -p /root/p2 && {fetch} && "
           "pip install -q transformers==4.53.2 accelerate "
           "'sae-ethos-pipeline @ git+https://github.com/RandallSPQR/SAE-Ethos-Calibration@v1.1.0' && "
           "cd /root/p2 && HF_HOME=/workspace/hf python pod_server_phase2_pilot.py")
    env = {"POD_KEY": key, **({"HF_TOKEN": os.environ["HF_TOKEN"]} if os.environ.get("HF_TOKEN") else {})}
    body = {"name": "phase2-pilot", "imageName": PS.IMAGE, "gpuTypeIds": list(gpus), "gpuTypePriority": "custom",
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


def job(base, auth, path, body, every=10, timeout=60):
    r = PS.curl(auth + ["-X", "POST", f"{base}{path}"], body, timeout=timeout)
    if not r.get("job"):
        raise SystemExit(f"{path}: no job id ({r})")
    j = PS.wait_job(base, auth, r["job"], every=every)
    if j["status"] != "done":
        raise SystemExit(f"{path} failed: {j.get('error')}")
    return j


def pod_item(it):
    return {"messages": it["messages"], "strip_llama_date": it.get("strip_llama_date", False),
            "strip_trailing_newline": it.get("strip_trailing_newline", False)}


def run(pod, key_file, model):
    slug = PS.slug(model)
    out = OUT / slug; out.mkdir(parents=True, exist_ok=True)
    recp = out / "records.jsonl"
    base, auth = PS.base_auth(pod, key_file)
    sel = json.loads((HERE / slug / "probe_result.json").read_text())["selected_layer"]
    # load
    PS.curl(auth + ["-X", "POST", f"{base}/load"], {"model": PS.POD_MODEL[model]}, timeout=90)
    while PS.curl(auth + [f"{base}/health"], timeout=30).get("loaded") != PS.POD_MODEL[model]:
        time.sleep(15)
    env = PS.curl(auth + [f"{base}/env"], timeout=30)
    if env.get("n_blocks") != PS.N_BLOCKS[model]:
        raise SystemExit(f"expected {PS.N_BLOCKS[model]} blocks, the pod reports {env.get('n_blocks')}")
    prep = job(base, auth, "/pilot_prepare", {"slug": slug, "layer": sel, "placebo_seed": Q.PLACEBO_SEED[model]})
    print(json.dumps({"layer": sel, **{k: prep[k] for k in ("v_norm", "cos_v_placebo", "placebo_norm", "n_train")}}), flush=True)
    items_all = [json.loads(l) for l in gzip.open(HERE / "probe_items.jsonl.gz", "rt")]
    cats = Q.pilot_categories(json.loads((HERE / "category_split.json").read_text())["training"])
    items = {h: Q.pilot_items(items_all, model, cats, h) for h in Q.HYPOTHESES}
    # exact (bitwise) mechanism checks on the pod at the alpha = 1 coefficient; the error against the intended vector
    # is recorded as the precision of bf16 steering, not tested
    checks = {k: job(base, auth, "/hook_check", {"slug": slug, "item": pod_item(items["H1"][0]), "kind": k,
                                                 "coef": Q.coef("H1", k, 1.0, prep["v_norm"])}) for k in Q.KINDS}
    print(json.dumps({"hook_check": checks}), flush=True)
    for k, c in checks.items():
        if not c["passes"]:
            raise SystemExit(f"hook check failed for {k}: {c}")
    (out / "setup.json").write_text(json.dumps({"model": model, "layer": sel, "categories": cats, "env": env,
                                                "prepare": prep, "hook_check": checks, "sampling": Q.SAMPLING,
                                                "batch": Q.BATCH[model]}, indent=1) + "\n")
    done = set()
    if recp.exists():
        done = {(r["hyp"], r["kind"], r["alpha"], r["batch"]) for r in map(json.loads, recp.open())}
    mi, B = MODELS.index(model), Q.BATCH[model]
    for c in Q.conditions():
        its = items[c["hyp"]]
        for b in range(0, len(its), B):
            if (c["hyp"], c["kind"], c["alpha"], b) in done:
                continue
            chunk = its[b:b + B]
            seed = Q.batch_seed(mi, c["hyp"], b)
            j = job(base, auth, "/generate_steered",
                    {"items": [pod_item(it) for it in chunk], "max_tokens": Q.SAMPLING["max_tokens"],
                     "temperature": Q.SAMPLING["temperature"], "top_p": Q.SAMPLING["top_p"], "seed": seed,
                     "slug": slug, "kind": c["kind"], "coef": Q.coef(c["hyp"], c["kind"], c["alpha"], prep["v_norm"])})
            with recp.open("a") as f:
                for it, res in zip(chunk, j["results"]):
                    f.write(json.dumps({**c, "batch": b, "seed": seed, "item_id": it["item_id"], "category": it["category"],
                                        "target": it["target"], "note": it["condition"], "text": res["text"],
                                        "ids": res["ids"], "finish": res["finish"], "prompt_count": res["prompt_count"]},
                                       ensure_ascii=False) + "\n")
            print(f"{model} {c['hyp']} {c['kind']} alpha {c['alpha']}: batch {b // B + 1}/{-(-len(its) // B)}", flush=True)
    # NLL of the first 64 tokens under the unsteered model
    recs = [json.loads(l) for l in recp.open()]
    by_id = {it["item_id"]: it for h in items for it in items[h]}
    todo = [k for k, r in enumerate(recs) if "nll" not in r]
    for s in range(0, len(todo), 40):
        ks = todo[s:s + 40]
        j = job(base, auth, "/nll", {"items": [pod_item(by_id[recs[k]["item_id"]]) for k in ks],
                                     "conts": [recs[k]["ids"][:Q.NLL_TOKENS] for k in ks]}, every=5)
        for k, n in zip(ks, j["nll"]):
            recs[k]["nll"] = n
        recp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs))
        print(f"{model}: nll {s + len(ks)}/{len(todo)}", flush=True)
    analyse(model)


def analyse(model):
    slug = PS.slug(model)
    out = OUT / slug
    recs = [json.loads(l) for l in (out / "records.jsonl").open()]
    want = len(Q.conditions()) * Q.N_PILOT * 5
    if len(recs) != want or any("nll" not in r for r in recs):
        raise SystemExit(f"{model}: {len(recs)} records of {want}, or NLL missing")
    rep = {"model": model, "n_lies": len(recs), "rules": {"viable_min": Q.VIABLE_MIN, "ppl_ratio_max": Q.PPL_RATIO_MAX,
                                                          "rep4_max": Q.REP4_MAX, "nll_tokens": Q.NLL_TOKENS},
           "hypotheses": Q.analyse(recs)}
    (out / "pilot_result.json").write_text(json.dumps(rep, indent=1) + "\n")
    (out / "PILOT.md").write_text(summary(model, rep) + "\n")
    print(summary(model, rep))


def summary(model, rep):
    f = lambda x, k=3: "-" if x is None or x != x else f"{x:.{k}f}"
    L = [f"# Dose-finding pilot (coherence only): {model}", ""]
    for h, r in rep["hypotheses"].items():
        u = r["unsteered"]
        L += [f"## {h} ({Q.HYPOTHESES[h]['note']} note, {'+' if Q.HYPOTHESES[h]['sign'] > 0 else '-'}alpha v): "
              f"**confirmatory alpha = {r['confirmatory_alpha'] if r['confirmatory_alpha'] is not None else 'none (untestable)'}**", "",
              f"Unsteered (alpha 0, n {u['n']}): viable {f(u['viable_share'], 2)}, rep4 {f(u['rep4_mean'])}, median words {f(u['words_median'], 0)}.", "",
              "| alpha | vector | viable (>= 0.95) | median ppl ratio (<= 2.0) | mean rep4 (<= 0.25) | median words | passes | coherent |",
              "|---|---|---|---|---|---|---|---|"]
        for a, g in r["grid"].items():
            for k in Q.KINDS:
                c = g[k]
                L.append(f"| {a} | {k} | {f(c['viable_share'], 2)} | {f(c['ppl_ratio_median'], 2)} | {f(c['rep4_mean'])} | "
                         f"{f(c['words_median'], 0)} | {'yes' if c['passes'] else 'no'} | {'yes' if g['coherent'] else 'no'} |")
        L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("pod-up"); a.add_argument("--commit", required=True); a.add_argument("--key-file", required=True)
    a.add_argument("--gpus", default=",".join(PS.GPUS)); a.add_argument("--watchdog-hours", type=float, default=3.0)
    a.add_argument("--cap-usd", type=float, default=CAP_USD); a.add_argument("--poll-hours", type=float, default=0.0)
    b = sub.add_parser("run"); b.add_argument("--pod", required=True); b.add_argument("--key-file", required=True)
    b.add_argument("--model", required=True, choices=MODELS)
    c = sub.add_parser("analyse"); c.add_argument("--model", required=True, choices=MODELS)
    d = sub.add_parser("pod-down"); d.add_argument("--pod", required=True)
    x = ap.parse_args()
    if x.cmd == "pod-up":
        pod_up(x.commit, x.key_file, x.gpus.split(","), x.watchdog_hours, x.cap_usd, x.poll_hours)
    elif x.cmd == "run":
        run(x.pod, x.key_file, x.model)
    elif x.cmd == "analyse":
        analyse(x.model)
    else:
        print(json.dumps(PS.pod_api("DELETE", f"/pods/{x.pod}")))


if __name__ == "__main__":
    main()
