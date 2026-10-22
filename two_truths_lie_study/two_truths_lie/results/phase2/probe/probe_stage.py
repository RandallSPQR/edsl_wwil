"""Phase 2 probe stage driver (PREREG_PHASE2 section 4; Addendum 1). Runs from this container; the pod does the work.

  python probe_stage.py pod-up --commit SHA --key-file PATH [--gpu ID] [--watchdog-hours H]
  python probe_stage.py extract --pod ID --key-file PATH --model M
  python probe_stage.py analyse --pod ID --key-file PATH --model M      -> <slug>/probe_result.json, vectors.npz, PROBE.md
  python probe_stage.py pod-down --pod ID

The pod mounts the network volume in EUR-IS-1 (Gemma weights), fetches pod_server.py (frozen) and this directory's
pod_server_phase2.py and src/perfect_lie/phase2_probe.py at the given commit, installs transformers 4.53.2 and
sae-ethos-pipeline v1.1.0, and serves on port 8000. The pod also terminates itself after the watchdog hours.
RunPod API calls go through curl (Cloudflare rejects urllib); the proxy supplies the RunPod credential.
"""
import argparse, gzip, json, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

REPO_RAW = "https://raw.githubusercontent.com/RandallSPQR/edsl_wwil"
FILES = {"pod_server.py": "two_truths_lie_study/two_truths_lie/results/phase2/identity_check/pod_server.py",
         "pod_server_phase2.py": "two_truths_lie_study/two_truths_lie/results/phase2/probe/pod_server_phase2.py",
         "phase2_probe.py": "two_truths_lie_study/two_truths_lie/src/perfect_lie/phase2_probe.py"}
IMAGE = "runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04"
GPU, DC, VOLUME = "NVIDIA RTX PRO 6000 Blackwell Server Edition", "EUR-IS-1", "u0isne6ams"
POD_MODEL = {"meta-llama/llama-3.1-8b-instruct": "meta-llama/Llama-3.1-8B-Instruct",
             "google/gemma-3-27b-it": "google/gemma-3-27b-it"}
N_BLOCKS = {"google/gemma-3-27b-it": 62, "meta-llama/llama-3.1-8b-instruct": 32}
CANDIDATES = {"google/gemma-3-27b-it": list(range(21, 42)), "meta-llama/llama-3.1-8b-instruct": list(range(11, 22))}
SHARD = 100


def slug(model):
    return model.split("/")[1].lower()


def curl(args, body=None, timeout=60):
    cmd = ["curl", "-sS", "-m", str(timeout)] + args
    if body is not None:
        cmd += ["-H", "Content-Type: application/json", "--data-binary", "@-"]
    r = subprocess.run(cmd, input=json.dumps(body) if body is not None else None, capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"error": (r.stdout or r.stderr)[:300]}


def pod_api(method, path, body=None):
    return curl(["-X", method, f"https://rest.runpod.io/v1{path}"], body)


def pod_up(commit, key_file, gpu, hours):
    key = Path(key_file).read_text().strip()
    fetch = " && ".join(f"curl -fsSL {REPO_RAW}/{commit}/{src} -o /root/p2/{dst}" for dst, src in FILES.items())
    cmd = (f"(sleep {int(hours * 3600)}; runpodctl remove pod $RUNPOD_POD_ID) >/dev/null 2>&1 & "
           f"mkdir -p /root/p2 && {fetch} && "
           "pip install -q transformers==4.53.2 accelerate "
           "'sae-ethos-pipeline @ git+https://github.com/RandallSPQR/SAE-Ethos-Calibration@v1.1.0' && "
           "cd /root/p2 && HF_HOME=/workspace/hf python pod_server_phase2.py")
    body = {"name": "phase2-probe", "imageName": IMAGE, "gpuTypeIds": [gpu], "gpuCount": 1, "cloudType": "SECURE",
            "dataCenterIds": [DC], "networkVolumeId": VOLUME, "volumeMountPath": "/workspace",
            "containerDiskInGb": 40, "ports": ["8000/http"], "env": {"POD_KEY": key},
            "dockerStartCmd": ["bash", "-c", cmd]}
    r = pod_api("POST", "/pods", body)
    print(json.dumps({k: r.get(k) for k in ("id", "costPerHr", "desiredStatus", "error", "machine") if k in r}, default=str))
    return r


def base_auth(pod, key_file):
    return f"https://{pod}-8000.proxy.runpod.net", ["-H", f"Authorization: Bearer {Path(key_file).read_text().strip()}"]


def wait_job(base, auth, jid, every=10):
    while True:
        time.sleep(every)
        j = curl(auth + [f"{base}/job/{jid}"], timeout=30)
        if j.get("status") in ("done", "error"):
            return j


def items_for(model):
    return [json.loads(l) for l in gzip.open(HERE / "probe_items.jsonl.gz", "rt") if json.loads(l)["model_id"] == model]


