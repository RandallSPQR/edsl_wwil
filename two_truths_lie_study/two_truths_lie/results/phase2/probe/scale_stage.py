"""Phase 2 steering-scale report driver (before the pilot; descriptive). Runs from this container.

  python scale_stage.py pod-up --commit SHA --key-file PATH [--watchdog-hours H] [--cap-usd C] [--poll-hours H]
  python scale_stage.py run --pod ID --key-file PATH --model M     -> <slug>/scale.json, SCALE.md
  python scale_stage.py pod-down --pod ID

Same pod as Addendum 3 (network volume, image, installs), serving pod_server_phase2_scale.py; no model is loaded.
The layer is the selected layer from <slug>/probe_result.json. pod-up refuses a pod whose hourly price x watchdog
hours exceeds the cap.
"""
import argparse, json, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import probe_stage as PS
import diag_stage as DS

FILES = {**DS.FILES,
         "pod_server_phase2_scale.py": "two_truths_lie_study/two_truths_lie/results/phase2/probe/pod_server_phase2_scale.py",
         "phase2_scale.py": "two_truths_lie_study/two_truths_lie/src/perfect_lie/phase2_scale.py"}


def pod_up(commit, key_file, gpus, hours, cap, poll_hours=0.0):
    key = Path(key_file).read_text().strip()
    fetch = " && ".join(f"curl -fsSL {PS.REPO_RAW}/{commit}/{src} -o /root/p2/{dst}" for dst, src in FILES.items())
    cmd = (f"(sleep {int(hours * 3600)}; runpodctl remove pod $RUNPOD_POD_ID) >/dev/null 2>&1 & "
           f"mkdir -p /root/p2 && {fetch} && "
           "pip install -q transformers==4.53.2 accelerate "
           "'sae-ethos-pipeline @ git+https://github.com/RandallSPQR/SAE-Ethos-Calibration@v1.1.0' && "
           "cd /root/p2 && python pod_server_phase2_scale.py")
    body = {"name": "phase2-scale", "imageName": PS.IMAGE, "gpuTypeIds": list(gpus), "gpuTypePriority": "custom",
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
    sel = json.loads((out / "probe_result.json").read_text())["selected_layer"]
    base, auth = PS.base_auth(pod, key_file)
    jid = PS.curl(auth + ["-X", "POST", f"{base}/scale"], {"slug": PS.slug(model), "layers": [sel]}, timeout=60).get("job")
    if not jid:
        raise SystemExit("no job id")
    j = PS.wait_job(base, auth, jid, every=10)
    if j["status"] != "done":
        raise SystemExit(f"scale report failed: {j.get('error')}")
    subprocess.run(["curl", "-sS", "-m", "300", "-f", "-o", str(out / "scale.json")] + auth
                   + [f"{base}/file/{PS.slug(model)}/scale.json"], check=True)
    rep = json.loads((out / "scale.json").read_text())
    (out / "SCALE.md").write_text(summary(model, sel, rep) + "\n")
    print(summary(model, sel, rep))


def summary(model, sel, rep):
    r = rep["layers"][str(sel)]
    g = lambda x: f"{x:,.1f}" if abs(x) >= 10 else f"{x:.3f}"
    L = [f"# Steering scale at the selected layer: {model}, layer {sel}", "",
         f"||v|| (alpha = 1 step, section 6) = {g(r['v_norm'])}. Frozen training items, last prompt token.", "",
         "| persona | pairs | residual norm median [10%, 90%] | gap on unit v mean (median) [10%, 90%] | "
         "own shift norm | cos(own shift, v) | level full / reversed | ||v|| / median norm |",
         "|---|---|---|---|---|---|---|---|"]
    for t, p in r["personas"].items():
        n, gp = p["residual_norm"], p["gap"]
        L.append(f"| {t} | {p['n_pairs']} | {g(n['median'])} [{g(n['q10'])}, {g(n['q90'])}] | "
                 f"{g(gp['mean'])} ({g(gp['median'])}) [{g(gp['q10'])}, {g(gp['q90'])}] | {g(p['shift_norm'])} | "
                 f"{p['shift_cos_v']:.3f} | {g(p['level']['full'])} / {g(p['level']['reversed'])} | {p['v_over_norm']:.4f} |")
    m = r["max_min_ratio"]
    L += ["", f"Max / min across the five personas: median residual norm {m['residual_norm_median']:.2f}x, "
              f"mean gap {m['gap_mean']:.2f}x, own shift norm {m['shift_norm']:.2f}x."]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("pod-up"); a.add_argument("--commit", required=True); a.add_argument("--key-file", required=True)
    a.add_argument("--gpus", default=",".join(PS.GPUS)); a.add_argument("--watchdog-hours", type=float, default=1.0)
    a.add_argument("--cap-usd", type=float, default=2.72); a.add_argument("--poll-hours", type=float, default=0.0)
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
