"""Sign test of the final-analysis runner (owner instruction, before Addendum 3). Synthetic data only.

Case A: full lies carry clearly MORE note-named cues than placebo lies. Case B: clearly FEWER.
Each case is written as a records file and run through the real runner (run_final.py) in a
subprocess; the test reads the runner's own final_report.json and final_report.md."""
import json, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
from src.perfect_lie.personas import load_instrument
inst = load_instrument()
MODELS = ["meta-llama/llama-3.1-8b-instruct", "google/gemma-3-27b-it", "openai/gpt-4o-mini", "google/gemini-2.5-flash-lite"]
FAM = {MODELS[0]: "meta", MODELS[1]: "google", MODELS[2]: "openai", MODELS[3]: "google"}
cue_ids = [c.id for c in inst.cues]

def synth(p_full_named, p_placebo_named, p_other=0.25, seed=11):
    rng = np.random.default_rng(seed); recs = []
    for m in MODELS:
        for row in inst.design:
            for t in row.targets:
                named = set(inst.personas[t].cues)
                for rep in range(1, 16):
                    for cond in ("none", "placebo", "full"):
                        p = np.array([(p_full_named if cond == "full" else p_placebo_named if cond == "placebo" else p_other)
                                      if c in named else p_other for c in cue_ids])
                        prim = dict(zip(cue_ids, map(bool, rng.random(len(cue_ids)) < p)))
                        goog = {c: (v if rng.random() > 0.05 else not v) for c, v in prim.items()}
                        g = {"primary": {"cues": prim}, "google": {"cues": goog}}
                        if rng.random() < 0.25:
                            g["secondary"] = {"cues": dict(prim)}
                        recs.append({"cell_id": f"synthetic|{m}|{row.prompt_id}|{t}|{cond}|{rep}", "model_id": m,
                                     "model_family": FAM[m], "prompt_id": row.prompt_id, "category": row.prompt_id,
                                     "target_id": t, "j1": row.j1, "j2": row.j2, "placebo_id": row.placebo,
                                     "condition": cond, "replicate": rep, "status": "complete",
                                     "lie": " ".join(["word"] * 350), "lie_word_range": [300, 400], "grades": g,
                                     "bhat_grades": {"primary": {"cues": dict(prim)}},
                                     "targets": {j: {"accept": bool(rng.random() < 0.5), "family": FAM[j]} for j in MODELS},
                                     "elicitation": {"flags": {"echo": False, "refusal": False, "breakdown": False}}})
    return recs

results = {}
for case, (pf, pp, want) in {"A_more_under_full": (0.75, 0.20, "positive"), "B_fewer_under_full": (0.20, 0.75, "negative")}.items():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td); (td / "out").mkdir()
        with open(td / "records.jsonl", "w") as fh:
            for r in synth(pf, pp): fh.write(json.dumps(r) + "\n")
        p = subprocess.run([sys.executable, str(HERE / "run_final.py"), str(td), str(td / "out")], capture_output=True, text=True,
                           cwd=str(ROOT), env={"PATH": "/usr/bin:/bin:/usr/local/bin"})
        if p.returncode != 0:
            print(p.stderr[-2000:]); raise SystemExit(1)
        rep = json.loads((td / "out" / "final_report.json").read_text())
        md = (td / "out" / "final_report.md").read_text()
    rows = {}
    for m in MODELS:
        r = rep["primary"]["models"][m]
        ok = (r["mean_lift"] > 0) == (want == "positive") and r["direction"] == want
        rows[m] = {"mean_lift": r["mean_lift"], "direction": r["direction"], "direction_label": r.get("direction_label"),
                   "decision": r["decision"], "sign_ok": ok}
    label = "more named cues under full" if want == "positive" else "fewer named cues under full (more under placebo)"
    results[case] = {"expected": want, "models": rows, "all_sign_ok": all(v["sign_ok"] for v in rows.values()),
                     "label_in_report_md": label in md}
    print(f"{case}: expected {want}")
    for m, v in rows.items():
        print(f"  {m:34s} lift {v['mean_lift']:+.3f}  decision {v['decision']:15s} direction '{v['direction_label']}'  ok {v['sign_ok']}")
    print(f"  label '{label}' appears in final_report.md: {label in md}")
(HERE / "sign_test.json").write_text(json.dumps(results, indent=1) + "\n")
