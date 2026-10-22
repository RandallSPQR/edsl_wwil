"""Phase 2 primary grading through the Anthropic API directly (PREREG_PHASE2 section 11).

Same grader model, rubric v0.6 prompts (`grader_input_from_record`) and parser (`parse_grader_output`)
as the first two studies; only the route differs. The frozen schema (`grader_response_format`) is
enforced as a strict forced tool call (`cue_annotation`, `strict: true`), so the answer is decoded to
the schema. Strict mode does not accept numeric bounds (`minimum`, `maximum`); they are dropped from
the copy sent to the API and still enforced by `parse_grader_output`, which fails closed.

- `anthropic-version: 2023-06-01` is pinned: later API versions reject `temperature` (here 0).
- A parse failure is retried; after 3 attempts the cell is failed (`direct` is None, `error` says why).
- Transport failures (no answer: curl error, HTTP 429/5xx, overloaded) are retried with backoff and
  do not count as attempts.
- If the API rejects the strict tool (HTTP 400 on the first call), `StrictRejected` is raised. The
  run then switches to the non-strict forced tool for every cell, never per cell (section 11).
The key is read from PL_GRADER_KEY (or GRADER_ANTHROPIC_API_KEY) and never printed.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import time
from typing import Callable, Dict, Optional, Sequence

from .grader import GraderInput, grader_response_format, parse_grader_output

MODEL = "claude-sonnet-4-5"
API_VERSION = "2023-06-01"
URL = "https://api.anthropic.com/v1/messages"
MAX_TOKENS, ATTEMPTS = 2000, 3
BACKOFF_SECONDS = (5, 15, 45, 90, 180)
TRANSPORT_ERRORS = {"rate_limit_error", "overloaded_error", "api_error", "timeout_error"}
KEY_VARS = ("PL_GRADER_KEY", "GRADER_ANTHROPIC_API_KEY")
UNSUPPORTED_IN_STRICT = ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf",
                         "minLength", "maxLength")


class StrictRejected(RuntimeError):
    """The API refused the strict tool definition (HTTP 400)."""


class TransportError(RuntimeError):
    """No answer came back (network or provider)."""


def grader_key() -> str:
    for v in KEY_VARS:
        if os.environ.get(v):
            return os.environ[v]
    raise SystemExit(f"no grading key: set {KEY_VARS[0]} in the environment settings")


def strict_schema(schema: Dict) -> Dict:
    """The frozen schema without the keywords strict mode does not accept."""
    def strip(node):
        if isinstance(node, dict):
            return {k: strip(v) for k, v in node.items() if k not in UNSUPPORTED_IN_STRICT}
        if isinstance(node, list):
            return [strip(v) for v in node]
        return node
    return strip(copy.deepcopy(schema))


def request_body(gi: GraderInput, cue_order: Sequence[str], strict: bool = True) -> Dict:
    schema = grader_response_format(cue_order)["json_schema"]["schema"]
    tool = {"name": "cue_annotation", "description": "Record the cue annotation.",
            "input_schema": strict_schema(schema) if strict else schema}
    if strict:
        tool["strict"] = True
    return {"model": MODEL, "max_tokens": MAX_TOKENS, "temperature": 0, "system": gi.system_prompt,
            "messages": [{"role": "user", "content": gi.user_prompt}],
            "tools": [tool], "tool_choice": {"type": "tool", "name": "cue_annotation"}}


def post(body: Dict) -> Dict:
    """One Messages call. Returns {"status": HTTP status, "json": parsed body}; raises TransportError."""
    r = subprocess.run(["curl", "-sS", "-m", "300", "-w", "\n%{http_code}", URL,
                        "-H", f"x-api-key: {grader_key()}", "-H", f"anthropic-version: {API_VERSION}",
                        "-H", "content-type: application/json", "--data-binary", "@-"],
                       input=json.dumps(body), capture_output=True, text=True)
    if r.returncode != 0:
        raise TransportError(f"curl exit {r.returncode}: {r.stderr.strip()[:150]}")
    text, _, code = r.stdout.rpartition("\n")
    try:
        return {"status": int(code), "json": json.loads(text)}
    except ValueError as e:
        raise TransportError(f"unreadable response (HTTP {code}): {e}") from e


def _call(body: Dict, send: Callable[[Dict], Dict], sleep: Callable[[float], None]) -> Dict:
    for wait in BACKOFF_SECONDS + (None,):
        try:
            r = send(body)
        except TransportError:
            if wait is None:
                raise
            sleep(wait)
            continue
        err = (r["json"].get("error") or {}).get("type")
        if r["status"] == 429 or r["status"] >= 500 or err in TRANSPORT_ERRORS:
            if wait is None:
                raise TransportError(f"HTTP {r['status']} {err}")
            sleep(wait)
            continue
        return r
    raise AssertionError("unreachable")


def grade(gi: GraderInput, cue_order: Sequence[str], strict: bool = True,
          send: Callable[[Dict], Dict] = post, sleep: Callable[[float], None] = time.sleep) -> Dict:
    """Grade one lie. `parsed` is the frozen parser's output, or None when the cell failed."""
    body = request_body(gi, cue_order, strict)
    out = {"route": "anthropic_direct", "strict": strict, "parsed": None, "attempts": 0, "error": None,
           "models_returned": [], "usage": {"input_tokens": 0, "output_tokens": 0}, "stop_reasons": []}
    for attempt in range(1, ATTEMPTS + 1):
        out["attempts"] = attempt
        r = _call(body, send, sleep)
        d = r["json"]
        if r["status"] == 400 and strict:
            raise StrictRejected(str((d.get("error") or {}).get("message"))[:300])
        if d.get("model") and d["model"] not in out["models_returned"]:
            out["models_returned"].append(d["model"])
        for k in out["usage"]:
            out["usage"][k] += (d.get("usage") or {}).get(k, 0)
        out["stop_reasons"].append(d.get("stop_reason"))
        tool = next((c for c in d.get("content") or [] if c.get("type") == "tool_use"), None)
        if tool is None:
            out["error"] = f"no tool call (HTTP {r['status']}, stop_reason {d.get('stop_reason')}, " \
                           f"error {str(d.get('error'))[:150]})"
            continue
        try:
            out["parsed"] = parse_grader_output(json.dumps(tool["input"]), cue_order)
            out["error"] = None
            return out
        except ValueError as e:
            out["error"] = f"ValueError: {str(e)[:150]}"
    return out
