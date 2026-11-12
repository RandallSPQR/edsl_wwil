"""Phase 2 identity check, part 1: temperature-0 diagnostic (not a gate). Rules: RULES.md.

20 prompts per model, seeded (20261021) and stratified 7 placebo / 7 full / 6 reversed, from the
reversed-note run's replay export. Each prompt's exact delivered messages go, at temperature 0 and the
run's max tokens, to (a) the API with the run's provider pin (OpenRouter; Llama: CoreWeave bf16, Gemma:
Novita bf16, no fallback) and (b) the pod (vLLM, pinned HF weights, bf16). Both completions are tokenised
with the pod's tokenizer; the first index where the token ids differ is the divergence position. Prompt
token counts (pod chat template vs the API's reported usage) are a template check.

  python diagnostic.py --gemma-pod POD_ID --llama-pod POD_ID --key-file PATH

The pod access key is read from --key-file and never written out. Writes diagnostic.json.
"""
import argparse, json, os, random, subprocess, sys, time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPLAY = ROOT / "results/perfect_lie_reversed/full_run/main/replay.jsonl"
SEED, PER_CONDITION = 20261021, {"placebo": 7, "full": 7, "reversed": 6}
PINS = {"meta-llama/llama-3.1-8b-instruct": {"only": ["coreweave"], "quantizations": ["bf16"], "allow_fallbacks": False},
        "google/gemma-3-27b-it": {"only": ["novita"], "quantizations": ["bf16"], "allow_fallbacks": False}}
POD_MODEL = {"meta-llama/llama-3.1-8b-instruct": "meta-llama/Llama-3.1-8B-Instruct",
             "google/gemma-3-27b-it": "google/gemma-3-27b-it"}


def post(url, body, headers, timeout=600):
    """curl, so Cloudflare-fronted hosts accept the request (they reject urllib's signature)."""
    args = ["curl", "-sS", "-m", str(timeout), "-X", "POST", url, "-H", "Content-Type: application/json"]
    for k, v in headers.items():
        args += ["-H", f"{k}: {v}"]
    r = subprocess.run(args + ["--data-binary", "@-"], input=json.dumps(body), capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"error": (r.stdout or r.stderr)[:300]}


def select(rows):
    out = []
    for model in PINS:
        by = defaultdict(list)
        for r in rows:
            if r["openrouter_id"] == model:
                by[r["condition"]].append(r)
        for cond, n in PER_CONDITION.items():
            pool = sorted(by[cond], key=lambda r: r["cell_id"])
            out += random.Random(f"{SEED}|{model}|{cond}").sample(pool, n)
    return out


def first_divergence(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return None if len(a) == len(b) else min(len(a), len(b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gemma-pod", required=True)
    ap.add_argument("--llama-pod", required=True)
    ap.add_argument("--key-file", required=True)
    a = ap.parse_args()
    key = Path(a.key_file).read_text().strip()
    pods = {"google/gemma-3-27b-it": a.gemma_pod, "meta-llama/llama-3.1-8b-instruct": a.llama_pod}
    or_key = os.environ["OPEN_ROUTER_API_KEY"]
    rows = [json.loads(l) for l in REPLAY.open()]
    results = []
    for r in select(rows):
        m = r["openrouter_id"]
        base = f"https://{pods[m]}-8000.proxy.runpod.net"
        auth = {"Authorization": f"Bearer {key}"}
        msgs = r["messages"]
        api = post("https://openrouter.ai/api/v1/chat/completions",
                   {"model": m, "messages": msgs, "temperature": 0, "max_tokens": r["max_output_tokens"],
                    "provider": PINS[m], "usage": {"include": True}},
                   {"Authorization": f"Bearer {or_key}"})
        pod = post(f"{base}/v1/chat/completions",
                   {"model": POD_MODEL[m], "messages": msgs, "temperature": 0, "max_tokens": r["max_output_tokens"]}, auth)
        rec = {"cell_id": r["cell_id"], "model": m, "condition": r["condition"]}
        if "choices" not in api or "choices" not in pod:
            rec["error"] = {"api": api.get("error"), "pod": pod.get("error") or pod.get("message")}
            results.append(rec); print(json.dumps(rec)[:300], flush=True); continue
        ta, tp = api["choices"][0]["message"]["content"] or "", pod["choices"][0]["message"]["content"] or ""
        tok = lambda text: post(f"{base}/tokenize", {"model": POD_MODEL[m], "prompt": text, "add_special_tokens": False}, auth).get("tokens")
        ka, kp = tok(ta), tok(tp)
        ptok = post(f"{base}/tokenize", {"model": POD_MODEL[m], "messages": msgs, "add_generation_prompt": True}, auth)
        rec.update({
            "api_provider": api.get("provider"), "api_finish": api["choices"][0].get("finish_reason"),
            "pod_finish": pod["choices"][0].get("finish_reason"),
            "prompt_tokens_api": (api.get("usage") or {}).get("prompt_tokens"),
            "prompt_tokens_pod_server": (pod.get("usage") or {}).get("prompt_tokens"),
            "prompt_tokens_pod_tokenize": ptok.get("count"),
            "completion_tokens_api": len(ka) if ka is not None else None,
            "completion_tokens_pod": len(kp) if kp is not None else None,
            "first_divergence": first_divergence(ka, kp) if ka is not None and kp is not None else "tokenize failed",
            "identical_text": ta == tp,
            "api_cost_usd": (api.get("usage") or {}).get("cost"),
            "api_text_head": ta[:160], "pod_text_head": tp[:160]})
        results.append(rec)
        print(json.dumps({k: rec[k] for k in ("model", "condition", "first_divergence", "prompt_tokens_api", "prompt_tokens_pod_server", "api_provider")}), flush=True)
    (HERE / "diagnostic.json").write_text(json.dumps({"rules": "RULES.md", "seed": SEED, "results": results}, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
