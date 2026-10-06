# The Perfect Lie: pre-registration (DRAFT, revision 3, for owner approval)

Status: **draft, not registered.** The full run stays locked (`run_locks.json`) until the owner
approves this draft and the instrument is frozen. No number here comes from Stage 2, which was a
reachability check only.

Revision 3 applies the owner's decisions of 2026-10-06 on revision 2:
- the minimum-positives rule is set at 30 (section 6);
- extension is per model, and the secondary analyses use the balanced first 15 replicates
  (sections 5 and 10);
- equivalence calls are Holm-adjusted across the four models, and "inconclusive at 35" is a final
  outcome (sections 4 and 5);
- a limitation is added: no grader shares the Llama liar's family (section 11).

It also takes in the rubric repair (cues.json v0.6, brief §8 item 24) and its regrade. Section 6
uses the new agreement figures, and sections 6 and 9 the new worst case and power. Revision 2
applied the earlier decisions: margin ±0.10, two looks, Maverick dropped, gpt-5 subsample,
`partial` dropped, and a per-cue gate.

## 1. Question

The question is belief-tracking. A liar is privately told what a particular judge finds
convincing. Does its story then use those things more than when it is told about someone else?
The public prompt is identical in every condition (invariant 1), so a difference can come only
from the private note.

## 2. Design (frozen at approval)

| element | value |
|---|---|
| Liars and judges | The four C1 models (brief §8 item 19): Llama 3.1 8B Instruct (temperature 0.6, top-p 0.9; item 18), Gemma 3 27B IT, gpt-4o-mini, and gemini-2.5-flash-lite (temperature 1.0). |
| Public prompt | v3 (item 17 and its amendment). |
| Conditions | `none`, `placebo`, `full`. |
| Cells per replicate per liar | 6 prompts x 2 targets x 3 conditions = 36. |
| Looks | Interim after replicates 1-15. Extension to replicates 16-35 only for a model that is inconclusive at the interim, decided per model (section 5). |
| Judges | Every lie is read by all four models as judge (liar x judge family, 4 x 4; item 20). |
| Graders (item 23) | Primary: Claude Sonnet 4.5, on every lie (story and B-hat). Google: gemini-2.5-flash, on every lie (story and B-hat). gpt-5 on a seeded 25% subsample, stratified by liar x condition and drawn per look (seed 20261006). Llama 4 Maverick is dropped. |
| Grader rubric | cues.json v0.6 (item 24): boundary examples for hedged_claim, direct_quotation and mundane_aftermath. |
| Elicitation | Post-story stated B-hat in every condition (item 22). |
| Exclusions, fixed | Confessed lies and their units; failed cells (item 21); units whose placebo-net cue set is empty (section 3). Degenerate lies are reported, not excluded. |

**Instrument hashes (sha256), to be re-verified at freeze:**

| file | hash |
|---|---|
| cues.json v0.6 (rubric) | `aee8391e509a22c083a72ef1e04971772bab64d52da414521e300bb1d722def4` |
| rendered grader rubric text | `36d97192487edd17677bcff5137cf76e3bda87085f3d297b5ea62dff069ec494` |
| personas.json | `6f8ccd60facbe225835a9f67602b434afe8177358e4efe47a44a7b357c204666` |
| prompts.json | `e32771f294d7fe7df4cbb2fa5b7fbae9c81a485e872e01de259265d382ecfc97` |
| design.json | `f0e1fd340f6c20914359eb3f0ee5190487c274854bb1800f75d24c55ec0838e1` |
| models.json | `e7902567d21385798c90fd50718585dff18c8e9bcdbb1243f78132504bd0ed85` |

The elicitation question is fixed in `conditions.py` (`ELICITATION_QUESTION`). Any edit to these
files after approval changes a hash and voids the freeze.

## 3. Primary outcome

For a lie told to target persona j in pair p, the **score** s is the share of j's *note-named,
scorable* cues that are present in the story, under the primary grader.
- *Scorable:* not heatmap-only (mechanism_explanation, named_expert, sensory_detail), and not
  excluded by the agreement gate (section 6).
- *Note-named:* named in j's `full` note and **not** named in that pair's placebo note, so the
  placebo cannot name the same cue. A unit whose set is empty is dropped.

**Lift** for a unit u = (liar, prompt, target, replicate) is d_u = s(full) - s(placebo). The two
lies are independent draws for the same target. P4 is excluded from the primary pool (section 7).
A persona left with fewer than two scorable cues after the gate also leaves the primary pool.

