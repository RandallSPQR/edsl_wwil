"""Follow-up study: reversed note (priming vs belief-tracking). DRAFT, not frozen.

Conditions per (category, target persona): placebo, full, reversed.
  full      the frozen first-study note: the target's beliefs (personas.json, unchanged).
  reversed  the same beliefs, same cue vocabulary, valence flipped (reversed_notes.json).
  placebo   a disjoint pool persona's beliefs in the full wording (design.json).
All three carry the same frozen neutral filler (see private_notes), so the conditions differ only
by content. The scaffold, public prompt (v3), target side and
grader are the frozen first-study instrument, imported unchanged.
"""

from __future__ import annotations

import difflib
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from . import DATA_DIR
from .conditions import (NOTE_HEADER, SYSTEM_SCAFFOLD, _belief_lines, _pad_to_words, _word_count,
                         public_user_prompt)
from .personas import Belief, Instrument, Persona
from .pipeline import Cell

REV_DIR = DATA_DIR.parent / "perfect_lie_reversed"
CONDITIONS = ("placebo", "full", "reversed")


def load_reversed() -> Dict:
    return json.loads((REV_DIR / "reversed_notes.json").read_text())


def load_design() -> Dict:
    return json.loads((REV_DIR / "design.json").read_text())


def load_categories() -> Dict:
    return json.loads((REV_DIR / "categories.json").read_text())


def reversed_beliefs(persona: Persona, rev: Optional[Dict] = None) -> tuple:
    rev = rev or load_reversed()
    texts = rev["reversed"][persona.id]
    if set(texts) != set(persona.cues):
        raise ValueError(f"{persona.id}: reversed cues {sorted(texts)} != full cues {sorted(persona.cues)}")
    return tuple(Belief(b.cue, texts[b.cue], b.strength_rank) for b in persona.beliefs)


def unpadded_notes(target: Persona, placebo: Persona, rev: Optional[Dict] = None) -> Dict[str, str]:
    rev = rev or load_reversed()
    if rev["header"]["full"] != NOTE_HEADER:
        raise ValueError("reversed_notes.json full header differs from the frozen NOTE_HEADER")
    if set(target.cues) & set(placebo.cues):
        raise ValueError(f"placebo {placebo.id} shares cues with target {target.id}")
    return {"full": NOTE_HEADER + _belief_lines(target.beliefs),
            "reversed": rev["header"]["reversed"] + _belief_lines(reversed_beliefs(target, rev)),
            "placebo": NOTE_HEADER + _belief_lines(placebo.beliefs)}


def private_notes(target: Persona, placebo: Persona, rev: Optional[Dict] = None) -> Dict[str, str]:
    """The three notes for one target. Each gets the SAME filler (the frozen neutral sentences, in
    order): as many as the shortest note needs to reach the longest unpadded note. The filler text
    is then identical across conditions; the notes differ only in the header word and beliefs."""
    raw = unpadded_notes(target, placebo, rev)
    shortest = min(raw.values(), key=_word_count)
    filler = _pad_to_words(shortest, max(_word_count(v) for v in raw.values()))[len(shortest):]
    return {k: (v + filler).rstrip() for k, v in raw.items()}


# ------------------------------------------------------------------ lint

def _tok(s: str) -> List[str]:
    return re.findall(r"[A-Za-z']+|[^\sA-Za-z']", s)


def lint_pair(full: str, rev: str, pairs: Sequence[Sequence[str]]) -> Dict:
    """Word-level diff of a full/reversed pair. Passes when every differing span is an allowed
    valence substitution (full side -> reversed side) and nothing else differs."""
    a, b = _tok(full), _tok(rev)
    allowed = {(tuple(_tok(x)), tuple(_tok(y))) for x, y in pairs}
    edits, bad = [], []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        span = (tuple(a[i1:i2]), tuple(b[j1:j2]))
        edits.append([" ".join(span[0]), " ".join(span[1])])
        if op != "replace" or span not in allowed:
            bad.append([op, " ".join(span[0]), " ".join(span[1])])
    return {"edits": edits, "violations": bad, "ok": not bad and bool(edits)}


