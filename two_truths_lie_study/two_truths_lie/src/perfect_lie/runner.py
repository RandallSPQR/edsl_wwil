"""Live execution: liar -> target -> cue graders -> trace probe, per cell.

Records are appended to <run_dir>/records.jsonl after every stage, so a crash resumes
at the stage it reached instead of paying for completed calls again. The last line for
a cell_id wins. <run_dir>/manifest.json is rewritten atomically as the run progresses.

Modes
  smoke  liar calls only, a few cells per family x reasoning level; checks that the
         reasoning field and output cap are honoured and what trace comes back.
  pilot  one liar family at reasoning off, one replicate, all prompts/pairs/conditions;
         every stage. Feeds the fabricability gate and cue calibration (Phase 2).
  full   the preregistered design (Phase 3).

Each mode has its own run_namespace in the cache key, so a pilot response can never be
served from cache inside the full run.
"""

from __future__ import annotations

import asyncio
import datetime
import hashlib
import json
import os
import platform
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

from .conditions import build_liar_prompts, target_system_prompt, target_user_prompt
from .grader import build_trace_probe_input, grader_input_from_record, parse_grader_output, RUBRIC_PREAMBLE, RUBRIC_OUTPUT
from .personas import Instrument, file_sha256
from .pipeline import Cell
from .scoring import parse_target_output

STAGES = ("liar", "target", "graders", "trace_probe")
MAX_PARSE_ATTEMPTS = 3


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


def cell_id(cell: Cell, namespace: str) -> str:
    return "|".join([namespace, cell.prompt_id, cell.j1, cell.j2, cell.target_id, cell.condition,
                     cell.model_id, cell.reasoning_level, f"r{cell.replicate}"])


def _price(entry: Dict, usage: Dict) -> float:
    pt = usage.get("prompt_tokens") or 0
    ct = usage.get("completion_tokens") or 0
    return pt / 1000 * entry["usd_per_1k_input"] + ct / 1000 * entry["usd_per_1k_output"]


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return ""


