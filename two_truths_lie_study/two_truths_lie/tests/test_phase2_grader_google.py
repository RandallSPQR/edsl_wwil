"""Addendum 2 Google grader (src/perfect_lie/grader_google.py) with a stubbed transport: no network calls."""
import json

import pytest

from src.perfect_lie import grader_google as G
from src.perfect_lie.grader import GraderInput

CUES = ["a", "b", "c"]
GI = GraderInput(system_prompt="SYS", user_prompt="USER", cue_order=CUES)


def answer(cues=None, conf=7):
    cues = cues or {"a": True, "b": False, "c": True}
    return json.dumps({"cues": cues, "counts": {k: int(v) for k, v in cues.items()}, "confidence": conf})


def ok(content, status=200):
    return {"status": status, "json": {"model": G.MODEL, "provider": "Google", "usage": {"prompt_tokens": 10, "completion_tokens": 5},
                                       "choices": [{"message": {"content": content}, "finish_reason": "stop"}]}}


def stub(responses):
    calls, it = [], iter(responses)

    def send(body):
        calls.append(body)
        r = next(it)
        if isinstance(r, Exception):
            raise r
        return r
    return send, calls


def test_request_body_matches_the_registered_settings():
    b = G.request_body(GI, CUES)
    assert b["model"] == "google/gemini-2.5-flash" and b["temperature"] == 0 and b["max_tokens"] == 2000
    assert b["reasoning"] == {"enabled": False}
    assert b["response_format"]["type"] == "json_schema" and b["response_format"]["json_schema"]["strict"] is True
    assert [m["role"] for m in b["messages"]] == ["system", "user"]


def test_success_first_attempt():
    send, calls = stub([ok(answer())])
    out = G.grade(GI, CUES, send=send, sleep=lambda s: None)
    assert out["parsed"]["cues"] == {"a": True, "b": False, "c": True} and out["attempts"] == 1 and len(calls) == 1
    assert out["usage"] == {"prompt_tokens": 10, "completion_tokens": 5} and out["providers"] == ["Google"]


def test_parse_failures_retried_then_failed_after_three():
    bad = json.dumps({"cues": {"a": "true", "b": False, "c": True}, "counts": {"a": 1, "b": 0, "c": 1}, "confidence": 7})
    send, calls = stub([ok(bad), ok(""), ok("I can't help with that")])
    out = G.grade(GI, CUES, send=send, sleep=lambda s: None)
    assert out["parsed"] is None and out["attempts"] == 3 and len(calls) == 3 and out["error"]


def test_transport_failures_do_not_count_as_attempts():
    waits = []
    send, calls = stub([G.TransportError("reset"), {"status": 429, "json": {"error": {"code": 429}}},
                        {"status": 200, "json": {"error": {"code": 502, "message": "upstream"}}}, ok(answer())])
    out = G.grade(GI, CUES, send=send, sleep=waits.append)
    assert out["parsed"] is not None and out["attempts"] == 1 and waits == [5, 15, 45]


def test_transport_gives_up_after_backoff():
    send, _ = stub([G.TransportError("x")] * 6)
    with pytest.raises(G.TransportError):
        G.grade(GI, CUES, send=send, sleep=lambda s: None)
