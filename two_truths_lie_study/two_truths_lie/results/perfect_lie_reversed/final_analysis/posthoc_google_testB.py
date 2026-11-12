"""POST HOC, DESCRIPTIVE (owner's request, 2026-10-22, after unblinding; not registered; no new model calls).

Test B (full - reversed) per liar model from the Google grader's annotations (gemini-2.5-flash, which graded
every lie), beside the registered primary B. Same lies, same cue pool (the registered gate's exclusions),
same fit and fallback (reversed_analysis.fit_model), so the only change is whose annotations give s.
The Google grader shares a family with two of the liars (Gemma 3 27B, Gemini 2.5 Flash-Lite).
Reported per model: B, SE, 95% CI (t, the fit's df), method, lies used, and whether each primary rejection
is preserved at the local alpha at which it was made (reversed_analysis.holds). No decision label.
Writes posthoc_google_testB.json and posthoc_google_testB.md.

Run it in the registered environment (requirements_review.txt: Python 3.11, numpy 2.4.6, pandas 2.3.3, scipy 1.17.1,
statsmodels 0.15.0). Under a newer stack (numpy 2.5, pandas 3.0, scipy 1.18, Python 3.13) Gemma's primary mixed
model converges instead of falling back, and its primary B prints as +0.431 instead of the registered +0.430.
"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
from scipy import stats
from src.perfect_lie import reversed_analysis as A, reversed_run as R
from src.perfect_lie.personas import load_instrument

NAME = {"meta-llama/llama-3.1-8b-instruct": "Llama 3.1 8B", "google/gemma-3-27b-it": "Gemma 3 27B",
        "openai/gpt-4o-mini": "gpt-4o-mini", "google/gemini-2.5-flash-lite": "Gemini 2.5 Flash-Lite"}

recs = A.load_records(ROOT / "results/perfect_lie_reversed/full_run/main/records.jsonl")
cfg, inst = R.load_config(), load_instrument()
models = cfg["liar_models"]
adj = A._adjudicated()
g = A.gate(recs, inst)
cues = A.target_cues(inst, cfg["targets"], g["excluded"])
lies_p = A.lie_table(recs, cues, grader="primary", adj=adj)
lies_g = A.lie_table(recs, cues, grader="google", adj=adj)
dec = A.decide_all(lies_p, models)


def ci(f):
    if not A._testable(f["B"], f["B_se"], f["df"]):
        return None
    h = stats.t.isf(0.025, f["df"]) * f["B_se"]
    return [f["B"] - h, f["B"] + h]


import platform, numpy, pandas, scipy, statsmodels
out = {"environment": {"python": platform.python_version(), "numpy": numpy.__version__, "pandas": pandas.__version__,
                       "scipy": scipy.__version__, "statsmodels": statsmodels.__version__},
       "note": "post hoc, descriptive; the Google grader shares a family with the Gemma and Gemini liars",
       "gate_excluded": g["excluded"], "pool": sorted(cues), "models": {}}
for m in models:
    fg = A.fit_model(lies_g[lies_g.model == m])
    d = dec[m]
    out["models"][m] = {
        "primary": {k: d[k] for k in ("B", "B_se", "df", "method", "label", "n")} | {"ci95": ci(d)},
        "google": {k: fg.get(k) for k in ("B", "B_se", "df", "method", "fallback_reason", "n", "K")} | {"ci95": ci(fg)},
        "google_minus_primary": fg["B"] - d["B"],
        "primary_rejections_preserved": A.holds(d, fg["B"], fg["B_se"], fg["df"]),
        "family_shared_with_grader": A.FAMILY[m] == "google"}
(HERE / "posthoc_google_testB.json").write_text(json.dumps(out, indent=1, default=float) + "\n")

f = lambda x, k=3: "n/a" if x is None or x != x else f"{x:+.{k}f}"
c = lambda v: f"[{f(v[0])}, {f(v[1])}]" if v else "n/a"
L = ["# Test B under the Google grader (post hoc, descriptive)", "",
     "Owner's request, 2026-10-22, after unblinding; not registered; no new model calls. Test B = full - reversed, "
     "from the Google grader's annotations (gemini-2.5-flash graded every lie), with the registered lies, cue pool "
     f"(gate exclusions {g['excluded']}) and fit/fallback; only the grader differs. **The Google grader shares a family "
     "with the Gemma 3 27B and Gemini 2.5 Flash-Lite liars**, so agreement on those two rows is weaker evidence of "
     "grader-robustness than on the other two.", "",
     "| liar | primary label | primary B [95% CI] | Google B [95% CI] | Google - primary | Google method | lies (primary / Google) | primary rejections preserved | grader same family |",
     "|---|---|---|---|---|---|---|---|---|"]
for m in models:
    r = out["models"][m]; p, q = r["primary"], r["google"]
    L.append(f"| {NAME[m]} | {p['label']} | {f(p['B'])} {c(p['ci95'])} | {f(q['B'])} {c(q['ci95'])} | {f(r['google_minus_primary'])} | "
             f"{q['method']} | {p['n']} / {q['n']} | {r['primary_rejections_preserved'].get('all_primary_rejections_preserved')} | "
             f"{'yes' if r['family_shared_with_grader'] else 'no'} |")
L += ["", "Preserved = the primary efficacy rejection holds for the Google B at the local Holm alpha at which the "
      "primary rejected (reversed_analysis.holds). Descriptive only: it changes no registered label."]
(HERE / "posthoc_google_testB.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
