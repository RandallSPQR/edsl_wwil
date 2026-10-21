"""Minimal model server for the Phase 2 identity check, run on the pod (HF transformers, bf16).

Why transformers and not vLLM: Phase 2 reads activations with transformers, and vLLM v0.9.2 produced
degenerate Gemma 3 output on the first pod (DIAGNOSTIC_SUMMARY.md). Every request must carry
`Authorization: Bearer $POD_KEY`. One model is loaded at a time.

Endpoints (JSON):
  GET  /health                         -> {"loaded": model id or null}
  POST /load      {"model"}            -> loads it (unloads the previous one); weights are looked up
                                          under /workspace first (network volume), else downloaded
  POST /render    {"messages", "strip_llama_date"} -> {"prompt": text, "ids": [...], "count"}
  POST /generate  {"messages", "max_tokens", "strip_llama_date"} -> greedy completion: text, ids
  POST /tokenize  {"text"}             -> {"ids": [...]} (no special tokens)

strip_llama_date removes the "Cutting Knowledge Date / Today Date" lines that the Llama 3.1 chat
template inserts into the system turn (the API provider renders without them).
"""
import gc, json, os, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

KEY = os.environ["POD_KEY"]
LLAMA_DATE = "Cutting Knowledge Date: December 2023\nToday Date: 26 Jul 2024\n\n"
STATE = {"id": None, "model": None, "tok": None}
LOCK = threading.Lock()


def cache_dir_for(model_id):
    """A local HF cache that already holds this model (e.g. on the network volume), if any."""
    name = "models--" + model_id.replace("/", "--")
    for root in ("/workspace", "/root/.cache/huggingface"):
        for p in Path(root).rglob(name) if Path(root).exists() else []:
            if (p / "snapshots").exists():
                return str(p.parent)
    return None


def load(model_id):
    with LOCK:
        if STATE["id"] == model_id:
            return
        STATE.update(id=None, model=None, tok=None); gc.collect(); torch.cuda.empty_cache()
        cd = cache_dir_for(model_id)
        tok = AutoTokenizer.from_pretrained(model_id, cache_dir=cd)
        if "gemma-3" in model_id:
            from transformers import Gemma3ForConditionalGeneration as M
        else:
            M = AutoModelForCausalLM
        model = M.from_pretrained(model_id, cache_dir=cd, torch_dtype=torch.bfloat16, device_map="cuda").eval()
        STATE.update(id=model_id, model=model, tok=tok, cache_dir=cd)


def render(messages, strip):
    text = STATE["tok"].apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    if strip:
        text = text.replace(LLAMA_DATE, "", 1)
    ids = STATE["tok"](text, add_special_tokens=False)["input_ids"]
    return text, ids


def generate(messages, max_tokens, strip):
    text, ids = render(messages, strip)
    x = torch.tensor([ids], device="cuda")
    with torch.no_grad():
        out = STATE["model"].generate(input_ids=x, attention_mask=torch.ones_like(x), max_new_tokens=max_tokens,
                                      do_sample=False, temperature=None, top_p=None, top_k=None)
    new = out[0, len(ids):].tolist()
    eos = STATE["tok"].eos_token_id
    eos = set(eos if isinstance(eos, list) else [eos]) | set(getattr(STATE["model"].generation_config, "eos_token_id", None) or [])
    finish = "stop" if new and new[-1] in eos else "length"
    if new and new[-1] in eos:
        new = new[:-1]
    return {"text": STATE["tok"].decode(new, skip_special_tokens=True), "ids": new, "prompt_count": len(ids), "finish": finish}


class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def _auth(self):
        if self.headers.get("Authorization") != f"Bearer {KEY}":
            self._send(401, {"error": "unauthorized"}); return False
        return True

    def do_GET(self):
        if self._auth():
            self._send(200, {"loaded": STATE["id"], "cache_dir": STATE.get("cache_dir"),
                             "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None})

    def do_POST(self):
        if not self._auth():
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            if self.path == "/load":
                load(body["model"]); return self._send(200, {"loaded": STATE["id"], "cache_dir": STATE.get("cache_dir")})
            if STATE["model"] is None:
                return self._send(409, {"error": "no model loaded"})
            if self.path == "/render":
                text, ids = render(body["messages"], body.get("strip_llama_date", False))
                return self._send(200, {"prompt": text, "ids": ids, "count": len(ids)})
            if self.path == "/generate":
                with LOCK:
                    return self._send(200, generate(body["messages"], int(body["max_tokens"]), body.get("strip_llama_date", False)))
            if self.path == "/tokenize":
                return self._send(200, {"ids": STATE["tok"](body["text"], add_special_tokens=False)["input_ids"]})
            self._send(404, {"error": "unknown path"})
        except Exception as e:  # noqa: BLE001
            self._send(500, {"error": f"{type(e).__name__}: {str(e)[:300]}"})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8000), H).serve_forever()
