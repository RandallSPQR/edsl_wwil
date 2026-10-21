# The Perfect Lie, Phase 2: a liar-side note-valence direction, probe and steering. Pre-registration (DRAFT)

Status: **draft, not frozen.** Five decisions are open (marked **OPEN**, collected in section 12). Nothing
in this document has been run except the identity check (section 2). No activation has been extracted
and no steering has been run.

## 1. Question

The reversed-note study showed that four liar models use the *valence* the private note states, not
only its words: with the cue words held fixed, "the judge finds this credible" produces far more of
those cues than "the judge finds this suspect" (Test B, +0.25 to +0.43; OSF results post). It did not
show how. This study asks two questions about the two open-weight liars:
- **Probe:** is the note's valence linearly represented in the liar's residual stream at the end of
  the prompt, in a direction that transfers to unseen personas and unseen wordings?
- **Steering:** is that direction causally sufficient to move behaviour? Adding it under the reversed
  note should raise the target-cue share *s* (H1); subtracting it under the full note should lower *s*
  (H2), each against a norm-matched random direction.

Scope: a positive result shows that a linear representation of the stated valence drives cue choice.
It still does not show that the liar models the judge's mind (the note states the belief); the
inferred-belief design remains the test for that.

## 2. Models, instrument, and the identity check (completed, disclosed)

- **Models:** Gemma 3 27B IT and Llama 3.1 8B Instruct, pinned HF weights (bf16), on RunPod pods in
  EUR-IS-1 (the network volume holding the Gemma weights).
- **Frozen instrument from the reversed-note study:** personas and notes (`reversed_notes.json`,
  `personas.json`), the 72 categories (`categories.json`), the public prompt v3, the cue grader rubric
  v0.6 with the primary grader (`anthropic/claude-sonnet-4.5` via OpenRouter, temperature 0), the
  registered gate exclusions (`historical_anchor`, `emotional_appeal`), and the scoring of *s*.
- **Rendering (decided by the identity check):** each model is rendered as its API provider rendered
  it in the reversed-note study:
  - **Llama:** the official template without its "Cutting Knowledge Date / Today Date" lines (as
    CoreWeave renders it).
  - **Gemma:** the official template without the newline after `<start_of_turn>model` (as Novita
    renders it). **The steered Gemma uses the provider's rendering, not Google's official template.**
- **Identity check (pod vs API), run 2026-10-21 under rules fixed in advance
  (`results/phase2/identity_check/RULES.md`):**
  - Temperature-0 diagnostic: template differences found and fixed (Llama date header; Gemma
    final newline). Not a gate.
  - Behavioral equivalence, 36 categories, TOST +/-0.10 on B and each condition's s, paired by
    category: **Llama passed** (B difference -0.004 [-0.060, +0.052]). **Gemma failed with the
    standard template** (B +0.073 [+0.015, +0.131]) and, in a one-shot re-test fixed in advance,
    **passed with the Novita rendering** (B +0.008 [-0.051, +0.068]; all four inside the margin).
  - **The API link is established for both models.** Phase 2's primary references are nevertheless
    the pod's own unsteered conditions.
  - Disclosure: every identity number above was seen before this draft. The identity runs generated
    and graded unsteered lies only; no activation, probe or steered output exists.
  - Note: one newline moved Gemma's B by 0.064. The rendering is part of the instrument.

**OPEN 1: compute stack.** The identity link was established on HF transformers 4.53.2, torch 2.8,
bf16 (`identity_check/pod_server.py`). The `sae-ethos-pipeline` v1.1.0 replay stack pins transformers
5.17.0, nnsight 0.7.0 and fp32 for the 27B (two A100s or one H200), and its renderers produce the
official templates (Gemma with the newline; Llama with the date header), which the identity check
showed do not match the API lies.
- (a) **Recommended:** run extraction and steering on the identity stack, with the pipeline's
  probe, vector, placebo, coherence and SAE code imported as a library; register the two renderers.
  The identity link then carries over unchanged.
