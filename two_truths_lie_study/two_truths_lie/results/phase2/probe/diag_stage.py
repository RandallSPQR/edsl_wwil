"""Phase 2 Addendum 3 driver: diagnostics on the stored probe-stage activations. Runs from this container.

  python diag_stage.py pod-up --commit SHA --key-file PATH [--watchdog-hours H] [--cap-usd C] [--poll-hours H]
  python diag_stage.py run --pod ID --key-file PATH --model M     -> <slug>/diagnostics.json, DIAGNOSTICS.md
  python diag_stage.py pod-down --pod ID

The pod mounts the same network volume (the activations are in /workspace/phase2/probe/<slug>/), fetches the probe
stage's files plus pod_server_phase2_diag.py and src/perfect_lie/phase2_diagnostics.py at the given commit, and
serves on port 8000. No model is loaded and no HF token is passed. The permutation layers are the selected layer and
its two neighbours, read from <slug>/probe_result.json. pod-up refuses a pod whose hourly price x watchdog hours
exceeds the cap (Addendum 3: $3), and the pod terminates itself after the watchdog hours.
"""
import argparse, json, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import probe_stage as PS

FILES = {**PS.FILES,
         "pod_server_phase2_diag.py": "two_truths_lie_study/two_truths_lie/results/phase2/probe/pod_server_phase2_diag.py",
         "phase2_diagnostics.py": "two_truths_lie_study/two_truths_lie/src/perfect_lie/phase2_diagnostics.py"}
CAP_USD = 3.0