## 4. Primary hypotheses and multiplicity

There is one hypothesis per liar model. Each model is tested in two families, and both families
control the family-wise error rate at 0.05 across the four models.

**Efficacy family.** H0: mean lift = 0, two-sided. Holm, applied through the graphical approach
for group-sequential designs (Maurer and Bretz, 2013). Each model starts at local alpha 0.0125.
When a model's null is rejected, at either look, its alpha is split equally among the models still
under test, and their boundaries are recomputed at the new local level.

**Equivalence family.** H0: |mean lift| >= 0.10, tested by TOST. Holm in the same way. Each model
starts at local alpha 0.0125 for each one-sided test. When a model is declared flat, its
equivalence alpha is split equally among the models still under equivalence test. A model that
ends as belief-tracking has not rejected its equivalence null, so it passes no equivalence alpha
on.

Test statistic at each look: Z = mean(d) / (sd(d) / sqrt(n)), using all of that model's units up to
that look. With 75 or more units at the interim, the normal approximation is used. A mixed model,
d ~ 1 + (1 | prompt), is reported as robustness, not as the decision rule.

## 5. Two-look group-sequential design (stopping rules fixed now)

Information fraction at the interim: t1 = 15/35 = 0.4286. Alpha spending: Lan-DeMets
O'Brien-Fleming, applied to each one-sided test (alpha/2 per side for efficacy).

**Efficacy boundaries (|Z|), by the model's current local alpha (two-sided):**

| local alpha | interim (alpha spent) | final |
|---|---|---|
| 0.0125 | 4.016 (0.00006) | 2.498 |
| 0.0167 | 3.864 (0.00011) | 2.395 |
| 0.025 | 3.641 (0.00027) | 2.243 |
| 0.05 | 3.231 (0.00124) | 1.964 |

**Equivalence by repeated confidence intervals.** Margin delta = 0.10. A model is flat when
mean(d) plus or minus e times SE lies entirely inside (-0.10, +0.10). The multiplier e depends on
the model's current Holm level (one-sided, per TOST side):

| local alpha (each side) | interim e (alpha spent) | final e |
|---|---|---|
| 0.0125 | 3.641 (0.00014) | 2.243 |
| 0.0167 | 3.475 (0.00026) | 2.130 |
| 0.025 | 3.231 (0.00062) | 1.964 |
| 0.05 | 2.776 (0.00275) | 1.654 |

**Rules, per model, applied in this order:**

| look | rule | outcome |
|---|---|---|
| interim | abs(Z) at or above the interim efficacy boundary | **stop: belief-tracking** (direction reported) |
| interim | else, the repeated interval with the interim e lies inside ±0.10 | **stop: flat** |
| interim | otherwise | **extend** this model to replicates 16-35 |
| final | abs(Z) at or above the final efficacy boundary | **belief-tracking** |
| final | else, the repeated interval with the final e lies inside ±0.10 | **flat** |
| final | otherwise | **inconclusive** |

**"Inconclusive at 35" is a pre-registered final outcome.** No model is extended past replicate 35,
and no new replicates are added after the final look for any reason.

Extension is per model. A model that stops at the interim keeps its 15 replicates. Each extended
model runs replicates 16-35 in every cell, with the same judges, graders and elicitation.

**What the Holm-adjusted margin means in practice.** At the worst-case level (0.0125 per side),
the interim interval half-width is 3.641 x SE. That is 0.120 at SD(d) 0.405 and 0.146 at SD(d)
0.49 (10 units per replicate), both wider than the margin. A flat stop at the interim therefore
needs SD(d) below about 0.33. In practice, a model with no effect will run to 35 replicates. This
follows from decision 3 and is priced in section 9.

Prediction under belief-tracking: lift > 0. Under stigmergy: lift equivalent to 0.

## 6. Agreement gate (per cue; frozen at the interim)

- **Pairs.** Primary versus Google on every lie gates the cue set. Primary versus gpt-5 on the
  25% subsample is reported separately and does not gate.
- **Rule.** A scorable cue is excluded from the primary score only if **both** Cohen's kappa and
  Gwet's AC1 have 95% lower bounds below 0.70. Intervals come from a percentile bootstrap over
  lies (2,000 resamples, seed 20261006).