- (b) Run on the pipeline's replay stack with custom renderers registered (`model_io.register`), plus
  a bridging check: its unsteered references TOST-equivalent (+/-0.10) to the identity pod lies on
  the 36 identity categories. About twice the GPU cost.

## 3. Category split

The 72 frozen categories are split once, seeded (20261023): **24 training categories** (probe,
layer choice, coherence pilot; never graded for the primary test) and **48 evaluation categories**
(steering outcomes). Categories are the clustering unit throughout. All five targets (P1, P2, P3,
P5, P6) are used in both splits.

## 4. Probe: direction construction (training split only)

- **Activations:** residual stream (block output) at every layer, at the last prompt token, i.e. the
  final token of the rendered prompt after the public prompt and the generation marker. The mean over
  the note's belief-line span is recorded and reported, but never used for selection.
- **Items:** 24 categories x 5 targets x {full, reversed}, rendered exactly as in the run; plus the
  same items under each of three paraphrase sets (section 5) and the placebo notes (for the control).
- **Direction:** v_L = the mean over items of (h_full - h_reversed) at layer L (paired within
  category x target). A logistic probe (pipeline `probe.train.fit_logistic`, 5-fold CV, C grid
  {0.01, 0.1, 1, 10}) is reported alongside; it is never used for steering (in the pipeline's 27B
  steering item 6 the logistic filter w/sigma was off-manifold and incoherent at every strength).
