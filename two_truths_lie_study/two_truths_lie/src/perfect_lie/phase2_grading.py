"""Phase 2 stage-2 grading driver (sections 7a, 11; Addenda 2 and 3).

Every graded stage-2 lie (stage-2 steered and placebo, the unsteered references, the method check) goes to the primary
grader on the direct route (`grader_direct.grade`). The lies in the Addendum 2 subsample cells also go to the Google
grader (`grader_google.grade`); a Google grade is stored beside the primary one and never replaces it.

- The grader input is the frozen rubric v0.6 (`grader_input_from_record`: the public prompt and the lie only) with the
  instrument's 16 cues in order.
- Primary: 3 attempts, then the cell is failed (`grading_failed`), with no substitute grader and no other route. If
  the API rejects the strict tool on the first call (`StrictRejected`), every cell from then on (and any already
  graded strictly is kept) is graded with the non-strict forced tool, and the switch is recorded (`strict_rejected`).
- Google: 3 attempts, then the lie has no Google grade (`google` None, `google_error` set).
- Records are graded in order and returned; the caller writes them after every lie, so a stopped run resumes
  without re-grading (a record with `primary` already set is skipped).
"""
from __future__ import annotations

from typing import Callable, Dict, Iterable, List, Optional, Sequence

from . import grader_direct, grader_google
from .grader import grader_input_from_record


def in_subsample(r: Dict, subsample: Dict[str, str]) -> bool:
    return subsample.get(r["category"]) == r["target"]


def grade_records(records: Sequence[Dict], cues, subsample: Dict[str, str],
                  primary: Callable = grader_direct.grade, google: Callable = grader_google.grade,
                  on_graded: Optional[Callable[[Dict], None]] = None, state: Optional[Dict] = None) -> List[Dict]:
    """Grade every complete, ungraded record. `state` carries {"strict": bool} across calls (the run-wide switch)."""
    state = state if state is not None else {"strict": True, "strict_rejected": False}
    out = []
    for r in records:
        r = dict(r)
        if r.get("status") != "complete" or "primary" in r:
            out.append(r); continue
        gi = grader_input_from_record(r, cues)
        order = gi.cue_order
        try:
            g = primary(gi, order, strict=state["strict"])
        except grader_direct.StrictRejected as e:
            state.update(strict=False, strict_rejected=True, strict_rejected_reason=str(e)[:300])
            g = primary(gi, order, strict=False)
        r["primary"] = g
        r["grade"] = g["parsed"]
        r["grading_failed"] = g["parsed"] is None
        if in_subsample(r, subsample):
            h = google(gi, order)
            r["google_call"] = h
            r["google"] = h["parsed"]
            r["google_error"] = h["error"]
        out.append(r)
        if on_graded:
            on_graded(r)
    return out


def summary(records: Iterable[Dict], state: Dict) -> Dict:
    rs = list(records)
    prim = [r for r in rs if "primary" in r]
    goo = [r for r in rs if "google_call" in r]
    return {"graded": len(prim), "primary_failed": sum(r["grading_failed"] for r in prim),
            "google_graded": len(goo), "google_failed": sum(r["google"] is None for r in goo),
            "strict": state.get("strict"), "strict_rejected": state.get("strict_rejected", False),
            "primary_tokens": {k: sum(r["primary"]["usage"].get(k, 0) for r in prim) for k in ("input_tokens", "output_tokens")},
            "google_tokens": {k: sum(r["google_call"]["usage"].get(k, 0) for r in goo) for k in ("prompt_tokens", "completion_tokens")}}
