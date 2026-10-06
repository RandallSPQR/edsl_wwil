"""Regrade existing lies under the current rubric (rubric repair, Phase 2).

Reads only each lie's text and public prompt (grader_input_from_record), so the grader input
carries no condition, persona or target. Writes new grades to a separate directory; the source
run's records are never modified. Kill on breach: once spend reaches the cap, in-flight calls
are cancelled.
"""

from __future__ import annotations

import asyncio
import datetime
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .grader import RUBRIC_OUTPUT, RUBRIC_PREAMBLE, cue_list_block, grader_input_from_record, grader_response_format, parse_grader_output
from .runner import load_records

ATTEMPTS = 3


def _price(entry: Dict, usage: Dict) -> float:
    return ((usage.get("prompt_tokens") or 0) / 1000 * entry["usd_per_1k_input"]
            + (usage.get("completion_tokens") or 0) / 1000 * entry["usd_per_1k_output"])


async def regrade(source_dir: Path, out_dir: Path, instrument, graders: Sequence[Dict], adapter, cap_usd: float,
                  namespace: str, concurrency: int = 4, billing_probe=None) -> Dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    recs = [r for r in load_records(source_dir) if r.get("status") == "complete" and r.get("lie")]
    cue_order = [c.id for c in instrument.cues]
    rubric = RUBRIC_PREAMBLE + "\n" + cue_list_block(instrument.cues) + RUBRIC_OUTPUT
    state = {"spent": 0.0, "killed": False, "billed0": None, "billed": 0.0}
    if billing_probe:
        try:
            state["billed0"] = billing_probe()
        except Exception:
            pass
    lock = asyncio.Lock()
    rows: List[Dict] = []
    sem = asyncio.Semaphore(concurrency)
    tasks: List[asyncio.Task] = []

    def effective():
        return max(state["spent"], state["billed"])

    async def charge(entry, usage):
        async with lock:
            state["spent"] += _price(entry, usage)
            if billing_probe and state["billed0"] is not None and len(rows) % 10 == 0:
                try:
                    state["billed"] = billing_probe() - state["billed0"]
                except Exception:
                    pass
            if effective() >= cap_usd and not state["killed"]:
                state["killed"] = True
                for t in tasks:
                    if t is not asyncio.current_task() and not t.done():
                        t.cancel()
        if state["killed"]:
            raise asyncio.CancelledError("spend cap breached")

    async def one(r, g):
        async with sem:
            if state["killed"]:
                return
            gi = grader_input_from_record({"user_prompt": r["user_prompt"], "lie": r["lie"]}, instrument.cues)
            failures = []
            for attempt in range(ATTEMPTS):
                out = await adapter.acall(role="grader", user_prompt=gi.user_prompt, system_prompt=gi.system_prompt,
                                          model_name=g["id"], temperature=g["temperature"], replicate=1,
                                          run_namespace=namespace, reasoning=g.get("reasoning"),
                                          max_output_tokens=g.get("max_output_tokens"), attempt=attempt,
                                          response_format=grader_response_format(cue_order))
                await charge(g, out["usage"])
                try:
                    parsed = parse_grader_output(out["text"], cue_order)
                    row = {"cell_id": r["cell_id"], "grader": g["role"], "model": g["id"], **parsed,
                           "attempt": attempt, "parse_failures": failures}
                    break
                except ValueError as e:
                    failures.append({"attempt": attempt, "error": str(e)[:300]})
            else:
                row = {"cell_id": r["cell_id"], "grader": g["role"], "model": g["id"], "failed": True,
                       "parse_failures": failures}
            async with lock:
                rows.append(row)
                with (out_dir / "regrades.jsonl").open("a") as f:
                    f.write(json.dumps(row) + "\n")

    tasks = [asyncio.ensure_future(one(r, g)) for r in recs for g in graders]
    await asyncio.gather(*tasks, return_exceptions=True)
    manifest = {
        "source": str(source_dir), "namespace": namespace, "graders": [g["id"] for g in graders],
        "lies": len(recs), "gradings_written": len(rows), "gradings_planned": len(tasks),
        "spend_usd": round(effective(), 4), "spend_counted_usd": round(state["spent"], 4),
        "billed_delta_usd": round(state["billed"], 4) if state["billed0"] is not None else None,
        "cap_usd": cap_usd, "killed_on_breach": state["killed"],
        "rubric_sha256": hashlib.sha256(rubric.encode()).hexdigest(),
        "finished_at": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def load_regrades(out_dir: Path) -> Dict[str, Dict[str, Dict]]:
    """cell_id -> grader role -> row (last row wins)."""
    out: Dict[str, Dict[str, Dict]] = {}
    p = Path(out_dir) / "regrades.jsonl"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                out.setdefault(r["cell_id"], {})[r["grader"]] = r
    return out
