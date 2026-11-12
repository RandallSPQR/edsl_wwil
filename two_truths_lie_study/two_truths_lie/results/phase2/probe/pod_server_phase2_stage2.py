"""Phase 2 stage-2 pod server (Addendum 7): the Addendum 5 server (`pod_server_phase2_placebo2.py`, imported unchanged:
the pilot's endpoints with the main-test placebo orthogonal to v) plus the method check's vectors and the naturalness
activations.

  POST /mc_prepare {"slug", "layer", "seeds": {target: seed}} -> per target t, at block L (the selected layer):
       v_fp,t = mean over the 40 training categories of h(full note of t) - h(the placebo note t receives), frozen
       wording, last prompt token. The placebo: Addendum 5's procedure with v_fp,t in place of v (the full and
       reversed training items, each condition centred on its own mean; pipeline probe.vectors.placebo_cov(., seed_t);
       the component along unit v_fp,t projected out; renormalised). Added vectors: alpha x ||v_fp,t|| x unit(v_fp,t)
       or unit(placebo_fp,t). Saved to /workspace/phase2/probe/<slug>/mc_vectors.npz. Returns per target ||v_fp,t||,
       ||v_fp,t|| / ||v||, cos(v_fp,t, v), cos(placebo_fp,t, v_fp,t) (target 0), the norm match, cos with the main
       placebo.
  Generation kinds: "steered" and "placebo" (main test, as before); "mc_steered:<t>" and "mc_placebo:<t>".
  POST /natural {"slug", "layer", "full": [items], "reversed": [items], "first_full": [ids], "first_reversed": [ids]}
       -> paired by position: the mean over pairs of h_full - h_reversed at block L at the last prompt token, and at
       the first generated token (one forward pass of prompt + the reference lie's first token, read at that token);
       cos of each with v, norms; the two vectors are saved to natural.npz.
Every request carries `Authorization: Bearer $POD_KEY`, as before.
"""
import json, sys
from http.server import ThreadingHTTPServer
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pod_server_phase2_placebo2 as P2      # unchanged (it points the pilot's vector lookup at pilot_vectors_v2.npz)
import pod_server_phase2_pilot as P1         # unchanged
import pod_server_phase2 as S2               # unchanged
import pod_server as S                       # frozen

TARGETS = ("P1", "P2", "P3", "P5", "P6")


def _vectors_stage2(slug):
    L, d = P2._vectors_v2(slug)
    p = S2.OUT / slug / "mc_vectors.npz"
    if p.exists():
        z = np.load(p)
        if int(z["layer"]) != L:
            raise ValueError("method-check vectors were built at another layer")
        for i, t in enumerate(z["targets"].tolist()):
            d[f"mc_steered:{t}"] = z["vfp_unit"][i]
            d[f"mc_placebo:{t}"] = z["pfp_unit"][i]
    return L, d


P1._vectors = _vectors_stage2                # every pilot endpoint now also knows the method-check kinds