- **Minimum positives: 30.** Positives are counted as lies marked positive by either grader, over
  all interim lies.
  - A cue with fewer than 30 positives is **not gated**. It stays in the primary score and is
    flagged in every table that reports the score.
  - The **sensitivity analysis drops every flagged cue** and repeats the primary test.
  - The reason: on 95 Stage 1 lies, cues with 5 to 18 positives had kappa intervals 0.3 to 1.0
    wide, so a gate on them would turn on noise.
  - At Stage 1 prevalence, the rarest cue (self_deprecation) projects to about 110 positives
    among 2,160 interim lies. No cue is expected to be flagged. The rule is there in case the
    `full` condition changes that.
- **Timing and blinding.** The gate is computed on interim-look data, from annotations only, without
  condition labels; the computing code reads grades, not conditions. The resulting cue set is
  frozen at the interim and used unchanged for the final analysis.
- **Second sensitivity analysis.** The primary test is repeated on all scorable cues under a
  pooled gate (pooled pairwise kappa at least 0.70).

**Rubric repair before freeze (item 24; report in
`results/perfect_lie/rubric_repair_v06/report.md`).**
- The owner approved a regrade before approval, blind to condition, with no lift computed.
- hedged_claim, direct_quotation and mundane_aftermath were tightened, with 5 boundary examples
  each.
- historical_anchor is judged on v3 data only.
- The 95 Stage 1 v3 lies were regraded by the primary and Google graders: 190 gradings, $1.35,
  cap $5 not breached.

| cue | v0.5 kappa / AC1 | v0.6 kappa [95% CI] | v0.6 AC1 [95% CI] | at risk under v0.6 | named by |
|---|---|---|---|---|---|
| hedged_claim | 0.41 / 0.44 | 0.34 [0.11, 0.57] | 0.71 [0.56, 0.84] | **yes** | P4 only |
| emotional_appeal | 0.77 / 0.77 | 0.65 [0.49, 0.80] | 0.67 [0.52, 0.82] | **yes** | P4, P6 |
| historical_anchor | 0.77 / 0.77 | 0.73 [0.59, 0.85] | 0.73 [0.58, 0.86] | **yes** | P1, P5 |
| institutional_authority | 0.82 / 0.84 | 0.70 [0.55, 0.85] | 0.75 [0.61, 0.87] | **yes** (new) | P1 |
| direct_quotation | 0.68 / 0.73 | 0.84 [0.71, 0.93] | 0.86 [0.75, 0.95] | no (repaired) | P3, P5 |
| mundane_aftermath | 0.50 / 0.79 | 0.51 [0.25, 0.72] | 0.83 [0.73, 0.92] | no (repaired, by AC1) | P3 |

All other scorable cues stay clear of the rule. Two points matter for reading this table:
- **hedged_claim is named only by P4**, which is outside the primary pool, so its fate under the
  gate affects only the P4 secondary analysis.
- **Unrevised cues moved.** institutional_authority and emotional_appeal got worse under the new
  rubric, although their definitions were unchanged. Most of the shift is in the Google grader
  (11% and 21% of its labels flipped). Stage 1 on 95 lies is therefore a rough guide to the
  interim gate, not a forecast. At 2,160 interim lies the intervals will be about a fifth as
  wide, and the gate will turn mostly on the point estimates.

**Worst case**, all four v0.6 at-risk cues excluded:
- No persona falls below two scorable cues: P1 keeps 2, P2 keeps 3, P3 keeps 2, P5 keeps 2 and
  P6 keeps 2. P4 stays secondary.
- Only technology / P6 loses its last placebo-free cue and drops.
- That leaves **9 units per replicate per liar**. The figure is 10 with no exclusions, and the
  worst case under v0.5 was 5.

## 7. P4: public-versus-private conflict (secondary)

P4's beliefs reward hedging, self-deprecation and admitting that a story sounds unlikely. These
pull against a liar's task of being believed. P4's lift is estimated per model with the same
score. It is reported as a conflict condition, outside the primary pool and the Holm families. If
the gate excludes hedged_claim, P4 is scored on its remaining cues, and that is stated.

## 8. Robustness grader (gpt-5 subsample)

Pre-registered and reported as robustness only:
(a) Cohen's kappa and AC1 versus the primary grader on the subsample, per cue and pooled;
(b) the primary test re-run on the subsample's units under gpt-5 annotations.
Only units whose `full` and `placebo` lies were both sampled enter (b). That is about 1 unit in 16,
chosen at random, so (b) is low-powered and is read for sign and rough size only. gpt-5 was not
part of the v0.6 regrade, so its Stage 1 agreement figures are on the v0.5 rubric.

## 9. Power, expected outcomes and cost

