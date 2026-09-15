"""Cell enumeration and the --dry-run cost estimate.

Nothing in this module calls a model. Execution (Phase 2 --pilot, Phase 3 full
run) is added after the cost estimate is approved.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Optional

from . import CONDITIONS, DATA_DIR
from .conditions import build_liar_prompts, target_system_prompt, target_user_prompt
from .grader import build_grader_input
from .personas import Instrument, load_instrument

DEFAULT_REPLICATES = (1, 2, 3, 4, 5)


@dataclass(frozen=True)
class Cell:
    prompt_id: str
    category: str
    j1: str
    j2: str
    target_id: str
    placebo_id: str
    condition: str
    model_id: str
    model_family: str
    replicate: int

    @property
    def unit_key(self) -> tuple:
        """The paired-comparison unit u = (prompt, pair, condition, model, replicate)."""
        return (self.prompt_id, self.j1, self.j2, self.condition, self.model_id, self.replicate)


def load_models(path: Optional[Path] = None) -> Dict:
    return json.loads((path or DATA_DIR / "models.json").read_text())


def enumerate_cells(
    instrument: Instrument,
    models: Dict,
    replicates=DEFAULT_REPLICATES,
    liar_model_ids: Optional[List[str]] = None,
) -> Iterator[Cell]:
    liars = models["liar_models"]
    if liar_model_ids is not None:
        liars = [m for m in liars if m["id"] in liar_model_ids]
    cat_by_prompt = {p.id: p.category for p in instrument.prompts}
    for row in instrument.design:
        for target_id in row.targets:
            for condition in CONDITIONS:
                for m in liars:
                    for replicate in replicates:
                        yield Cell(
                            prompt_id=row.prompt_id, category=cat_by_prompt[row.prompt_id],
                            j1=row.j1, j2=row.j2, target_id=target_id, placebo_id=row.placebo,
                            condition=condition, model_id=m["id"], model_family=m["family"], replicate=replicate,
                        )


# ---------------------------------------------------------------- cost

def _tokens(text: str, words_to_tokens: float) -> int:
    return int(round(len(text.split()) * words_to_tokens))


@dataclass
class CostLine:
    label: str
    model_id: str
    calls: int
    input_tokens: int
    output_tokens: int
    usd: float


@dataclass
class CostEstimate:
    n_cells: int
    n_units: int
    gameplay: List[CostLine]
    grader: List[CostLine]
    price_source: str
    price_fetched_at: Optional[str]

    @property
    def gameplay_usd(self) -> float:
        return sum(l.usd for l in self.gameplay)

    @property
    def grader_usd(self) -> float:
        return sum(l.usd for l in self.grader)

    @property
    def total_usd(self) -> float:
        return self.gameplay_usd + self.grader_usd

    def to_dict(self) -> dict:
        d = asdict(self)
        d.update(gameplay_usd=self.gameplay_usd, grader_usd=self.grader_usd, total_usd=self.total_usd)
        return d


def estimate_cost(instrument: Instrument, models: Dict, cells: List[Cell]) -> CostEstimate:
    ta = models["token_assumptions"]
    w2t = ta["words_to_tokens"]
    liar_by_id = {m["id"]: m for m in models["liar_models"]}
    target = models["target_model"]
    grader = models["grader_model"]
    cat_by_prompt = {p.id: p.category for p in instrument.prompts}
    design_by_prompt = {r.prompt_id: r for r in instrument.design}

    # Liar: measured user prompt tokens (per category) + assumed system tokens per condition.
    liar_lines: Dict[str, CostLine] = {}
    liar_output = ta["liar_output_tokens"]
    target_in_total = target_out_total = 0
    grader_in_total = grader_out_total = 0
    # Measure the exact texts for one representative cell per (prompt, condition, target).
    sys_cache: Dict[tuple, int] = {}
    user_cache: Dict[str, int] = {}
    grader_sys_tokens = _tokens(build_grader_input("", "", instrument.cues).system_prompt, w2t)
    grader_fixed_user = _tokens(build_grader_input("", "", instrument.cues).user_prompt, w2t)
    target_fixed = _tokens(target_user_prompt(""), w2t)

    for c in cells:
        key = (c.prompt_id, c.condition, c.target_id)
        if key not in sys_cache:
            lp = build_liar_prompts(c.condition, design_by_prompt[c.prompt_id], c.target_id,
                                    instrument.personas, cat_by_prompt[c.prompt_id])
            sys_cache[key] = _tokens(lp.system_prompt, w2t)
            user_cache[c.prompt_id] = _tokens(lp.user_prompt, w2t)
        in_tok = sys_cache[key] + user_cache[c.prompt_id]
        line = liar_lines.get(c.model_id)
        if line is None:
            line = liar_lines[c.model_id] = CostLine(f"liar[{c.model_family}]", c.model_id, 0, 0, 0, 0.0)
        line.calls += 1
        line.input_tokens += in_tok
        line.output_tokens += liar_output

        # Target: persona system prompt + template + the lie.
        tsys = _tokens(target_system_prompt(instrument.personas[c.target_id]), w2t)
        target_in_total += tsys + target_fixed + liar_output
        target_out_total += ta["target_output_tokens"]

        # Grader: rubric + public prompt + the lie.
        grader_in_total += grader_sys_tokens + grader_fixed_user + user_cache[c.prompt_id] + liar_output
        grader_out_total += ta["grader_output_tokens"]

    for mid, line in liar_lines.items():
        p = liar_by_id[mid]
        line.usd = line.input_tokens / 1000 * p["usd_per_1k_input"] + line.output_tokens / 1000 * p["usd_per_1k_output"]

    target_line = CostLine(
        "target", target["id"], len(cells), target_in_total, target_out_total,
        target_in_total / 1000 * target["usd_per_1k_input"] + target_out_total / 1000 * target["usd_per_1k_output"],
    )
    grader_line = CostLine(
        "grader", grader["id"], len(cells), grader_in_total, grader_out_total,
        grader_in_total / 1000 * grader["usd_per_1k_input"] + grader_out_total / 1000 * grader["usd_per_1k_output"],
    )
    n_units = len({c.unit_key for c in cells})
    return CostEstimate(
        n_cells=len(cells), n_units=n_units,
        gameplay=list(liar_lines.values()) + [target_line], grader=[grader_line],
        price_source=models.get("price_source", ""), price_fetched_at=models.get("price_fetched_at"),
    )


def format_estimate(est: CostEstimate, replicates, liar_ids) -> str:
    out = []
    out.append(f"cells (lies):            {est.n_cells}")
    out.append(f"paired units u:          {est.n_units}")
    out.append(f"replicates:              {list(replicates)}")
    out.append(f"liar models:             {liar_ids}")
    out.append("")
    hdr = f"{'line':22s} {'model':40s} {'calls':>6s} {'in_tok':>10s} {'out_tok':>10s} {'usd':>9s}"
    out.append("GAMEPLAY (liar + target)")
    out.append(hdr)
    for l in est.gameplay:
        out.append(f"{l.label:22s} {l.model_id:40s} {l.calls:6d} {l.input_tokens:10d} {l.output_tokens:10d} {l.usd:9.2f}")
    out.append(f"{'gameplay subtotal':22s} {'':40s} {'':6s} {'':10s} {'':10s} {est.gameplay_usd:9.2f}")
    out.append("")
    out.append("GRADER")
    out.append(hdr)
    for l in est.grader:
        out.append(f"{l.label:22s} {l.model_id:40s} {l.calls:6d} {l.input_tokens:10d} {l.output_tokens:10d} {l.usd:9.2f}")
    out.append(f"{'grader subtotal':22s} {'':40s} {'':6s} {'':10s} {'':10s} {est.grader_usd:9.2f}")
    out.append("")
    out.append(f"TOTAL                                                                                  {est.total_usd:9.2f}")
    out.append("")
    out.append(f"price source: {est.price_source}")
    return "\n".join(out)


# ---------------------------------------------------------------- gates

class PreflightError(RuntimeError):
    """A live run was requested but a setup requirement is unmet."""


def preflight(models: Dict, prompts_raw: Dict, mode: str) -> List[str]:
    """Return the list of unmet requirements for `mode` in {"dry-run", "pilot", "full"}.

    The full run refuses while any price is unverified or any fact prompt lacks
    pilot evidence of fabricability. The pilot is what produces that evidence,
    so it is gated only on the key being present (checked at call time by EDSL).
    """
    problems: List[str] = []
    if mode == "dry-run":
        return problems
    if mode == "full":
        if not models.get("price_fetched_at") or "UNVERIFIED" in str(models.get("price_source", "")):
            problems.append("model prices are UNVERIFIED: run `run_perfect_lie.py --refresh-prices` first")
        for p in prompts_raw["prompts"]:
            fab = p.get("fabricability") or {}
            if fab.get("status") != "verified_in_pilot" or not fab.get("evidence"):
                problems.append(f"prompt {p['id']!r}: fabricability not verified in pilot (status={fab.get('status')!r})")
    return problems
