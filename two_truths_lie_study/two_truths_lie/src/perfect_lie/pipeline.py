"""Model classes, cell enumeration, the --dry-run cost estimate, and run gates.

Nothing in this module calls a model. models.json holds every class; a run works on
one class at a time through select_class(), which returns a view whose liar_models
and target_models are that class's.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Optional

from . import CONDITIONS, DATA_DIR
from .conditions import build_liar_prompts, target_system_prompt, target_user_prompt
from .grader import build_grader_input
from .personas import Instrument, load_instrument

DEFAULT_REPLICATES = (1, 2, 3, 4, 5)
REASONING_LEVELS = ("off", "low", "high")
TIERS = {"tier1": ("off",), "tier2": ("low", "high"), "all": REASONING_LEVELS}


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
    reasoning_level: str
    reasoning: Optional[Dict]  # OpenRouter unified `reasoning` field for this level; None = not sent
    max_output_tokens: int
    temperature: float        # fixed per family, identical at every level
    replicate: int
    provider: Optional[Dict] = None   # OpenRouter provider routing (pin), None = default routing
    system_role: bool = True          # False: private block folded into the user turn (Gemma)
    class_id: str = ""
    prompt_version: str = ""          # public prompt version (prompts.json); "" = active
    top_p: Optional[float] = None     # sampling exception (Llama 3.1 8B); None = EDSL default

    @property
    def unit_key(self) -> tuple:
        """The paired-comparison unit u = (prompt, pair, condition, model, level, replicate)."""
        return (self.prompt_id, self.j1, self.j2, self.condition, self.model_id, self.reasoning_level, self.replicate)

    @property
    def tier(self) -> str:
        return "tier1" if self.reasoning_level == "off" else "tier2"


def load_models(path: Optional[Path] = None) -> Dict:
    """The whole models file, validated across every class. Use select_class() for a run."""
    models = json.loads((path or DATA_DIR / "models.json").read_text())
    validate_models(models)
    return models


def select_class(models: Dict, class_id: str) -> Dict:
    """A view of the models file for one class: liar_models and target_models are the
    class's; graders, trace probe, token assumptions and prices are shared."""
    if class_id not in models["classes"]:
        raise ValueError(f"unknown class {class_id!r}; classes: {sorted(models['classes'])}")
    c = models["classes"][class_id]
    view = {k: v for k, v in models.items() if k != "classes"}
    view.update(class_id=class_id, class_name=c.get("name"), class_status=c.get("status"),
                liar_models=c["liar_models"], target_models=c["target_models"])
    return view


def _validate_liar(models: Dict, m: Dict) -> None:
    if "temperature" not in m:
        raise ValueError(f"{m['id']}: a single family-level temperature is required")
    levels = m["levels"]
    for name, lv in levels.items():
        if "temperature" in lv:
            raise ValueError(f"{m['id']}/{name}: temperature must not vary by reasoning level")
    if "off" not in levels:
        raise ValueError(f"{m['id']}: every family needs an `off` level (Tier 1)")
    unknown = set(levels) - set(REASONING_LEVELS)
    if unknown:
        raise ValueError(f"{m['id']}: unknown reasoning levels {sorted(unknown)}")
    for name, lv in levels.items():
        if "reasoning" not in lv or "expected_thinking_tokens" not in lv or "max_output_tokens" not in lv:
            raise ValueError(f"{m['id']}/{name}: level needs reasoning, expected_thinking_tokens, max_output_tokens")
        if lv["max_output_tokens"] < lv["expected_thinking_tokens"] + models["reasoning_design"]["story_output_tokens"]:
            raise ValueError(f"{m['id']}/{name}: max_output_tokens must exceed thinking + story")
    off = levels["off"]["reasoning"]
    if not m.get("reasoning_capable", True):
        if off is not None or set(levels) != {"off"}:
            raise ValueError(f"{m['id']}: a model without a reasoning mode has only `off`, with reasoning null")
    elif m.get("true_off_available", False):
        if off != {"enabled": False}:
            raise ValueError(f"{m['id']}: true_off_available but off level is {off}")
    elif not m.get("true_off_note"):
        raise ValueError(f"{m['id']}: no true off level; document the exception in true_off_note")
    if m.get("weights") == "open" and m.get("provider") and "bf16" not in (m["provider"].get("quantizations") or []):
        raise ValueError(f"{m['id']}: an open-weight pin must require bf16 so pod replay matches")


