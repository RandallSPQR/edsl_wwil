"""Pilot 1 report: degeneration and viability at temperatures 0.6 and 0.8 (rules: PILOT_RULES.md)."""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
from src.perfect_lie.scoring import degenerate_tail, confession, lie_viability, _STOPWORDS
from src.perfect_lie.runner import load_records

NAME = {"meta-llama/llama-3.1-8b-instruct": "Llama 3.1 8B", "google/gemma-3-27b-it": "Gemma 3 27B",
        "openai/gpt-4o-mini": "gpt-4o-mini", "google/gemini-2.5-flash-lite": "Gemini 2.5 Flash-Lite"}


def tail_stop_rate(text, window=150):
    w = re.findall(r"[A-Za-z']+", text)[-window:]
    return sum(x.lower() in _STOPWORDS for x in w) / len(w) if len(w) >= 50 else None


res = {}
for t in ("0.6", "0.8"):
    recs = load_records(HERE / f"degeneration_t{t}")
    mf = json.loads((HERE / f"degeneration_t{t}" / "manifest.json").read_text())
    res[t] = {"spend_usd": mf["spend_usd"], "failed_cells": mf["n_error"], "models": {}}
    for m in NAME:
        rs = [r for r in recs if r["model_id"] == m]
        lies = [r for r in rs if r.get("lie")]
        nv = [(r["category"], lie_viability(r)) for r in lies if lie_viability(r)]
        res[t]["models"][m] = {
            "lies": len(lies), "failed": sum(r.get("status") == "error" for r in rs),
            "degenerate": sum(degenerate_tail(r["lie"]) for r in lies),
            "non_viable": len(nv), "non_viable_detail": nv,
            "confessions": [(r["category"], confession(r["lie"])) for r in lies if confession(r["lie"])],
            "words_min_median_max": [min(r["lie_words"] for r in lies), sorted(r["lie_words"] for r in lies)[len(lies) // 2],
                                     max(r["lie_words"] for r in lies)] if lies else None,
            "min_tail_stopword_rate": min((x for x in (tail_stop_rate(r["lie"]) for r in lies) if x is not None), default=None),
            "finish_length": sum(r.get("liar_finish_reason") == "length" for r in lies)}
ok08 = all(res["0.8"]["models"][m]["degenerate"] == 0 and res["0.8"]["models"][m]["failed"] == 0
           and res["0.8"]["models"][m]["non_viable"] <= res["0.6"]["models"][m]["non_viable"] for m in NAME)
res["proposal"] = {"temperature": 0.8 if ok08 else 0.6, "top_p": 0.9,
                   "rule": "0.8 if every model has 0 degenerate lies and no more non-viable lies at 0.8 than at 0.6; else 0.6"}
(HERE / "degeneration_report.json").write_text(json.dumps(res, indent=1) + "\n")
L = ["# Pilot 1: degeneration check (placebo, 24 lies per model per temperature, top_p 0.9)", "",
     f"Spend: ${res['0.6']['spend_usd'] + res['0.8']['spend_usd']:.3f} (cap $3).", "",
     "| model | T | lies | failed | degenerate | non-viable | confessions | words min / median / max | lowest tail stop-word rate (degenerate below 0.15) |",
     "|---|---|---|---|---|---|---|---|---|"]
for m in NAME:
    for t in ("0.6", "0.8"):
        x = res[t]["models"][m]
        L.append(f"| {NAME[m]} | {t} | {x['lies']} | {x['failed']} | {x['degenerate']} | {x['non_viable']} | {len(x['confessions'])} | "
                 f"{' / '.join(map(str, x['words_min_median_max'] or []))} | {x['min_tail_stopword_rate']:.2f} |")
L += ["", "Non-viable lies: " + ("; ".join(f"{NAME[m]} T={t}: {res[t]['models'][m]['non_viable_detail']}"
                                           for t in ("0.6", "0.8") for m in NAME if res[t]["models"][m]["non_viable_detail"]) or "none"), "",
      f"**Proposal (rule fixed in PILOT_RULES.md): temperature {res['proposal']['temperature']}, top_p 0.9, for all four models.**"]
(HERE / "degeneration_report.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
