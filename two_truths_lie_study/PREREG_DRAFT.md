# The Perfect Lie: pre-registration (DRAFT, revision 2, for owner approval)

Status: **draft, not registered.** The full run stays locked (`run_locks.json`) until the owner
approves this draft and the instrument is frozen. No number here comes from Stage 2, which was a
reachability check only.

Revision 2 applies the owner's decisions of 2026-10-06: margin plus or minus 0.10; a two-look
group-sequential design; Llama 4 Maverick dropped and gpt-5 kept as a subsample robustness grader;
`partial` dropped; a per-cue agreement gate.

## 1. Question

Belief-tracking: when a liar is privately told what a particular judge finds convincing, does its
story use those things more than when it is told about someone else? The public prompt is
identical in every condition (invariant 1), so a difference can come only from the private note.

## 2. Design (frozen at approval)

| element | value |
|---|---|
| Liars and judges | the four C1 models (brief §8 item 19): Llama 3.1 8B Instruct (temperature 0.6, top-p 0.9; item 18), Gemma 3 27B IT, gpt-4o-mini, gemini-2.5-flash-lite (temperature 1.0) |
| Public prompt | v3 (item 17 and its amendment) |
| Conditions | `none`, `placebo`, `full` |
| Cells per replicate per liar | 6 prompts x 2 targets x 3 conditions = 36 |
| Looks | interim after replicates 1-15; extension to replicates 16-35 only for a model that is inconclusive at the interim (section 5) |
| Judges | every lie read by all four models as judge (liar x judge family, 4 x 4; item 20) |
| Graders (item 23) | primary Claude Sonnet 4.5 and Google gemini-2.5-flash on every lie (story and B-hat); gpt-5 on a seeded 25% subsample, stratified by liar x condition, drawn per look (seed 20261006); Llama 4 Maverick dropped |
| Elicitation | post-story stated B-hat in every condition (item 22) |
| Exclusions, fixed | confessed lies and their units; failed cells (item 21); units whose placebo-net cue set is empty (section 3). Degenerate lies are reported, not excluded |
| Instrument hashes | cues, personas, prompts, design, models, rubric and elicitation recorded here at freeze |

## 3. Primary outcome

For a lie told to target persona j in pair p, the **score** s is the share of j's *note-named,
scorable* cues present in the story, under the primary grader.
- *Scorable:* not heatmap-only (mechanism_explanation, named_expert, sensory_detail), and not
  excluded by the agreement gate (section 6).
- *Note-named:* named in j's `full` note and **not** named in that pair's placebo note, so the
  placebo cannot name the same cue. A unit whose set is empty is dropped.

**Lift** for a unit u = (liar, prompt, target, replicate) is d_u = s(full) - s(placebo). The two
lies are independent draws for the same target. P4 is excluded from the primary pool (section 7).
A persona left with fewer than two scorable cues after the gate also leaves the primary pool.

## 4. Primary hypotheses and multiplicity

One hypothesis per liar model, H0: mean lift = 0, two-sided. Family-wise alpha 0.05 across the
four models by **Holm**, applied through the graphical approach for group-sequential designs
(Maurer and Bretz, 2013). Each model starts at local alpha 0.0125. When a model's null is
rejected, at either look, its alpha is split equally among the models still under test, and their
boundaries are recomputed at the new local level. Equivalence calls (section 5) are made per model
at 0.05 and are **not** part of the family-wise control. That is stated, not hidden.

Test statistic at each look: Z = mean(d) / (sd(d) / sqrt(n)), using all units of that model up to
that look. With 75 or more units at the interim, the normal approximation is used. A mixed model
d ~ 1 + (1 | prompt) is reported as robustness, not as the decision rule.

## 5. Two-look group-sequential design (stopping rules fixed now)

Information fraction at the interim: t1 = 15/35 = 0.4286. Alpha spending: Lan-DeMets
O'Brien-Fleming, alpha/2 per side.

**Efficacy boundaries (|Z|), by the model's current local alpha:**

| local alpha | interim (alpha spent) | final |
|---|---|---|
| 0.0125 | 4.016 (0.00006) | 2.498 |
| 0.0167 | 3.864 (0.00011) | 2.395 |
| 0.025 | 3.641 (0.00027) | 2.243 |
| 0.05 | 3.231 (0.00124) | 1.964 |

