"""Phase 2 identity check, part 1, re-run: temperature-0 diagnostic (not a gate) on the fixed pod.

Same rules and the same seeded 40 prompts as diagnostic.py (RULES.md). Changes, both fixes from the
first diagnostic (DIAGNOSTIC_SUMMARY.md):
  * the pod runs HF transformers (pod_server.py), greedy, bf16, one model at a time; Gemma's weights
    come from the network volume in EUR-IS-1;
  * Llama is rendered without the template's date header (strip_llama_date), as CoreWeave renders it.
The API is called again at temperature 0, so the API's own run-to-run agreement with the first
diagnostic is reported too.

  python diagnostic_tf.py --pod POD_ID --key-file PATH
"""
import argparse, json, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import diagnostic as D   # selection, pins, curl helper and divergence rule are reused unchanged

POD_MODEL = D.POD_MODEL


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pod", required=True)
    ap.add_argument("--key-file", required=True)
    a = ap.parse_args()
    key = Path(a.key_file).read_text().strip()
    base, auth = f"https://{a.pod}-8000.proxy.runpod.net", {"Authorization": f"Bearer {Path(a.key_file).read_text().strip()}"}
    or_key = os.environ["OPEN_ROUTER_API_KEY"]
    first = {r["cell_id"]: r for r in json.loads((HERE / "diagnostic.json").read_text())["results"]}
    rows = [json.loads(l) for l in D.REPLAY.open()]
    sel = D.select(rows)
    results, loaded = [], None
    for r in sel:
        m = r["openrouter_id"]
        if loaded != m:
            print("loading", POD_MODEL[m], D.post(f"{base}/load", {"model": POD_MODEL[m]}, auth, timeout=3000), flush=True)
            loaded = m
        strip = m.startswith("meta-llama")
        msgs = r["messages"]
        api = D.post("https://openrouter.ai/api/v1/chat/completions",
                     {"model": m, "messages": msgs, "temperature": 0, "max_tokens": r["max_output_tokens"],
                      "provider": D.PINS[m], "usage": {"include": True}}, {"Authorization": f"Bearer {or_key}"})
        pod = D.post(f"{base}/generate", {"messages": msgs, "max_tokens": r["max_output_tokens"], "strip_llama_date": strip}, auth, timeout=1200)
        rec = {"cell_id": r["cell_id"], "model": m, "condition": r["condition"]}
        if "choices" not in api or "ids" not in pod:
            rec["error"] = {"api": str(api.get("error"))[:200], "pod": str(pod.get("error"))[:200]}
            results.append(rec); print(json.dumps(rec)[:300], flush=True); continue
        ta = api["choices"][0]["message"]["content"] or ""
        ka = D.post(f"{base}/tokenize", {"text": ta}, auth).get("ids")
        kp = pod["ids"]
        prev = first.get(r["cell_id"], {})
        rec.update({
            "api_provider": api.get("provider"), "api_finish": api["choices"][0].get("finish_reason"), "pod_finish": pod["finish"],
            "prompt_tokens_api": (api.get("usage") or {}).get("prompt_tokens"), "prompt_tokens_pod": pod["prompt_count"],
            "completion_tokens_api": len(ka) if ka is not None else None, "completion_tokens_pod": len(kp),
            "first_divergence": D.first_divergence(ka, kp) if ka is not None else "tokenize failed",
            "identical_text": ta == pod["text"],
            "api_same_as_first_diagnostic": (ta[:160] == prev.get("api_text_head")) if prev.get("api_text_head") is not None else None,
            "api_cost_usd": (api.get("usage") or {}).get("cost"),
            "api_text_head": ta[:160], "pod_text_head": pod["text"][:160]})
        results.append(rec)
        print(json.dumps({k: rec[k] for k in ("model", "condition", "first_divergence", "prompt_tokens_api", "prompt_tokens_pod", "pod_finish", "api_same_as_first_diagnostic")}), flush=True)
    (HERE / "diagnostic_tf.json").write_text(json.dumps({"rules": "RULES.md", "seed": D.SEED, "results": results}, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
