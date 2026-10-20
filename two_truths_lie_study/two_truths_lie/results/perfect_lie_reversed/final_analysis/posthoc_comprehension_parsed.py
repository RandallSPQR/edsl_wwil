"""POST HOC, DESCRIPTIVE (owner's request, 2026-10-20, after unblinding; not registered).

Balanced accuracy of the comprehension check on PARSEABLE answers only, beside the registered figure
(which counts an unparsed answer as incorrect). Re-scores with the frozen scorer exactly as
reversed_analysis.comprehension does, drops samples whose answer could not be parsed, and runs the
registered bootstrap (C.discrimination: 2,000 resamples, seed 20261015). Also reports, within parsed
samples, the share of note lines left unmatched (an unmatched line counts as incorrect).
Writes posthoc_comprehension_parsed.json.
"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
from src.perfect_lie import comprehension as C, reversed_analysis as A, reversed_run as R

recs = A.load_records(ROOT / "results/perfect_lie_reversed/full_run/comprehension/records.jsonl")
models = R.load_config()["liar_models"]
scored = []
for r in recs:
    if r.get("status") not in ("complete", "error"):
        continue
    r = dict(r)
    try:
        items, mode = C.parse_with_mode(r.get("answer") if r.get("status") == "complete" else None)
        r["score"], r["parse_mode"] = C.score(items, r["note_lines"], r["condition"]), mode
    except (ValueError, json.JSONDecodeError, KeyError):
        r["score"], r["parse_mode"] = None, None
    scored.append(r)

registered = C.discrimination(scored)
parsed = C.discrimination([r for r in scored if r["score"]])
out = {"label": "post hoc, descriptive; not registered; cannot change any label", "models": {}}
for m in models:
    ps = [r for r in scored if r["model_id"] == m and r["condition"] in ("full", "reversed") and r["score"]]
    lines = [x for r in ps for x in r["score"]["lines"]]
    out["models"][m] = {
        "registered_all_samples": {k: registered[m].get(k) for k in ("balanced_accuracy", "acc_full", "acc_reversed", "criterion_c", "n_samples")}
                                  | {"ci95": registered[m]["ci95"]["balanced_accuracy"]},
        "parsed_only": {k: parsed[m].get(k) for k in ("balanced_accuracy", "acc_full", "acc_reversed", "criterion_c", "n_samples")}
                       | {"ci95": parsed[m]["ci95"]["balanced_accuracy"]},
        "unparsed_samples": sum(1 for r in scored if r["model_id"] == m and r["condition"] in ("full", "reversed") and not r["score"]),
        "parsed_lines_unmatched_share": (sum(not x["matched"] for x in lines) / len(lines)) if lines else None,
    }
(HERE / "posthoc_comprehension_parsed.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
