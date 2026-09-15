"""The four identification invariants of PERFECT_LIE.md §2, plus design validity.

None of these tests calls a model. The EDSL-level checks use Model("test").
"""

import itertools
import os
import re

import pytest

from src.perfect_lie import CONDITIONS
from src.perfect_lie.conditions import (
    NOTE_HEADER, SYSTEM_SCAFFOLD, build_liar_prompts, build_private_note, pair_full_words,
    public_user_prompt, target_user_prompt,
)
from src.perfect_lie.grader import build_grader_input, parse_grader_output
from src.perfect_lie.personas import load_instrument


@pytest.fixture(scope="module")
def instrument():
    return load_instrument()


def _category(instrument, prompt_id):
    return next(p.category for p in instrument.prompts if p.id == prompt_id)


# ---------------------------------------------------------------- Test 1

def test_1_public_environment_byte_identical_across_conditions(instrument):
    """E_t (liar user prompt, target template) is identical across conditions and targets."""
    for row in instrument.design:
        cat = _category(instrument, row.prompt_id)
        renders = {
            (cond, t): build_liar_prompts(cond, row, t, instrument.personas, cat)
            for cond in CONDITIONS for t in row.targets
        }
        users = {lp.user_prompt for lp in renders.values()}
        assert len(users) == 1, f"{row.prompt_id}: liar user prompt varies across conditions/targets"
        assert users.pop() == public_user_prompt(cat)
        # System prompts differ across conditions, but every one starts with the same scaffold
        # and the `none` system prompt is exactly the scaffold.
        for (cond, t), lp in renders.items():
            assert lp.system_prompt.startswith(SYSTEM_SCAFFOLD)
            if cond == "none":
                assert lp.system_prompt == SYSTEM_SCAFFOLD
    # Target-facing template is a pure function of the story slot.
    assert target_user_prompt("S") == target_user_prompt("S")
    assert target_user_prompt("A") != target_user_prompt("B")


def test_1_private_information_never_in_public_prompt(instrument):
    """No persona belief text, persona id, or condition label appears in E_t."""
    for row in instrument.design:
        public = public_user_prompt(_category(instrument, row.prompt_id))
        for p in instrument.personas.values():
            assert p.id not in public
            assert p.name not in public
            for b in p.beliefs:
                assert b.text not in public
        for cond in ("placebo", "partial", "full"):
            assert not re.search(rf"\b{cond}\b", public, flags=re.IGNORECASE)


@pytest.mark.skipif(os.environ.get("PERFECT_LIE_SKIP_EDSL") == "1", reason="EDSL not available")
def test_1_edsl_rendered_prompts_carry_block_in_system_only(instrument):
    """At the EDSL layer, the rendered user prompt equals E_t and the system prompt
    begins with the private block, for every condition, using the offline test model."""
    edsl = pytest.importorskip("edsl")
    os.environ["EDSL_RUNNING_IN_PYTEST"] = "True"
    from src.edsl_adapter import PerfectLieAdapter
    adapter = PerfectLieAdapter(service_name=None)
    row = instrument.design[0]
    cat = _category(instrument, row.prompt_id)
    rendered_users = set()
    for cond in CONDITIONS:
        for t in row.targets:
            lp = build_liar_prompts(cond, row, t, instrument.personas, cat)
            r = adapter.render(lp.user_prompt, lp.system_prompt, "test", 1.0, seed=1)
            assert r["user_prompt"] == lp.user_prompt
            assert r["system_prompt"].startswith(lp.system_prompt)
            rendered_users.add(r["user_prompt"])
            # The block text must not have leaked into the user prompt.
            if cond != "none":
                assert NOTE_HEADER.strip() not in r["user_prompt"]
    assert len(rendered_users) == 1


def test_1_edsl_seed_separates_cache_keys():
    """Replicates with identical prompts must not collapse into one cached response."""
    pytest.importorskip("edsl")
    from edsl.caching.cache_entry import CacheEntry
    keys = {
        CacheEntry.gen_key(model="m", parameters={"temperature": 1.0, "seed": s},
                           system_prompt="s", user_prompt="u", iteration=0)
        for s in range(1, 6)
    }
    assert len(keys) == 5


# ---------------------------------------------------------------- Test 2

def test_2_placebo_yoked_within_pair_and_names_neither_target(instrument):
    for row in instrument.design:
        cat = _category(instrument, row.prompt_id)
        j1, j2 = row.targets
        s1 = build_liar_prompts("placebo", row, j1, instrument.personas, cat).system_prompt
        s2 = build_liar_prompts("placebo", row, j2, instrument.personas, cat).system_prompt
        assert s1 == s2, f"{row.prompt_id}: placebo block differs between {j1} and {j2}"
        assert row.placebo not in (j1, j2)
        for t in (j1, j2):
            p = instrument.personas[t]
            assert p.id not in s1 and p.name not in s1
            for b in p.beliefs:
                # A target's belief text never appears in the placebo block, even when
                # the placebo persona shares a cue with the target.
                assert b.text not in s1, f"{row.prompt_id}: placebo names target {t} belief {b.cue}"


def test_2_placebo_length_matched_to_full(instrument):
    for row in instrument.design:
        cat = _category(instrument, row.prompt_id)
        placebo = build_liar_prompts("placebo", row, row.j1, instrument.personas, cat).system_prompt
        for t in row.targets:
            full = build_liar_prompts("full", row, t, instrument.personas, cat).system_prompt
            diff = abs(len(placebo.split()) - len(full.split()))
            assert diff <= 8, f"{row.prompt_id}/{t}: placebo vs full word count differs by {diff}"


