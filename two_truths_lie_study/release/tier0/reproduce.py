"""Tier 0: rebuild every CPU-derivable result of The Perfect Lie from the released raw records, then the write-up
(Methods, Findings, figure captions, figures) and the claims check. No network, no GPU, no API key.

  python release/tier0/reproduce.py [--work DIR] [--perm-chunks N] [--keep]

Steps:
  1. Copy the released study tree into a fresh work tree (default two_truths_lie_study/build/tier0).
  2. Delete every file Tier 0 rebuilds (so no step can pass by reusing a released output) and decompress the raw
     records (*.jsonl.gz) into place.
  3. Run each registered analysis script, unchanged, inside the work tree (STEPS below).
  4. Compare every rebuilt file with the released one: byte-identical, numerically equal (|diff| <= 1e-9, same
     structure), or DIFFERENT.
  5. Rebuild the write-up there (derive_levels.py, build.py) and run its check_claims.py, which re-hashes every
     source the manifest cites: a pass means the rebuilt sources are byte-identical to the released ones and every
     number in the texts matches them.
Files that only a GPU or an API call can produce (activations, steering-vector setup, the identity check's pod lies)
are inputs here: carried over and verified against EXPECTED.json, and listed with the tier that would regenerate
them.

Writes tier0_report.json and TIER0_REPORT.md into the work tree's release/ copy and prints the summary. Exit code 0
only if every rebuilt file matches and the claims check passes.
"""
import argparse, gzip, hashlib, json, math, os, platform, shutil, subprocess, sys, time
from pathlib import Path

REL = Path(__file__).resolve().parents[1]          # .../two_truths_lie_study/release
STUDY = REL.parent                                  # .../two_truths_lie_study
NET_GUARD = REL / "tier0" / "netguard"              # sitecustomize that refuses non-loopback sockets
M = ["meta-llama/llama-3.1-8b-instruct", "google/gemma-3-27b-it"]
TTL = "two_truths_lie"
P1F = f"{TTL}/results/perfect_lie/final_analysis"
RVF = f"{TTL}/results/perfect_lie_reversed/final_analysis"
P2 = f"{TTL}/results/phase2"
PILOT = {m: f"{P2}/pilot/{m.split('/')[1]}" for m in M}
S2 = {m: f"{P2}/stage2/{m.split('/')[1]}" for m in M}

