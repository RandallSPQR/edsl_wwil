# The Perfect Lie — brief, design, and TODO

One document, per repo convention. Claude Code reads this first. Lives at
`edsl_wwil/two_truths_lie_study/PERFECT_LIE.md`.

Deadline: results and writeup by Nov 13, 2026 (Free Systems Fast Grant window Oct 5 – Nov 13).
Budget: ~$250 OpenRouter credits. Cheap models for gameplay, one larger model as blind grader.

Revision 2.1 (Sept 15): yoked placebo, directional tailoring score, global cue ontology,
pre-specified partial cues, persona-pair rotation, fixed-effect model term, and an explicit
instrument-development phase before preregistration; primary test stated as β_full = T_full − T_placebo, figure zero line at T = 0.

---

## 1. The question

Stigmergy: aᵢ = f(Eₜ)
Strategy:  aᵢ = f(Eₜ, B̂ⱼ, B̂ⱼ(B̂ᵢ), …)

Eₜ is the common trace (the shared transcript). B̂ⱼ is the liar's model of one particular
counterpart's beliefs. The test is whether ∂aᵢ/∂B̂ⱼ ≠ 0 with Eₜ held fixed: whether the lie
moves *in the direction the target's beliefs predict* when what the liar privately knows
about the target moves, and nothing in the shared trace has changed.

**Headline claim, stated narrowly.** The test identifies target-conditioned strategic
adaptation: whether an agent's action changes in the direction predicted by privately
supplied beliefs about a specific counterpart, conditional on an invariant public
environment. It does not claim higher-order theory of mind and it does not claim an
internal representation. It establishes whether B̂ⱼ enters the policy. The Missing Piece
(4×4 game) then asks whether B̂ⱼ(B̂ᵢ) does. The Missing Piece is out of scope for this grant.

The architecture is:

    private belief perturbation  →  directionally predicted rhetorical change,
    holding public state fixed.

The placebo controls for "private perturbation → any textual change." The directional
score establishes the arrow above.

## 2. Identification — four invariants, each backed by a test

1. **B̂ⱼ never enters Eₜ.** Information about the target goes to the liar through the
   liar's system prompt and nowhere else. The shared transcript seen by liar, target, and
   grader is byte-identical across conditions except for the lie itself.
   *Test:* serialize Eₜ for every condition of a fixed (prompt, pair, model, replicate); assert equality.

2. **Placebo is yoked within each paired comparison.** For a given (prompt, pair, model,
   replicate), both targets j₁ and j₂ receive the *same* irrelevant persona C in the placebo
   condition, with C ∉ {j₁, j₂}. Arbitrary sensitivity to private text can then move both
   lies but cannot separate them by target identity.
   *Test:* for every pair, placebo private content is identical across j₁ and j₂ and names
   neither target's persona.

3. **The grader is blind by construction.** The grader receives a fixed global cue ontology
   identical for every lie, every condition, and every target, and scores every lie against
   every cue. It is never told which cues belong to which persona; that mapping happens
   downstream in analysis.
   *Test:* grader input contains no persona id, no condition label, and the full cue list in
   fixed order.

4. **Directional, not distance.** The primary measure is whether the two lies differ *toward
   their respective targets*, not merely whether they differ. See §3, Measures.

5. **The thinking trace never enters the cue grader.** Thinking-tier liars may return a
   reasoning trace. It is stored, and read only by a separate blind trace probe. The cue
   grader's input is built from the public prompt and the lie text alone.
   *Test:* build the grader input from a record carrying a sentinel trace; assert the
   sentinel is absent. The trace probe input contains the trace and nothing else.

## 3. Design

### Why a reasoning tier
Tier 1 alone answers "does B̂ⱼ enter the policy?". The tier answers "what governs whether
it enters?", and each outcome means something different:
- *Baked in:* T_full > 0 at R = off, flat in R. Target-conditioning is a property of the base
  policy, not of deliberation.
- *Emergent with deliberation:* T_full ≈ 0 at R = off, rising in R. B̂ⱼ enters only through
  inference-time computation.