def test_2_placebo_filler_is_cue_neutral(instrument):
    from src.perfect_lie.conditions import FILLER_SENTENCES
    banned = {c.id.replace("_", " ") for c in instrument.cues} | {"date", "number", "expert", "family", "witness", "source", "emotion", "joke", "doubt"}
    for s in FILLER_SENTENCES:
        for word in banned:
            assert word not in s.lower(), f"filler {s!r} mentions {word!r}"


# ---------------------------------------------------------------- Test 3

def test_3_grader_input_is_blind(instrument):
    """No persona id/name, no condition label, no target id; full ontology in fixed order."""
    row = instrument.design[0]
    public = public_user_prompt(_category(instrument, row.prompt_id))
    lie = "On 14 March 1987 my grandmother saw the lake freeze in under an hour."
    gi = build_grader_input(public, lie, instrument.cues)
    text = gi.system_prompt + "\n" + gi.user_prompt
    for p in instrument.personas.values():
        assert p.id not in text
        assert p.name not in text
        for b in p.beliefs:
            assert b.text not in text
    for word in ("placebo", "partial", "full", "condition", "persona", "personas", "target"):
        assert not re.search(rf"\b{word}\b", text, flags=re.IGNORECASE), f"grader input mentions {word!r}"
    # Full ontology, fixed order, positions increasing.
    ids = [c.id for c in instrument.cues]
    assert list(gi.cue_order) == ids
    positions = [gi.system_prompt.index(f" {cid}: ") for cid in ids]
    assert positions == sorted(positions)
    for c in instrument.cues:
        assert c.definition in gi.system_prompt


def test_3_grader_input_identical_up_to_public_prompt_and_lie(instrument):
    """The rubric (system prompt) is byte-identical for every call."""
    rows = instrument.design
    systems = {
        build_grader_input(public_user_prompt(_category(instrument, r.prompt_id)), f"lie {i}", instrument.cues).system_prompt
        for i, r in enumerate(rows)
    }
    assert len(systems) == 1


def test_3_grader_output_parser_requires_every_cue(instrument):
    ids = [c.id for c in instrument.cues]
    good = {"cues": {i: False for i in ids}, "counts": {i: 0 for i in ids}, "confidence": 7}
    import json
    parsed = parse_grader_output("prefix " + json.dumps(good) + " suffix", ids)
    assert list(parsed["cues"]) == ids
    bad = dict(good); bad["cues"] = {i: False for i in ids[:-1]}
    with pytest.raises(ValueError):
        parse_grader_output(json.dumps(bad), ids)


# ---------------------------------------------------------------- Test 4

def test_4_partial_uses_exactly_prespecified_partial_cues(instrument):
    for row in instrument.design:
        cat = _category(instrument, row.prompt_id)
        for t in row.targets:
            p = instrument.personas[t]
            note = build_liar_prompts("partial", row, t, instrument.personas, cat).system_prompt
            used = [b for b in p.beliefs if b.text in note]
            assert [b.cue for b in used] == [b.cue for b in p.beliefs if b.cue in p.partial_cues]
            assert len(used) == 2
            assert set(b.cue for b in used) == set(p.partial_cues)
            # Nothing from any other persona.
            for other in instrument.personas.values():
                if other.id == t:
                    continue
                for b in other.beliefs:
                    if b.text in note:
                        raise AssertionError(f"{row.prompt_id}/{t}: partial note contains {other.id} belief {b.cue}")


def test_4_partial_is_deterministic_never_a_redraw(instrument):
    row = instrument.design[0]
    cat = _category(instrument, row.prompt_id)
    notes = {build_liar_prompts("partial", row, row.j1, instrument.personas, cat).system_prompt for _ in range(20)}
    assert len(notes) == 1


def test_4_partial_cues_are_neither_strongest_nor_weakest(instrument):
    for p in instrument.personas.values():
        n = len(p.beliefs)
        for cue in p.partial_cues:
            r = p.belief_for(cue).strength_rank
            assert 1 < r < n


# ---------------------------------------------------------------- design validity

def test_design_rotation_and_placebo(instrument):
    """Each persona on 2 prompts with 2 different partners; placebo not in pair; each persona placebo once."""
    partners = {pid: [] for pid in instrument.personas}
    placebo_uses = {pid: 0 for pid in instrument.personas}
    for row in instrument.design:
        partners[row.j1].append(row.j2)
        partners[row.j2].append(row.j1)
        placebo_uses[row.placebo] += 1
        assert row.placebo not in row.pair
        assert not set(instrument.personas[row.j1].cues) & set(instrument.personas[row.j2].cues)
    for pid, ps in partners.items():
        assert len(ps) == 2 and ps[0] != ps[1], pid
    assert all(n == 1 for n in placebo_uses.values())


def test_every_belief_maps_to_one_ontology_cue(instrument):
    cue_ids = {c.id for c in instrument.cues}
    for p in instrument.personas.values():
        assert len({b.cue for b in p.beliefs}) == len(p.beliefs)
        assert {b.cue for b in p.beliefs} <= cue_ids


def test_condition_set_is_exactly_four():
    assert CONDITIONS == ("none", "placebo", "partial", "full")
    with pytest.raises(ValueError):
        build_private_note("bogus", None, None, 0)
