"""Phase 2 grading route check (RULES.md): regrade 50 identity-check pod lies through the Anthropic API
directly and compare with their stored OpenRouter primary grades. Needs GRADER_ANTHROPIC_API_KEY.

  python regrade_direct.py   -> regrade_direct.json, regrade_direct.md
"""
import json, os, random, subprocess, sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from src.perfect_lie.grader import grader_input_from_record, grader_response_format, parse_grader_output
from src.perfect_lie.personas import load_instrument
from src.perfect_lie import reversed_analysis as A

SEED, MODEL, PER = 20261024, "claude-sonnet-4-5", {"placebo": 9, "full": 8, "reversed": 8}
RUNS = {"meta-llama/llama-3.1-8b-instruct": "pod_run", "google/gemma-3-27b-it": "pod_run_novita"}
GATED = ["historical_anchor", "emotional_appeal"]


def sample():
    out = []
    for m, run in RUNS.items():
        recs = [r for r in A.load_records(ROOT / f"results/phase2/identity_check/{run}/records.jsonl")
                if r["model_id"] == m and (r.get("grades") or {}).get("primary")]
        for cond, n in PER.items():
            pool = sorted((r for r in recs if r["condition"] == cond), key=lambda r: r["cell_id"])
            out += random.Random(f"{SEED}|{m}|{cond}").sample(pool, n)
    return out


KEY_VARS = ("GRADER_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY")


def grader_key():
    """The Anthropic API key for grading. Read from GRADER_ANTHROPIC_API_KEY: in a Claude Code cloud
    environment ANTHROPIC_API_KEY is reserved for the session's own authentication and is not passed
    through. Never printed."""
    for v in KEY_VARS:
        if os.environ.get(v):
            return os.environ[v]
    raise SystemExit(f"no grading key: set {KEY_VARS[0]} in the environment settings")


def call(system, user, schema):
    body = {"model": MODEL, "max_tokens": 2000, "temperature": 0, "system": system,
            "messages": [{"role": "user", "content": user}],
            "tools": [{"name": "cue_annotation", "description": "Record the cue annotation.", "input_schema": schema}],
            "tool_choice": {"type": "tool", "name": "cue_annotation"}}
    r = subprocess.run(["curl", "-sS", "-m", "300", "https://api.anthropic.com/v1/messages",
                        "-H", f"x-api-key: {grader_key()}", "-H", "anthropic-version: 2023-06-01",
                        "-H", "content-type: application/json", "--data-binary", "@-"],
                       input=json.dumps(body), capture_output=True, text=True)
    return json.loads(r.stdout)


def kappa(a, b):
    n = len(a)
    if not n:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return None if pe == 1 else (po - pe) / (1 - pe)


def main():
    inst = load_instrument()
    cue_order = [c.id for c in inst.cues]
    schema = grader_response_format(cue_order)["json_schema"]["schema"]
    scorable = {c.id for c in inst.cues if not c.heatmap_only and c.id not in GATED}
    rows, models_seen, usage = [], set(), {"input_tokens": 0, "output_tokens": 0}
    for r in sample():
        gi = grader_input_from_record(r, inst.cues)
        parsed, err = None, None
        for attempt in range(3):
            d = call(gi.system_prompt, gi.user_prompt, schema)
            models_seen.add(d.get("model"))
            for k in usage:
                usage[k] += (d.get("usage") or {}).get(k, 0)
            tool = next((c for c in d.get("content", []) if c.get("type") == "tool_use"), None)
            try:
                parsed = parse_grader_output(json.dumps(tool["input"]), cue_order)
                break
            except Exception as e:  # noqa: BLE001
                err = f"{type(e).__name__}: {str(e)[:150]}" if tool else str(d.get("error"))[:150]
        rows.append({"cell_id": r["cell_id"], "model": r["model_id"], "condition": r["condition"],
                     "openrouter": r["grades"]["primary"]["cues"], "direct": parsed["cues"] if parsed else None,
                     "attempts": attempt + 1, "error": None if parsed else err})
    ok = [x for x in rows if x["direct"]]
    per_cue = {}
    for c in cue_order:
        a = [bool(x["openrouter"][c]) for x in ok]; b = [bool(x["direct"][c]) for x in ok]
        per_cue[c] = {"agreement": sum(p == q for p, q in zip(a, b)) / len(a) if a else None, "kappa": kappa(a, b),
                      "positives_openrouter": sum(a), "positives_direct": sum(b), "scorable": c in scorable}
    def pooled(cues):
        a = [bool(x["openrouter"][c]) for x in ok for c in cues]; b = [bool(x["direct"][c]) for x in ok for c in cues]
        return {"labels": len(a), "agreement": sum(p == q for p, q in zip(a, b)) / len(a), "kappa": kappa(a, b)}
    all_, sc = pooled(cue_order), pooled(sorted(scorable))
    decision = (all_["kappa"] is not None and all_["kappa"] >= 0.90) or all_["agreement"] >= 0.97
    out = {"model_requested": MODEL, "models_returned": sorted(m for m in models_seen if m), "n": len(rows),
           "parsed": len(ok), "failures": [x for x in rows if not x["direct"]], "usage": usage,
           "pooled_all_cues": all_, "pooled_scorable_cues": sc, "per_cue": per_cue,
           "decision": "switch to the direct route" if decision else "stay on OpenRouter", "rows": rows}
    (HERE / "regrade_direct.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in ("models_returned", "n", "parsed", "pooled_all_cues", "pooled_scorable_cues", "decision", "usage")}, indent=1))


if __name__ == "__main__":
    main()