def extract(pod, key_file, model):
    base, auth = base_auth(pod, key_file)
    r = curl(auth + ["-X", "POST", f"{base}/load"], {"model": POD_MODEL[model]}, timeout=90)
    while curl(auth + [f"{base}/health"], timeout=30).get("loaded") != POD_MODEL[model]:
        time.sleep(15)
    env = curl(auth + [f"{base}/env"], timeout=30)
    print(json.dumps(env), flush=True)
    if env.get("n_blocks") != N_BLOCKS[model]:
        raise SystemExit(f"expected {N_BLOCKS[model]} decoder blocks, the pod reports {env.get('n_blocks')}")
    items = items_for(model)
    log = []
    for k in range(0, len(items), SHARD):
        chunk = items[k:k + SHARD]
        jid = curl(auth + ["-X", "POST", f"{base}/extract_batch"],
                   {"items": chunk, "slug": slug(model), "shard": k // SHARD}, timeout=60).get("job")
        if not jid:
            raise SystemExit(f"shard {k // SHARD}: no job id")
        j = wait_job(base, auth, jid)
        if j["status"] != "done":
            raise SystemExit(f"shard {k // SHARD} failed: {j.get('error')}")
        log.append({"shard": k // SHARD, **{x: j.get(x) for x in ("n", "shape", "kept", "prompt_count", "span_len")}})
        print(f"{model}: {k + len(chunk)}/{len(items)} {log[-1]}", flush=True)
    out = HERE / slug(model); out.mkdir(exist_ok=True)
    (out / "extract_log.json").write_text(json.dumps({"env": env, "shards": log}, indent=1) + "\n")


def analyse(pod, key_file, model, n_boot, seed):
    from src.perfect_lie import phase2_probe as P
    base, auth = base_auth(pod, key_file)
    jid = curl(auth + ["-X", "POST", f"{base}/analyse"],
               {"slug": slug(model), "candidates": CANDIDATES[model], "n_boot": n_boot, "seed": seed}, timeout=60).get("job")
    j = wait_job(base, auth, jid, every=20)
    if j["status"] != "done":
        raise SystemExit(f"analysis failed: {j.get('error')}")
    out = HERE / slug(model); out.mkdir(exist_ok=True)
    for name in ("probe_result.json", "vectors.npz"):
        subprocess.run(["curl", "-sS", "-m", "300", "-f", "-o", str(out / name)] + auth + [f"{base}/file/{slug(model)}/{name}"],
                       check=True)
    rep = json.loads((out / "probe_result.json").read_text())
    (out / "PROBE.md").write_text(summary(model, rep) + "\n")
    print(summary(model, rep))


def summary(model, rep):
    f = lambda x: "-" if x is None or x != x else f"{x:.3f}"
    lines = [f"# Probe stage: {model}", "", f"**Gate: {rep['gate']}**; selected layer: {rep['selected_layer']}", "",
             "Pass = AUROC >= 0.70 and 95% cluster-bootstrap lower bound > 0.50 (clusters = categories, "
             f"{rep['n_boot']} resamples, seed {rep['seed']}) for held-out personas and each held-out wording.", "",
             "| layer | held-out personas | set A | set B | set C | mean wording | passes | control AUROC [90%] | inside [0.40, 0.60] | cos(v, c) |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for L in rep["candidates"]:
        r = rep["per_layer"][str(L)]
        hp, hw, c = r["held_out_personas"], r["held_out_wordings"], r["control"]
        cell = lambda t: f"{f(t['auroc'])} [{f(t['ci95'][0])}, {f(t['ci95'][1])}]"
        lines.append(f"| {L} | {cell(hp)} | {cell(hw['A'])} | {cell(hw['B'])} | {cell(hw['C'])} | {f(r['mean_wording_auroc'])} | "
                     f"{'yes' if r['passes'] else 'no'} | {f(c['auroc'])} [{f(c['ci90'][0])}, {f(c['ci90'][1])}] | "
                     f"{'yes' if c['inside_band'] else 'no'} | {f(c['cos_v_c'])} |")
    lines += ["", "Logistic probe (reported, never used for steering):", "",
              "| layer | C | cos(w, v) | held-out personas | set A | set B | set C |", "|---|---|---|---|---|---|---|"]
    for L in rep["candidates"]:
        g = rep["per_layer"][str(L)].get("logistic")
        if g:
            lines.append(f"| {L} | {g['C']} | {f(g['cos_with_v'])} | {f(g['held_out_personas']['auroc'])} | "
                         + " | ".join(f(g['held_out_wordings'][s]['auroc']) for s in ('A', 'B', 'C')) + " |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("pod-up"); a.add_argument("--commit", required=True); a.add_argument("--key-file", required=True)
    a.add_argument("--gpu", default=GPU); a.add_argument("--watchdog-hours", type=float, default=2.5)
    for name in ("extract", "analyse"):
        b = sub.add_parser(name); b.add_argument("--pod", required=True); b.add_argument("--key-file", required=True)
        b.add_argument("--model", required=True, choices=sorted(POD_MODEL))
        if name == "analyse":
            from src.perfect_lie.phase2_probe import N_BOOT, BOOT_SEED
            b.add_argument("--n-boot", type=int, default=N_BOOT); b.add_argument("--seed", type=int, default=BOOT_SEED)
    d = sub.add_parser("pod-down"); d.add_argument("--pod", required=True)
    x = ap.parse_args()
    if x.cmd == "pod-up":
        pod_up(x.commit, x.key_file, x.gpu, x.watchdog_hours)
    elif x.cmd == "extract":
        extract(x.pod, x.key_file, x.model)
    elif x.cmd == "analyse":
        analyse(x.pod, x.key_file, x.model, x.n_boot, x.seed)
    else:
        print(json.dumps(pod_api("DELETE", f"/pods/{x.pod}")))


if __name__ == "__main__":
    main()
