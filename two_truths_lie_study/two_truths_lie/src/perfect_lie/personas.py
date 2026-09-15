"""Load and validate the cue ontology, personas, fact prompts, and design table.

Everything here is pure data handling; nothing calls a model.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import DATA_DIR


# ---------------------------------------------------------------- hashing

def file_sha256(path: Path) -> str:
    """SHA-256 of a file's bytes. Recorded in PREREG.md and run manifests."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------- cues

@dataclass(frozen=True)
class Cue:
    id: str
    definition: str
    baseline_pressure: str


def load_cues(path: Optional[Path] = None) -> List[Cue]:
    """Return the global cue ontology in file order (the fixed grader order)."""
    path = path or DATA_DIR / "cues.json"
    raw = json.loads(path.read_text())
    cues = [Cue(c["id"], c["definition"], c.get("baseline_pressure", "unknown")) for c in raw["cues"]]
    ids = [c.id for c in cues]
    if len(ids) != len(set(ids)):
        raise ValueError("cues.json contains duplicate cue ids")
    if not (12 <= len(cues) <= 16):
        raise ValueError(f"cues.json must hold 12-16 cues (K), found {len(cues)}")
    return cues


# ---------------------------------------------------------------- personas

@dataclass(frozen=True)
class Belief:
    cue: str
    text: str
    strength_rank: int


@dataclass(frozen=True)
class Persona:
    id: str
    name: str
    summary: str
    beliefs: Tuple[Belief, ...]
    partial_cues: Tuple[str, str]

    @property
    def cues(self) -> Tuple[str, ...]:
        return tuple(b.cue for b in self.beliefs)

    def belief_for(self, cue: str) -> Belief:
        for b in self.beliefs:
            if b.cue == cue:
                return b
        raise KeyError(f"{self.id} has no belief mapped to cue {cue!r}")

    @property
    def partial_beliefs(self) -> Tuple[Belief, ...]:
        """The pre-specified partial beliefs, in belief-list order (never a redraw)."""
        return tuple(b for b in self.beliefs if b.cue in self.partial_cues)


def load_personas(path: Optional[Path] = None, cues: Optional[List[Cue]] = None) -> Dict[str, Persona]:
    """Load personas.json and validate it against the cue ontology."""
    path = path or DATA_DIR / "personas.json"
    cues = cues if cues is not None else load_cues()
    cue_ids = {c.id for c in cues}
    raw = json.loads(path.read_text())

    personas: Dict[str, Persona] = {}
    for p in raw["personas"]:
        beliefs = tuple(Belief(b["cue"], b["text"], int(b["strength_rank"])) for b in p["beliefs"])
        persona = Persona(
            id=p["id"], name=p["name"], summary=p["summary"],
            beliefs=beliefs, partial_cues=tuple(p["partial_cues"]),
        )
        _validate_persona(persona, cue_ids)
        if persona.id in personas:
            raise ValueError(f"duplicate persona id {persona.id}")
        personas[persona.id] = persona

    if len(personas) != 6:
        raise ValueError(f"personas.json must hold exactly 6 personas, found {len(personas)}")
    return personas


def _validate_persona(p: Persona, cue_ids: set) -> None:
    if not (4 <= len(p.beliefs) <= 6):
        raise ValueError(f"{p.id}: personas carry 4-6 beliefs, found {len(p.beliefs)}")
    cues = [b.cue for b in p.beliefs]
    if len(cues) != len(set(cues)):
        raise ValueError(f"{p.id}: each belief must map to a distinct cue")
    unknown = set(cues) - cue_ids
    if unknown:
        raise ValueError(f"{p.id}: beliefs reference cues not in ontology: {sorted(unknown)}")
    ranks = sorted(b.strength_rank for b in p.beliefs)
    if ranks != list(range(1, len(p.beliefs) + 1)):
        raise ValueError(f"{p.id}: strength_rank must be a permutation of 1..{len(p.beliefs)}")
    if len(p.partial_cues) != 2 or len(set(p.partial_cues)) != 2:
        raise ValueError(f"{p.id}: partial_cues must be exactly two distinct cues")
    if not set(p.partial_cues) <= set(cues):
        raise ValueError(f"{p.id}: partial_cues must be a subset of the persona's own cues")
    # Neither strongest nor weakest: ranks strictly inside (1, n).
    n = len(p.beliefs)
    for cue in p.partial_cues:
        r = p.belief_for(cue).strength_rank
        if r in (1, n):
            raise ValueError(f"{p.id}: partial cue {cue} is rank {r}; must be neither strongest (1) nor weakest ({n})")


