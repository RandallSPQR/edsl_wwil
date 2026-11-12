"""Phase 2 steering-scale pod server: the Addendum 3 server (`pod_server_phase2_diag.py`, imported unchanged) plus one
endpoint for the per-persona scale report on the stored activations. No model is loaded.

  POST /scale {"slug", "layers"} -> {"job"}; runs phase2_scale.scale_report on /workspace/phase2/probe/<slug>/
       (last-token activations and the probe stage's vectors.npz); writes scale.json there.
  GET  /file/<slug>/scale.json  -> that file
Every request carries `Authorization: Bearer $POD_KEY`, as before.
"""
import json, sys
from http.server import ThreadingHTTPServer
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pod_server_phase2_diag as S3          # unchanged
import pod_server_phase2 as S2               # unchanged


def run_scale(body):
    import phase2_scale as SC
    slug = body["slug"]
    if not S2.SLUG.match(slug):
        raise ValueError("bad slug")
    layers = [int(L) for L in body["layers"]]
    X, ids = S2.load_acts(slug)
    meta = [S2.meta_of(i) for i in ids]
    V = np.load(S2.OUT / slug / "vectors.npz")["v"]
    rep = SC.scale_report({L: X[:, L, :] for L in layers}, meta, layers, V)
    rep.update(slug=slug, n_items=len(ids))
    (S2.OUT / slug / "scale.json").write_text(json.dumps(rep, indent=1))
    return {"status": "done"}


class H4(S3.H3):
    def do_GET(self):
        parts = self.path[len("/file/"):].split("/") if self.path.startswith("/file/") else []
        if len(parts) == 2 and parts[1] == "scale.json":
            if not self._auth():
                return
            p = S2.OUT / parts[0] / parts[1]
            if not S2.SLUG.match(parts[0]) or not p.exists():
                return self._send(404, {"error": "missing"})
            b = p.read_bytes()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
            return
        return super().do_GET()

    def do_POST(self):
        if self.path != "/scale":
            return super().do_POST()
        if not self._auth():
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            return self._send(200, {"job": S2.job(run_scale, body)})
        except Exception as e:  # noqa: BLE001
            self._send(500, {"error": f"{type(e).__name__}: {str(e)[:300]}"})


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8000), H4).serve_forever()