# (id, what, command run from the work tree's two_truths_lie/, files it writes (relative to the study root))
STEPS = [
    ("s1.final", "Study 1: registered final analysis (sections 4-8, Addenda 1-3)",
     ["results/perfect_lie/final_analysis/run_final.py"], [f"{P1F}/final_report.json", f"{P1F}/final_report.md"]),
    ("s1.gpt5", "Study 1: post hoc, gpt-5 subsample units scored by the primary grader",
     ["results/perfect_lie/final_analysis/gpt5_same_units.py"], [f"{P1F}/gpt5_same_units.json"]),
    ("rv.final", "Reversed note: registered final analysis (sections 4, 5, 7, 11a, 11)",
     ["results/perfect_lie_reversed/final_analysis/run_final.py", "--real", "--i-am-unblinding"],
     [f"{RVF}/final_report.json", f"{RVF}/final_report.md"]),
    ("rv.perm_chunk", "Reversed note: blinded permutation check, sample chunks recomputed and compared",
     ["../release/tier0/perm_chunk.py", "{perm_chunks}"], []),
    ("rv.perm", "Reversed note: permutation check assembled from its 20 chunks (section 4a)",
     ["results/perfect_lie_reversed/final_analysis/perm_check_chunked.py"], [f"{RVF}/perm_check.json"]),
    ("rv.posthoc_comp", "Reversed note: post hoc, comprehension on parseable answers",
     ["results/perfect_lie_reversed/final_analysis/posthoc_comprehension_parsed.py"],
     [f"{RVF}/posthoc_comprehension_parsed.json"]),
    ("rv.posthoc_google", "Reversed note: post hoc, Test B from the Google grader",
     ["results/perfect_lie_reversed/final_analysis/posthoc_google_testB.py"],
     [f"{RVF}/posthoc_google_testB.json", f"{RVF}/posthoc_google_testB.md"]),
    ("p2.identity", "Phase 2: identity check, behavioral equivalence (section 2)",
     ["results/phase2/identity_check/behavioral.py", "analyse"], [f"{P2}/identity_check/behavioral_result.json"]),
    ("p2.identity_novita", "Phase 2: identity check, Gemma template re-test",
     ["results/phase2/identity_check/behavioral.py", "analyse", "--variant", "novita"],
     [f"{P2}/identity_check/behavioral_result_novita.json"]),
    ("p2.route", "Phase 2: grading-route check summary from its stored labels (section 11)",
     ["../release/tier0/rebuild_route.py"], [f"{P2}/grading_route/regrade_direct.json"]),
    *[(f"p2.pilot.{m.split('/')[1]}", f"Phase 2: stage-1 pilot coherence, {m} (section 6, Addendum 4)",
       ["results/phase2/probe/pilot_stage.py", "analyse", "--model", m],
       [f"{PILOT[m]}/pilot_result.json", f"{PILOT[m]}/PILOT.md"]) for m in M],
    *[(f"p2.pilot2.{m.split('/')[1]}", f"Phase 2: pilot with the Addendum 5 placebo, {m}",
       ["results/phase2/probe/pilot2_stage.py", "analyse", "--model", m],
       [f"{PILOT[m]}/pilot2_result.json", f"{PILOT[m]}/PILOT2.md"]) for m in M],
    ("p2.alphas", "Phase 2: confirmatory alphas from the two pilots (alpha rule, section 6)",
     ["../release/tier0/rebuild_alphas.py"], [f"{P2}/pilot/confirmatory_alphas.json"]),
    *[(f"p2.mc.{m.split('/')[1]}", f"Phase 2: method-check coherence pre-check, {m} (Addendum 7)",
       ["results/phase2/probe/stage2_stage.py", "mc-analyse", "--model", m],
       [f"{PILOT[m]}/mc_precheck.json", f"{PILOT[m]}/MC_PRECHECK.md"]) for m in M],
    ("p2.coherence", "Phase 2: stage-2 coherence gate and grading summaries (sections 6, 7a)",
     ["../release/tier0/rebuild_stage2_extras.py"],
     [f"{S2[m]}/{f}" for m in M for f in ("coherence.json", "grading_summary.json")]),
    ("p2.permcheck", "Phase 2: blinded permutation check (section 10)",
     ["results/phase2/probe/stage2_stage.py", "permcheck"], [f"{P2}/stage2/permutation_check.json"]),
    ("p2.analyse", "Phase 2: registered stage-2 analysis (sections 7, 7a, 8, 9; Addendum 2)",
     ["results/phase2/probe/stage2_stage.py", "analyse", "--i-am-unblinding"],
     [f"{P2}/stage2/stage2_result.json", f"{P2}/stage2/STAGE2.md"]),
    ("w.levels", "Write-up: descriptive levels for figures 2 and 3",
     ["../writeup/derive_levels.py"], ["writeup/derived/levels.json"]),
    ("w.build", "Write-up: Methods, Findings, captions, figures, claims manifest",
     ["../writeup/build.py"],
     ["writeup/METHODS.md", "writeup/FINDINGS.md", "writeup/FIGURES.md", "writeup/PAPER.md", "writeup/CLAIMS_MANIFEST.csv",
      *[f"writeup/figures/{f}" for f in ("fig1_study1_lift.png", "fig2_reversed_levels.png",
                                         "fig3_steering_levels.png", "fig4_method_check.png")]]),
    ("w.check", "Write-up: claims check (every manifest value against the rebuilt sources)",
     ["../writeup/check_claims.py"], ["writeup/check_output.txt"]),
]

# Produced on a GPU pod or by an API call; Tier 0 carries them over and verifies them against EXPECTED.json.
INPUT_ONLY = {
    f"{P2}/probe/{s}/{f}": "Tier 3 (GPU): needs the probe-stage activations"
    for s in ("gemma-3-27b-it", "llama-3.1-8b-instruct") for f in ("probe_result.json", "vectors.npz", "diagnostics.json", "scale.json")
}
INPUT_ONLY.update({f"{PILOT[m]}/{f}": "Tier 3 (GPU): computed on the pod from the model's activations"
                   for m in M for f in ("setup.json", "setup_placebo2.json", "mc_precheck_setup.json")})