def pod_up(commit, key_file, gpus, hours, cap, poll_hours=0.0):
    key = Path(key_file).read_text().strip()
    fetch = " && ".join(f"curl -fsSL {PS.REPO_RAW}/{commit}/{src} -o /root/p2/{dst}" for dst, src in FILES.items())
    cmd = (f"(sleep {int(hours * 3600)}; runpodctl remove pod $RUNPOD_POD_ID) >/dev/null 2>&1 & "
           f"mkdir -p /root/p2 && {fetch} && "
           "pip install -q transformers==4.53.2 accelerate "
           "'sae-ethos-pipeline @ git+https://github.com/RandallSPQR/SAE-Ethos-Calibration@v1.1.0' && "
           "cd /root/p2 && python pod_server_phase2_diag.py")
    body = {"name": "phase2-diag", "imageName": PS.IMAGE, "gpuTypeIds": list(gpus), "gpuTypePriority": "custom",
            "gpuCount": 1, "cloudType": "SECURE", "dataCenterIds": [PS.DC], "networkVolumeId": PS.VOLUME,
            "volumeMountPath": "/workspace", "containerDiskInGb": 40, "ports": ["8000/http"], "env": {"POD_KEY": key},
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


def run(pod, key_file, model):
    out = HERE / PS.slug(model)
    reg = json.loads((out / "probe_result.json").read_text())
    sel = reg["selected_layer"]
    if sel is None:
        raise SystemExit(f"{model} failed the gate; no diagnostics")
    perm_layers = [sel - 1, sel, sel + 1]
    base, auth = PS.base_auth(pod, key_file)
    jid = PS.curl(auth + ["-X", "POST", f"{base}/diagnose"],
                  {"slug": PS.slug(model), "perm_layers": perm_layers, "candidates": PS.CANDIDATES[model]}, timeout=60).get("job")
    if not jid:
        raise SystemExit("no job id")
    j = PS.wait_job(base, auth, jid, every=20)
    if j["status"] != "done":
        raise SystemExit(f"diagnostics failed: {j.get('error')}")
    import subprocess
    subprocess.run(["curl", "-sS", "-m", "300", "-f", "-o", str(out / "diagnostics.json")] + auth
                   + [f"{base}/file/{PS.slug(model)}/diagnostics.json"], check=True)
    rep = json.loads((out / "diagnostics.json").read_text())
    (out / "DIAGNOSTICS.md").write_text(summary(model, rep) + "\n")
    print(summary(model, rep))


def summary(model, rep):
    f = lambda x: "-" if x is None or x != x else f"{x:.3f}"
    names = {"held_out_personas": "held-out personas", "A": "set A", "B": "set B", "C": "set C"}
    sr = rep["stop_rule"]
    L = [f"# Addendum 3 diagnostics: {model}", "",
         f"**Stop rule (mean null AUROC inside [{sr['band'][0]:.2f}, {sr['band'][1]:.2f}] for every test below): "
         f"{'holds' if sr['pilot_may_run'] else 'BREACHED: ' + '; '.join(sr['outside'])}.** Observed statistics "
         f"{'match' if rep['observed_matches_registered'] else 'DO NOT match'} the registered ones"
         f"{'' if rep['observed_matches_registered'] else ': ' + '; '.join(rep['mismatches'])}.", "",
         f"## (a) Label-permutation null ({rep['n_perm']} permutations within persona, seed {rep['seed']})", "",
         "| layer | test | observed | null mean | null SD | null 2.5% | null 97.5% | null max | p |",
         "|---|---|---|---|---|---|---|---|---|"]
    for Ls in map(str, rep["perm_layers"]):
        for k, nm in names.items():
            r = rep["permutation"][Ls][k]; n = r["null"]
            L.append(f"| {Ls}{' (selected)' if int(Ls) == rep['selected_layer'] else ''} | {nm} | {f(r['observed'])} | "
                     f"{f(n['mean'])} | {f(n['sd'])} | {f(n['q025'])} | {f(n['q975'])} | {f(n['max'])} | {r['p']:.4f} |")
    targets = sorted(next(iter(rep["within_fold"].values()))["folds"])
    L += ["", f"## (b) Within-fold held-out-persona AUROC (descriptive; 95% cluster bootstrap over categories, "
              f"{rep['n_boot']} resamples, seed {rep['boot_seed']})", "",
          "| layer | registered pooled | " + " | ".join(targets) + " | mean | min |",
          "|---|---|" + "---|" * len(targets) + "---|---|"]
    for Ls, w in rep["within_fold"].items():
        cells = [f"{f(w['folds'][t]['auroc'])} [{f(w['folds'][t]['ci95'][0])}, {f(w['folds'][t]['ci95'][1])}]" for t in targets]
        L.append(f"| {Ls}{' (selected)' if int(Ls) == rep['selected_layer'] else ''} | {f(w['pooled_registered'])} | "
                 + " | ".join(cells) + f" | {f(w['mean_auroc'])} | {f(w['min_auroc'])} |")
    L += ["", "Mean projection on unit v per fold (full / reversed), which sets how the folds line up when pooled:", "",
          "| layer | " + " | ".join(targets) + " |", "|---|" + "---|" * len(targets)]
    for Ls, w in rep["within_fold"].items():
        L.append(f"| {Ls} | " + " | ".join(f"{w['folds'][t]['mean_unit_projection']['full']:.1f} / "
                                          f"{w['folds'][t]['mean_unit_projection']['reversed']:.1f}" for t in targets) + " |")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("pod-up"); a.add_argument("--commit", required=True); a.add_argument("--key-file", required=True)
    a.add_argument("--gpus", default=",".join(PS.GPUS)); a.add_argument("--watchdog-hours", type=float, default=1.0)
    a.add_argument("--cap-usd", type=float, default=CAP_USD); a.add_argument("--poll-hours", type=float, default=0.0)
    b = sub.add_parser("run"); b.add_argument("--pod", required=True); b.add_argument("--key-file", required=True)
    b.add_argument("--model", required=True, choices=sorted(PS.POD_MODEL))
    d = sub.add_parser("pod-down"); d.add_argument("--pod", required=True)
    x = ap.parse_args()
    if x.cmd == "pod-up":
        pod_up(x.commit, x.key_file, x.gpus.split(","), x.watchdog_hours, x.cap_usd, x.poll_hours)
    elif x.cmd == "run":
        run(x.pod, x.key_file, x.model)
    else:
        print(json.dumps(PS.pod_api("DELETE", f"/pods/{x.pod}")))


if __name__ == "__main__":
    main()
