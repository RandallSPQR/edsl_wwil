"""Pilot 4c report: comprehension as discrimination (owner, 2026-10-11), with option- and line-order
randomisation. Per model: balanced accuracy, Youden's J, d', criterion c (95% bootstrap over samples),
parse counts, and c split by which option was listed first. Unrandomised Pilot 4b shown for comparison."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
from src.perfect_lie import comprehension as C
from src.perfect_lie.runner import load_records

NAME = {"meta-llama/llama-3.1-8b-instruct": "Llama", "google/gemma-3-27b-it": "Gemma",
        "openai/gpt-4o-mini": "gpt-4o-mini", "google/gemini-2.5-flash-lite": "Gemini"}


def load(name):
    rs = [r for r in load_records(HERE / name) if r.get("status") == "complete"]
    for r in rs:
        try:
            items, mode = C.parse_with_mode(r.get("answer"))
            r["score"], r["parse_mode"] = C.score(items, r["note_lines"], r["condition"]), mode
        except (ValueError, json.JSONDecodeError):
            r["score"], r["parse_mode"] = None, None
    return rs


v2, v1 = load("comprehension_pilot_v2"), load("comprehension_pilot")
d2, d1 = C.discrimination(v2), C.discrimination(v1)
by_order = {}
for o in (0, 1):
    sub = [r for r in v2 if r.get("variant", {}).get("option_order") == o]
    by_order[o] = C.discrimination(sub, n_boot=500)
parse = {m: {k: sum(1 for r in v2 if r["model_id"] == m and r["condition"] in ("full", "reversed") and r["parse_mode"] == k)
             for k in ("strict", "tolerant", None)} for m in NAME}
placebo = {m: [r for r in v2 if r["model_id"] == m and r["condition"] == "placebo"] for m in NAME}
out = {"v2": d2, "v1_unrandomised": d1, "c_by_first_option": {o: {m: x["criterion_c"] for m, x in d.items()} for o, d in by_order.items()},
       "parse_full_reversed": {m: {str(k): v for k, v in p.items()} for m, p in parse.items()},
       "placebo_format_parsed": {m: sum(1 for r in rs if r["score"]) for m, rs in placebo.items()}}
(HERE / "comprehension_pilot_v2_report.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
f = lambda x: "n/a" if x is None else f"{x:+.2f}" if isinstance(x, float) and x < 0 else f"{x:.2f}"
ci = lambda c: "n/a" if not c else f"[{c[0]:.2f}, {c[1]:.2f}]"
L = ["# Pilot 4c: comprehension check with randomised option and line order", "",
     "Rule: comprehension holds if the balanced-accuracy lower 95% bound is >= 0.85. c > 0 leans \"convincing\", c < 0 leans \"suspicious\".",
     "10 full + 10 reversed samples per model (40 lines each); intervals are wide at pilot size.", "",
     "| model | parsed (strict / tolerant / not) | acc full | acc reversed | balanced accuracy [95%] | J [95%] | criterion c [95%] | c, convincing first / suspicious first | holds |",
     "|---|---|---|---|---|---|---|---|---|"]
for m, n in NAME.items():
    x = d2[m]; p = parse[m]
    L.append(f"| {n} | {p['strict']} / {p['tolerant']} / {p[None]} | {x['acc_full']:.2f} | {x['acc_reversed']:.2f} | "
             f"{x['balanced_accuracy']:.2f} {ci(x['ci95']['balanced_accuracy'])} | {f(x['youden_j'])} {ci(x['ci95']['youden_j'])} | "
             f"{f(x['criterion_c'])} {ci(x['ci95']['criterion_c'])} | {f(by_order[0].get(m, {}).get('criterion_c'))} / "
             f"{f(by_order[1].get(m, {}).get('criterion_c'))} | {'yes' if x['comprehension_holds'] else 'no'} |")
L += ["", "Unrandomised Pilot 4b, same metrics, for comparison:", "",
      "| model | balanced accuracy [95%] | J | criterion c [95%] | holds |", "|---|---|---|---|---|"]
for m, n in NAME.items():
    x = d1[m]
    L.append(f"| {n} | {x['balanced_accuracy']:.2f} {ci(x['ci95']['balanced_accuracy'])} | {f(x['youden_j'])} | "
             f"{f(x['criterion_c'])} {ci(x['ci95']['criterion_c'])} | {'yes' if x['comprehension_holds'] else 'no'} |")
L += ["", "Placebo format check, parsed of 10: " + ", ".join(f"{NAME[m]} {v}" for m, v in out["placebo_format_parsed"].items()) + "."]
(HERE / "comprehension_pilot_v2_report.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