INPUT_ONLY.update({f"{S2[m]}/{f}": "Tier 3 (GPU): computed on the pod from the model's activations"
                   for m in M for f in ("setup.json", "natural.json")})
INPUT_ONLY.update({f"{P2}/identity_check/{d}/records.jsonl": "Tier 3 (GPU) generation, Tier 1 (API) grading"
                   for d in ("pod_run", "pod_run_novita")})
INPUT_ONLY.update({
    f"{TTL}/results/perfect_lie/interim_look/interim_blind.json": "frozen at the interim by registration (section 6); "
                                                                  "the final analysis recomputes the gate and checks it matches",
    f"{RVF}/perm_chunks": "decision counts per chunk; Tier 0 recomputes a sample (rv.perm_chunk), make reproduce-full all",
})

# Released files that record the environment that wrote them. Only these fields may differ, and only within the pins
# (the Python patch version: uv installs 3.11.15, the Docker image has 3.11.18, the release was written on 3.11.17).
ENV_STAMPS = {f"{RVF}/posthoc_google_testB.json": ["/environment/python"]}

# Released files written before a later commit added report fields. The rebuilt file must equal the released one once
# exactly these keys are removed; every released value is then reproduced, and the released bytes are kept.
LATER_FIELDS = {
    f"{P2}/identity_check/behavioral_result.json": {
        "keys": ["variant"], "commit": "950e8a7 added --variant after this result (2c8111c) was written"},
    **{f"{S2[m]}/coherence.json": {
        "keys": ["n_complete", "generation_failed"],
        "commit": "Addendum 8 (f4a70a7) added these counts after this file (8e66e71) was written; 0 failures"}
       for m in M},
}

TOL = 1e-9
THREAD_VARS = ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
               "NUMEXPR_NUM_THREADS")
SKIP_COPY = {".git", "__pycache__", "build", "web", "backend", ".pytest_cache", ".venv"}