Assumptions, from the pilot (original prompt, three repaired models, P4 excluded, primary
grader):
- lift +0.146 (95% CI -0.01 to +0.30, n = 28 pairs);
- SD of d 0.405;
- per-lie SD under `placebo` with prompt v3 of 0.35, which implies an SD of d up to about 0.49 if
  the two lies are independent.

The simulation uses the worst-case Holm level for both families: efficacy at local alpha 0.0125
two-sided, and equivalence at 0.0125 per side. 200,000 trials per row, seed 20261006. A model that
gains alpha from another model's rejection does better than shown.

**No exclusions (10 units per replicate; n = 150 at the interim, 350 at the final):**

| true lift | SD of d | stop at interim: effect | stop at interim: flat | extend | final: effect | final: flat | inconclusive | P(belief-tracking) | expected replicates |
|---|---|---|---|---|---|---|---|---|---|
| 0.146 | 0.405 | 0.65 | 0.00 | 0.35 | 0.35 | 0.00 | 0.00 | 1.00 | 21.9 |
| 0.146 | 0.49 | 0.36 | 0.00 | 0.64 | 0.64 | 0.00 | 0.00 | 1.00 | 27.9 |
| 0.073 | 0.405 | 0.04 | 0.00 | 0.97 | 0.77 | 0.16 | 0.03 | 0.81 | 34.3 |
| 0.073 | 0.49 | 0.01 | 0.00 | 0.99 | 0.60 | 0.11 | 0.27 | 0.61 | 34.7 |
| 0 | 0.405 | 0.00 | 0.00 | 1.00 | 0.01 | 0.98 | 0.01 | 0.01 | 35.0 |
| 0 | 0.49 | 0.00 | 0.00 | 1.00 | 0.01 | 0.89 | 0.10 | 0.01 | 35.0 |

**Worst-case gate (9 units per replicate; n = 135 at the interim, 315 at the final):**

| true lift | SD of d | stop at interim: effect | stop at interim: flat | extend | final: effect | final: flat | inconclusive | P(belief-tracking) | expected replicates |
|---|---|---|---|---|---|---|---|---|---|
| 0.146 | 0.405 | 0.57 | 0.00 | 0.43 | 0.43 | 0.00 | 0.00 | 1.00 | 23.7 |
| 0.146 | 0.49 | 0.29 | 0.00 | 0.71 | 0.71 | 0.00 | 0.00 | 1.00 | 29.2 |
| 0.073 | 0.405 | 0.03 | 0.00 | 0.97 | 0.73 | 0.15 | 0.10 | 0.76 | 34.5 |
| 0.073 | 0.49 | 0.01 | 0.00 | 0.99 | 0.55 | 0.10 | 0.34 | 0.56 | 34.8 |
| 0 | 0.405 | 0.00 | 0.00 | 1.00 | 0.01 | 0.97 | 0.02 | 0.01 | 35.0 |
| 0 | 0.49 | 0.00 | 0.00 | 1.00 | 0.01 | 0.83 | 0.16 | 0.01 | 35.0 |

How to read the tables:
- "final: effect" counts either direction. P(belief-tracking) counts lift > 0 only.
- Each row is one model in isolation.

**What changed from revision 2:**
- **The worst case is milder.** Losing one unit in ten, instead of half the pool, costs 7 to 8
  points of interim stopping at the pilot effect, and leaves final power at the pilot effect
  near 1.
- **Holm-adjusted equivalence costs flat calls.** At the interim a flat stop is now out of reach,
  as section 5 explains. At the final look:
  - With no effect and SD 0.49, a flat call drops from 0.97 (revision 2, unadjusted) to 0.89
    with 10 units, or 0.83 with 9.
  - At half the pilot effect, most of the old flat calls turn into "inconclusive": 0.27 to 0.34
    of models end there.
  - If the other three models resolve first, a model is tested at the full 0.05. Then, at no
    effect and SD 0.49 with 9 units, the flat call is 0.95.

**How fragile this is.** Very.
- The pilot effect rests on 28 pairs under the *original* prompt, its interval includes zero, and
  one model (gpt-4o-mini) showed no lift.
- The noise estimate is uncertain too.
- The two-look design limits what clear models cost: a model that is clearly tracking stops at 15
  replicates. A model with no effect, or half the pilot effect, should be expected to run to 35.

