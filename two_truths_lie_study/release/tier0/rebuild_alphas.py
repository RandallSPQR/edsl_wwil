"""Rebuild results/phase2/pilot/confirmatory_alphas.json from the two pilot results (alpha rule, PREREG_PHASE2
section 6: the largest grid alpha at which the steered and placebo lies both pass the coherence gate). The file was
assembled from pilot2_result.json (Addendum 5 placebo; in force) and pilot_result.json (retired placebo; superseded).
Run from two_truths_lie/ after the pilot analyses.
"""
import json
from pathlib import Path

P = Path.cwd() / "results/phase2/pilot"
SLUGS = ["gemma-3-27b-it", "llama-3.1-8b-instruct"]


def alphas(name):
    return {s: {h: v["confirmatory_alpha"] for h, v in json.loads((P / s / name).read_text())["hypotheses"].items()}
            for s in SLUGS}


out = {"stage": "stage-1 dose-finding pilot, re-applied with the Addendum 5 placebo",
       "rule": "largest grid alpha at which steered and placebo both pass the coherence gate",
       "confirmatory_alpha": alphas("pilot2_result.json"),
       "supersedes": {"source": "Addendum 4 pilot with the retired placebo (commit 7928d46)",
                      "confirmatory_alpha": alphas("pilot_result.json")}}
(P / "confirmatory_alphas.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out["confirmatory_alpha"]))
