"""Minimal model server for the Phase 2 identity check, run on the pod (HF transformers, bf16).

Why transformers and not vLLM: Phase 2 reads activations with transformers, and vLLM v0.9.2 produced
degenerate Gemma 3 output on the first pod (DIAGNOSTIC_SUMMARY.md). Every request must carry
`Authorization: Bearer $POD_KEY`. One model is loaded at a time.

Endpoints (JSON):
  GET  /health                         -> {"loaded": model id or null}
  POST /load      {"model"}            -> loads it (unloads the previous one); weights are looked up
                                          under /workspace first (network volume), else downloaded
  POST /render    {"messages", "strip_llama_date"} -> {"prompt": text, "ids": [...], "count"}
  POST /generate  {"messages", "max_tokens", "strip_llama_date"} -> {"job": id}; greedy generation runs
                                          in the background (the RunPod proxy cuts requests at ~100 s)
  GET  /job/<id>                       -> {"status": "running"} or the result: text, ids, prompt_count, finish
  POST /generate_batch {"items": [{"messages", "strip_llama_date", "strip_trailing_newline"}],
                        "max_tokens", "temperature", "top_p", "seed"} -> {"job": id}; the result holds one
                                          {text, ids, prompt_count, finish} per item, in order. Left-padded
                                          batch; temperature 0 is greedy; the torch seed is set once per batch.
  POST /tokenize  {"text"}             -> {"ids": [...]} (no special tokens)

strip_llama_date removes the "Cutting Knowledge Date / Today Date" lines that the Llama 3.1 chat
template inserts into the system turn (the API provider renders without them).
"""
import gc, json, os, threading, uuid
os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")   # torch 2.4's dynamo cannot compile Gemma 3's hybrid cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

KEY = os.environ["POD_KEY"]
LLAMA_DATE = "Cutting Knowledge Date: December 2023\nToday Date: 26 Jul 2024\n\n"
STATE = {"id": None, "model": None, "tok": None}
LOCK = threading.Lock()
JOBS = {}


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


def render(messages, strip, strip_trailing_newline=False):
    text = STATE["tok"].apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    if strip:
        text = text.replace(LLAMA_DATE, "", 1)
    if strip_trailing_newline and text.endswith("\n"):
        text = text[:-1]   # template-end test: a provider that omits the newline after the model-turn marker
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


def generate_batch(items, max_tokens, temperature, top_p, seed):
    tok, model = STATE["tok"], STATE["model"]
    rendered = [render(it["messages"], it.get("strip_llama_date", False), it.get("strip_trailing_newline", False))[1]
                for it in items]
    pad = tok.pad_token_id if tok.pad_token_id is not None else (tok.eos_token_id if isinstance(tok.eos_token_id, int) else tok.eos_token_id[0])
    width = max(len(r) for r in rendered)
    x = torch.tensor([[pad] * (width - len(r)) + r for r in rendered], device="cuda")
    mask = torch.tensor([[0] * (width - len(r)) + [1] * len(r) for r in rendered], device="cuda")
    kw = dict(do_sample=False, temperature=None, top_p=None, top_k=None) if not temperature else \
        dict(do_sample=True, temperature=float(temperature), top_p=float(top_p), top_k=0)
    torch.manual_seed(int(seed))
    with torch.no_grad():
        out = model.generate(input_ids=x, attention_mask=mask, max_new_tokens=int(max_tokens), pad_token_id=pad, **kw)
    eos = tok.eos_token_id
    eos = set(eos if isinstance(eos, list) else [eos]) | set(getattr(model.generation_config, "eos_token_id", None) or [])
    res = []
    for i, r in enumerate(rendered):
        new = out[i, width:].tolist()
        stop = next((k for k, t in enumerate(new) if t in eos), None)
        ids = new[:stop] if stop is not None else new
        res.append({"text": tok.decode(ids, skip_special_tokens=True), "ids": ids, "prompt_count": len(r),
                    "finish": "stop" if stop is not None else "length"})
    return res


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
        if not self._auth():
            return
        if self.path.startswith("/job/"):
            j = JOBS.get(self.path[len("/job/"):])
            return self._send(200 if j is not None else 404, j if j is not None else {"error": "unknown job"})
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
                jid = uuid.uuid4().hex
                JOBS[jid] = {"status": "running"}

                def work(jid=jid, body=body):
                    try:
                        with LOCK:
                            JOBS[jid] = {"status": "done", **generate(body["messages"], int(body["max_tokens"]), body.get("strip_llama_date", False))}
                    except Exception as e:  # noqa: BLE001
                        JOBS[jid] = {"status": "error", "error": f"{type(e).__name__}: {str(e)[:300]}"}
                threading.Thread(target=work, daemon=True).start()
                return self._send(200, {"job": jid})
            if self.path == "/generate_batch":
                jid = uuid.uuid4().hex
                JOBS[jid] = {"status": "running"}

                def work_batch(jid=jid, body=body):
                    try:
                        with LOCK:
                            JOBS[jid] = {"status": "done", "results": generate_batch(
                                body["items"], body["max_tokens"], body.get("temperature", 0), body.get("top_p", 1.0), body.get("seed", 0))}
                    except Exception as e:  # noqa: BLE001
                        JOBS[jid] = {"status": "error", "error": f"{type(e).__name__}: {str(e)[:300]}"}
                threading.Thread(target=work_batch, daemon=True).start()
                return self._send(200, {"job": jid})
            if self.path == "/tokenize":
                return self._send(200, {"ids": STATE["tok"](body["text"], add_special_tokens=False)["input_ids"]})
            self._send(404, {"error": "unknown path"})
        except Exception as e:  # noqa: BLE001
            self._send(500, {"error": f"{type(e).__name__}: {str(e)[:300]}"})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8000), H).serve_forever()
