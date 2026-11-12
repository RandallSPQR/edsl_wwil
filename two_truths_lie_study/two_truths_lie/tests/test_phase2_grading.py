"""Phase 2 stage-2 grading driver (src/perfect_lie/phase2_grading.py) with stubbed graders: no network calls."""
from src.perfect_lie import grader_direct, phase2_grading as PG
from src.perfect_lie.personas import load_instrument

CUES = load_instrument().cues
SUB = {"k0": "P1", "k1": "P2"}


def rec(cat, tgt, status="complete", **kw):
    return {"category": cat, "target": tgt, "status": status, "user_prompt": "Tell a story.", "lie": "Once upon a time.",
            **kw}


def parsed(present=()):
    return {"cues": {c.id: c.id in present for c in CUES}, "counts": {c.id: int(c.id in present) for c in CUES},
            "confidence": 7}


class Primary:
    def __init__(self, fail=(), reject_strict=False):
        self.calls, self.fail, self.reject = [], set(fail), reject_strict

    def __call__(self, gi, order, strict=True):
        self.calls.append(strict)
        if strict and self.reject:
            raise grader_direct.StrictRejected("no strict")
        n = len(self.calls)
        return {"parsed": None if n in self.fail else parsed(), "error": "x" if n in self.fail else None,
                "usage": {"input_tokens": 100, "output_tokens": 10}}


def google(gi, order):
    return {"parsed": parsed(), "error": None, "usage": {"prompt_tokens": 50, "completion_tokens": 5}}


def test_every_complete_lie_primary_graded_and_only_the_subsample_by_google():
    recs = [rec("k0", "P1"), rec("k0", "P2"), rec("k1", "P2"), rec("k2", "P1"), rec("k1", "P2", status="generation_failed")]
    p = Primary()
    out = PG.grade_records(recs, CUES, SUB, primary=p, google=google)
    assert len(p.calls) == 4 and all(p.calls)
    assert [("google" in r) for r in out] == [True, False, True, False, False]
    assert all(not r["grading_failed"] for r in out[:4]) and "primary" not in out[4]


def test_grader_input_uses_the_frozen_rubric_and_cue_order():
    seen = {}

    def primary(gi, order, strict=True):
        seen["gi"], seen["order"] = gi, order
        return {"parsed": parsed(), "error": None, "usage": {}}
    PG.grade_records([rec("k2", "P1")], CUES, SUB, primary=primary, google=google)
    assert list(seen["order"]) == [c.id for c in CUES] and "Once upon a time." in seen["gi"].user_prompt


def test_failed_primary_is_missing_with_no_substitute():
    out = PG.grade_records([rec("k0", "P1"), rec("k2", "P1")], CUES, SUB, primary=Primary(fail={1}), google=google)
    assert out[0]["grading_failed"] and out[0]["grade"] is None and out[0]["google"] is not None
    assert not out[1]["grading_failed"]


def test_strict_rejection_switches_every_cell_from_then_on():
    state = {"strict": True}
    p = Primary(reject_strict=True)
    PG.grade_records([rec("k2", "P1"), rec("k3", "P1")], CUES, SUB, primary=p, google=google, state=state)
    assert p.calls == [True, False, False] and state["strict"] is False and state["strict_rejected"]


def test_resume_skips_graded_records_and_summary():
    first = PG.grade_records([rec("k0", "P1"), rec("k2", "P1")], CUES, SUB, primary=Primary(), google=google)
    p = Primary()
    again = PG.grade_records(first + [rec("k3", "P1")], CUES, SUB, primary=p, google=google)
    assert len(p.calls) == 1
    s = PG.summary(again, {"strict": True})
    assert s["graded"] == 3 and s["google_graded"] == 1 and s["primary_tokens"]["input_tokens"] == 300
