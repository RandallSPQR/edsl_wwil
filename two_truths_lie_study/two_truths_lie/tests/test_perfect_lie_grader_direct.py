"""Phase 2 direct-route grader (src/perfect_lie/grader_direct.py). Offline: no call leaves the process."""
import pytest

from src.perfect_lie import grader_direct as G
from src.perfect_lie.grader import GraderInput

CUES = ["a", "b", "c"]
GI = GraderInput(system_prompt="SYS", user_prompt="USER", cue_order=tuple(CUES))


def answer(cues=None, counts=None, confidence=7):
    cues = cues if cues is not None else {"a": True, "b": False, "c": False}
    counts = counts if counts is not None else {"a": 1, "b": 0, "c": 0}
    return {"status": 200, "json": {"model": "m-1", "stop_reason": "tool_use",
                                    "usage": {"input_tokens": 10, "output_tokens": 2},
                                    "content": [{"type": "tool_use", "name": "cue_annotation",
                                                 "input": {"cues": cues, "counts": counts,
                                                           "confidence": confidence}}]}}


def sender(*responses):
    calls = []
    def send(body):
        calls.append(body)
        r = responses[len(calls) - 1]
        if isinstance(r, Exception):
            raise r
        return r
    return send, calls


def walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk(v)


def test_strict_body_shape():
    body = G.request_body(GI, CUES)
    tool = body["tools"][0]
    assert tool["strict"] is True and tool["name"] == "cue_annotation"
    assert body["tool_choice"] == {"type": "tool", "name": "cue_annotation"}
    assert body["temperature"] == 0 and body["model"] == G.MODEL and "thinking" not in body
    assert body["system"] == "SYS" and body["messages"] == [{"role": "user", "content": "USER"}]
    for node in walk(tool["input_schema"]):
        assert not set(node) & set(G.UNSUPPORTED_IN_STRICT)
        if node.get("type") == "object":
            assert node["additionalProperties"] is False and set(node["required"]) == set(node["properties"])


def test_non_strict_body_keeps_the_frozen_schema():
    from src.perfect_lie.grader import grader_response_format
    tool = G.request_body(GI, CUES, strict=False)["tools"][0]
    assert "strict" not in tool
    assert tool["input_schema"] == grader_response_format(CUES)["json_schema"]["schema"]


def test_api_version_is_pinned():
    assert G.API_VERSION == "2023-06-01"


def test_parses_first_answer():
    send, calls = sender(answer())
    out = G.grade(GI, CUES, send=send, sleep=lambda s: None)
    assert out["parsed"]["cues"] == {"a": True, "b": False, "c": False}
    assert out["attempts"] == 1 and out["error"] is None and len(calls) == 1
    assert out["models_returned"] == ["m-1"] and out["route"] == "anthropic_direct" and out["strict"]


def test_malformed_answer_is_retried_then_parsed():
    send, calls = sender(answer(cues={"a": True, "b": False}), answer())
    out = G.grade(GI, CUES, send=send, sleep=lambda s: None)
    assert out["parsed"] is not None and out["attempts"] == 2


def test_cell_fails_after_three_attempts():
    bad = answer(cues={"a": True, "b": False})
    send, calls = sender(bad, bad, bad, answer())
    out = G.grade(GI, CUES, send=send, sleep=lambda s: None)
    assert out["parsed"] is None and out["attempts"] == 3 and len(calls) == 3
    assert "keys differ from ontology" in out["error"]


def test_bounds_dropped_from_strict_schema_are_still_enforced():
    bad = answer(confidence=11)
    send, _ = sender(bad, bad, bad)
    out = G.grade(GI, CUES, send=send, sleep=lambda s: None)
    assert out["parsed"] is None and "confidence" in out["error"]


def test_transport_failures_retry_without_spending_attempts():
    waits = []
    send, calls = sender(G.TransportError("reset"), {"status": 529, "json": {"error": {"type": "overloaded_error"}}},
                         {"status": 429, "json": {"error": {"type": "rate_limit_error"}}}, answer())
    out = G.grade(GI, CUES, send=send, sleep=waits.append)
    assert out["parsed"] is not None and out["attempts"] == 1 and len(calls) == 4 and waits == [5, 15, 45]


def test_transport_gives_up_after_backoff():
    send, _ = sender(*[G.TransportError("down")] * (len(G.BACKOFF_SECONDS) + 1))
    with pytest.raises(G.TransportError):
        G.grade(GI, CUES, send=send, sleep=lambda s: None)


def test_strict_rejection_is_raised_not_counted():
    send, _ = sender({"status": 400, "json": {"type": "error", "error": {"type": "invalid_request_error",
                                                                        "message": "strict not supported"}}})
    with pytest.raises(G.StrictRejected):
        G.grade(GI, CUES, send=send, sleep=lambda s: None)


def test_no_tool_call_is_a_parse_failure():
    empty = {"status": 200, "json": {"model": "m-1", "stop_reason": "refusal", "content": []}}
    send, _ = sender(empty, empty, empty)
    out = G.grade(GI, CUES, send=send, sleep=lambda s: None)
    assert out["parsed"] is None and "no tool call" in out["error"] and out["stop_reasons"] == ["refusal"] * 3


def test_key_never_in_body(monkeypatch):
    monkeypatch.setenv("PL_GRADER_KEY", "sk-test-secret")
    assert "sk-test-secret" not in str(G.request_body(GI, CUES))
