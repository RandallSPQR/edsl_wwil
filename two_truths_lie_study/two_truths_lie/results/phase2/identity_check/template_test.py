"""Gemma template-end test (hypothesis from DIAGNOSTIC_SUMMARY.md, re-run section): Novita renders the
prompt without the newline after `<start_of_turn>model`, so its completions begin with a newline or colon.

On the pod, greedy, the 20 Gemma diagnostic prompts with the standard template minus its final newline.
Supported if most completions then begin with a newline or colon, as every Novita completion did.
Also reports the first divergence from the API completions saved in diagnostic_tf.json (Novita is not
deterministic at temperature 0, so that comparison is indicative only).

  python template_test.py --pod POD_ID --key-file PATH   -> template_test.json
"""
import argparse, json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import diagnostic as D
from diagnostic_tf import get

ap = argparse.ArgumentParser(); ap.add_argument("--pod", required=True); ap.add_argument("--key-file", required=True)
a = ap.parse_args()
base, auth = f"https://{a.pod}-8000.proxy.runpod.net", {"Authorization": f"Bearer {Path(a.key_file).read_text().strip()}"}
rows = [r for r in D.select([json.loads(l) for l in D.REPLAY.open()]) if r["openrouter_id"] == "google/gemma-3-27b-it"]
api = {r["cell_id"]: r for r in json.loads((HERE / "diagnostic_tf.json").read_text())["results"]}
D.post(f"{base}/load", {"model": "google/gemma-3-27b-it"}, auth, timeout=90)
while get(f"{base}/health", auth).get("loaded") != "google/gemma-3-27b-it":
    time.sleep(15)
out = []
for i in range(0, len(rows), 10):
    chunk = rows[i:i + 10]
    jid = D.post(f"{base}/generate_batch", {"items": [{"messages": r["messages"], "strip_trailing_newline": True} for r in chunk],
                                            "max_tokens": 40, "temperature": 0, "seed": 0}, auth, timeout=60)["job"]
    while (j := get(f"{base}/job/{jid}", auth)).get("status") not in ("done", "error"):
        time.sleep(5)
    for r, res in zip(chunk, j["results"]):
        ka = D.post(f"{base}/tokenize", {"text": api[r["cell_id"]]["api_text_head"]}, auth).get("ids") or []
        out.append({"cell_id": r["cell_id"], "pod_head": res["text"][:80], "api_head": api[r["cell_id"]]["api_text_head"][:80],
                    "pod_starts_newline_or_colon": res["text"][:1] in "\n:",
                    "first_divergence_vs_api": D.first_divergence(ka[:len(res["ids"])], res["ids"][:len(ka)])})
summary = {"n": len(out), "pod_starts_newline_or_colon": sum(o["pod_starts_newline_or_colon"] for o in out),
           "first_divergence": sorted((o["first_divergence_vs_api"] if o["first_divergence_vs_api"] is not None else 99) for o in out)}
(HERE / "template_test.json").write_text(json.dumps({"summary": summary, "results": out}, indent=1, ensure_ascii=False) + "\n")
print(json.dumps(summary))
