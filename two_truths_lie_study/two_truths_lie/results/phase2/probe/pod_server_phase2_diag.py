"""Phase 2 Addendum 3 pod server: the probe-stage server (`pod_server_phase2.py`, imported unchanged, which imports
the frozen `pod_server.py`) plus one endpoint for the diagnostics on the stored activations. No model is loaded.

  POST /diagnose {"slug", "perm_layers", "candidates", "n_perm", "seed"} -> {"job"}; runs
       phase2_diagnostics.diagnose on /workspace/phase2/probe/<slug>/shard_*.npz (last-token activations), with the
       probe stage's probe_result.json beside them; writes diagnostics.json there.
  GET  /file/<slug>/diagnostics.json  -> that file
Every request carries `Authorization: Bearer $POD_KEY`, as before.
"""
import json, sys
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pod_server_phase2 as S2               # unchanged: load_acts, meta_of, job, H2, OUT, SLUG
import pod_server as S                       # frozen


def run_diagnose(body):
    import phase2_diagnostics as D
    slug = body["slug"]
    if not S2.SLUG.match(slug):
        raise ValueError("bad slug")
    perm_layers, cands = [int(L) for L in body["perm_layers"]], [int(L) for L in body["candidates"]]
    X, ids = S2.load_acts(slug)
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate items across shards")
    meta = [S2.meta_of(i) for i in ids]
    registered = json.loads((S2.OUT / slug / "probe_result.json").read_text())
    rep = D.diagnose({L: X[:, L, :] for L in sorted(set(perm_layers) | set(cands))}, meta, perm_layers, cands,
                     registered, n_perm=int(body.get("n_perm", D.N_PERM)), seed=int(body.get("seed", D.PERM_SEED)))
    rep.update(slug=slug, n_items=len(ids))
    (S2.OUT / slug / "diagnostics.json").write_text(json.dumps(rep, indent=1))
    return {"status": "done", "stop_rule": rep["stop_rule"], "observed_matches_registered": rep["observed_matches_registered"]}


class H3(S2.H2):
    def do_GET(self):
        parts = self.path[len("/file/"):].split("/") if self.path.startswith("/file/") else []
        if len(parts) == 2 and parts[1] == "diagnostics.json":
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
        if self.path != "/diagnose":
            return super().do_POST()
        if not self._auth():
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            return self._send(200, {"job": S2.job(run_diagnose, body)})
        except Exception as e:  # noqa: BLE001
            self._send(500, {"error": f"{type(e).__name__}: {str(e)[:300]}"})


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8000), H3).serve_forever()
