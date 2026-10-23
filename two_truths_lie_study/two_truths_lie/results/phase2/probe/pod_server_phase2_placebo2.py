"""Phase 2 Addendum 5 pod server: the stage-1 pilot server (`pod_server_phase2_pilot.py`, imported unchanged) with the
retired placebo replaced by the Addendum 5 placebo.

  POST /placebo2_prepare {"slug", "layer", "placebo_seed"} -> the new placebo, saved with unit(v_L) to
       /workspace/phase2/probe/<slug>/pilot_vectors_v2.npz (the retired pilot_vectors.npz is left as it is):
       H = last-token block-L outputs of the 400 frozen full and reversed training items; Xc = H with each condition
       centred on its own mean (removes the full - reversed difference); p = pipeline probe.vectors.placebo_cov(Xc,
       seed); p minus its component along unit(v); renormalised to unit length. The added vector is then
       sign x alpha x ||v_L|| x unit(p), the same length as the steered one.
       Returns cos(unit p, v) after the projection (target 0), before it (after the centring), cos with the retired
       placebo, and the norm match ||alpha ||v|| unit(p)|| / ||alpha ||v|| unit(v)||.
Every other endpoint is the pilot server's, reading pilot_vectors_v2.npz instead of pilot_vectors.npz, so /hook_check
and /generate_steered with kind "placebo" use the new placebo and kind "steered" the same unit(v) as before.
"""
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pod_server_phase2_pilot as P1         # unchanged
import pod_server_phase2 as S2               # unchanged


def _vectors_v2(slug):
    if not S2.SLUG.match(slug):
        raise ValueError("bad slug")
    z = np.load(S2.OUT / slug / "pilot_vectors_v2.npz")
    return int(z["layer"]), {"steered": z["v_unit"], "placebo": z["placebo_unit"]}


P1._vectors = _vectors_v2                    # every pilot endpoint now reads the Addendum 5 vectors


def run_prepare2(body):
    import sae_ethos_pipeline  # noqa: F401  (puts the pipeline's import root on sys.path)
    from probe.vectors import placebo_cov
    slug, L, seed = body["slug"], int(body["layer"]), int(body["placebo_seed"])
    if not S2.SLUG.match(slug):
        raise ValueError("bad slug")
    X, ids = S2.load_acts(slug)
    meta = [S2.meta_of(i) for i in ids]
    Xc = []
    for cond in ("full", "reversed"):
        k = [i for i, m in enumerate(meta) if m["wording"] == "frozen" and m["condition"] == cond]
        H = X[k, L, :].astype(np.float64)
        Xc.append(H - H.mean(0))
    Xc = np.concatenate(Xc)
    v = np.load(S2.OUT / slug / "vectors.npz")["v"][L].astype(np.float64)
    vn = float(np.linalg.norm(v)); u = v / vn
    p0 = placebo_cov(Xc, seed)
    p = p0 - (p0 @ u) * u
    p = p / np.linalg.norm(p)
    old = np.load(S2.OUT / slug / "pilot_vectors.npz")["placebo_unit"]
    np.savez(S2.OUT / slug / "pilot_vectors_v2.npz", layer=L, v_unit=u, v_norm=vn, placebo_unit=p, placebo_seed=seed)
    return {"status": "done", "v_norm": vn, "n_train": int(Xc.shape[0]), "cos_v_placebo": float(p @ u),
            "cos_v_placebo_before_projection": float(p0 @ u / np.linalg.norm(p0)), "cos_retired_placebo": float(p @ old),
            "norm_match": float(np.linalg.norm(vn * p) / np.linalg.norm(vn * u))}


class H6(P1.H5):
    def do_POST(self):
        if self.path != "/placebo2_prepare":
            return super().do_POST()
        if not self._auth():
            return
        import json
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            return self._send(200, {"job": S2.job(run_prepare2, body)})
        except Exception as e:  # noqa: BLE001
            self._send(500, {"error": f"{type(e).__name__}: {str(e)[:300]}"})


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8000), H6).serve_forever()
