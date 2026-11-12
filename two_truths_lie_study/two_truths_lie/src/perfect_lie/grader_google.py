"""Phase 2 descriptive grading by the Google grader on the Addendum 2 subsample (Addendum 3, item 3: OpenRouter).

The reversed-note study's gate grader with its settings: `google/gemini-2.5-flash` on OpenRouter, temperature 0,
reasoning disabled, max 2000 output tokens, the frozen rubric v0.6 prompts (`grader_input_from_record`), the frozen
schema as `response_format` (`grader_response_format`: json_schema, strict) and the frozen parser
(`parse_grader_output`). Only the subsample's lies are sent, and never in place of a primary grade.

- A parse failure (including an empty answer or a refusal) is retried; after 3 attempts the lie has no Google grade.
- Transport failures (no answer: curl error, HTTP 408 / 429 / 5xx, or an error object with such a code) are retried
  with backoff (5, 15, 45, 90, 180 s) and do not count as attempts.
- OpenRouter's credential is supplied by the environment's proxy; if OPEN_ROUTER_API_KEY is set it is sent as the
  bearer token. It is never printed.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from typing import Callable, Dict, Sequence

from .grader import GraderInput, grader_response_format, parse_grader_output

MODEL = "google/gemini-2.5-flash"
URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_TOKENS, ATTEMPTS = 2000, 3
BACKOFF_SECONDS = (5, 15, 45, 90, 180)
TRANSPORT_CODES = {408, 429}


class TransportError(RuntimeError):
    """No answer came back (network or provider)."""


def request_body(gi: GraderInput, cue_order: Sequence[str]) -> Dict:
    return {"model": MODEL, "temperature": 0, "max_tokens": MAX_TOKENS, "reasoning": {"enabled": False},
            "messages": [{"role": "system", "content": gi.system_prompt}, {"role": "user", "content": gi.user_prompt}],
            "response_format": grader_response_format(cue_order)}


def post(body: Dict) -> Dict:
    """One chat-completions call. Returns {"status": HTTP status, "json": parsed body}; raises TransportError."""
    auth = ["-H", f"Authorization: Bearer {os.environ['OPEN_ROUTER_API_KEY']}"] if os.environ.get("OPEN_ROUTER_API_KEY") else []
    r = subprocess.run(["curl", "-sS", "-m", "300", "-w", "\n%{http_code}", URL, *auth,
                        "-H", "content-type: application/json", "--data-binary", "@-"],
                       input=json.dumps(body), capture_output=True, text=True)
    if r.returncode != 0:
        raise TransportError(f"curl exit {r.returncode}: {r.stderr.strip()[:150]}")
    text, _, code = r.stdout.rpartition("\n")
    try:
        return {"status": int(code), "json": json.loads(text)}
    except ValueError as e:
        raise TransportError(f"unreadable response (HTTP {code}): {e}") from e


def _transport(r: Dict) -> bool:
    err = r["json"].get("error") or {}
    code = err.get("code") if isinstance(err, dict) else None
    return (r["status"] in TRANSPORT_CODES or r["status"] >= 500 or
            (isinstance(code, int) and (code in TRANSPORT_CODES or code >= 500)))


def _call(body: Dict, send: Callable[[Dict], Dict], sleep: Callable[[float], None]) -> Dict:
    for wait in BACKOFF_SECONDS + (None,):
        try:
            r = send(body)
        except TransportError:
            if wait is None:
                raise
            sleep(wait)
            continue
        if _transport(r):
            if wait is None:
                raise TransportError(f"HTTP {r['status']} {str(r['json'].get('error'))[:150]}")
            sleep(wait)
            continue
        return r
    raise AssertionError("unreachable")


def grade(gi: GraderInput, cue_order: Sequence[str], send: Callable[[Dict], Dict] = post,
          sleep: Callable[[float], None] = time.sleep) -> Dict:
    """Grade one lie. `parsed` is the frozen parser's output, or None when the lie got no Google grade."""
    body = request_body(gi, cue_order)
    out = {"route": "openrouter", "model": MODEL, "parsed": None, "attempts": 0, "error": None,
           "models_returned": [], "providers": [], "usage": {"prompt_tokens": 0, "completion_tokens": 0}}
    for attempt in range(1, ATTEMPTS + 1):
        out["attempts"] = attempt
        r = _call(body, send, sleep)
        d = r["json"]
        for k, f in (("models_returned", "model"), ("providers", "provider")):
            if d.get(f) and d[f] not in out[k]:
                out[k].append(d[f])
        for k in out["usage"]:
            out["usage"][k] += (d.get("usage") or {}).get(k, 0) or 0
        choice = (d.get("choices") or [{}])[0]
        content = (choice.get("message") or {}).get("content")
        if not content:
            out["error"] = f"no content (HTTP {r['status']}, finish {choice.get('finish_reason')}, " \
                           f"error {str(d.get('error'))[:150]})"
            continue
        try:
            out["parsed"] = parse_grader_output(content, cue_order)
            out["error"] = None
            return out
        except (ValueError, json.JSONDecodeError) as e:
            out["error"] = f"{type(e).__name__}: {str(e)[:150]}"
    return out
