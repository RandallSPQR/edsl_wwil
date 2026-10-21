# The Perfect Lie, Phase 2: a liar-side note-valence direction, probe and steering. Pre-registration (DRAFT)

Status: **draft, not frozen** (revision 2, 2026-10-21: two-stage design, covariance-matched placebo,
identity-check stack, method-check control, grading route pending a check). Open decisions are marked
**OPEN** and collected in section 12. Nothing has been run except the identity check (section 2). No
activation has been extracted and no steering has been run.

## 1. Question

The reversed-note study showed that four liar models use the *valence* the private note states, not
only its words: with the cue words held fixed, "the judge finds this credible" produces far more of
those cues than "the judge finds this suspect" (Test B, +0.25 to +0.43; OSF results post). It did not
show how. This study asks two questions about the two open-weight liars:
- **Probe:** is the note's valence linearly represented in the liar's residual stream at the end of
  the prompt, in a direction that transfers to unseen personas and unseen wordings?
- **Steering:** is that direction causally sufficient to move behaviour? Adding it under the reversed
  note should raise the target-cue share *s* (H1); subtracting it under the full note should lower *s*
  (H2), each against a covariance-matched placebo direction.

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

**Compute stack (decided):** the identity-check stack, HF transformers 4.53.2, torch 2.8, bf16
(`identity_check/pod_server.py`, extended with residual-stream reads and steering hooks), with the
`sae-ethos-pipeline` v1.1.0 code used as a library for probes (`probe.train`, `probe.transfer`),
vectors and placebos (`probe.vectors`), coherence (`probe.coherence`) and SAEs (`replay.sae`). The
pipeline's own replay stack is not used: it pins transformers 5.17.0, nnsight 0.7.0 and fp32 for the
27B, and its renderers produce the official templates, which the identity check showed do not match
the API lies. The two renderers of this section are used instead.

## 3. Category split

The 72 frozen categories are split once, seeded (20261023), into **K evaluation categories**
(confirmatory steering outcomes only) and **72 - K training categories** (probe, layer choice,
dose-finding pilot, method check). **OPEN 1: K in {32, 36, 48}** (section 8). Categories are the
clustering unit throughout. All five targets (P1, P2, P3, P5, P6) are used in both splits.

## 4. Probe: direction construction (training split only)

- **Activations:** residual stream (block output) at every layer, at the last prompt token, i.e. the
  final token of the rendered prompt after the public prompt and the generation marker. The mean over
  the note's belief-line span is recorded and reported, but never used for selection.
- **Items:** the training categories x 5 targets x {full, reversed}, rendered exactly as in the run; plus the
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

## 6. Steering: two stages

