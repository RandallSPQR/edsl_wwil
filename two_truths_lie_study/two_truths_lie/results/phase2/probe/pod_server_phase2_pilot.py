"""Phase 2 stage 1 pod server (Addendum 4): the probe-stage server (`pod_server_phase2.py`, imported unchanged, which
imports the frozen `pod_server.py`) plus the steering extension of section 6.

  POST /pilot_prepare {"slug", "layer", "placebo_seed"} -> {v_norm, cos_v_placebo, n_train}; the steering direction
       unit(v_L) (vectors.npz, the probe stage's v) and the covariance-matched placebo: pipeline
       `probe.vectors.placebo_cov(Xc, seed)` with Xc the centred last-token block-L outputs of the frozen full and
       reversed training items. Saved to /workspace/phase2/probe/<slug>/pilot_vectors.npz.
  POST /hook_check {"slug", "item", "kind", "coef"} -> one prompt's forward pass with and without the steering hook.
       Exact checks (bf16, bitwise): the hook's output equals its input plus the added vector in the block's dtype; the
       model carries that output forward (hidden_states[L + 1] of the steered pass); the hook saw every prompt position;
       and block L's input (hidden_states[L]) is unchanged by steering (relative difference < 1e-3). Descriptive: the
       steered minus unsteered hidden_states[L + 1] against coef x unit(d) (relative error, cosine), i.e. the precision
       of bf16 steering.
  POST /generate_steered {"items", "max_tokens", "temperature", "top_p", "seed", "slug", "kind", "coef"} -> {"job"};
       the frozen `generate_batch`, with a forward hook on decoder block L that adds coef x unit(d) to the block's
       output at every position (prompt and generated), d = v (kind "steered") or the placebo (kind "placebo");
       kind "none" runs it unhooked.
  POST /nll {"items", "conts"} -> {"job"}; per item, one unpadded unsteered forward pass of prompt + cont; the per-token
       NLL of cont (teacher-forced). The caller sends the first 64 generated tokens.
Every request carries `Authorization: Bearer $POD_KEY`, as before.
"""
import json, sys
from http.server import ThreadingHTTPServer
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pod_server_phase2 as S2               # unchanged: blocks, load_acts, meta_of, job, H2, OUT, SLUG
import pod_server as S                       # frozen: STATE, render, generate_batch


def _vectors(slug):
    if not S2.SLUG.match(slug):
        raise ValueError("bad slug")
    z = np.load(S2.OUT / slug / "pilot_vectors.npz")
    return int(z["layer"]), {"steered": z["v_unit"], "placebo": z["placebo_unit"]}


def run_prepare(body):
    import sae_ethos_pipeline  # noqa: F401  (puts the pipeline's import root on sys.path)
    from probe.vectors import placebo_cov
    slug, L, seed = body["slug"], int(body["layer"]), int(body["placebo_seed"])
    if not S2.SLUG.match(slug):
        raise ValueError("bad slug")
    X, ids = S2.load_acts(slug)
    meta = [S2.meta_of(i) for i in ids]
    keep = [k for k, m in enumerate(meta) if m["wording"] == "frozen" and m["condition"] in ("full", "reversed")]
    H = X[keep, L, :].astype(np.float64)
    Xc = H - H.mean(0)
    p = placebo_cov(Xc, seed)
    v = np.load(S2.OUT / slug / "vectors.npz")["v"][L].astype(np.float64)
    vn = float(np.linalg.norm(v))
    np.savez(S2.OUT / slug / "pilot_vectors.npz", layer=L, v_unit=v / vn, v_norm=vn, placebo_unit=p, placebo_seed=seed)
    return {"status": "done", "v_norm": vn, "cos_v_placebo": float(p @ (v / vn)), "placebo_norm": float(np.linalg.norm(p)),
            "n_train": len(keep)}


class Steer:
    """Context manager: a forward hook on decoder block L adding `add` (d,) to the block output at every position.
    With `record` (a dict), the hook also stores its input and output (for the hook check only)."""
    def __init__(self, L, add, record=None):
        self.L, self.add, self.record = L, add, record

    def __enter__(self):
        a = torch.as_tensor(self.add, dtype=torch.float32, device="cuda")
        rec = self.record

        def fn(_m, _inp, out):
            hs = out[0] if isinstance(out, tuple) else out
            hs2 = hs + a.to(hs.dtype)
            if rec is not None:
                rec["in"], rec["out"], rec["a"] = hs.detach().clone(), hs2.detach().clone(), a.to(hs.dtype)
            return (hs2,) + tuple(out[1:]) if isinstance(out, tuple) else hs2
        self.h = S2.blocks()[self.L].register_forward_hook(fn)
        return self

    def __exit__(self, *exc):
        self.h.remove()