class Run:
    def __init__(self, *, mode: str, run_dir: Path, cells: List[Cell], instrument: Instrument, models: Dict,
                 adapter, spend_cap_usd: float, concurrency: int = 4, models_path: Optional[Path] = None,
                 stages: tuple = STAGES, trace_probe_locked: bool = True, billing_probe=None):
        if mode not in ("smoke", "pilot", "full"):
            raise ValueError(f"unknown mode {mode!r}")
        self.mode = mode
        self.namespace = mode
        self.run_dir = Path(run_dir)
        self.cells = cells
        self.instrument = instrument
        self.models = models
        self.adapter = adapter
        self.spend_cap = float(spend_cap_usd)
        self.concurrency = concurrency
        self.models_path = models_path
        self.stages = stages if mode != "smoke" else ("liar",)
        # Owner lock (data/perfect_lie/run_locks.json): the trace probe never runs while locked.
        self.trace_probe_locked = trace_probe_locked
        if trace_probe_locked:
            self.stages = tuple(st for st in self.stages if st != "trace_probe")
        # billing_probe() returns the total billed on the key. Spend for the cap is the larger
        # of the run's own counter and the billed delta since the run started, because a call
        # that times out on our side can still complete and be billed upstream.
        self.billing_probe = billing_probe
        self.billed_at_start = None
        self.billed_delta = 0.0
        self.liar_by_id = {m["id"]: m for m in models["liar_models"]}
        self.design_by_prompt = {r.prompt_id: r for r in instrument.design}
        self.records: Dict[str, Dict] = {}
        self.spent = 0.0
        self.cap_reached = False
        self.started_at = None
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------ persistence

    @property
    def records_path(self) -> Path:
        return self.run_dir / "records.jsonl"

    def load(self) -> None:
        """Resume: read existing records; the last line for each cell_id wins."""
        self.run_dir.mkdir(parents=True, exist_ok=True)
        if self.records_path.exists():
            for line in self.records_path.read_text().splitlines():
                if line.strip():
                    r = json.loads(line)
                    self.records[r["cell_id"]] = r
            self.spent = sum(r.get("cost_usd", 0.0) for r in self.records.values())
        mf = self.run_dir / "manifest.json"
        if mf.exists():
            prev = json.loads(mf.read_text())
            if prev.get("mode") != self.mode:
                raise ValueError(f"{self.run_dir} holds a {prev.get('mode')} run; refusing to resume it as {self.mode}")
            if prev.get("hashes") != self._hashes():
                raise ValueError(f"{self.run_dir}: instrument or model file changed since this run started; "
                                 "start a new run directory instead of resuming")
            self.started_at = prev.get("started_at")

    async def _append(self, record: Dict) -> None:
        async with self._lock:
            self.records[record["cell_id"]] = record
            with self.records_path.open("a") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            self.write_manifest()

    def _hashes(self) -> Dict[str, str]:
        h = dict(self.instrument.hashes)
        if self.models_path:
            h["models"] = file_sha256(self.models_path)
        h["grader_rubric"] = hashlib.sha256((RUBRIC_PREAMBLE + RUBRIC_OUTPUT).encode()).hexdigest()
        return h

    def write_manifest(self, finished: bool = False) -> None:
        recs = list(self.records.values())
        manifest = {
            "mode": self.mode, "run_namespace": self.namespace, "run_dir": str(self.run_dir),
            "git_sha": _git("rev-parse", "HEAD"), "git_dirty": bool(_git("status", "--porcelain")),
            "started_at": self.started_at, "updated_at": utc_now(), "finished_at": utc_now() if finished else None,
            "hashes": self._hashes(),
            "liar_models": sorted({c.model_id for c in self.cells}),
            "reasoning_levels": sorted({c.reasoning_level for c in self.cells}),
            "replicates": sorted({c.replicate for c in self.cells}),
            "target_model": self.models["target_model"]["id"],
            "graders": [g["id"] for g in self.models["graders"]],
            "trace_probe": (self.models.get("trace_probe") or {}).get("id"),
            "stages": list(self.stages),
            "price_source": self.models.get("price_source"), "price_fetched_at": self.models.get("price_fetched_at"),
            "n_cells_planned": len(self.cells),
            "n_complete": sum(r.get("status") == "complete" for r in recs),
            "n_error": sum(r.get("status") == "error" for r in recs),
            "spend_usd": round(self.effective_spend(), 4), "spend_counted_usd": round(self.spent, 4),
            "openrouter_billed_delta_usd": round(self.billed_delta, 4) if self.billed_at_start is not None else None,
            "spend_cap_usd": self.spend_cap, "spend_cap_reached": self.cap_reached,
            "trace_probe_locked": self.trace_probe_locked,
            "python": platform.python_version(),
            "edsl_version": _edsl_version(),
        }
        tmp = self.run_dir / "manifest.json.tmp"
        tmp.write_text(json.dumps(manifest, indent=2) + "\n")
        os.replace(tmp, self.run_dir / "manifest.json")

    # ------------------------------------------------------------ execution

    def pending(self) -> List[Cell]:
        return [c for c in self.cells if self.records.get(cell_id(c, self.namespace), {}).get("status") != "complete"]

    async def run(self) -> Dict:
        self.load()
        self.started_at = self.started_at or utc_now()
        if self.billing_probe:
            try:
                self.billed_at_start = self.billing_probe()
            except Exception:
                self.billed_at_start = None
        self.write_manifest()
        sem = asyncio.Semaphore(self.concurrency)

        async def guarded(cell: Cell):
            async with sem:
                self._refresh_billed()
                if self.effective_spend() >= self.spend_cap:
                    self.cap_reached = True
                    return
                await self.run_cell(cell)

        await asyncio.gather(*(guarded(c) for c in self.pending()))
        self._refresh_billed()
        self.write_manifest(finished=not self.cap_reached and not self.pending())
        return json.loads((self.run_dir / "manifest.json").read_text())

    def _refresh_billed(self) -> None:
        if self.billing_probe and self.billed_at_start is not None:
            try:
                self.billed_delta = max(self.billed_delta, self.billing_probe() - self.billed_at_start)
            except Exception:
                pass

    def effective_spend(self) -> float:
        return max(self.spent, self.billed_delta)

    async def _charge_failed_call(self, entry: Dict, max_output_tokens: Optional[int], rec: Dict) -> None:
        """A failed call may still be billed upstream (and retried by EDSL). Charge a
        conservative bound so the cap stays honest: every attempt at the full output cap."""
        attempts = int(os.environ.get("EDSL_MAX_ATTEMPTS", "3"))
        est = attempts * ((max_output_tokens or 2000) / 1000 * entry["usd_per_1k_output"]
                          + 2000 / 1000 * entry["usd_per_1k_input"])
        async with self._lock:
            self.spent += est
        rec["cost_usd"] = rec.get("cost_usd", 0.0) + est
        rec["cost_includes_failed_call_bound"] = True

    async def _charge(self, entry: Dict, usage: Dict) -> float:
        cost = _price(entry, usage)
        async with self._lock:
            self.spent += cost
        return cost

    def _base_record(self, cell: Cell) -> Dict:
        d = asdict(cell)
        d.update(cell_id=cell_id(cell, self.namespace), run_namespace=self.namespace, mode=self.mode,
                 status="pending", stage_done=None, cost_usd=0.0, errors=[])
        return d

    async def run_cell(self, cell: Cell) -> None:
        cid = cell_id(cell, self.namespace)
        rec = dict(self.records.get(cid) or self._base_record(cell))
        rec["errors"] = []
        try:
            if rec.get("stage_done") is None:
                await self._liar(cell, rec)
                rec["stage_done"] = "liar"
                rec["status"] = "complete" if self.stages == ("liar",) else "in_progress"
                await self._append(rec)
            elif rec.get("status") == "error":
                rec["status"] = "in_progress"
            if "target" in self.stages and rec["stage_done"] == "liar":
                await self._target(cell, rec)
                rec["stage_done"] = "target"
                await self._append(rec)
            if "graders" in self.stages and rec["stage_done"] == "target":
                await self._graders(rec)
                rec["stage_done"] = "graders"
                await self._append(rec)
            if "trace_probe" in self.stages and rec["stage_done"] == "graders":
                await self._trace_probe(rec)
                rec["stage_done"] = "trace_probe"
            if rec["stage_done"] == self.stages[-1] and rec["status"] != "complete":
                rec["status"] = "complete"
                await self._append(rec)
        except Exception as e:  # recorded, retried on resume; never silently dropped
            rec["status"] = "error"
            rec["errors"].append({"stage_after": rec.get("stage_done"), "error": f"{type(e).__name__}: {e}"[:2000],
                                  "at": utc_now()})
            await self._append(rec)

    async def _liar(self, cell: Cell, rec: Dict) -> None:
        lp = build_liar_prompts(cell.condition, self.design_by_prompt[cell.prompt_id], cell.target_id,
                                self.instrument.personas, cell.category)
        try:
            out = await self.adapter.acall(role="liar", user_prompt=lp.user_prompt, system_prompt=lp.system_prompt,
                                           model_name=cell.model_id, temperature=cell.temperature,
                                           replicate=cell.replicate, run_namespace=self.namespace,
                                           reasoning=cell.reasoning, max_output_tokens=cell.max_output_tokens)
        except Exception:
            await self._charge_failed_call(self.liar_by_id[cell.model_id], cell.max_output_tokens, rec)
            raise
        cost = await self._charge(self.liar_by_id[cell.model_id], out["usage"])
        rec.update(lie=out["text"], user_prompt=lp.user_prompt, liar_system_prompt=lp.system_prompt,
                   liar_usage=out["usage"], liar_finish_reason=out["finish_reason"],
                   liar_latency_ms=out.get("latency_ms"), lie_words=len((out["text"] or "").split()),
                   thinking_trace=out.get("thinking_trace"), thinking_trace_kind=out.get("thinking_trace_kind"))
        rec["cost_usd"] = rec.get("cost_usd", 0.0) + cost

    async def _call_parsed(self, *, role: str, entry: Dict, system_prompt: str, user_prompt: str,
                           parse, rec: Dict, label: str):
        """Call and parse strictly; a malformed answer is retried with a new attempt id so the
        retry reaches the model instead of the cached malformed answer."""
        last_err = None
        for attempt in range(MAX_PARSE_ATTEMPTS):
            out = await self.adapter.acall(role=role, user_prompt=user_prompt, system_prompt=system_prompt,
                                           model_name=entry["id"], temperature=entry["temperature"],
                                           replicate=1, run_namespace=self.namespace,
                                           reasoning=entry.get("reasoning"),
                                           max_output_tokens=entry.get("max_output_tokens"), attempt=attempt)
            rec["cost_usd"] = rec.get("cost_usd", 0.0) + await self._charge(entry, out["usage"])
            try:
                return parse(out["text"]), out, attempt
            except ValueError as e:
                last_err = e
                rec.setdefault("parse_failures", []).append({"call": label, "attempt": attempt, "error": str(e)[:500]})
        raise ValueError(f"{label}: no well-formed answer after {MAX_PARSE_ATTEMPTS} attempts: {last_err}")

    async def _target(self, cell: Cell, rec: Dict) -> None:
        t = self.models["target_model"]
        parsed, out, attempt = await self._call_parsed(
            role="target", entry=t, system_prompt=target_system_prompt(self.instrument.personas[cell.target_id]),
            user_prompt=target_user_prompt(rec["lie"]), parse=parse_target_output, rec=rec, label="target")
        rec["target"] = {**parsed, "raw": out["text"], "attempt": attempt, "usage": out["usage"]}

    async def _graders(self, rec: Dict) -> None:
        cue_order = [c.id for c in self.instrument.cues]
        gi = grader_input_from_record(rec, self.instrument.cues)
        grades = {}
        for g in self.models["graders"]:
            parsed, out, attempt = await self._call_parsed(
                role="grader", entry=g, system_prompt=gi.system_prompt, user_prompt=gi.user_prompt,
                parse=lambda txt: parse_grader_output(txt, cue_order), rec=rec, label=f"grader[{g['role']}]")
            grades[g["role"]] = {**parsed, "model": g["id"], "attempt": attempt, "usage": out["usage"]}
        rec["grades"] = grades

    async def _trace_probe(self, rec: Dict) -> None:
        if self.trace_probe_locked:
            raise RuntimeError("trace probe is locked by the owner (run_locks.json); it must not run")
        tp = self.models.get("trace_probe")
        if not tp or not rec.get("thinking_trace") or rec.get("reasoning_level") == "off":
            rec["trace_probe"] = None
            return
        pi = build_trace_probe_input(rec["thinking_trace"])

        def parse(txt: str) -> Dict:
            start, end = txt.find("{"), txt.rfind("}")
            if start < 0:
                raise ValueError("no JSON object")
            obj = json.loads(txt[start:end + 1])
            if set(obj) != {"audience_reference", "quote", "confidence"}:
                raise ValueError(f"trace probe keys {sorted(obj)}")
            if type(obj["audience_reference"]) is not bool or type(obj["confidence"]) is not int \
                    or not 1 <= obj["confidence"] <= 10 or not isinstance(obj["quote"], str):
                raise ValueError("trace probe field types")
            return obj

        parsed, out, attempt = await self._call_parsed(role="trace_probe", entry=tp, system_prompt=pi.system_prompt,
                                                       user_prompt=pi.user_prompt, parse=parse, rec=rec,
                                                       label="trace_probe")
        rec["trace_probe"] = {**parsed, "model": tp["id"], "attempt": attempt}