- *Absent at every R:* stigmergy holds even with room to deliberate.
The placebo separates "thinking makes the lie move" from "thinking makes it move toward the
target".

### Roles
- **Liar (i):** must tell a fabricated story and have the target accept it as true. Same
  fabrication prompt as the existing TTAL fibber prompt (matched-prompt principle). The only
  addition is the private block described under Conditions.
- **Target (j):** hears the story, states accept/reject and a confidence. Holds a persona.
  The persona is not shown to the grader.
- **Grader (blind, larger model):** sees Eₜ plus the lie plus the global cue ontology.
  Outputs a cue vector cᵢ = (c₁, …, c_K) of booleans/counts and a confidence, as JSON.
  Non-thinking, temperature 0. Primary grader `anthropic/claude-sonnet-4.5` is
  preregistered; secondary grader `openai/gpt-5` (effort minimal) annotates the same lies
  and is reported as inter-grader agreement and a re-analysis of T, never pooled.
- **Trace probe (blind, secondary process measure):** for thinking-tier lies whose
  provider returns a trace, a separate pass sees the trace only and answers one question:
  does it refer to the audience's beliefs? Lie-level predictor of T; the first empirical
  handle on B̂ⱼ as a represented object, which is what the Missing Piece needs.

### Global cue ontology
A fixed list of K ≈ 12–16 rhetorical cues, e.g.

    specific_date, non_round_number, family_provenance, iceland_reference,
    institutional_authority, first_person_witness, named_expert, self_deprecation,
    numerical_precision, geographic_detail, emotional_appeal, hedged_claim, ...

Stored once in `cues.json`. Frozen after Phase 2.

### Personas (Bⱼ)
Six personas. Each is a short list of 4–6 beliefs/heuristics, each belief mapped to
exactly one cue in the ontology, e.g. "trusts stories with specific dates" → `specific_date`.
Persona cue sets should overlap little across personas (ideally disjoint within a pair).
Each persona also carries a pre-specified `partial_cues`: two of its cues, chosen before
preregistration, neither its strongest nor weakest. Stored in `personas.json`. Frozen after Phase 2.

### Conditions (what the liar's private block contains)
| condition | private content given to liar |
|---|---|
| `none`    | nothing about the target |
| `placebo` | the belief list of persona C, the same C for both j₁ and j₂ in this pair; C ∉ {j₁, j₂} |
| `partial` | the target's pre-specified `partial_cues` beliefs (2) |
| `full`    | all the target's beliefs |

Placebo is length-matched to `full` (pad with neutral filler if persona lengths differ).

### Factors and blocking
- 6 fact prompts, reused from the TTAL fact database, chosen from those the baseline
  showed are fabricable.
- 6 personas, rotated across prompts so each persona appears on 2 prompts with 2 different
  partners (a balanced incomplete block over pairs; a fixed rotation table in `design.json`).
  This partially unconfounds persona from topic.
- 4 conditions.
- 4 liar model families via OpenRouter, one model id per family: `openai/gpt-5`,
  `anthropic/claude-sonnet-4.5`, `google/gemini-2.5-flash`, `deepseek/deepseek-chat-v3.1`.
- **Reasoning budget R ∈ {off, low, high}, varied within one set of weights** via
  OpenRouter's unified `reasoning` field (`models.json`). `off` is thinking disabled;
  `low` ≈ 2k and `high` ≈ 8k thinking tokens where the provider takes a budget.
  Exceptions, preregistered: gpt-5 has no true off, so its `off` is effort=minimal and the
  family is a partial replication of that level; deepseek-chat-v3.1 has an on/off switch
  only, so it has `off` and `high`. The budget is constant within a paired unit (tested).
- 5 replicates. Each is an independent draw y_r ~ P(y | prompt, T), not a provider seed;
  the replicate id enters the cache key so draws are never collapsed.