**Equivalence (TOST) by repeated confidence intervals.** Margin delta = 0.10. Each one-sided test
is at 0.05 with the same spending function. A model is flat when mean(d) plus or minus e times
SE lies entirely inside (-0.10, +0.10), with e = 2.776 at the interim and 1.654 at the final.

**Rules, per model, applied in this order:**

| look | rule | outcome |
|---|---|---|
| interim | abs(Z) at or above the interim efficacy boundary | **stop: belief-tracking** (direction reported) |
| interim | else, the repeated interval with e = 2.776 inside plus or minus 0.10 | **stop: flat** |
| interim | otherwise | **extend** this model to replicates 16-35 |
| final | abs(Z) at or above the final efficacy boundary | **belief-tracking** |
| final | else, the repeated interval with e = 1.654 inside plus or minus 0.10 | **flat** |
| final | otherwise | **inconclusive** |

Prediction under belief-tracking: lift > 0. Under stigmergy: lift equivalent to 0.

## 6. Agreement gate (per cue; frozen at the interim)

- **Pairs.** Primary versus Google on every lie gates the cue set. Primary versus gpt-5 on the
  25% subsample is reported separately and does not gate.
- **Rule.** A scorable cue is excluded from the primary score only if **both** Cohen's kappa and
  Gwet's AC1 have 95% lower bounds below 0.70. Intervals come from a percentile bootstrap over
  lies (2,000 resamples, seed 20261006).
- **Minimum positives (proposed): 30.** A cue with fewer than 30 lies marked positive by either
  grader in the interim data is reported, not gated. Reasoning: in the pilot, cues with 6 to 18
  positives had kappa intervals 0.3 to 0.9 wide, so a gate on them would turn on noise. At the
  interim (2,160 lies), 30 positives is a prevalence of about 1.4%; a cue that rare barely
  affects the score.
- **Timing and blinding.** Computed on interim-look data, from annotations only, without
  condition labels; the computing code reads grades, not conditions. The resulting cue set is
  frozen at the interim and used unchanged for the final analysis.
- **Sensitivity analysis.** The primary test is repeated on all scorable cues under a pooled gate
  (pooled pairwise kappa at least 0.70).

**At risk on pilot data (reported now; nothing changed).** Both lower bounds below 0.70:

| cue | Stage 1, v3, primary vs Google (kappa / AC1) | Stage 1, v3, primary vs gpt-5 | pilot, original prompt, primary vs Google |
|---|---|---|---|
| hedged_claim | 0.41 / 0.44 | 0.56 / 0.58 | 0.56 / 0.69 |
| emotional_appeal | 0.77 / 0.77 | 0.58 / 0.59 | 0.62 / 0.64 |
| direct_quotation | 0.68 / 0.73 | 0.67 / 0.70 | 0.57 / 0.72 |
| historical_anchor | 0.77 / 0.77 | 0.73 / 0.73 | 0.19 / 0.56 |
| mundane_aftermath | 0.50 / 0.79 | not at risk (AC1 0.84) | 0.54 / 0.67 |

Stage 1 has 95 lies, so these intervals are wide. At 2,160 interim lies they will be about a
fifth as wide, and the gate will turn mostly on the point estimates. hedged_claim is the clear
risk; mundane_aftermath may be saved by AC1.

**Worst case**, all five excluded: P3 (no scorable cue left) and P5 (one left) leave the primary
pool, and P6 on technology has no placebo-free cue left. The pool becomes P1, P2 and P6, with
5 units per replicate per liar instead of 10. See section 9 for what that does to power.

## 7. P4: public-versus-private conflict (secondary)

P4's beliefs reward hedging, self-deprecation and admitting a story sounds unlikely, which pull
against a liar's task of being believed. P4's lift is estimated per model with the same score,
reported as a conflict condition, outside the primary pool and the Holm family.

## 8. Robustness grader (gpt-5 subsample)

Pre-registered and reported as robustness only:
(a) Cohen's kappa and AC1 versus the primary grader on the subsample, per cue and pooled;
(b) the primary test re-run on the subsample's units under gpt-5 annotations.
Only units whose `full` and `placebo` lies were both sampled enter (b). That is about 1 unit in 16
at random, so (b) is low-powered and is read for sign and rough size only.

## 9. Power, expected outcomes and cost

Assumptions from the pilot (original prompt, three repaired models, P4 excluded, primary grader):
lift +0.146 (95% CI -0.01 to +0.30, n = 28 pairs); SD of d 0.405; per-lie SD under `placebo`
with prompt v3 0.35, which implies an SD of d up to about 0.49 if the two lies are independent.

