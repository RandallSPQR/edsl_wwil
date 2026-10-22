"""Phase 2 pod server: the frozen identity-check server (`pod_server.py`, imported unchanged: same loader and the
same `render`, i.e. the renderings of PREREG_PHASE2 section 2) plus the probe stage's endpoints (Addendum 1).

  POST /extract_batch {"items": [...], "slug", "shard"} -> {"job"}; per item, one unpadded forward pass (batch 1,
       bf16, no cache); forward hooks on every decoder block record the block output (0-based block index L) at the
       last prompt token, and its mean over the tokens of the note's belief lines. Saved float32 to
       /workspace/phase2/probe/<slug>/shard_<shard>.npz (last, span: N x n_layers x d; item_ids; prompt_count;
       span_tokens). An existing shard with the same item ids is kept (resume).
  POST /analyse {"slug", "candidates", "n_boot", "seed"} -> {"job"}; runs phase2_probe.analyse on the saved
       activations; writes probe_result.json and vectors.npz (v_L and c_L at every layer, frozen wording) beside them.
  GET  /env                      -> package versions, GPU, loaded model, number of decoder blocks
  GET  /file/<slug>/<name>       -> a result file under /workspace/phase2/probe (json or npz bytes)
Every request carries `Authorization: Bearer $POD_KEY`, as before.
"""
import json, os, re, sys, threading, uuid
from http.server import ThreadingHTTPServer
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pod_server as S                       # frozen: load, render, STATE, LOCK, JOBS, H

OUT = Path("/workspace/phase2/probe")
SLUG = re.compile(r"^[a-z0-9.\-]+$")


def blocks():
    """The decoder blocks of the loaded text model (not a vision tower)."""
    model = S.STATE["model"]
    cfg = getattr(model.config, "text_config", model.config)
    n = cfg.num_hidden_layers
    found = [(name, m) for name, m in model.named_modules()
             if isinstance(m, torch.nn.ModuleList) and name.endswith("layers") and len(m) == n and "vision" not in name]
    if len(found) != 1:
        raise RuntimeError(f"expected one decoder ModuleList of length {n}, found {[f[0] for f in found]}")
    return found[0][1]


def belief_token_span(text, ids, block):
    """Token indices whose characters overlap the belief block (which must occur once in the rendered text)."""
    if text.count(block) != 1:
        raise ValueError("belief block not found exactly once in the rendered prompt")
    s = text.index(block); e = s + len(block)
    enc = S.STATE["tok"](text, add_special_tokens=False, return_offsets_mapping=True)
    if enc["input_ids"] != ids:
        raise ValueError("offset tokenization differs from render()")
    toks = [i for i, (a, b) in enumerate(enc["offset_mapping"]) if a < e and b > s]
    if not toks:
        raise ValueError("empty belief span")
    return toks[0], toks[-1] + 1


def extract(items):
    layers = blocks()
    grabbed = {}

    def hook(L):
        def f(_m, _inp, out):
            grabbed[L] = out[0] if isinstance(out, tuple) else out
        return f
    handles = [layer.register_forward_hook(hook(L)) for L, layer in enumerate(layers)]
    last, span, counts, spans = [], [], [], []
    try:
        for k, it in enumerate(items):
            text, ids = S.render(it["messages"], it.get("strip_llama_date", False), it.get("strip_trailing_newline", False))
            a, b = belief_token_span(text, ids, it["belief_block"])
            grabbed.clear()
            x = torch.tensor([ids], device="cuda")
            with torch.no_grad():
                out = S.STATE["model"](input_ids=x, attention_mask=torch.ones_like(x), use_cache=False,
                                       output_hidden_states=(k == 0))
            h = torch.stack([grabbed[L][0] for L in range(len(layers))]).float()     # n_layers x T x d
            if k == 0:   # self-check: block L's hook output is hidden_states[L + 1] (the last entry is after the final norm)
                hs = out.hidden_states
                for L in range(len(layers) - 1):
                    if not torch.equal(hs[L + 1][0].float(), h[L]):
                        raise RuntimeError(f"hook output of block {L} differs from hidden_states[{L + 1}]")
            last.append(h[:, -1, :].cpu().numpy()); span.append(h[:, a:b, :].mean(1).cpu().numpy())
            counts.append(len(ids)); spans.append([a, b])
    finally:
        for hd in handles:
            hd.remove()
    return np.stack(last), np.stack(span), counts, spans