def run_mc_prepare(body):
    import sae_ethos_pipeline  # noqa: F401  (puts the pipeline's import root on sys.path)
    from probe.vectors import placebo_cov
    slug, L, seeds = body["slug"], int(body["layer"]), {t: int(s) for t, s in body["seeds"].items()}
    if not S2.SLUG.match(slug):
        raise ValueError("bad slug")
    X, ids = S2.load_acts(slug)
    meta = [S2.meta_of(i) for i in ids]
    idx = {(m["category"], m["target"], m["condition"]): k for k, m in enumerate(meta) if m["wording"] == "frozen"}
    cats = sorted({c for c, _, _ in idx})
    Xc = []
    for cond in ("full", "reversed"):
        H = X[[idx[(c, t, cond)] for c in cats for t in TARGETS], L, :].astype(np.float64)
        Xc.append(H - H.mean(0))
    Xc = np.concatenate(Xc)
    v = np.load(S2.OUT / slug / "vectors.npz")["v"][L].astype(np.float64)
    pmain = np.load(S2.OUT / slug / "pilot_vectors_v2.npz")["placebo_unit"]
    vu, pu, info = [], [], {}
    for t in TARGETS:
        d = np.stack([X[idx[(c, t, "full")], L, :].astype(np.float64) - X[idx[(c, t, "placebo")], L, :] for c in cats]).mean(0)
        n = float(np.linalg.norm(d)); u = d / n
        p0 = placebo_cov(Xc, seeds[t])
        p = p0 - (p0 @ u) * u
        p = p / np.linalg.norm(p)
        vu.append(u); pu.append(p)
        info[t] = {"vfp_norm": n, "vfp_over_v": n / float(np.linalg.norm(v)), "cos_vfp_v": float(u @ v / np.linalg.norm(v)),
                   "cos_placebo_vfp": float(p @ u), "cos_placebo_vfp_before_projection": float(p0 @ u / np.linalg.norm(p0)),
                   "norm_match": float(np.linalg.norm(n * p) / np.linalg.norm(n * u)), "cos_with_main_placebo": float(p @ pmain),
                   "seed": seeds[t], "n_categories": len(cats)}
    np.savez(S2.OUT / slug / "mc_vectors.npz", layer=L, targets=np.array(TARGETS), vfp_unit=np.stack(vu),
             vfp_norm=np.array([info[t]["vfp_norm"] for t in TARGETS]), pfp_unit=np.stack(pu),
             seeds=np.array([seeds[t] for t in TARGETS]))
    return {"status": "done", "targets": info}


def run_natural(body):
    slug, L = body["slug"], int(body["layer"])
    v = np.load(S2.OUT / slug / "vectors.npz")["v"][L].astype(np.float64)
    blocks = S2.blocks()
    P1.no_hooks()
    grab = {}
    h = blocks[L].register_forward_hook(lambda _m, _i, out: grab.__setitem__("h", (out[0] if isinstance(out, tuple) else out)[0]))
    try:
        def reps(items, firsts):
            last, first = [], []
            for it, ft in zip(items, firsts):
                _, ids = S.render(it["messages"], it.get("strip_llama_date", False), it.get("strip_trailing_newline", False))
                x = torch.tensor([ids + ([int(ft[0])] if ft else [])], device="cuda")
                with torch.no_grad():
                    S.STATE["model"](input_ids=x, use_cache=False)
                hs = grab["h"].float()
                last.append(hs[len(ids) - 1].cpu().numpy())
                first.append(hs[len(ids)].cpu().numpy() if ft else np.full(hs.shape[-1], np.nan, np.float32))
            return np.stack(last).astype(np.float64), np.stack(first).astype(np.float64)
        lf, ff = reps(body["full"], body["first_full"])
        lr, fr = reps(body["reversed"], body["first_reversed"])
    finally:
        h.remove()
    P1.no_hooks()
    d_last = (lf - lr).mean(0)
    ok = ~(np.isnan(ff).any(1) | np.isnan(fr).any(1))
    d_first = (ff[ok] - fr[ok]).mean(0)
    cos = lambda a: float(a @ v / (np.linalg.norm(a) * np.linalg.norm(v) + 1e-12))
    np.savez(S2.OUT / slug / "natural.npz", layer=L, d_last=d_last, d_first=d_first)
    return {"status": "done", "layer": L, "n_pairs": int(len(lf)), "n_pairs_first": int(ok.sum()),
            "cos_last_token_evaluation": cos(d_last), "cos_first_generated_token": cos(d_first),
            "norm_last": float(np.linalg.norm(d_last)), "norm_first": float(np.linalg.norm(d_first)),
            "v_norm": float(np.linalg.norm(v))}


class H7(P2.H6):
    ROUTES2 = {"/mc_prepare": run_mc_prepare, "/natural": run_natural}

    def do_POST(self):
        fn = self.ROUTES2.get(self.path)
        if fn is None:
            return super().do_POST()
        if not self._auth():
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            if self.path == "/natural" and S.STATE["model"] is None:
                return self._send(409, {"error": "no model loaded"})
            return self._send(200, {"job": S2.job(fn, body)})
        except Exception as e:  # noqa: BLE001
            self._send(500, {"error": f"{type(e).__name__}: {str(e)[:300]}"})


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8000), H7).serve_forever()