- **Generalization tests (both required):**
  - (a) **Held-out personas:** leave one target out; v from the other four; AUROC of the projection
    on the held-out target's full vs reversed items, pooled over the five folds.
  - (b) **Held-out wordings:** v from the frozen wording; AUROC on each paraphrase set separately.
  - Pass rule (the pipeline's transfer rule, `probe/transfer.py`): AUROC >= 0.70 and the 95%
    cluster-bootstrap lower bound (clusters = categories, 2,000 resamples) > 0.50, for (a) and for
    each of the three sets in (b). **A direction counts only if it passes (a) and all of (b).**
- **Control: cue mention.** c_L = mean(h over full and reversed items) - mean(h over placebo items)
  (notes that name the target's cues vs notes that do not). Projections of full vs reversed onto c_L
  must show no separation: the 90% bootstrap CI of the AUROC inside [0.40, 0.60]. cos(v_L, c_L) is
  reported.
- **Layer rule (fixed now, applied on the training split before any steering):** candidates are the
  middle third of layers (Gemma 21-41 of 62; Llama 11-21 of 32). Among candidates that pass both
  generalization tests, the layer with the highest mean held-out-wording AUROC (mean over the three
  sets); ties go to the lower layer. If no candidate passes, that model has no transferable valence
  direction: its steering hypotheses are not run and are reported as untestable (they stay in the
  Holm family and are never rejected).

## 5. Paraphrase sets (held-out wordings)

Three sets (A, B, C) in `results/phase2/prereg_draft/paraphrase_sets.json`, generated by
`paraphrases.py`. Each set replaces only the valence spans, i.e. the words that differ between a frozen
full line and its frozen reversed line (header: credible/suspect; lines: more/less, most/least,
Trusts/Distrusts, Believes/Doubts, convinced/unconvinced, reassured/suspicious, Warms to/Distrusts,
nothing/something, invented/genuine). Lint (`paraphrase_lint.md`), every line of every set passes:
with the valence spans masked, the frozen full, frozen reversed, paraphrased full and paraphrased
reversed token sequences are identical, so every cue word is unchanged; each replaced span is a listed
pair; no new valence word shares a stem with a cue's name (this caught and replaced "skeptical" in
set C); every paraphrase differs from the frozen wording.

| frozen pair | set A | set B | set C |
|---|---|---|---|
| credible / suspect | convincing / doubtful | believable / dubious | plausible / questionable |
| more / less | much more / much less | all the more / all the less | far more / far less |
| most / least | above all / least of all | especially / hardly at all | most of all / not at all |
| Trusts / Distrusts | Has faith in / Has no faith in | Relies on / Is wary of | Credits / Discredits |
| Believes / Doubts | Accepts / Questions | Gives credit to / Discounts | Is persuaded by / Has misgivings about |
| convinced / unconvinced | persuaded / unpersuaded | won over / left cold | impressed / unimpressed |
| reassured / suspicious | put at ease / put on guard | comforted / alarmed | relieved / wary |
| Warms to / Distrusts | Is drawn to / Is put off by | Likes / Dislikes | Takes to / Is cold toward |
| nothing / something | nothing whatsoever / something | nothing / a great deal | no secret / a secret |
| invented / genuine | made up / authentic | fabricated / true | contrived / honest |

Paraphrased notes are used for activations only, never for generation or grading.

## 6. Steering (primary; evaluation split)

- **Vector:** unit(v_L*) at the selected layer L*, scaled by alpha x ||v_L*|| (alpha = 1 adds the
  note's own average full - reversed shift). Added at the output of block L* at every prompt position
  and every generated position (the pipeline's convention, `probe/steer_backend.py`).
- **Hypotheses:** H1: reversed note + alpha v raises s. H2: full note - alpha v lowers s.
- **Dose curve:** alpha in {0.25, 0.5, 1, 2, 4}.
- **Placebo:** a random unit direction (isotropic, seeded), at the same layer, scaled identically, at
  every alpha. **OPEN 4:** also a covariance-matched placebo (pipeline `vectors.placebo_cov`), which
  in the pipeline's item 6b moved behaviour far more than isotropic ones (median dP 0.161 vs ~0).
- **Coherence gate** per model x hypothesis x alpha x vector; all three must hold, for the steered
  and the placebo lies alike, or that alpha does not count:
  - viability: >= 95% of lies pass the frozen viability screen (word range, not degenerate);
  - perplexity: median ratio <= 2.0 of the continuation's NLL under the unsteered model to that of
    unsteered continuations (pipeline `probe/coherence.py`, 64 greedy tokens);
  - repetition: repeated-4-gram share <= 0.25.
- **Primary alpha (alpha\*):** from a coherence pilot on the training split (24 categories, one target
  per category rotating, not graded for cues): the largest grid alpha at which steered and placebo
  pass, per model and hypothesis. Fixed and committed before any evaluation lie is graded. If alpha\*
  fails the gate in the evaluation run (checked before grading), the next lower passing alpha is used.
- **Unsteered references:** the pod's own placebo, full and reversed lies on the evaluation split.
- **Sampling, rendering, grading:** as in the identity check (temperature 0.6, top_p 0.9, top_k off,
  seeded; renderings of section 2; primary grader through the frozen runner; registered gate).

## 7. Primary analysis

- **Unit:** per model x hypothesis, per evaluation category k (K = 48), Delta_k = the mean over the
  five targets of s(steered) - s(placebo vector) at alpha\*.
- **Efficacy family (alpha = 0.05):** two-sided t on K - 1 df; Holm across the four tests
  (2 models x 2 hypotheses). A rejection in the predicted direction (H1 Delta > 0; H2 Delta < 0)
  reads **steerable**; a rejection in the other direction reads **opposite** and is reported.
- **Equivalence family (alpha = 0.05):** TOST at +/-0.10 on Delta, Holm across the four. Joint
  rejection reads **not steerable within +/-0.10**, but only if the positive control passed.
- **Positive control (OPEN 2).** The specified control, "the known vector from G4", does not exist
  for these models: in `sae-ethos-pipeline` v1.1.0 the legacy G4 vector is a Gemma-2-9B SAE feature,
  and both Gemma-3-27B G4 runs (items 6 and 6b) ended NOT_EVALUABLE; the Llama package has no G4.
  Proposed in-run known-answer control: v_fp = mean(h_full) - mean(h_placebo) on the training
  split, added at alpha = 1 under the placebo note, against the same random placebo; prediction s
  rises (the first study's full - placebo effect was large in every model). Pass: one-sided t at 0.05
  per model. If it fails for a model, that model's null steering results read "inconclusive:
  positive control failed", never "not steerable".
- **Naturalness:** cos(v_L\*, mean of (h_full - h_reversed) at the first generated token at L\*) and
  cos(v_L\*, the same last-token shift on the evaluation split, out of sample). Reported.
- **Effect relative to the note:** Delta / (s_full - s_reversed) from the unsteered references.
- **Dose curve:** Delta at every coherent alpha with 95% CIs; reported, not tested.
- **Missing data:** failed generations or gradings are counted per cell and reported; a tipping-point
  analysis as in the reversed-note study.

## 8. Power and sample size

The identity runs give the per-category SD of the difference between two independent sets of lies
(5 targets each), which is the structure of steered vs placebo: 0.118-0.140; the worst case 0.14
is used. Two-sided t at Holm's strictest level 0.0125:

| true Delta | K = 24 | K = 36 | K = 48 | K = 72 |
|---|---|---|---|---|
| 0.05 | 0.19 | 0.32 | 0.46 | 0.68 |
| 0.075 | 0.48 | 0.71 | 0.86 | 0.97 |
| 0.10 | 0.77 | 0.94 | 0.99 | 1.00 |

TOST at +/-0.10 with a true Delta of 0: power 0.99 at K = 36 and 1.00 at K = 48. **Proposed: K = 48
evaluation categories** (24 kept for training). For scale: the reversed-note B was 0.24 (Llama) and
0.43 (Gemma), so a Delta of 0.075 is a third of Llama's note effect.

## 9. Secondary and exploratory (labelled, after the primary)

- **Secondary: Llama dissociation.** Llama's held-out probe AUROC for note valence beside its
  comprehension check (registered balanced accuracy 0.42 [0.35, 0.49]; post hoc, parseable answers
  only, 0.54 [0.47, 0.60]): does Llama represent the valence it cannot report? Gemma reported
  alongside. Descriptive.
- **Exploratory: SAE features and MLP neurons most aligned with v.** Gemma Scope 2
  (`gemma-scope-2-27b-it-res`, layer 40, or the nearest available to L\*) and Goodfire Llama layer 19:
  decoder rows ranked by cosine with v, top 20 with Neuronpedia labels. MLP neurons at layers <= L\*
  whose output weights align with v. Optional ablation of the top features. New code (the pipeline
  has no alignment or neuron analysis). Run only after the primary.

## 10. Analysis discipline

- Analysis code validated on simulated data (null, effect, opposite-effect and incoherent-alpha
  scenarios), sign-tested, and committed before any evaluation lie is graded.
- Blinded permutation check before unblinding: steered and placebo labels swapped within category x
  target cells, 10,000 permutations, decision shares only.
- Screen matches (confession, refusal) listed blind for owner adjudication before unblinding.
- OSF addendum before unblinding; results reported as found.

## 11. Cost estimate

Measured rates (RTX PRO 6000 Blackwell, bf16, batched): Gemma about 12 lies/min, Llama about 36
lies/min; grading $0.013 per lie (primary only).

| item | full design (K = 48, all alphas on all targets) | lean (alpha\* on all targets; other alphas on 2 targets) |
|---|---|---|
| lies generated per model | 6,000 + 480 pilot | 3,700 + 480 pilot |
| GPU hours (both models, incl. extraction, perplexity, loads) | about 13 h | about 9 h |
| GPU cost at $2.49/h | about $32 | about $22 |
| lies graded (both models) | about 12,000 | about 7,400 |
| grading cost | about $156 | about $96 |
| **total** | **about $190** | **about $120** |

Option (b) in OPEN 1 roughly doubles the GPU line. The RunPod balance is $37.03.

## 12. Open decisions

1. **Stack:** (a) identity stack with pipeline code as a library (recommended), or (b) pipeline replay
   stack plus a bridging check.
2. **Positive control:** the in-run full - placebo direction (proposed), since no validated G4 vector
   exists for these models; or another control.
3. **Design size:** K = 48 evaluation categories; full or lean grading of the dose curve.
4. **Placebo:** isotropic only (as specified), or isotropic plus covariance-matched.
5. **Budget:** RunPod top-up and the OpenRouter grading total.