# ---------------------------------------------------------------- prompts

@dataclass(frozen=True)
class FactPrompt:
    id: str
    category: str


def load_prompts(path: Optional[Path] = None) -> List[FactPrompt]:
    path = path or DATA_DIR / "prompts.json"
    raw = json.loads(path.read_text())
    prompts = [FactPrompt(p["id"], p["category"]) for p in raw["prompts"]]
    if len(prompts) != 6:
        raise ValueError(f"prompts.json must hold exactly 6 fact prompts, found {len(prompts)}")
    if len({p.id for p in prompts}) != 6:
        raise ValueError("prompts.json has duplicate prompt ids")
    return prompts


# ---------------------------------------------------------------- design

@dataclass(frozen=True)
class DesignRow:
    """One fact prompt with its persona pair and the pair's fixed placebo persona."""
    prompt_id: str
    j1: str
    j2: str
    placebo: str

    @property
    def pair(self) -> Tuple[str, str]:
        return (self.j1, self.j2)

    @property
    def targets(self) -> Tuple[str, str]:
        return (self.j1, self.j2)


def load_design(
    path: Optional[Path] = None,
    personas: Optional[Dict[str, Persona]] = None,
    prompts: Optional[List[FactPrompt]] = None,
) -> List[DesignRow]:
    """Load design.json and validate the rotation and placebo assignment."""
    path = path or DATA_DIR / "design.json"
    personas = personas if personas is not None else load_personas()
    prompts = prompts if prompts is not None else load_prompts()
    raw = json.loads(path.read_text())
    rows = [DesignRow(r["prompt_id"], r["j1"], r["j2"], r["placebo"]) for r in raw["rows"]]
    validate_design(rows, personas, prompts)
    return rows


def validate_design(rows: List[DesignRow], personas: Dict[str, Persona], prompts: List[FactPrompt]) -> None:
    prompt_ids = [p.id for p in prompts]
    if [r.prompt_id for r in rows] != prompt_ids:
        raise ValueError("design.json rows must cover the six prompts in prompts.json order, once each")

    appearances: Dict[str, List[str]] = {pid: [] for pid in personas}
    placebo_uses: Dict[str, int] = {pid: 0 for pid in personas}
    for r in rows:
        for pid in (r.j1, r.j2, r.placebo):
            if pid not in personas:
                raise ValueError(f"design row {r.prompt_id}: unknown persona {pid}")
        if r.j1 == r.j2:
            raise ValueError(f"design row {r.prompt_id}: pair must be two distinct personas")
        if r.placebo in (r.j1, r.j2):
            raise ValueError(f"design row {r.prompt_id}: placebo persona {r.placebo} is in the pair")
        # Disjoint cue sets within a pair.
        overlap = set(personas[r.j1].cues) & set(personas[r.j2].cues)
        if overlap:
            raise ValueError(f"design row {r.prompt_id}: pair {r.j1}/{r.j2} share cues {sorted(overlap)}")
        appearances[r.j1].append(r.j2)
        appearances[r.j2].append(r.j1)
        placebo_uses[r.placebo] += 1

    for pid, partners in appearances.items():
        if len(partners) != 2:
            raise ValueError(f"{pid} appears on {len(partners)} prompts; each persona must appear on exactly 2")
        if partners[0] == partners[1]:
            raise ValueError(f"{pid} has the same partner twice; partners must differ")
    for pid, n in placebo_uses.items():
        if n != 1:
            raise ValueError(f"{pid} is the placebo persona {n} times; each persona serves as placebo exactly once")


# ---------------------------------------------------------------- bundle

@dataclass(frozen=True)
class Instrument:
    cues: List[Cue]
    personas: Dict[str, Persona]
    prompts: List[FactPrompt]
    design: List[DesignRow]
    hashes: Dict[str, str]


def load_instrument(data_dir: Optional[Path] = None) -> Instrument:
    d = data_dir or DATA_DIR
    cues = load_cues(d / "cues.json")
    personas = load_personas(d / "personas.json", cues)
    prompts = load_prompts(d / "prompts.json")
    design = load_design(d / "design.json", personas, prompts)
    hashes = {name: file_sha256(d / f"{name}.json") for name in ("cues", "personas", "prompts", "design")}
    return Instrument(cues, personas, prompts, design, hashes)