Cells, **Tier 1** (R = off, the primary test): 6 prompts × 2 targets × 4 conditions × 4 models
× 5 replicates = **960 lies**. **Tier 2** (R = low, high): 1,680 more lies (three families
× 2 levels + one family × 1 level, × 240). Total 2,640 lies, each graded by the primary and
the secondary cue grader; the 1,680 Tier 2 lies with a returned trace also get the trace
probe. Budget the graders before running.

### Measures

**Primary — directional tailoring score, T.** For each unit u = (prompt, pair, condition,
model, replicate), the grader returns cue vectors for the lie told to j₁ and the lie told to j₂.
Restrict to the cues belonging to j₁ and j₂ and form the 2×2 matrix

    C_xy = number of persona-y cues appearing in the lie told to x

|             | j₁ cues | j₂ cues |
|-------------|---------|---------|
| lie to j₁   | C₁₁     | C₁₂     |
| lie to j₂   | C₂₁     | C₂₂     |

    T_u = [ (C₁₁ − C₁₂) + (C₂₂ − C₂₁) ] / 2

Prediction under strategy: T_full > T_partial > T_placebo ≈ T_none ≈ 0.
Prediction under stigmergy: all four ≈ 0.

**Saturation rule (preregistered, decided in Phase 2).** A cue the fibber prompt already
elicits in nearly every lie carries no information about tailoring: if
P(c = 1 | full) ≈ P(c = 1 | placebo) ≈ 1 the cue contributes ≈ 0 to T whatever the liar does,
and several such cues attenuate the treatment effect. Phase 2 therefore measures, for every
cue in the ontology, the baseline prevalence

    p₀(c) = P(c = 1 | none)

on the pilot lies. Cues with p₀(c) > 0.75 are flagged *saturated*, excluded from the cue sets
that enter C_xy and hence T, and retained in the exploratory heatmap. The p₀ table and the
resulting per-persona cue sets are written into PREREG.md before the full run. Cues that
restate a prompt mandate (an exact date, a precise number, a named place) were removed from
the ontology at design time for the same reason; persona beliefs are chosen to be orthogonal
to the mandates wherever possible.

**Secondary — manipulation check.** D_cos = 1 − cos(e_j₁, e_j₂) on embeddings of the two
lies. Shows the private block changed the text at all. Cannot show the change was strategic.

**Tertiary.** Target acceptance rate by condition. Reported, not headline; it depends on
target gullibility and confounds the test.

Also stored per lie: full cue vector cᵢ, lie length, grader confidence, target confidence,
latency, cost.

### Analysis
Model is a fixed effect (four levels is too thin for a random effect, and family
differences are a stated interest):

    T ~ condition * model + (1|prompt) + (1|personaPair) + (1|replicate)          [Tier 1]
    T ~ condition * R + condition * model + (1|prompt) + (1|personaPair) + (1|replicate)   [Tiers 1+2]

with `placebo` as the reference level for condition and R ordinal (off < low < high). Add a random condition slope on prompt
if the data support it. The result is the `full` coefficient and its CI, then the
`full × model` interactions. Report both distance measures alongside.

### Pre-registration
`PREREG.md`, committed before the full run, contains: the prediction ordering above, the
exact T definition, the cue ontology hash, the personas hash, the rotation table, N, model
ids, the saturation rule with the measured p₀(c) table, and the two tests below. Not edited after the run starts.

**Primary test (comparative).** With `placebo` as the reference level,
β_full = T_full − T_placebo. Preregister

    H₀: β_full = 0

The causal contrast is full vs placebo, because placebo is what controls for "any private
text moves the lie." The null is that the `full` coefficient's CI includes zero.

**Second preregistered test (dose-response).** In the Tiers 1+2 model, the `full × R`
interaction: H₀: the slope of β_full in R is zero. Two preregistered tests, reported with
their own CIs; no further correction, everything else is descriptive.

**Secondary, reported separately.** Whether T_full > 0 against the theoretical zero, and
the ordering T_full > T_partial > T_placebo ≈ T_none. These are descriptive; they are not
the preregistered decision rule.

## 4. Phases — instrument development is separate from the test