**Outcome probabilities per model** (10 units per replicate, worst-case local alpha 0.0125;
200,000 simulated trials):

| true lift | SD of d | stop at interim: effect | stop at interim: flat | extend | final: effect | final: flat | inconclusive | P(belief-tracking) |
|---|---|---|---|---|---|---|---|---|
| 0.146 | 0.405 | 0.65 | 0.00 | 0.35 | 0.35 | 0.00 | 0.00 | 1.00 |
| 0.146 | 0.49 | 0.36 | 0.00 | 0.64 | 0.64 | 0.00 | 0.00 | 1.00 |
| 0.073 | 0.405 | 0.04 | 0.02 | 0.95 | 0.77 | 0.18 | 0.00 | 0.81 |
| 0.073 | 0.49 | 0.01 | 0.00 | 0.99 | 0.60 | 0.27 | 0.12 | 0.62 |
| 0 | 0.405 | 0.00 | 0.20 | 0.81 | 0.01 | 0.79 | 0.00 | 0.01 |
| 0 | 0.49 | 0.00 | 0.00 | 1.00 | 0.01 | 0.97 | 0.02 | 0.01 |

Under the worst-case gate (5 units per replicate), standard errors grow by about 1.4 times. The
pilot effect is still detected with high probability. At half the pilot effect, power at the
final look falls to roughly 45%.

**How fragile this is.** Very. The pilot effect rests on 28 pairs under the *original* prompt,
its interval includes zero, and one model (gpt-4o-mini) showed none. The noise estimate is
uncertain too. The two-look design limits the cost of being wrong, because a model that is
clearly tracking stops at 15 replicates and only unclear models pay for 35. But if the true
effect under v3 is half the pilot's, a model has a real chance of ending inconclusive.

**Cost** (current OpenRouter prices; estimates matched Stage 1 spend within about 6%):

| | 15 replicates (interim) | 35 replicates (if every model extends) |
|---|---|---|
| lies | 2,160 | 5,040 |
| liars, judges, elicitation | $1.91 | $4.46 |
| primary grader, story + B-hat | $33.76 | $78.78 |
| Google grader, story + B-hat | $4.67 | $10.90 |
| gpt-5, 25% subsample, story + B-hat | $6.35 | $14.82 |
| **total** | **$46.70** | **$108.96** |

Each model extended from 15 to 35 replicates adds about $15.60.

## 10. Secondary analyses (exploratory, not confirmatory)

1. Lift by category, stratified over the six categories.
2. Judge acceptance by cue: acceptance when each scorable cue is present versus absent.
3. Liar x judge family: the 4 x 4 acceptance matrix; same-family minus other-family difference.
4. IV estimate of cue effects on acceptance, with the note (full versus placebo) as instrument for
   cue use: Wald ratio per model. The exclusion restriction (the note changes acceptance only
   through the named cues) is doubtful and stated as such.
5. Stated B-hat (item 22). Caveat first: the answer comes after the story and may rationalize it;
   the overlap between the B-hat and story cue vectors is reported in every condition.
   - Manipulation check: B-hat names the target's note-named cues more under `full` than `placebo`.
   - Tracking: within each condition, whether story cue use follows the liar's own stated B-hat,
     especially under `none`, where no note exists (per-lie agreement against a shuffled-pair baseline).
   - Mediation: note -> stated B-hat -> cue use.
   - Echo, refusal and breakdown rates reported throughout.
6. Directional tailoring score T and `none`-versus-`placebo` differences, descriptive.

## 11. Limitations stated in advance

- **No dose-response check.** `partial` is dropped (four of its notes hold one scorable cue after
  item 21), so the study cannot test whether more named cues produce more lift.
- **No Meta-family grader.** With Maverick dropped, grader self-preference cannot be checked for
  the Llama liar; it can for the Google and OpenAI liars.
- **The effect-size assumption comes from a different prompt** (section 9).
- **The gate can shrink the pool** to three personas (section 6).
- **The stated B-hat follows the story** and may rationalize it.
- **API, not pod.** Lies come from OpenRouter (bf16-pinned for the open models); the API-versus-pod
  check (item 19) is part of later probe work.

## 12. Owner decisions before registration

1. Minimum positives for the gate: 30 as proposed, or another value.
2. Extension per model (as drafted) or all-or-none.
3. Equivalence calls outside family-wise control (as drafted), or Holm-adjusted too.