def run_extract(body):
    slug, shard, items = body["slug"], int(body["shard"]), body["items"]
    if not SLUG.match(slug):
        raise ValueError("bad slug")
    d = OUT / slug; d.mkdir(parents=True, exist_ok=True)
    path = d / f"shard_{shard:04d}.npz"
    ids = [it["item_id"] for it in items]
    if path.exists():
        z = np.load(path)
        if list(z["item_ids"]) == ids:
            return {"status": "done", "kept": True, "n": len(ids), "shape": list(z["last"].shape)}
    last, span, counts, spans = extract(items)
    tmp = d / f".shard_{shard:04d}.tmp.npz"
    np.savez(tmp, last=last, span=span, item_ids=np.array(ids), prompt_count=np.array(counts), span_tokens=np.array(spans))
    tmp.rename(path)
    return {"status": "done", "kept": False, "n": len(ids), "shape": list(last.shape),
            "prompt_count": [min(counts), max(counts)], "span_len": [min(b - a for a, b in spans), max(b - a for a, b in spans)]}


def load_acts(slug, key="last"):
    """All shards of a model, in shard order: (N x n_layers x d float32, item ids)."""
    zs = [np.load(p) for p in sorted((OUT / slug).glob("shard_*.npz"))]
    return np.concatenate([z[key] for z in zs]), [i for z in zs for i in z["item_ids"].tolist()]


def meta_of(item_id):
    m, cat, tgt, cond, w = item_id.split("|")
    return {"model_id": m, "category": cat, "target": tgt, "condition": cond, "wording": w}


def run_analyse(body):
    import phase2_probe as P
    slug = body["slug"]
    if not SLUG.match(slug):
        raise ValueError("bad slug")
    cands = [int(L) for L in body["candidates"]]
    X, ids = load_acts(slug)
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate items across shards")
    meta = [meta_of(i) for i in ids]
    rep, _, _ = P.analyse({L: X[:, L, :] for L in cands}, meta, cands, n_boot=int(body.get("n_boot", P.N_BOOT)),
                          seed=int(body.get("seed", P.BOOT_SEED)))
    # v_L and c_L at every layer (frozen wording), for the record and for the steering stages
    n_layers = X.shape[1]
    ix = P.Index(meta)
    f, r = ix.pairs("frozen"); p = ix.sel("placebo", "frozen")
    V = np.stack([(X[f, L].astype(np.float64) - X[r, L]).mean(0) for L in range(n_layers)])
    Cc = np.stack([X[np.concatenate([f, r]), L].astype(np.float64).mean(0) - X[p, L].mean(0) for L in range(n_layers)])
    np.savez(OUT / slug / "vectors.npz", v=V, c=Cc)
    rep.update(slug=slug, n_items=len(ids), n_layers=int(n_layers), per_layer={str(k): v for k, v in rep["per_layer"].items()})
    (OUT / slug / "probe_result.json").write_text(json.dumps(rep, indent=1))
    return {"status": "done", "result": rep}


def env():
    import importlib.metadata as md
    vers = {}
    for p in ("torch", "transformers", "accelerate", "numpy", "sae-ethos-pipeline"):
        try:
            vers[p] = md.version(p)
        except md.PackageNotFoundError:
            vers[p] = None
    out = {"versions": vers, "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
           "loaded": S.STATE["id"], "cuda": torch.version.cuda}
    if S.STATE["model"] is not None:
        out["n_blocks"] = len(blocks())
    return out


def job(fn, body):
    jid = uuid.uuid4().hex
    S.JOBS[jid] = {"status": "running"}

    def work():
        try:
            with S.LOCK:
                S.JOBS[jid] = fn(body)
        except Exception as e:  # noqa: BLE001
            S.JOBS[jid] = {"status": "error", "error": f"{type(e).__name__}: {str(e)[:300]}"}
    threading.Thread(target=work, daemon=True).start()
    return jid


class H2(S.H):
    def do_GET(self):
        if self.path == "/env":
            return self._auth() and self._send(200, env())
        if self.path.startswith("/file/"):
            if not self._auth():
                return
            parts = self.path[len("/file/"):].split("/")
            if len(parts) != 2 or not SLUG.match(parts[0]) or parts[1] not in ("probe_result.json", "vectors.npz"):
                return self._send(404, {"error": "unknown file"})
            p = OUT / parts[0] / parts[1]
            if not p.exists():
                return self._send(404, {"error": "missing"})
            b = p.read_bytes()
            self.send_response(200); self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
            return
        return super().do_GET()

    def do_POST(self):
        if self.path not in ("/extract_batch", "/analyse"):
            return super().do_POST()
        if not self._auth():
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            if self.path == "/extract_batch" and S.STATE["model"] is None:
                return self._send(409, {"error": "no model loaded"})
            return self._send(200, {"job": job(run_extract if self.path == "/extract_batch" else run_analyse, body)})
        except Exception as e:  # noqa: BLE001
            self._send(500, {"error": f"{type(e).__name__}: {str(e)[:300]}"})


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8000), H2).serve_forever()