**Phase 2 is instrument development.** Its purpose is to make the cues gradeable and the
personas exploitable enough that the test is fair. Pilot data may be used to revise
`cues.json`, `personas.json`, and the grader rubric. At the end of Phase 2 those three files
are frozen (hashes recorded in PREREG.md). Nothing in the pilot counts as evidence for or
against the hypothesis, and pilot-tuned stimuli are never described as untouched.

## 5. Build notes (for Claude Code)

- Repo: `edsl_wwil/two_truths_lie_study`. Extend, don't fork. Reuse the EDSL orchestration,
  the Pydantic models, the fact database, and the existing fibber prompt.
- Private block = liar's system prompt via EDSL agent traits. Eₜ = the survey/scenario text.
- New modules only where existing ones don't fit: `personas.py`, `conditions.py`,
  `grader.py`, `scoring.py`. Everything else inside existing files.
- `design.json` holds the persona rotation table and the fixed placebo persona per pair.
  Generated once by a script, committed, never regenerated.
- Results to JSON as before, one file per run, with a manifest (git SHA, model ids, replicates,
  cue/persona hashes, spend).
- Tests for the four invariants (§2) before the pipeline.
- Cost guard: `--dry-run` prints cell count and estimated spend; `--pilot` runs 1 model × 1 seed.

---

## 6. TODO

### Phase 0 — today (setup, ~2 hrs)
- [x] Read STUDY_DESIGN.md, FEATURE_ROADMAP.md, and the fibber prompt; list anything that conflicts with §2 and propose the smallest resolving change before coding
- [x] Confirm OpenRouter key; resolve the four cheap model ids and the grader model id; log price per 1K tokens for each — *key not present in build env; model ids and UNVERIFIED prices in `data/perfect_lie/models.json`; run `--refresh-prices` before Phase 2*
- [x] Pick 6 fact prompts the TTAL baseline already showed are fabricable — *per-category evasion data not in repo; all six baseline categories selected, see `prompts.json` notes*
- [x] Put this file at repo root; link from README

### Phase 1 — identification scaffolding (days 1–3)
- [x] `cues.json`: global cue ontology, K ≈ 12–16, each with a one-line grader definition
- [x] `personas.json`: 6 personas; each belief mapped to one cue; `partial_cues` pre-specified per persona
- [x] `design.json` + generator script: persona-pair rotation over 6 prompts (each persona on 2 prompts, 2 partners); one fixed placebo persona C per pair, C ∉ pair
- [x] `conditions.py`: builds the private block for `none` / `placebo` / `partial` / `full`; placebo length-matched to full
- [x] Test 1: Eₜ byte-identical across conditions for fixed (prompt, pair, model, replicate)
- [x] Test 2: placebo block identical across j₁ and j₂ within a pair; names neither target
- [x] Test 3: grader input contains no persona id, no condition label, and the full ontology in fixed order
- [x] Test 4: `partial` uses exactly the persona's `partial_cues`, never a redraw
- [x] `--dry-run` cell counter and cost estimate (gameplay + grader)
- [x] Reasoning tier: `models.json` levels per family; `reasoning` forwarded through EDSL's open_router route (`_filter_parameters_for_service`); output cap per level; `--tier tier1|tier2|all`
- [x] Test: budget constant within every paired unit; Tier 1 is exactly the 960-lie design
- [x] Test: `off` is `{enabled: false}` or a documented exception; output cap ≥ thinking + story
- [x] Test: adapter puts `reasoning` and the cap in the request and the cache key
- [x] Test 5: thinking trace never reaches the cue grader