def validate_models(models: Dict) -> None:
    for cid, c in models["classes"].items():
        if c.get("status") not in ("proposed", "approved", "retired"):
            raise ValueError(f"class {cid}: status must be proposed, approved or retired")
        ids = [m["id"] for m in c["liar_models"]]
        if len(ids) != len(set(ids)):
            raise ValueError(f"class {cid}: duplicate liar ids")
        for m in c["liar_models"]:
            _validate_liar(models, m)
        tids = [t["id"] for t in c["target_models"]]
        if not set(ids) <= set(tids):
            raise ValueError(f"class {cid}: every liar must also be a target (liar x target crossing)")
        for t in c["target_models"]:
            if "temperature" not in t or "max_output_tokens" not in t:
                raise ValueError(f"{cid}/{t['id']}: target needs temperature and max_output_tokens")
    roles = [g["role"] for g in models["graders"]]
    if roles.count("primary") != 1 or len(roles) != len(set(roles)):
        raise ValueError("graders need unique roles and exactly one role=primary")
    for e in [models.get("trace_probe") or {}] + list(models["graders"]):
        if e and ("temperature" not in e or "max_output_tokens" not in e):
            raise ValueError(f"{e.get('id')}: temperature and max_output_tokens are required")


def enumerate_cells(
    instrument: Instrument,
    models: Dict,
    replicates=DEFAULT_REPLICATES,
    liar_model_ids: Optional[List[str]] = None,
    levels=REASONING_LEVELS,
    prompt_version: Optional[str] = None,
    conditions=CONDITIONS,
) -> Iterator[Cell]:
    from .conditions import active_prompt_version
    prompt_version = prompt_version or active_prompt_version()
    liars = models["liar_models"]
    if liar_model_ids is not None:
        liars = [m for m in liars if m["id"] in liar_model_ids]
    cat_by_prompt = {p.id: p.category for p in instrument.prompts}
    for row in instrument.design:
        for target_id in row.targets:
            for condition in [c for c in CONDITIONS if c in conditions]:
                for m in liars:
                    for level in levels:
                        lv = m["levels"].get(level)
                        if lv is None:
                            continue  # family lacks this level (documented in models.json)
                        for replicate in replicates:
                            yield Cell(
                                prompt_id=row.prompt_id, category=cat_by_prompt[row.prompt_id],
                                j1=row.j1, j2=row.j2, target_id=target_id, placebo_id=row.placebo,
                                condition=condition, model_id=m["id"], model_family=m["family"],
                                reasoning_level=level,
                                reasoning=dict(lv["reasoning"]) if lv["reasoning"] is not None else None,
                                max_output_tokens=int(lv["max_output_tokens"]),
                                temperature=float(m["temperature"]), replicate=replicate,
                                provider=dict(m["provider"]) if m.get("provider") else None,
                                system_role=bool(m.get("system_role", True)),
                                class_id=models.get("class_id", ""),
                                prompt_version=prompt_version,
                                top_p=m.get("top_p"),
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
    n_cells_by_tier: Dict[str, int]
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


def _usd(price: Dict, in_tok: int, out_tok: int) -> float:
    return in_tok / 1000 * price["usd_per_1k_input"] + out_tok / 1000 * price["usd_per_1k_output"]


def estimate_cost(instrument: Instrument, models: Dict, cells: List[Cell], liar_only: bool = False,
                  include_trace_probe: bool = False, include_elicitation: bool = False) -> CostEstimate:
    ta = models["token_assumptions"]
    w2t = ta["words_to_tokens"]
    liar_by_id = {m["id"]: m for m in models["liar_models"]}
    targets = models["target_models"]
    cat_by_prompt = {p.id: p.category for p in instrument.prompts}
    design_by_prompt = {r.prompt_id: r for r in instrument.design}
    story_out = ta["liar_output_tokens"]

    sys_cache: Dict[tuple, int] = {}
    user_cache: Dict[str, int] = {}
    gi0 = build_grader_input("", "", instrument.cues)
    grader_sys_tokens = _tokens(gi0.system_prompt, w2t)
    grader_fixed_user = _tokens(gi0.user_prompt, w2t)
    target_fixed = _tokens(target_user_prompt(""), w2t)

    liar_lines: Dict[tuple, CostLine] = {}
    target_in = target_out = 0
    grader_in = grader_out = 0
    trace_cells = 0
    tier_counts: Dict[str, int] = {}

    for c in cells:
        tier_counts[c.tier] = tier_counts.get(c.tier, 0) + 1
        key = (c.prompt_id, c.condition, c.target_id, c.prompt_version)
        if key not in sys_cache:
            lp = build_liar_prompts(c.condition, design_by_prompt[c.prompt_id], c.target_id,
                                    instrument.personas, cat_by_prompt[c.prompt_id], c.prompt_version or None)
            sys_cache[key] = _tokens(lp.system_prompt, w2t)
            user_cache[c.prompt_id] = _tokens(lp.user_prompt, w2t)
        in_tok = sys_cache[key] + user_cache[c.prompt_id]
        think = liar_by_id[c.model_id]["levels"][c.reasoning_level]["expected_thinking_tokens"]
        lk = (c.model_id, c.reasoning_level)
        line = liar_lines.get(lk)
        if line is None:
            line = liar_lines[lk] = CostLine(f"liar[{c.model_family}/{c.reasoning_level}]", c.model_id, 0, 0, 0, 0.0)
        line.calls += 1
        line.input_tokens += in_tok
        line.output_tokens += story_out + think
        if c.reasoning_level != "off":
            trace_cells += 1

        tsys = _tokens(target_system_prompt(instrument.personas[c.target_id]), w2t)
        target_in += tsys + target_fixed + story_out
        target_out += ta["target_output_tokens"]

        grader_in += grader_sys_tokens + grader_fixed_user + user_cache[c.prompt_id] + story_out
        grader_out += ta["grader_output_tokens"]

    for (mid, _), line in liar_lines.items():
        line.usd = _usd(liar_by_id[mid], line.input_tokens, line.output_tokens)

    # Every lie is read by every target in the class panel (liar family x target family).
    target_lines = [CostLine(f"target[{t.get('family', '?')}]", t["id"], len(cells), target_in, target_out,
                             _usd(t, target_in, target_out)) for t in targets]
    if liar_only:
        n_units = len({c.unit_key for c in cells})
        return CostEstimate(
            n_cells=len(cells), n_units=n_units, n_cells_by_tier=dict(sorted(tier_counts.items())),
            gameplay=list(liar_lines.values()), grader=[],
            price_source=models.get("price_source", ""), price_fetched_at=models.get("price_fetched_at"),
        )

    grader_lines = []
    for g in models["graders"]:
        frac = (g.get("subsample") or {}).get("fraction", 1.0)
        n = round(len(cells) * frac)
        gin = round(grader_in * frac)
        out = round(grader_out * frac) + n * g.get("expected_thinking_tokens", 0)
        label = f"grader[{g['role']}]" + (f" {frac:.0%}" if frac < 1 else "")
        grader_lines.append(CostLine(label, g["id"], n, gin, out, _usd(g, gin, out)))
    if include_elicitation and cells:
        # One more liar call per cell (the conversation so far + the question; a short answer),
        # and every grader codes the answer (rubric + short answer).
        from .grader import build_bhat_grader_input
        from .conditions import ELICITATION_QUESTION
        el_out = 120
        bh = build_bhat_grader_input(ELICITATION_QUESTION, " ".join(["word"] * 90), instrument.cues)
        bh_in = _tokens(bh.system_prompt + bh.user_prompt, w2t)
        el_lines: Dict[str, CostLine] = {}
        for c in cells:
            in_tok = sys_cache[(c.prompt_id, c.condition, c.target_id, c.prompt_version)] + user_cache[c.prompt_id] \
                + story_out + _tokens(ELICITATION_QUESTION, w2t)
            line = el_lines.setdefault(c.model_id, CostLine(f"elicit[{c.model_family}]", c.model_id, 0, 0, 0, 0.0))
            line.calls += 1
            line.input_tokens += in_tok
            line.output_tokens += el_out
        for mid, line in el_lines.items():
            line.usd = _usd(liar_by_id[mid], line.input_tokens, line.output_tokens)
        target_lines = target_lines + list(el_lines.values())
        for g in models["graders"]:
            frac = (g.get("subsample") or {}).get("fraction", 1.0)
            n = round(len(cells) * frac)
            out = n * (ta["grader_output_tokens"] + g.get("expected_thinking_tokens", 0))
            label = f"bhat[{g['role']}]" + (f" {frac:.0%}" if frac < 1 else "")
            grader_lines.append(CostLine(label, g["id"], n, n * bh_in, out, _usd(g, n * bh_in, out)))
    tp = models.get("trace_probe")
    if include_trace_probe and tp and trace_cells:
        tin = trace_cells * ta["trace_probe_input_tokens"]
        tout = trace_cells * ta["trace_probe_output_tokens"]
        grader_lines.append(CostLine("trace_probe", tp["id"], trace_cells, tin, tout, _usd(tp, tin, tout)))

    n_units = len({c.unit_key for c in cells})
    return CostEstimate(
        n_cells=len(cells), n_units=n_units, n_cells_by_tier=dict(sorted(tier_counts.items())),
        gameplay=list(liar_lines.values()) + target_lines, grader=grader_lines,
        price_source=models.get("price_source", ""), price_fetched_at=models.get("price_fetched_at"),
    )


def format_estimate(est: CostEstimate, replicates, liar_ids, levels) -> str:
    out = []
    out.append(f"cells (lies):            {est.n_cells}   by tier: {est.n_cells_by_tier}")
    out.append(f"paired units u:          {est.n_units}")
    out.append(f"replicates:              {list(replicates)}")
    out.append(f"reasoning levels:        {list(levels)}")
    out.append(f"liar models:             {liar_ids}")
    out.append("")
    hdr = f"{'line':26s} {'model':32s} {'calls':>6s} {'in_tok':>10s} {'out_tok':>10s} {'usd':>9s}"
    out.append("GAMEPLAY (liar + target)")
    out.append(hdr)
    for l in est.gameplay:
        out.append(f"{l.label:26s} {l.model_id:32s} {l.calls:6d} {l.input_tokens:10d} {l.output_tokens:10d} {l.usd:9.2f}")
    out.append(f"{'gameplay subtotal':26s} {'':32s} {'':6s} {'':10s} {'':10s} {est.gameplay_usd:9.2f}")
    out.append("")
    out.append("GRADER (cue graders + trace probe)")
    out.append(hdr)
    for l in est.grader:
        out.append(f"{l.label:26s} {l.model_id:32s} {l.calls:6d} {l.input_tokens:10d} {l.output_tokens:10d} {l.usd:9.2f}")
    out.append(f"{'grader subtotal':26s} {'':32s} {'':6s} {'':10s} {'':10s} {est.grader_usd:9.2f}")
    out.append("")
    out.append(f"{'TOTAL':26s} {'':32s} {'':6s} {'':10s} {'':10s} {est.total_usd:9.2f}")
    out.append("")
    out.append(f"price source: {est.price_source}")
    return "\n".join(out)


# ---------------------------------------------------------------- gates

class PreflightError(RuntimeError):
    """A live run was requested but a setup requirement is unmet."""


def priced_entries(models: Dict) -> List[Dict]:
    """Every priced entry: for the whole file, all classes; for a class view, that class."""
    if "classes" in models:
        classes = list(models["classes"].values())
        liars = [m for c in classes for m in c["liar_models"]]
        targets = [t for c in classes for t in c["target_models"]]
    else:
        liars, targets = list(models["liar_models"]), list(models["target_models"])
    return liars + targets + list(models["graders"]) + ([models["trace_probe"]] if models.get("trace_probe") else [])


def preflight(models: Dict, prompts_raw: Dict, mode: str, env: Optional[Dict] = None) -> List[str]:
    """Return the list of unmet requirements for `mode` in {"dry-run", "smoke", "pilot", "full"}.

    Every live mode needs the OpenRouter key and verified prices (the runtime spend cap is
    computed from them). The full run additionally needs pilot evidence that every fact
    prompt fabricates. Price verification is checked per entry, not only at the file
    level, so a stale entry cannot hide behind a file-level timestamp.
    """
    problems: List[str] = []
    if mode == "dry-run":
        return problems
    env = os.environ if env is None else env
    if mode in ("pilot", "full") and models.get("class_status") != "approved":
        problems.append(f"class {models.get('class_id')} is {models.get('class_status')!r}; the owner must approve it "
                        "(status 'approved' in models.json) before a pilot or full run. A smoke test may run on a proposed class.")
    key_var = models.get("env_key", "OPEN_ROUTER_API_KEY")
    if not env.get(key_var):
        misnamed = [n for n in ("OPENROUTER_API_KEY", "OPENROUTER_KEY", "OPEN_ROUTER_KEY") if env.get(n)]
        hint = f" ({misnamed[0]} is set, but EDSL reads {key_var}; rename it)" if misnamed else \
            " (put it in two_truths_lie/.env or the environment; check with --check-env)"
        problems.append(f"{key_var} is not set in this environment{hint}")
    if not models.get("price_fetched_at") or "UNVERIFIED" in str(models.get("price_source", "")):
        problems.append("model prices are UNVERIFIED: run `run_perfect_lie.py --refresh-prices` first")
    unverified = []
    for e in priced_entries(models):
        if not e.get("price_verified_at") and e["id"] not in unverified:
            unverified.append(e["id"])
    for mid in unverified:
        problems.append(f"price for {mid!r} has no price_verified_at; refresh prices")
    if mode == "full":
        for p in prompts_raw["prompts"]:
            fab = p.get("fabricability") or {}
            if fab.get("status") != "verified_in_pilot" or not fab.get("evidence"):
                problems.append(f"prompt {p['id']!r}: fabricability not verified in pilot (status={fab.get('status')!r})")
    return problems


SMOKE_CONDITIONS = ("full", "none", "placebo", "partial")


def smoke_cells(instrument: Instrument, models: Dict, per_level: int = 4) -> List[Cell]:
    """A few liar cells per family x level, on the first design row, replicate 1.

    Conditions cycle full, none, placebo, partial so the longest private block is always
    included and `none` lies feed the viability screen for every family.
    """
    row = instrument.design[0]
    out: List[Cell] = []
    all_cells = list(enumerate_cells(instrument, models, replicates=(1,)))
    for m in models["liar_models"]:
        for level in m["levels"]:
            picked = 0
            for cond in SMOKE_CONDITIONS * 2:
                if picked >= per_level:
                    break
                target = row.targets[picked % 2]
                match = [c for c in all_cells if c.prompt_id == row.prompt_id and c.model_id == m["id"]
                         and c.reasoning_level == level and c.condition == cond and c.target_id == target]
                if match and match[0] not in out:
                    out.append(match[0])
                    picked += 1
    return out


# ---------------------------------------------------------------- looks and the robustness subsample

LOOKS = {"interim": tuple(range(1, 16)), "extension": tuple(range(16, 36))}


def look_of(replicate: int) -> str:
    for name, reps in LOOKS.items():
        if replicate in reps:
            return name
    return "outside"


def subsample_cell_ids(cells: List[Cell], fraction: float, seed: int, namespace: str) -> set:
    """Seeded, stratified random subsample: within each (liar model, condition, look) the cells
    are ordered by cell id, shuffled with a seed derived from (seed, stratum, look), and the
    first round(fraction * n) are taken. Deterministic for a given cell set."""
    import random
    from .runner import cell_id
    groups: Dict[tuple, List[str]] = {}
    for c in cells:
        groups.setdefault((c.model_id, c.condition, look_of(c.replicate)), []).append(cell_id(c, namespace))
    chosen = set()
    for key, ids in sorted(groups.items()):
        ids = sorted(ids)
        random.Random(f"{seed}|{key[0]}|{key[1]}|{key[2]}").shuffle(ids)
        chosen.update(ids[:round(fraction * len(ids))])
    return chosen