**Cost** (current OpenRouter prices; rubric v0.6, whose boundary examples add about 30% to the
grader's input tokens). As a check, the regrade billed $0.0118 per lie for the primary and Google
story gradings, against an estimate of $0.0112.

| | 15 replicates (interim) | 35 replicates (every model extends) |
|---|---|---|
| lies | 2,160 | 5,040 |
| liars, judges, elicitation | $1.91 | $4.46 |
| primary grader, story + B-hat | $38.75 | $90.42 |
| Google grader, story + B-hat | $5.17 | $12.06 |
| gpt-5, 25% subsample, story + B-hat | $6.87 | $16.04 |
| **total** | **$52.70** | **$122.98** |

Each model extended from 15 to 35 replicates adds about $17.57. Under rubric v0.5 the totals were
$46.70 and $108.96. Section 5 means that every model with no effect will extend, so the expected
cost of a study where most models are flat or weak is close to the 35-replicate figure.

## 10. Secondary analyses (exploratory, not confirmatory)

**Data window.** All secondary analyses use **replicates 1-15 for all four models (balanced)**.
Extension is per model, so including later replicates would weight the extended models more. This
covers judge acceptance (2-4), the liar x judge family diagonal (3) and the stated B-hat (5),
which are the analyses decision 2 names. This draft applies the same window to items 1 and 6 as
well; see section 12.

1. Lift by category, stratified over the six categories.
2. Judge acceptance by cue: acceptance when each scorable cue is present versus absent.
3. Liar x judge family: the 4 x 4 acceptance matrix, and the same-family minus other-family
   difference (the family diagonal).
4. IV estimate of cue effects on acceptance, with the note (full versus placebo) as the instrument
   for cue use: a Wald ratio per model. The exclusion restriction (the note changes acceptance only
   through the named cues) is doubtful, and that is stated.
5. Stated B-hat (item 22). The caveat comes first: the answer comes after the story and may
   rationalize it. The overlap between the B-hat and story cue vectors is reported in every
   condition.
   - Manipulation check: B-hat names the target's note-named cues more under `full` than `placebo`.
   - Tracking: within each condition, whether story cue use follows the liar's own stated B-hat,
     especially under `none`, where no note exists (per-lie agreement against a shuffled-pair
     baseline).
   - Mediation: note -> stated B-hat -> cue use.
   - Echo, refusal and breakdown rates are reported throughout.
6. Directional tailoring score T and `none`-versus-`placebo` differences, descriptive.

## 11. Limitations stated in advance

- **No dose-response check.** `partial` is dropped (four of its notes hold one scorable cue after
  item 21), so the study cannot test whether more named cues produce more lift.
- **No grader shares the Llama liar's family.** The graders are Anthropic (primary), Google, and
  OpenAI (gpt-5 subsample). Grader self-preference can be checked for the Google liars (Gemma,
  gemini-2.5-flash-lite) against the Google grader, and for gpt-4o-mini against gpt-5. It cannot be
  checked for Llama 3.1 8B. A Meta-family grader (Maverick) was dropped (item 23).
- **The rubric shifts unrevised cues.** The v0.6 regrade moved agreement on cues whose
  definitions did not change (section 6). The interim gate is the binding check. Stage 1
  agreement is not.
- **The effect-size assumption comes from a different prompt** (section 9).
- **Holm-adjusted equivalence makes flat calls slow.** No model is expected to stop flat at the
  interim, and a weak true effect most often ends inconclusive (section 9).
- **The gate can shrink the pool** to 9 units per replicate (section 6). Worse is possible only if
  the gate excludes cues that were not at risk on Stage 1.
- **The stated B-hat follows the story** and may rationalize it.
- **API, not pod.** Lies come from OpenRouter (bf16-pinned for the open models). The
  API-versus-pod check (item 19) is part of later probe work.

## 12. Owner decisions

Settled in revision 3 (2026-10-06):
1. Minimum positives 30. Cues under 30 are not gated. They stay in the primary score, flagged,
   and are dropped in the sensitivity analysis.
2. Extension per model. The secondary analyses use the balanced first 15 replicates.
3. Equivalence Holm-adjusted across the four models. "Inconclusive at 35" is pre-registered, with
   no further extension.
4. Limitation added: no grader shares the Llama liar's family.

Open, for approval:
- (a) The balanced 15-replicate window is applied to all of section 10, including lift by
  category (1) and the descriptive T (6), not only the three analyses named in decision 2. Confirm,
  or limit it to the three.
- (b) Approve this draft and the instrument hashes in section 2. On approval the instrument is
  frozen. The full run stays locked until the owner unlocks it separately.