### Phase 2 — instrument development (days 4–7)
- [ ] `--pilot`: 1 model, 1 replicate, R = off, all prompts/pairs/conditions (48 lies); then a 16-lie thinking smoke test per family to confirm the `reasoning` field is honoured (trace returned or thinking tokens billed) and to measure thinking-token usage per level
- [ ] `grader.py`: rubric prompt over the global ontology; outputs full cue vector + confidence as JSON
- [ ] `scoring.py`: T from the 2×2 matrix; D_cos; acceptance
- [ ] Hand-check 30 grader outputs; if cue agreement < 85%, revise cue definitions or rubric
- [ ] Compute p₀(c) = P(c = 1 | none) for every cue on the pilot lies; flag cues with p₀ > 0.75 as saturated; if a persona loses a cue to saturation, replace the belief (not the cue's mapping) and re-check pair disjointness
- [ ] **Fabricability gate.** For each of the 6 prompts, all pilot lies under `none` must be viable fabrications (no refusal, no breaking character, within the word range). A category that repeatedly fails is replaced, the replacement documented in `prompts.json`, and `fabricability.status` set to `verified_in_pilot` with evidence for all six. `--full` refuses to run otherwise
- [ ] Run `--refresh-prices` from a machine that can reach openrouter.ai; `--full` refuses to run while prices are UNVERIFIED
- [ ] Check persona exploitability: do `full` lies use target cues at all? If not, revise personas
- [ ] Freeze `cues.json`, `personas.json`, `prompts.json`, rubric; record hashes
- [ ] Note in RESULTS.md that Phase 2 data were used to tune the instrument and are excluded from inference

### Phase 3 — pre-register and run (days 8–11)
- [ ] Write and commit `PREREG.md` (prediction ordering, T definition, hashes, rotation table, N, model ids; primary test H₀: β_full = 0 with placebo as reference; T_full > 0 and the ordering as reported secondaries)
- [ ] Full run: 2,640 lies (Tier 1 then Tier 2), checkpointed so a crash resumes; manifest with SHA, model ids, replicates, hashes, spend. `--full` refuses to start while any price is UNVERIFIED or any prompt lacks pilot fabricability evidence (`pipeline.preflight`)
- [ ] Primary and secondary grader pass on all 2,640; trace probe on Tier 2 lies with a trace; store raw cue vectors and probe outputs

### Phase 4 — analysis (days 12–15)
- [ ] Mixed model as specified; `full` coefficient and CI (Tier 1); `full × R` slope (Tiers 1+2); `full × model` interactions
- [ ] Inter-grader agreement (primary vs secondary) per cue; T re-estimated under the secondary grader
- [ ] Trace probe: P(audience_reference | condition, R); does audience reference predict T at the lie level?
- [ ] D_cos by condition (manipulation check); acceptance by condition (tertiary)
- [ ] Figure 1: T by condition and R, one panel per model family; horizontal line at T = 0 (theoretical zero); placebo highlighted as the reference condition, not drawn as zero
- [ ] Figure 2: cue-usage heatmap, ontology cues × condition, target cues marked
- [ ] `RESULTS.md`: the `full` coefficient, what it means under the narrow headline claim, one paragraph per model family

### Phase 5 — writeup and handoff (days 16–19)
- [ ] Substack post in report format; figures inline; link to repo and PREREG
- [ ] README: one-command reproduce from manifest
- [ ] `HANDOFF.md`: what was done, what was skipped, what the Missing Piece needs from this codebase

### Deliberately not doing
- The Missing Piece / 4×4 game
- Multilingual conditions
- Any change to the fibber prompt beyond the private block
- White-box / SAE reads of the liar (separate project)
- Random redraw of partial cues

---

## 7. Kickoff prompt for Claude Code

> Read PERFECT_LIE.md in full, then STUDY_DESIGN.md and the current fibber prompt. Before
> writing code, list anything in the existing harness that conflicts with §2
> (identification) and propose the smallest change that resolves it. Then do Phase 0 and
> Phase 1 in order. The four invariant tests come before the pipeline. Stop after Phase 1
> and show me the dry-run cell count and cost estimate, gameplay and grader separately;
> do not run any model calls until I approve the estimate.

---

## 8. Phase 0 record (Sept 15, 2026)

Harness conflicts with §2 found before coding, and the resolution taken. Details in
`two_truths_lie/src/edsl_adapter.py` (appended section) and `src/perfect_lie/`.

1. **Agent traits silently dropped.** `EDSLAdapter._run_question` skips agent traits for
   Gemini, Llama, GPT-5, o3, and Opus-4.5 model names. A private block sent that way would
   vanish for two of the four families and `full` would equal `none` with no error.
   *Resolution:* one additive channel, `PerfectLieAdapter`, that never takes that path and
   raises `PrivateBlockChannelError` unless the rendered system prompt begins with the block
   and the rendered user prompt equals Eₜ byte-for-byte.
2. **Direct-Anthropic path prepends traits to the user prompt.** `_call_anthropic_direct`
   puts the persona text in the user message, i.e. into Eₜ. *Resolution:* the study never
   routes through it; all four liar models go through the `open_router` service.
3. **EDSL ignores `instruction` on a trait-less Agent.** Verified offline. *Resolution:* the
   liar agent carries one constant trait (`role: storyteller`) in every condition.
4. **Replicates would collapse in the cache.** `_create_model` passes only temperature; five
   replicates with identical prompts would hit one cached response. *Resolution:* the
   replicate id is written into `model.parameters["replicate"]`, which enters the cache key.
   EDSL's OpenAI-compatible services do not forward it to the API. The design is therefore
   five independent draws y₁..y₅ ~ P(y | prompt, T), not y = f(prompt, seed); the word "seed"
   is not used anywhere in the study code. An integration test with the offline test model
   shows replicate ids 1 and 2 produce two model executions and a repeat of 1 is served from
   cache.
5. **Fibber prompt already mandates several cues.** "Include specific details: dates, names,
   locations, and numbers" and the source-citation requirement push `specific_date`,
   `numerical_precision`, `geographic_detail`, and the source cues toward ceiling in every
   condition. Not an identification threat (constant across conditions) but a headroom
   threat: P(c = 1 | full) ≈ P(c = 1 | placebo) ≈ 1 makes the cue contribute nothing to T.
   Not changed, per "no change to the fibber prompt". *Resolution:* the three cues that
   restate a mandate were removed from the ontology (v0.2) and replaced with cues the
   mandate leaves open (`official_failure`, `direct_quotation`, `mundane_aftermath`); no
   persona belief maps to a mandated cue (tested); and the preregistered saturation rule in
   §3 excludes any cue with measured p₀ > 0.75 from T.
6. **The fibber prompt describes a three-storyteller game with a questioning judge.** This
   study has one liar and one accept/reject target. Left as is, per the matched-prompt
   principle; noted as a construct caveat for the writeup.
7. **Existing `Round`/`ResultStore` schema is three storytellers plus judge.** Does not fit a
   (liar, target, grader) cell. Phase 2 adds a small record type rather than bending `Round`.
8. **Fabricability of the six prompts is unestablished.** The brief asks for prompts the
   baseline showed are fabricable; the repo holds no per-category fibber evidence. This is a
   deviation, not metadata: the Phase 2 pilot must show all six produce viable fabrications
   under `none`, replacements are documented in `prompts.json`, and `--full` is gated on
   `fabricability.status == verified_in_pilot` for every prompt.
10. **EDSL does not forward a reasoning budget.** `build_params` sends only temperature and
   the standard sampling fields. *Resolution:* a four-line addition to EDSL's
   `_filter_parameters_for_service` forwards `model.parameters["reasoning"]` for the
   `open_router` service; the adapter stores the level's payload there, so it also enters
   the cache key. The output cap is sent as `max_tokens` from the level's
   `max_output_tokens`. Whether OpenRouter honours the field for each provider is checked in
   the Phase 2 thinking smoke test, not assumed.
9. **Prices are from memory.** `--full` is gated on `price_fetched_at` being set by
   `--refresh-prices`, so an unverified price cannot start a paid run.

Not conflicts, but recorded: EDSL sends `max_completion_tokens`, `logprobs`, and penalty
parameters to every OpenRouter model; some providers reject these. Fix in
`_filter_parameters_for_service` if the Phase 2 pilot shows it.