**Common to both stages.**
- **Vector:** unit(v_L\*) at the selected layer L\*, scaled by alpha x ||v_L\*|| (alpha = 1 adds the
  note's own average full - reversed shift). Added at the output of block L\* at every prompt position
  and every generated position (the pipeline's convention, `probe/steer_backend.py`).
- **Hypotheses:** H1: reversed note + alpha v raises s. H2: full note - alpha v lowers s.
- **Placebo: covariance-matched direction only** (pipeline `vectors.placebo_cov`, seeded): a random
  direction drawn from the covariance of the training activations at L\*, at the same layer, scaled
  identically, at every alpha used. (In the pipeline's item 6b, covariance-matched placebos moved
  behaviour far more than isotropic ones, so this is the stricter null.)
- **Coherence gate** per model x hypothesis x alpha; all three must hold for the steered *and* the
  placebo lies, or that alpha does not count:
  - viability: >= 95% of lies pass the frozen viability screen (word range, not degenerate);
  - perplexity: median ratio <= 2.0 of the continuation's NLL under the unsteered model to that of
    unsteered continuations (pipeline `probe/coherence.py`, first 64 generated tokens);
  - repetition: repeated-4-gram share <= 0.25.
- **Sampling, rendering, grading:** as in the identity check (temperature 0.6, top_p 0.9, top_k off,
  seeded; the renderings of section 2; the frozen grader and gate).

**Stage 1: dose-finding pilot (exploratory).**
- Training categories only: 8 of them, seeded (20261025), x 5 targets; both models; both hypotheses;
  alpha in {0.25, 0.5, 1, 2, 4}; steered and placebo. 800 lies per model.
- The coherence gate is applied to every alpha. **OPEN 3:** the pilot lies are or are not graded for
  cues; if graded, the s values are exploratory and reported as such.
- **Alpha rule, fixed now:** per model and hypothesis, alpha_max = the largest grid alpha at which the
  steered and the placebo lies both pass the coherence gate. **The confirmatory alphas are alpha_max
  and alpha_max / 2.** If alpha_max = 0.25, the second alpha is 0.125 (not piloted; its coherence is
  checked in stage 2). If no alpha passes, that model and hypothesis is untestable (it stays in both
  Holm families and is never rejected).
- The alphas are committed before stage 2 starts. **Pilot data never enters the confirmatory test.**

**Stage 2: confirmatory run.**
- The K evaluation categories x 5 targets; both models; both hypotheses; the two confirmatory alphas
  only; steered and placebo.
- The coherence gate is re-applied in stage 2 before any grading. An alpha that fails it there does
  not count (its tests are untestable, never rejected).
- **Unsteered references:** the pod's own placebo, full and reversed lies on the evaluation categories.

**Method check (positive control, one alpha, small subset).** Labelled a method check, not an
independent known vector: no validated G4 vector exists for these models (the pipeline's legacy G4
vector is a Gemma-2-9B SAE feature; both Gemma-3-27B G4 runs ended NOT_EVALUABLE; the Llama package
has no G4). Direction v_fp = mean(h_full) - mean(h_placebo) on the training categories (the note's own
full vs placebo shift, which raised s strongly in every model in the first study), added at alpha = 1
under the placebo note, against a covariance-matched placebo, on 16 evaluation categories (seeded) x
5 targets, in the stage-2 run. Prediction: s rises. Pass: one-sided t at 0.05 per model. If it fails
for a model, that model's null steering results read "inconclusive: method check failed".

## 7. Primary analysis (stage 2 only)

- **Unit:** per model x hypothesis x confirmatory alpha, per evaluation category k, Delta_k = the mean
  over the five targets of s(steered) - s(placebo) at that alpha.
- **Efficacy family (alpha = 0.05):** two-sided t on K - 1 df; **Holm across the eight tests**
  (2 models x 2 hypotheses x 2 alphas). A rejection in the predicted direction (H1 Delta > 0;
  H2 Delta < 0) reads **steerable at that alpha**; in the other direction, **opposite**, reported.
- **Equivalence family (alpha = 0.05):** TOST at +/-0.10 on Delta, Holm across the eight. Joint
  rejection reads **not steerable within +/-0.10 at that alpha**, only if the method check passed.
- **Per model and hypothesis label:** steerable if either alpha is steerable in the predicted
  direction; not steerable if both alphas are equivalent and neither is steerable; otherwise
  inconclusive (opposite results reported beside the label).
- **Naturalness:** cos(v_L\*, mean of (h_full - h_reversed) at the first generated token at L\*), and
  cos(v_L\*, the last-token shift on the evaluation categories, out of sample). Reported.
- **Effect relative to the note:** Delta / (s_full - s_reversed) from the unsteered references.
- **Missing data:** failed generations or gradings counted per cell and reported, with a tipping
  point as in the reversed-note study.

## 8. Power and sample size

The identity runs give the per-category SD of the difference between two independent sets of lies
(5 targets each), the structure of steered vs placebo: 0.118-0.140; the worst case 0.14 is used.
Two-sided t; Holm across eight, so the strictest level is 0.05/8 = 0.00625 (the first test), then
0.05/7 and so on.

| K | true Delta 0.05 | 0.075 | 0.10 | TOST +/-0.10 at Delta 0 (level 0.00625) |
|---|---|---|---|---|
| 32 | 0.20 | 0.55 | 0.86 | 0.83 |
| 36 | 0.24 | 0.62 | 0.91 | 0.89 |
| 48 | 0.36 | 0.80 | 0.98 | 0.98 |

(Efficacy power at the strictest Holm level; at the least strict level 0.05: K = 32, 0.50 / 0.84 /
0.97; K = 36, 0.55 / 0.88 / 0.99; K = 48, 0.68 / 0.95 / 1.00.)
Assumption: the covariance-matched placebo does not itself move s by more than sampling noise. If it
moves s in the predicted direction, Delta shrinks and power falls. For scale, the reversed-note B was
0.24 (Llama) and 0.43 (Gemma).

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
  scenarios), sign-tested, and committed before any stage-2 lie is graded.
- Blinded permutation check on stage 2 before unblinding: steered and placebo labels swapped within category x
  target cells, 10,000 permutations, decision shares only.
- Screen matches (confession, refusal) listed blind for owner adjudication before unblinding.
- OSF addendum before unblinding; results reported as found.

## 11. Cost estimate (two-stage design)

Measured rates (RTX PRO 6000 Blackwell, bf16, batched): Gemma about 12 lies/min, Llama about 36
lies/min; grading about $0.013 per lie (primary grader; the same per-token price on either route).

Lies per model: pilot 800 (both hypotheses x 5 alphas x steered/placebo x 8 categories x 5 targets);
stage 2: 40K confirmatory (2 alphas x 2 hypotheses x 2 vectors x K x 5), 15K unsteered references,
160 method check.

| K | stage-2 lies (both models) | GPU hours | GPU cost ($2.49/h) | stage-2 grading | total |
|---|---|---|---|---|---|
| 32 | 3,840 | about 6.0 | about $15 | about $50 | **about $65** |
| 36 | 4,280 | about 6.4 | about $16 | about $55 | **about $72** |
| 48 | 5,600 | about 7.7 | about $19 | about $73 | **about $92** |

GPU hours include the pilot (1,600 lies), activation extraction (training items under four wordings
plus placebo notes), perplexity scoring for the coherence gate and model loads. Grading the pilot
(OPEN 3) adds about $21. The RunPod balance is $37.03.

## 12. Open decisions

1. **K, the number of evaluation categories:** 32, 36 or 48 (power and cost in sections 8 and 11).
2. **Grading route:** Anthropic API direct or OpenRouter, decided by the regrade check
   (`results/phase2/grading_route/RULES.md`: 50 identity-check pod lies; switch if kappa >= 0.90 or
   label agreement >= 97%). It needs `ANTHROPIC_API_KEY` in the environment; not yet run.
3. **Whether to grade the pilot** (exploratory s on the dose curve, about $21) or apply only the
   coherence gate.
4. **Budget:** the RunPod balance covers the GPU line at any K; grading as in section 11.

Decided in revision 2: two-stage design and alpha rule; covariance-matched placebo only; the
identity-check stack with the pipeline as a library; the method check.