def _edsl_version() -> str:
    try:
        import edsl
        return getattr(edsl, "__version__", "")
    except Exception:
        return ""


def load_records(run_dir: Path) -> List[Dict]:
    """Last record per cell_id, in file order of first appearance."""
    out: Dict[str, Dict] = {}
    p = Path(run_dir) / "records.jsonl"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                out[r["cell_id"]] = r
    return list(out.values())


# ------------------------------------------------------------ smoke test report

def smoke_report(records: List[Dict], models: Dict) -> List[Dict]:
    """Per family x level: did the provider honour the reasoning field and the output cap?"""
    from collections import defaultdict
    from statistics import median
    from .scoring import lie_viability
    groups = defaultdict(list)
    for r in records:
        groups[(r["model_id"], r["reasoning_level"])].append(r)
    liar_by_id = {m["id"]: m for m in models["liar_models"]}
    rows = []
    for (mid, level), rs in sorted(groups.items()):
        ok = [r for r in rs if r.get("lie")]
        rt = [((r.get("liar_usage") or {}).get("reasoning_tokens") or 0) for r in ok]
        ct = [((r.get("liar_usage") or {}).get("completion_tokens") or 0) for r in ok]
        cap = liar_by_id[mid]["levels"][level]["max_output_tokens"]
        true_off = liar_by_id[mid].get("true_off_available", False)
        flags = []
        if len(ok) < len(rs):
            flags.append(f"{len(rs) - len(ok)} call(s) failed")
        if level == "off" and true_off and any(x > 0 for x in rt):
            flags.append("reasoning tokens at off: reasoning not disabled")
        if level != "off" and ok and not any(x > 0 for x in rt):
            flags.append("no reasoning tokens: reasoning field ignored or not reported")
        if any(r.get("liar_finish_reason") == "length" for r in ok):
            flags.append("finish_reason=length: thinking ate the story; raise the cap")
        if any(x > cap for x in ct):
            flags.append(f"completion tokens exceed cap {cap}: max_completion_tokens not respected")
        bad = [lie_viability(r) for r in ok]
        if any(bad):
            flags.append(f"{sum(bool(b) for b in bad)} lie(s) fail viability screen")
        rows.append({"model_id": mid, "level": level, "n": len(rs), "n_ok": len(ok),
                     "median_completion_tokens": median(ct) if ct else None,
                     "median_reasoning_tokens": median(rt) if rt else None, "cap": cap,
                     "trace_kinds": sorted({str(r.get("thinking_trace_kind")) for r in ok}),
                     "flags": flags})
    # Ordering check across levels within a family.
    by_family = defaultdict(dict)
    for row in rows:
        by_family[row["model_id"]][row["level"]] = row
    for mid, lv in by_family.items():
        lo, hi = lv.get("low"), lv.get("high")
        if lo and hi and lo["median_reasoning_tokens"] is not None and hi["median_reasoning_tokens"] is not None \
                and hi["median_reasoning_tokens"] <= lo["median_reasoning_tokens"]:
            hi["flags"].append("high does not use more reasoning than low")
    return rows
