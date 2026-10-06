"""Stage 2 reachability check.

Stage 2 output is a reachability check only and feeds no estimate (owner, 2026-10-06). This
report therefore counts what ran and what failed. It computes no cue rates, no T, no lift and
no acceptance rates.
"""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from typing import Dict, List, Sequence

from .scoring import confession, degenerate_tail


def reachability(records: Sequence[Dict], manifest: Dict) -> Dict:
    judges = manifest.get("target_models") or []
    graders = manifest.get("graders") or []
    out: Dict = {"n_cells": len(records), "spend_usd": manifest.get("spend_usd"),
                 "killed_on_breach": manifest.get("killed_on_breach"), "models": {}}
    by = defaultdict(list)
    for r in records:
        by[r["model_id"]].append(r)
    for mid, rs in sorted(by.items()):
        lies = [r for r in rs if r.get("lie")]
        words = [len(r["lie"].split()) for r in lies]
        el = [r["elicitation"] for r in rs if r.get("elicitation")]
        flags = [e.get("flags") or {} for e in el]
        overlaps = [f["note_overlap"] for f in flags if f.get("note_overlap") is not None]
        story_pf = sum(1 for r in rs for f in r.get("parse_failures", []) if str(f.get("call", "")).startswith("grader"))
        bhat_pf = sum(1 for r in rs for f in r.get("parse_failures", []) if str(f.get("call", "")).startswith("bhat"))
        out["models"][mid] = {
            "cells": len(rs), "complete": sum(r.get("status") == "complete" for r in rs),
            "failed": [{"cell_id": r["cell_id"], "status": r.get("status"),
                        "error": (r.get("errors") or [{}])[-1].get("error")} for r in rs if r.get("status") != "complete"],
            "lies": len(lies),
            "all_judges_read": sum(set(judges) <= set((r.get("targets") or {})) for r in lies),
            "all_graders_scored": sum(len(r.get("grades") or {}) >= 2 for r in lies),
            "confessions": sum(bool(confession(r["lie"])) for r in lies),
            "degenerate": sum(degenerate_tail(r["lie"]) for r in lies),
            "words": {"min": min(words) if words else None, "median": statistics.median(words) if words else None,
                      "max": max(words) if words else None,
                      "in_300_400": sum(300 <= w <= 400 for w in words)},
            "story_grader_parse_failures": story_pf,
            "elicitation": {"answered": len(el),
                            "bhat_coded_by_all_graders": sum(len(r.get("bhat_grades") or {}) == len(graders) for r in rs),
                            "bhat_parse_failures": bhat_pf,
                            "refusal": sum(bool(f.get("refusal")) for f in flags),
                            "breakdown": sum(bool(f.get("breakdown")) for f in flags),
                            "echo": sum(bool(f.get("echo")) for f in flags),
                            "note_overlap_mean": statistics.mean(overlaps) if overlaps else None,
                            "note_overlap_max": max(overlaps) if overlaps else None},
        }
    return out


def render(res: Dict, run_dir: str) -> str:
    L = ["# Stage 2 reachability check", "",
         f"Run: `{run_dir}`. Reachability only: no cue rates, no T, no lift, no acceptance rates are computed,",
         "and nothing here feeds any estimate.", "",
         f"Cells: {res['n_cells']}. Spend: ${res['spend_usd']:.2f}. Killed on breach: {res['killed_on_breach']}.", "",
         "## Stories", "",
         "| liar | cells | complete | read by all 4 judges | scored by all 4 graders | confessions | degenerate | words min / median / max | in 300-400 | story parse failures |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for mid, m in res["models"].items():
        w = m["words"]
        L.append(f"| {mid} | {m['cells']} | {m['complete']} | {m['all_judges_read']} | {m['all_graders_scored']} | "
                 f"{m['confessions']} | {m['degenerate']} | {w['min']} / {w['median']} / {w['max']} | "
                 f"{w['in_300_400']}/{m['lies']} | {m['story_grader_parse_failures']} |")
    L += ["", "## Post-story elicitation (stated B-hat): rates only", "",
          "| liar | answered | coded by all 4 graders | B-hat parse failures | refusal | breakdown | echo of note | mean / max overlap with note |",
          "|---|---|---|---|---|---|---|---|"]
    for mid, m in res["models"].items():
        e = m["elicitation"]
        ov = "n/a" if e["note_overlap_mean"] is None else f"{e['note_overlap_mean']:.2f} / {e['note_overlap_max']:.2f}"
        L.append(f"| {mid} | {e['answered']} | {e['bhat_coded_by_all_graders']} | {e['bhat_parse_failures']} | "
                 f"{e['refusal']} | {e['breakdown']} | {e['echo']} | {ov} |")
    L += ["", "## Failed cells", ""]
    fails = [f for m in res["models"].values() for f in m["failed"]]
    L += [f"- {f['cell_id']}: {f['status']}: {str(f['error'])[:300]}" for f in fails] or ["None."]
    return "\n".join(L) + "\n"
