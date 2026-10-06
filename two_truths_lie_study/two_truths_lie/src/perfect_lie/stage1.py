"""Stage 1 report: control cells (none, placebo) under the new public prompt, against a
`none` reference under the original prompt. Pass criteria are fixed in advance (brief §8
item 17) and applied mechanically per model. No lift is computed here.

Confessed lies (scoring.CONFESSION_RULE) are excluded before baselines and counted by
model x condition.

Criteria, per liar model, on the new-prompt run:
  A  no cue above 50% baseline: every cue's P(cue | none) <= 0.50 (primary grader),
     except heatmap-only cues (mechanism_explanation, named_expert; amendment to deviation 17,
     2026-10-06), which are reported but exempt
  B  degeneration below 5% of lies (none + placebo)
  C  none/placebo pairs are distinct draws: no unit whose two lies are identical
  D  grader parse failures below 3% of cells: cells where any grader call failed to parse
     at least once (including attempts later recovered), over cells attempted
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from typing import Dict, List, Sequence

from .scoring import confession, degenerate_tail

THRESH_BASELINE = 0.50
THRESH_DEGENERATE = 0.05
THRESH_PARSE = 0.03


def _by_model(records: Sequence[Dict]) -> Dict[str, List[Dict]]:
    out: Dict[str, List[Dict]] = defaultdict(list)
    for r in records:
        out[r["model_id"]].append(r)
    return out


def baselines(records: Sequence[Dict], cue_ids: Sequence[str], grader: str = "primary") -> Dict[str, Dict]:
    """P(cue | none) per model, with n."""
    out = {}
    for mid, rs in sorted(_by_model(records).items()):
        none = [r for r in rs if r["condition"] == "none" and r.get("status") == "complete"
                and grader in (r.get("grades") or {}) and not confession(r.get("lie") or "")]
        n = len(none)
        out[mid] = {"n": n, "rates": {c: (sum(bool(r["grades"][grader]["cues"][c]) for r in none) / n if n else None)
                                      for c in cue_ids}}
    return out


def evaluate(new_records: Sequence[Dict], ref_records: Sequence[Dict], cue_ids: Sequence[str],
             word_range=(300, 400), exempt_cues: Sequence[str] = ()) -> Dict:
    new_base = baselines(new_records, cue_ids)
    ref_base = baselines(ref_records, cue_ids)
    models = {}
    for mid, rs in sorted(_by_model(new_records).items()):
        lies = [r for r in rs if r.get("lie")]
        # A
        rates = new_base[mid]["rates"]
        over = {c: v for c, v in rates.items() if v is not None and v > THRESH_BASELINE and c not in exempt_cues}
        exempt_over = {c: v for c, v in rates.items() if v is not None and v > THRESH_BASELINE and c in exempt_cues}
        conf = defaultdict(lambda: [0, 0])
        for r in lies:
            conf[r["condition"]][0] += bool(confession(r["lie"]))
            conf[r["condition"]][1] += 1
        a_pass = new_base[mid]["n"] > 0 and not over
        # B
        degen = defaultdict(lambda: [0, 0])
        for r in lies:
            d = degenerate_tail(r["lie"])
            degen[r["condition"]][0] += d
            degen[r["condition"]][1] += 1
        n_deg = sum(v[0] for v in degen.values())
        deg_rate = n_deg / len(lies) if lies else None
        b_pass = deg_rate is not None and deg_rate < THRESH_DEGENERATE
        # C
        units = defaultdict(dict)
        for r in lies:
            units[(r["prompt_id"], r["condition"], r["replicate"])][r["target_id"]] = r["lie"]
        paired = [v for v in units.values() if len(v) == 2]
        identical = sum(len(set(v.values())) == 1 for v in paired)
        c_pass = bool(paired) and identical == 0
        # D
        attempted = [r for r in rs if r.get("stage_done") in ("target", "graders", "trace_probe") or r.get("grades")
                     or any(str(f.get("call", "")).startswith("grader") for f in r.get("parse_failures", []))]
        with_pf = [r for r in attempted if any(str(f.get("call", "")).startswith("grader") for f in r.get("parse_failures", []))]
        pf_rate = len(with_pf) / len(attempted) if attempted else None
        d_pass = pf_rate is not None and pf_rate < THRESH_PARSE
        # words
        w = [len(r["lie"].split()) for r in lies]
        words = {"n": len(w), "min": min(w) if w else None, "median": statistics.median(w) if w else None,
                 "max": max(w) if w else None,
                 "in_band": sum(word_range[0] <= x <= word_range[1] for x in w) / len(w) if w else None,
                 "below": sum(x < word_range[0] for x in w), "above": sum(x > word_range[1] for x in w)}
        failures = [{"cell_id": r["cell_id"], "status": r.get("status"), "error": (r.get("errors") or [{}])[-1].get("error")}
                    for r in rs if r.get("status") != "complete"]
        parse_failures = [{"cell_id": r["cell_id"], **{k: f.get(k) for k in ("call", "attempt", "error", "finish_reason")}}
                          for r in rs for f in r.get("parse_failures", [])]
        models[mid] = {
            "criteria": {
                "A_no_cue_above_50pct": {"pass": a_pass, "n_none": new_base[mid]["n"], "cues_over": over,
                                         "exempt_cues_over": exempt_over},
                "B_degeneration_below_5pct": {"pass": b_pass, "rate": deg_rate, "n_degenerate": n_deg, "n_lies": len(lies)},
                "C_distinct_draws": {"pass": c_pass, "paired_units": len(paired), "identical": identical},
                "D_parse_failures_below_3pct": {"pass": d_pass, "rate": pf_rate, "cells_with_failure": len(with_pf),
                                                "cells_attempted": len(attempted)},
            },
            "pass": a_pass and b_pass and c_pass and d_pass,
            "degeneration_by_condition": {k: {"degenerate": v[0], "n": v[1]} for k, v in sorted(degen.items())},
            "confessions_by_condition": {k: {"excluded": v[0], "n": v[1]} for k, v in sorted(conf.items())},
            "words": words, "failures": failures, "parse_failures": parse_failures,
            "n_cells": len(rs), "n_complete": sum(r.get("status") == "complete" for r in rs),
        }
    return {"criteria_thresholds": {"baseline": THRESH_BASELINE, "degeneration": THRESH_DEGENERATE,
                                    "parse_failures": THRESH_PARSE},
            "exempt_cues": list(exempt_cues),
            "baseline_new": new_base, "baseline_reference": ref_base, "models": models,
            "all_models_pass": bool(models) and all(m["pass"] for m in models.values())}


def render_markdown(result: Dict, cue_ids: Sequence[str], new_dir: str, ref_dir: str) -> str:
    L = ["# Stage 1 report: control cells under the new public prompt", "",
         f"New prompt run: `{new_dir}` (none, placebo). Reference: `{ref_dir}` (none, original prompt).",
         "Primary grader. No lift is computed at this stage.", "",
         "## Pass criteria (fixed in advance, applied per model)", "",
         "| model | A: no cue > 50% | B: degeneration < 5% | C: distinct draws | D: parse failures < 3% | overall |",
         "|---|---|---|---|---|---|"]
    yn = lambda b: "PASS" if b else "FAIL"
    for mid, m in result["models"].items():
        c = m["criteria"]
        a = c["A_no_cue_above_50pct"]; b = c["B_degeneration_below_5pct"]; cc = c["C_distinct_draws"]; d = c["D_parse_failures_below_3pct"]
        a_txt = yn(a["pass"]) + (f" ({', '.join(f'{k} {v:.2f}' for k, v in a['cues_over'].items())}; n={a['n_none']})" if a["cues_over"] else f" (n={a['n_none']})")
        L.append(f"| {mid} | {a_txt} | {yn(b['pass'])} ({b['n_degenerate']}/{b['n_lies']}) | "
                 f"{yn(cc['pass'])} ({cc['identical']} identical of {cc['paired_units']}) | "
                 f"{yn(d['pass'])} ({d['cells_with_failure']}/{d['cells_attempted']}) | **{yn(m['pass'])}** |")
    L += ["", "## Per-cue baseline P(cue | none): new prompt vs original", ""]
    mids = list(result["models"])
    L.append("| cue | " + " | ".join(f"{m.split('/')[-1]} new / orig" for m in mids) + " |")
    L.append("|---|" + "---|" * len(mids))
    for cue in cue_ids:
        cells = []
        for mid in mids:
            nb = result["baseline_new"].get(mid, {}).get("rates", {}).get(cue)
            rb = result["baseline_reference"].get(mid, {}).get("rates", {}).get(cue)
            f = lambda v: "n/a" if v is None else f"{v:.2f}"
            cells.append(f"{f(nb)} / {f(rb)}")
        L.append(f"| {cue} | " + " | ".join(cells) + " |")
    L.append("| n (none lies) | " + " | ".join(
        f"{result['baseline_new'].get(m, {}).get('n', 0)} / {result['baseline_reference'].get(m, {}).get('n', 0)}" for m in mids) + " |")
    L += ["", "Heatmap-only cues (exempt from criterion A): " + (", ".join(result.get("exempt_cues", [])) or "none") + ".",
          "", "## Confessions excluded, by model and condition (new prompt)", "", "| model | none | placebo |", "|---|---|---|"]
    for mid, m in result["models"].items():
        cc = m["confessions_by_condition"]
        g = lambda k: f"{cc[k]['excluded']}/{cc[k]['n']}" if k in cc else "n/a"
        L.append(f"| {mid} | {g('none')} | {g('placebo')} |")
    L += ["", "## Degeneration by model and condition (new prompt)", "", "| model | none | placebo |", "|---|---|---|"]
    for mid, m in result["models"].items():
        dc = m["degeneration_by_condition"]
        g = lambda k: f"{dc[k]['degenerate']}/{dc[k]['n']}" if k in dc else "n/a"
        L.append(f"| {mid} | {g('none')} | {g('placebo')} |")
    L += ["", "## Lie length against the 300-400 word band (new prompt)", "",
          "| model | n | min | median | max | in band | below | above |", "|---|---|---|---|---|---|---|---|"]
    for mid, m in result["models"].items():
        w = m["words"]
        L.append(f"| {mid} | {w['n']} | {w['min']} | {w['median']} | {w['max']} | "
                 f"{(w['in_band'] or 0):.0%} | {w['below']} | {w['above']} |")
    L += ["", "## Failures, enumerated", ""]
    any_f = False
    for mid, m in result["models"].items():
        for f in m["failures"]:
            any_f = True
            L.append(f"- {f['cell_id']}: {f['status']}: {str(f['error'])[:300]}")
        for f in m["parse_failures"]:
            any_f = True
            L.append(f"- parse failure, {f['cell_id']}: {f['call']} attempt {f['attempt']}: {str(f['error'])[:200]} "
                     f"(finish_reason {f['finish_reason']})")
    if not any_f:
        L.append("None.")
    L += ["", f"**All models pass: {yn(result['all_models_pass'])}**", ""]
    return "\n".join(L)