def short(path):
    """A rebuilt file's name with enough of its directory to tell the models apart."""
    parts = Path(path).parts
    return "/".join(parts[-2:]) if parts[-2] in ("gemma-3-27b-it", "llama-3.1-8b-instruct") else parts[-1]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def same_numbers(a, b):
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(same_numbers(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(same_numbers(x, y) for x, y in zip(a, b))
    if isinstance(a, bool) or isinstance(b, bool) or a is None or b is None or isinstance(a, str):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if math.isnan(a) or math.isnan(b):
            return math.isnan(a) and math.isnan(b)
        return abs(a - b) <= TOL * max(1.0, abs(a), abs(b))
    return a == b


def drop_keys(o, keys):
    if isinstance(o, dict):
        return {k: drop_keys(v, keys) for k, v in o.items() if k not in keys}
    if isinstance(o, list):
        return [drop_keys(x, keys) for x in o]
    return o


def compare(rebuilt, released, rel_path=None):
    if not rebuilt.exists():
        return "MISSING"
    if rebuilt.read_bytes() == released.read_bytes():
        return "identical"
    if released.suffix == ".json":
        try:
            old, new = json.loads(released.read_text()), json.loads(rebuilt.read_text())
            if same_numbers(old, new):
                return "numerically equal"
            stamps = ENV_STAMPS.get(rel_path)
            if stamps:
                o2, n2 = json.loads(json.dumps(old)), json.loads(json.dumps(new))
                diffs = []
                for p in stamps:
                    *parent, leaf = p.strip("/").split("/")
                    a, b = o2, n2
                    for k in parent:
                        a, b = a[k], b[k]
                    if str(b[leaf]).startswith("3.11.") and a[leaf] != b[leaf]:
                        diffs.append(f"{p} {a[leaf]} -> {b[leaf]}")
                    b[leaf] = a[leaf]
                if same_numbers(o2, n2):
                    shutil.copy2(released, rebuilt)      # keep the released bytes, as for LATER_FIELDS
                    return "equal; only the recorded environment differs (" + "; ".join(diffs) + ")"
            add = LATER_FIELDS.get(rel_path)
            if add and same_numbers(old, drop_keys(new, set(add["keys"]))):
                shutil.copy2(released, rebuilt)          # downstream steps and the claims check use the released bytes
                return f"equal; current code adds {', '.join(add['keys'])} ({add['commit']})"
        except ValueError:
            pass
    return "DIFFERENT"


def copy_tree(src, dst):
    def ignore(d, names):
        out = {n for n in names if n in SKIP_COPY}
        out |= {n for n in names if n.endswith(".jsonl") and (n + ".gz") in names}   # decompressed afresh below
        return out
    shutil.copytree(src, dst, ignore=ignore, symlinks=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", type=Path, default=STUDY / "build" / "tier0")
    ap.add_argument("--perm-chunks", type=int, default=1, help="permutation chunks to recompute (0-20; 870 s each "
                                                                "on 4 cores)")
    ap.add_argument("--allow-unpinned", action="store_true", help="run even if package versions differ from the pins")
    ap.add_argument("--only", nargs="*", default=None, help="run only steps whose id starts with one of these prefixes "
                                                             "(debugging; a partial run never reports PASS)")
    a = ap.parse_args()
    t_all = time.time()
    pins = json.loads((REL / "tier0" / "EXPECTED.json").read_text())["environment"]
    env_now = {"python": platform.python_version()}
    import importlib.metadata as md
    for p in pins["packages"]:
        try:
            env_now[p] = md.version(p)
        except md.PackageNotFoundError:
            env_now[p] = None
    drift = {k: (pins["packages"].get(k, pins.get("python")), v) for k, v in env_now.items()
             if (k == "python" and not v.startswith(pins["python"])) or (k != "python" and v != pins["packages"][k])}
    print(f"environment: {env_now}")
    if drift and not a.allow_unpinned:
        raise SystemExit(f"environment differs from the pins ({drift}); install it from uv.lock or the Dockerfile "
                         "(see ENVIRONMENT.md), or pass --allow-unpinned to see what changes")

    # 1-2: work tree
    work = a.work.resolve()
    if work.exists():
        shutil.rmtree(work)
    root = work / STUDY.name
    t = time.time()
    copy_tree(STUDY, root)
    exp = json.loads((REL / "tier0" / "EXPECTED.json").read_text())["files"]
    bad_inputs = [f for f, h in exp.items() if (STUDY / f).is_file() and sha(STUDY / f) != h]
    if bad_inputs:
        raise SystemExit(f"released files differ from EXPECTED.json: {bad_inputs[:5]}")
    for sid, _, _, outs in STEPS:
        if a.only is None or any(sid.startswith(x) for x in a.only):
            for o in outs:
                (root / o).unlink(missing_ok=True)
    n_gz = 0
    for gz in root.rglob("*.jsonl.gz"):
        with gzip.open(gz, "rb") as f, open(gz.with_suffix(""), "wb") as g:
            shutil.copyfileobj(f, g)
        n_gz += 1
    setup_s = time.time() - t
    print(f"work tree {root} ready in {setup_s:.0f} s ({n_gz} record files decompressed)")

    # 3: steps
    # One BLAS/OpenMP thread: the registered fits were run single-threaded, and a multi-threaded BLAS changes the
    # summation order enough to flip the convergence flag of the reversed-note robustness model (ENVIRONMENT.md).
    env = {**os.environ, "PYTHONPATH": str(NET_GUARD) + os.pathsep + os.environ.get("PYTHONPATH", ""),
           "PYTHONHASHSEED": "0", "MPLBACKEND": "Agg", "TIER0_NO_NETWORK": "1", "PYTHONDONTWRITEBYTECODE": "1",
           **{v: "1" for v in THREAD_VARS}}
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
        env.pop(k, None)
    log = []
    for sid, what, cmd, outs in STEPS:
        if a.only is not None and not any(sid.startswith(x) for x in a.only):
            continue
        cmd = [x.replace("{perm_chunks}", str(a.perm_chunks)) for x in cmd]
        t = time.time()
        p = subprocess.run([sys.executable, *cmd], cwd=root / TTL, env=env, capture_output=True, text=True)
        dt = time.time() - t
        if sid == "w.check":                             # the checker prints its report; keep it beside the write-up
            (root / "writeup/check_output.txt").write_text(p.stdout)
        res = {f: compare(root / f, STUDY / f, f) for f in outs}
        ok = p.returncode == 0 and all(v not in ("DIFFERENT", "MISSING") for v in res.values())
        log.append({"step": sid, "what": what, "seconds": round(dt, 1), "exit": p.returncode, "outputs": res,
                    "ok": ok, "stderr_tail": p.stderr[-2000:] if p.returncode else "",
                    "stdout_head": p.stdout[:300] if sid == "w.check" else "",
                    "stdout_tail": p.stdout[-1500:] if sid in ("w.check", "rv.perm_chunk") else ""})
        print(f"[{'ok' if ok else 'FAIL'}] {sid:<26} {dt:7.1f} s  " + ", ".join(f"{short(k)}: {v}" for k, v in res.items()),
              flush=True)
        if p.returncode:
            print(p.stderr[-2000:], flush=True)

    inputs = {f: {"reason": r, "sha256_ok": (all(sha(x) == exp.get(str(x.relative_to(root)))
                                                for x in (root / f).rglob("*") if x.is_file())
                                            if (root / f).is_dir() else sha(root / f) == exp.get(f))}
              for f, r in INPUT_ONLY.items()}
    total = time.time() - t_all
    rebuilt = {f: v for s in log for f, v in s["outputs"].items()}
    summary = {
        "passed": a.only is None and all(s["ok"] for s in log) and all(i["sha256_ok"] for i in inputs.values()),
        "runtime_seconds": round(total, 1), "setup_seconds": round(setup_s, 1),
        "environment": env_now, "pinned": pins, "cpu_count": os.cpu_count(), "machine": platform.machine(),
        "platform": platform.platform(), "perm_chunks_recomputed": a.perm_chunks,
        "counts": {k: sum(1 for v in rebuilt.values() if v.split(";")[0] == k)
                   for k in ("identical", "numerically equal", "equal", "DIFFERENT", "MISSING")},
        "steps": log, "inputs_carried_over": inputs,
    }
    out = root / "release"
    (out / "tier0_report.json").write_text(json.dumps(summary, indent=1) + "\n")
    L = ["# Tier 0 report", "", f"**{'PASS' if summary['passed'] else 'FAIL'}** in {total / 60:.1f} min "
         f"({os.cpu_count()} CPUs, {platform.platform()}, Python {env_now['python']}).", "",
         "Rebuilt files: " + ", ".join(f"{v} {k}" for k, v in summary["counts"].items()) + ".", "",
         "| step | what | seconds | outputs |", "|---|---|---|---|"]
    for s in log:
        L.append(f"| {s['step']} | {s['what']} | {s['seconds']} | "
                 + ("; ".join(f"`{short(k)}` {v}" for k, v in s["outputs"].items()) or ("ok" if s["ok"] else "FAIL")) + " |")
    L += ["", "Inputs carried over (not CPU-derivable), verified by sha256:", ""]
    L += [f"- `{f}`: {'sha256 ok' if i['sha256_ok'] else 'SHA256 MISMATCH'} ({i['reason']})" for f, i in inputs.items()]
    chk = next((s for s in log if s["step"] == "w.check"), {"stdout_tail": "(claims check not run)"})
    L += ["", "Claims check output (head and tail; in full in the work tree's `writeup/check_output.txt`):", "", "```",
          chk.get("stdout_head", "").strip(), "...", chk["stdout_tail"].strip()[-700:], "```"]
    (out / "TIER0_REPORT.md").write_text("\n".join(L) + "\n")
    print(f"\n{'PASS' if summary['passed'] else 'FAIL'}: Tier 0 in {total:.0f} s; rebuilt {summary['counts']}; "
          f"report: {out / 'TIER0_REPORT.md'}")
    sys.exit(0 if summary["passed"] else 1)


if __name__ == "__main__":
    main()