def lint_all(personas: Dict[str, Persona], rev: Optional[Dict] = None, design: Optional[Dict] = None) -> Dict:
    rev = rev or load_reversed()
    design = design or load_design()
    out = {"header": lint_pair(rev["header"]["full"], rev["header"]["reversed"], rev["valence_pairs"]),
           "beliefs": [], "notes": {}}
    for pid in design["targets"]:
        p = personas[pid]
        for b, rb in zip(p.beliefs, reversed_beliefs(p, rev)):
            res = lint_pair(b.text, rb.text, rev["valence_pairs"])
            out["beliefs"].append({"persona": pid, "cue": b.cue, "full": b.text, "reversed": rb.text,
                                   "words_full": _word_count(b.text), "words_reversed": _word_count(rb.text), **res})
        notes = private_notes(p, personas[design["placebo_for_target"][pid]], rev)
        out["notes"][pid] = {"placebo_persona": design["placebo_for_target"][pid],
                             "words": {k: _word_count(v) for k, v in notes.items()},
                             "unpadded_words": {k: _word_count(v) for k, v in unpadded_notes(
                                 p, personas[design["placebo_for_target"][pid]], rev).items()},
                             "text": notes}
    out["ok"] = out["header"]["ok"] and all(x["ok"] for x in out["beliefs"])
    return out


# ------------------------------------------------------------------ cells and pilots

def make_cell(*, category: str, target_id: str, condition: str, model: Dict, replicate: int,
              temperature: float, top_p: Optional[float], placebo_id: str) -> Cell:
    lv = model["levels"]["off"]
    return Cell(prompt_id=category, category=category, j1=target_id, j2=placebo_id, target_id=target_id,
                placebo_id=placebo_id, condition=condition, model_id=model["id"], model_family=model["family"],
                reasoning_level="off", reasoning=dict(lv["reasoning"]) if lv["reasoning"] is not None else None,
                max_output_tokens=int(lv["max_output_tokens"]), temperature=float(temperature),
                replicate=replicate, provider=dict(model["provider"]) if model.get("provider") else None,
                system_role=bool(model.get("system_role", True)), class_id="C1", prompt_version="v3",
                top_p=top_p)


def liar_prompts(cell: Cell, instrument: Instrument) -> Dict[str, str]:
    notes = private_notes(instrument.personas[cell.target_id], instrument.personas[cell.placebo_id])
    return {"system_prompt": SYSTEM_SCAFFOLD + notes[cell.condition],
            "user_prompt": public_user_prompt(cell.category, "v3")}


def make_run_class():
    """A Run whose liar stage builds the follow-up notes; everything after the liar is the frozen runner."""
    from .runner import Run, check_pin, prompt_word_range

    class FollowupRun(Run):
        def __init__(self, *, namespace: str, **kw):
            super().__init__(mode="pilot", **kw)
            self.namespace = namespace
            from .pipeline import subsample_cell_ids
            self.subsamples = {g["role"]: subsample_cell_ids(self.cells, g["subsample"]["fraction"],
                                                             g["subsample"]["seed"], self.namespace)
                               for g in self.models["graders"] if g.get("subsample")}

        async def _liar(self, cell: Cell, rec: Dict) -> None:
            lp = liar_prompts(cell, self.instrument)
            try:
                out = await self.adapter.acall(role="liar", user_prompt=lp["user_prompt"],
                                               system_prompt=lp["system_prompt"], model_name=cell.model_id,
                                               temperature=cell.temperature, replicate=cell.replicate,
                                               run_namespace=self.namespace, reasoning=cell.reasoning,
                                               max_output_tokens=cell.max_output_tokens, provider=cell.provider,
                                               system_role=cell.system_role, draw_key=f"target={cell.target_id}",
                                               top_p=cell.top_p)
            except Exception:
                await self._charge_failed_call(self.liar_by_id[cell.model_id], cell.max_output_tokens, rec)
                raise
            cost = await self._charge(self.liar_by_id[cell.model_id], out["usage"])
            rec["cost_usd"] = rec.get("cost_usd", 0.0) + cost
            check_pin(cell.provider, out.get("served_provider"), f"liar {cell.model_id}")
            rec.update(lie=out["text"], user_prompt=lp["user_prompt"], liar_system_prompt=lp["system_prompt"],
                       liar_usage=out["usage"], liar_finish_reason=out["finish_reason"],
                       liar_latency_ms=out.get("latency_ms"), lie_words=len((out["text"] or "").split()),
                       liar_generation_id=out.get("generation_id"), liar_served_provider=out.get("served_provider"),
                       liar_provider_pin=cell.provider, liar_system_role=cell.system_role,
                       liar_delivered_messages=out.get("delivered_messages"),
                       lie_word_range=list(prompt_word_range("v3")),
                       liar_rendered_system_prompt=out.get("system_prompt"))

    return FollowupRun