def _add(slug, kind, coef):
    L, d = _vectors(slug)
    if kind not in d:
        raise ValueError(f"unknown kind {kind}")
    return L, float(coef) * d[kind]


def no_hooks():
    if any(len(b._forward_hooks) for b in S2.blocks()):
        raise RuntimeError("a forward hook is still registered on a decoder block")


def run_hook_check(body):
    L, add = _add(body["slug"], body["kind"], body["coef"])
    it = body["item"]
    _, ids = S.render(it["messages"], it.get("strip_llama_date", False), it.get("strip_trailing_newline", False))
    x = torch.tensor([ids], device="cuda")
    no_hooks()
    rec = {}
    with torch.no_grad():
        hs0 = S.STATE["model"](input_ids=x, output_hidden_states=True, use_cache=False).hidden_states
        with Steer(L, add, rec):
            hs1 = S.STATE["model"](input_ids=x, output_hidden_states=True, use_cache=False).hidden_states
    no_hooks()
    exact_add = bool(torch.equal(rec["out"], rec["in"] + rec["a"]))
    carried = bool(torch.equal(hs1[L + 1], rec["out"]))
    positions = int(rec["in"].shape[1])
    before = float((hs1[L].float() - hs0[L].float()).norm() / (hs0[L].float().norm() + 1e-12))
    diff = (hs1[L + 1][0].float() - hs0[L + 1][0].float()).cpu().numpy().astype(np.float64)
    target = np.asarray(add, np.float64)
    rel = np.linalg.norm(diff - target[None, :], axis=1) / np.linalg.norm(target)
    cos = diff @ target / (np.linalg.norm(diff, axis=1) * np.linalg.norm(target) + 1e-12)
    passes = exact_add and carried and positions == len(ids) and before < 1e-3
    return {"status": "done", "layer": L, "passes": passes, "exact_add": exact_add, "carried_forward": carried,
            "positions": positions, "prompt_tokens": len(ids), "block_input_rel_change": before,
            "rel_err_max": float(rel.max()), "rel_err_median": float(np.median(rel)), "argmax_rel_err_position": int(rel.argmax()),
            "cos_min": float(cos.min()), "add_norm": float(np.linalg.norm(target))}


def run_generate(body):
    kind = body["kind"]
    args = (body["items"], body["max_tokens"], body.get("temperature", 0), body.get("top_p", 1.0), body.get("seed", 0))
    no_hooks()
    if kind == "none":
        res = S.generate_batch(*args)
    else:
        L, add = _add(body["slug"], kind, body["coef"])
        with Steer(L, add):
            res = S.generate_batch(*args)
    no_hooks()
    return {"status": "done", "results": res}


def run_nll(body):
    no_hooks()
    out = []
    for it, cont in zip(body["items"], body["conts"]):
        _, ids = S.render(it["messages"], it.get("strip_llama_date", False), it.get("strip_trailing_newline", False))
        if not cont:
            out.append([]); continue
        x = torch.tensor([ids + list(cont)], device="cuda")
        with torch.no_grad():
            lg = S.STATE["model"](input_ids=x, use_cache=False).logits[0].float()
        lp = torch.log_softmax(lg, -1)
        n = len(ids)
        out.append([float(-lp[n - 1 + j, t]) for j, t in enumerate(cont)])
    return {"status": "done", "nll": out}


class H5(S2.H2):
    ROUTES = {"/pilot_prepare": run_prepare, "/hook_check": run_hook_check, "/generate_steered": run_generate,
              "/nll": run_nll}

    def do_POST(self):
        fn = self.ROUTES.get(self.path)
        if fn is None:
            return super().do_POST()
        if not self._auth():
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            if self.path != "/pilot_prepare" and S.STATE["model"] is None:
                return self._send(409, {"error": "no model loaded"})
            return self._send(200, {"job": S2.job(fn, body)})
        except Exception as e:  # noqa: BLE001
            self._send(500, {"error": f"{type(e).__name__}: {str(e)[:300]}"})


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8000), H5).serve_forever()
