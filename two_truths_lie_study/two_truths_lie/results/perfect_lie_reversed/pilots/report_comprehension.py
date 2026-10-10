"""Comprehension check report: parse rate, sample accuracy and per-line accuracy by model x
condition, with 95% Wilson intervals. Usage: python report_comprehension.py [RUN_DIR_NAME]"""
import json, sys
from collections import defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
from src.perfect_lie.runner import load_records
from src.perfect_lie.stage1 import wilson

name = sys.argv[1] if len(sys.argv) > 1 else "comprehension_pilot"
recs = [r for r in load_records(HERE / name) if r.get("status") == "complete"]
mf = json.loads((HERE / name / "manifest.json").read_text())
NAME = {"meta-llama/llama-3.1-8b-instruct": "Llama", "google/gemma-3-27b-it": "Gemma",
        "openai/gpt-4o-mini": "gpt-4o-mini", "google/gemini-2.5-flash-lite": "Gemini"}
g = defaultdict(list)
for r in recs:
    g[(r["model_id"], r["condition"])].append(r)
rows = {}
for (m, c), rs in sorted(g.items()):
    parsed = [r for r in rs if r.get("score")]
    k_ok = sum(r["score"]["correct"] for r in parsed)
    lines = [x for r in parsed for x in r["score"]["lines"]]
    rows[f"{m}|{c}"] = {"n": len(rs), "parsed": len(parsed), "parse_rate": len(parsed) / len(rs),
                        "sample_correct": k_ok, "sample_accuracy": k_ok / len(parsed) if parsed else None,
                        "sample_accuracy_wilson95": wilson(k_ok, len(parsed)) if parsed else None,
                        "line_accuracy": sum(x["correct"] for x in lines) / len(lines) if lines else None,
                        "lines_unmatched": sum(not x["matched"] for x in lines),
                        "parse_errors": [r["parse_error"] for r in rs if r.get("parse_error")][:5]}
out = {"run": name, "spend_usd": mf["spend_usd"], "complete": mf["n_complete"], "planned": mf["n_cells_planned"],
       "errors": mf["n_error"], "by_model_condition": rows}
(HERE / f"{name}_report.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
L = [f"# Comprehension check: {name}", "",
     f"{mf['n_complete']}/{mf['n_cells_planned']} calls complete, {mf['n_error']} failed; spend ${mf['spend_usd']:.3f}.", "",
     "Placebo is a format check only (expected answer: convincing for every line).", "",
     "| model | condition | n | parsed | sample accuracy [95% Wilson] | per-line accuracy | unmatched lines |",
     "|---|---|---|---|---|---|---|"]
for k, x in rows.items():
    m, c = k.split("|")
    sa = "n/a" if x["sample_accuracy"] is None else f"{x['sample_accuracy']:.2f} [{x['sample_accuracy_wilson95'][0]:.2f}, {x['sample_accuracy_wilson95'][1]:.2f}]"
    la = "n/a" if x["line_accuracy"] is None else f"{x['line_accuracy']:.2f}"
    L.append(f"| {NAME[m]} | {c} | {x['n']} | {x['parsed']} | {sa} | {la} | {x['lines_unmatched']} |")
errs = [(k, e) for k, x in rows.items() for e in x["parse_errors"]]
L += ["", "Parse errors: " + ("; ".join(f"{k}: {e}" for k, e in errs) if errs else "none")]
(HERE / f"{name}_report.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
