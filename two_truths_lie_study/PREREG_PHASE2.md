# The Perfect Lie, Phase 2: a liar-side note-valence direction, probe and steering. Pre-registration (frozen)

**Status: FROZEN on 2026-10-22** (revision 4). Revision 3 (2026-10-21: 32 evaluation categories; one
confirmatory alpha per model x hypothesis; Holm family of 4; powered for Delta = 0.10; pilot checked for
coherence only; covariance-matched placebo; identity-check stack; method check), plus the probe gate and
stop rule (section 4), the grading route (section 11) and the grader-failure rules (section 7a).
- Nothing has been run except the identity check (section 2) and the grading-route check (section 11).
  No activation has been extracted and no steering has been run.
- **No Phase 2 compute runs until the owner confirms this registration is posted on OSF.**
- Any later change is made by a dated addendum, as in the first two studies.

**Frozen instrument and code (sha256).**
- The cue grader rubric is unchanged from the first two studies.
- The renderers are the `strip_llama_date` (Llama) and `strip_trailing_newline` (Gemma) options of
  `pod_server.py`, as used by `behavioral.py` in the identity check.
- **Analysis code** (section 10) and the pod server's activation and steering extensions are not
  written yet. Each is committed and its hash added by a dated addendum before it is used: the
  probe code before activation extraction, the analysis code before any stage-2 lie is graded.

| group | file (under `two_truths_lie/`) | sha256 |
|---|---|---|
| first-study and reversed-note instrument (byte-identical to `PREREG_REVERSED.md`) | `data/perfect_lie/cues.json` | `aee8391e509a22c083a72ef1e04971772bab64d52da414521e300bb1d722def4` |
| first-study and reversed-note instrument (byte-identical to `PREREG_REVERSED.md`) | `data/perfect_lie/personas.json` | `6f8ccd60facbe225835a9f67602b434afe8177358e4efe47a44a7b357c204666` |
| first-study and reversed-note instrument (byte-identical to `PREREG_REVERSED.md`) | `data/perfect_lie/prompts.json` | `e32771f294d7fe7df4cbb2fa5b7fbae9c81a485e872e01de259265d382ecfc97` |
| first-study and reversed-note instrument (byte-identical to `PREREG_REVERSED.md`) | `data/perfect_lie_reversed/reversed_notes.json` | `3936fc48b94409d68c0163e0f6c0aad8b01ebea082541239a36e07731f672a4c` |
| first-study and reversed-note instrument (byte-identical to `PREREG_REVERSED.md`) | `data/perfect_lie_reversed/categories.json` | `2afefbd31af1f988a5890ab838379dee7cc65f6f845e6f9d076ecd6b24a21f3f` |
| first-study and reversed-note instrument (byte-identical to `PREREG_REVERSED.md`) | `src/perfect_lie/grader.py` | `ddeb49ec5cd29d24be36f7b5a64ac888230507e94ecdb197f461d5b47368a9fb` |
| first-study and reversed-note instrument (byte-identical to `PREREG_REVERSED.md`) | `src/perfect_lie/scoring.py` | `bedf5749dd4ff59bb67cde1c9f0cd29ae3a256132206bb92a4e9ade8e3cd7625` |
| paraphrase sets (section 5) | `results/phase2/prereg_draft/paraphrase_sets.json` | `917ce24e18489a31539d35f1576f0d566172cee1c2bd2518796f8fd441a2a0eb` |
| paraphrase sets (section 5) | `results/phase2/prereg_draft/paraphrases.py` | `b1030f2e6c93eacb2625d2ee947a9e4650ff2a3584cb492df29e95443bd83d95` |
| paraphrase sets (section 5) | `results/phase2/prereg_draft/paraphrase_lint.md` | `282c2c2037198451d35f9d74dca036507f4aa97e830d3906f215f71902915959` |
| identity check: rules, renderers, pod server (section 2) | `results/phase2/identity_check/RULES.md` | `86d116c7d8df0706d320159978bb13c00c9a94bae251ba2a1cd62f91d3ea624b` |
| identity check: rules, renderers, pod server (section 2) | `results/phase2/identity_check/pod_server.py` | `f2897167b8c2720985e8e85a1b09f5087e92f7e46c5749cb768a97c295fdf868` |
| identity check: rules, renderers, pod server (section 2) | `results/phase2/identity_check/template_test.py` | `8870abb505e282d55fab0ff48d0e088b7f430355ce145541256a1a683441a2a9` |
| identity check: rules, renderers, pod server (section 2) | `results/phase2/identity_check/behavioral.py` | `c80a49a046b8d1711c1d9419886e79ee0d976c7fa692688cb89a3bbdc2c809b6` |
| grading route (section 11) | `results/phase2/grading_route/RULES.md` | `43fa6f799be334f1fb68f5b84b5ddd80a34549cb758b06125f27bae8021e2294` |
| grading route (section 11) | `results/phase2/grading_route/regrade_direct.py` | `29dc3b7b5f5c6e4464eb41f5686b60a2dd6532b8989e534431d02b4ef72b4f8e` |
| grading route (section 11) | `results/phase2/grading_route/regrade_direct.json` | `8ba35d03fc64be9e903ef6894dec43b53ab821be5324a59f37448b905e97efa0` |
| grading route (section 11) | `src/perfect_lie/grader_direct.py` | `4d61c62ecc1ff8ec15b168880cd43bbb11b2b1966ee423af6b4d5ae3771cce78` |
| grading route (section 11) | `tests/test_perfect_lie_grader_direct.py` | `b23135ada95e84db0bb1742afaa865a6c55eeb8677ff39a9fa255f70534df41c` |
| grading route (section 11) | `results/phase2/requirements_phase2.txt` | `b38f33226555469cf056750585b8ac886cbd539415127aaeff298becaf42cab7` |
| | grader rubric (RUBRIC_PREAMBLE + RUBRIC_OUTPUT) | `c638fea116fbb397631f2c7a28dac8f01a63cd8990fcb70365dbb7e98f3a303f` |

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
  v0.6 and the primary grader model (Claude Sonnet 4.5, temperature 0; graded through OpenRouter in
  the first two studies and the identity check, and **through the Anthropic API directly for all of
  Phase 2**, section 11), the
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
dose-finding pilot, and the method check's direction). **K = 32** (owner, 2026-10-21): 32 evaluation
and 40 training categories. Categories are the
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
- **Probe gate and stop rule (fixed now).** The probe stage runs first, on the training categories,
  and its result is committed before any steered lie is generated.
  - A model passes the gate only if some candidate layer passes **both** generalization tests: held-out
    personas, and **every one of the three held-out paraphrase wordings**.
  - **If the direction fails held-out-persona transfer or held-out-wording transfer (any one of the
    three paraphrase sets), Phase 2 stops for that model before steering: no dose-finding pilot, no
    confirmatory steering, no method check.** That failed transfer is reported as the model's Phase 2
    result. A direction that separates full from
    reversed only in the frozen wording may track the frozen valence words themselves (for example
    "suspect" vs "credible") rather than valence; steering along it would not test the hypothesis.
  - That model's two hypotheses are reported as **untestable: no transferable valence direction**.
    They stay in both Holm families and are never rejected.
  - **If neither model passes, the study ends after activation extraction** (about 1 GPU-hour, no
    grading). The probe results, including the failed transfer, are reported as the study's result.
  - The cue-mention control is reported beside the gate; it is a check on the instrument, not part of
    the stop rule.

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
  seeded; the renderings of section 2; the frozen grader and gate, on the direct route of section 11).

**Stage 1: dose-finding pilot (exploratory).**
- Runs only for models that passed the probe gate (section 4).
- Training categories only: 8 of them, seeded (20261025), x 5 targets; both models; both hypotheses;
  alpha in {0.25, 0.5, 1, 2, 4}; steered and placebo. 800 lies per model.
- The coherence gate is applied to every alpha. **The pilot is not graded for cues** (coherence only),
  so no outcome is seen before stage 2.
- **Alpha rule, fixed now:** per model and hypothesis, **the single confirmatory alpha is the largest
  grid alpha at which the steered and the placebo lies both pass the coherence gate in the pilot.** If
  no alpha passes, that model and hypothesis is untestable (it stays in both Holm families and is
  never rejected).
- The four alphas are committed before stage 2 starts. **Pilot data never enters the confirmatory
  test.** The pilot's coherence measures across the dose curve are reported as exploratory.

**Stage 2: confirmatory run.**
- Runs only for models that passed the probe gate and have a coherent alpha for that hypothesis.
- The 32 evaluation categories x 5 targets; both models; both hypotheses; the one confirmatory alpha
  per model and hypothesis; steered and placebo.
- The coherence gate is re-applied in stage 2 before any grading. If the confirmatory alpha fails it
  there, that model and hypothesis is untestable (never rejected); no other alpha is substituted.
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

- **Unit:** per model x hypothesis, per evaluation category k (K = 32), Delta_k = the mean over the five
  targets of s(steered) - s(placebo) at the confirmatory alpha.
- **Efficacy family (alpha = 0.05):** two-sided t on 31 df; **Holm across four tests** (2 models x 2
  hypotheses). A rejection in the predicted direction (H1 Delta > 0; H2 Delta < 0) reads **steerable**;
  in the other direction, **opposite**, reported.
- **Equivalence family (alpha = 0.05):** TOST at +/-0.10 on Delta, Holm across the four.
- **The study is powered for Delta = 0.10** (section 8). Labels per model and hypothesis:
  - **steerable:** efficacy rejected in the predicted direction;
  - **not steerable within +/-0.10:** equivalence rejected, efficacy not, and the method check passed;
  - **inconclusive:** anything else. **A null on an effect smaller than 0.10 is inconclusive, not "not
    steerable"**; a failed method check also makes a null inconclusive.
- **Naturalness:** cos(v_L\*, mean of (h_full - h_reversed) at the first generated token at L\*), and
  cos(v_L\*, the last-token shift on the evaluation categories, out of sample). Reported.
- **Effect relative to the note:** Delta / (s_full - s_reversed) from the unsteered references.
- **Missing data:** section 7a. In the primary analysis a target whose steered or placebo lie is
  missing drops out of that category's Delta_k (pairwise); a category with no complete pair drops out,
  and the df fall accordingly.

## 7a. Failed cells, balance check and tipping point

- **Cell:** one lie (category x target x arm). Arms graded in Phase 2: stage-2 steered and placebo
  (per model x hypothesis), the unsteered references (placebo, full, reversed note), and the method
  check's steered and placebo lies.
- **Generation failures** (no lie returned after the pod's retries) and **non-viable lies** are as in
  section 6 (coherence gate) and the reversed-note study; they are counted separately from grading
  failures.
- **Grading, transport:** a call that returned no answer (network, HTTP 429/5xx, overloaded) is
  retried with backoff (5, 15, 45, 90, 180 s) and does not count as an attempt.
- **Grading, answer:** an answer that the frozen parser rejects (including a missing tool call or a
  refusal) is retried; **after 3 attempts the cell is failed.** A failed cell has no primary score and
  is missing. **No substitute grader and no other route** (OpenRouter is never used as a fallback).
- **Counts:** failed cells, generation and grading separately, are reported by model x hypothesis x arm.
- **Balance check (pre-registered):** per model x hypothesis, an exact multinomial test of equal
  grading-failure probability across three arms: steered, placebo, and the unsteered reference of that
  hypothesis (the reversed note for H1, the full note for H2). Monte Carlo, 100,000 draws, seed
  20261026; also pooled over models. p < 0.05 flags "grading failures imbalanced across arms"; that
  result is then read together with its tipping point. Not a gate; it changes no decision (as in the
  reversed-note study). The method check's two arms are reported as counts.
- **Tipping point for the primary contrast,** per model x hypothesis, over all missing stage-2 steered
  and placebo cells (failed generation or grading):
  - impute every missing steered lie at s_steered - delta and every missing placebo lie at
    s_placebo + delta in the predicted direction of the hypothesis (H1: against a rise, so steered down
    and placebo up; H2: steered up and placebo down), with each arm's observed mean, clipped to [0, 1],
    and recompute every Delta_k over all five targets;
  - report the smallest delta that changes the label of section 7 (steerable / not steerable within
    +/-0.10 / inconclusive), and the same in the opposite direction;
  - also report the worst case (H1: missing steered at 0, missing placebo at 1; H2: the reverse).

## 8. Power and sample size

The identity runs give the per-category SD of the difference between two independent sets of lies
(5 targets each), the structure of steered vs placebo: 0.118-0.140; the worst case 0.14 is used.
K = 32, two-sided t on 31 df, Holm across four (the first test at 0.0125, the last at 0.05).

| true Delta | power at 0.0125 (first Holm test) | power at 0.05 (last) |
|---|---|---|
| 0.05 | 0.28 | 0.50 |
| 0.075 | 0.65 | 0.84 |
| **0.10** | **0.91** | **0.97** |
| 0.125 | 0.99 | 1.00 |

- Minimum detectable effect at 80% power: 0.088 at 0.0125; 0.072 at 0.05.
- TOST at +/-0.10: power 0.90 / 0.97 when the true Delta is 0; 0.74 / 0.90 at 0.025; 0.37 / 0.63 at
  0.05. A small true effect is therefore likely to end inconclusive, as section 7 states.
- **Assumption about the placebo:** the covariance-matched placebo does not itself move s beyond
  sampling noise. In the pipeline's item 6b on Gemma 3 27B, covariance-matched placebos moved behaviour
  (median dP 0.161 against about 0 for isotropic ones). If the placebo moves s in the predicted
  direction, the contrast Delta shrinks by that amount and power falls accordingly (for example, a
  0.10 effect against a placebo that moves s by 0.025 has the power of a 0.075 effect: 0.65 / 0.84).
  The placebo's own shift relative to the unsteered references is reported.
- For scale, the reversed-note B was 0.24 (Llama) and 0.43 (Gemma).
- The SD above comes from OpenRouter-graded identity lies; Phase 2 grades directly (section 11). The
  route's offset (fewer positive labels) is assumed not to change that SD materially; the observed
  per-category SD of Delta is reported.

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

## 11. Grading route (decided) and cost

**Route (decided 2026-10-22 by the grading-route check, `results/phase2/grading_route/RULES.md`).**
- **All Phase 2 grading goes through the Anthropic API directly:** the stage-2 steered and placebo
  lies, the unsteered references, and the method check's steered and placebo lies (the pilot is not
  graded). **No Phase 2 contrast mixes routes**, and no Phase 2 lie is graded on OpenRouter.
- **Call** (`src/perfect_lie/grader_direct.py`): Messages API, model `claude-sonnet-4-5` (the returned
  model string is recorded; the check returned `claude-sonnet-4-5-20250929`), temperature 0, max
  tokens 2000, no extended thinking, `anthropic-version: 2023-06-01` (pinned: later API versions
  reject `temperature`). The frozen rubric v0.6 prompts (`grader_input_from_record`) and parser
  (`parse_grader_output`) are unchanged.
- **Schema enforcement:** the frozen schema (`grader_response_format`) is sent as a forced tool call
  (`cue_annotation`) with **`strict: true`**, so the answer is decoded to the schema. Strict mode does
  not accept numeric bounds, so `minimum` / `maximum` are dropped from the copy sent to the API; the
  frozen parser still enforces them and fails closed. If the API rejects the strict tool (HTTP 400) on
  the first call, the run switches to the non-strict forced tool (the check's form) for **every** cell,
  never per cell, and this is reported. Failures: section 7a (3 attempts, then the cell is failed).
- **Check result** (50 identity-check pod lies; `regrade_direct.json`, commit d09a144): 49 parsed (one
  Llama reversed-note lie failed 3 attempts, each time omitting the `self_deprecation` key; the check
  did not use `strict`). Against the stored OpenRouter grades:

  | pooled | labels | agreement | kappa |
  |---|---|---|---|
  | all cues (decision basis) | 784 | 96.2% | **0.915** |
  | cues that enter s | 539 | 97.0% | 0.919 |

  Kappa >= 0.90, so the rule selects the direct route. Twelve of the 16 cues fall below one of the two
  thresholds on their own and are flagged, not decisive (RULES.md): document_citation,
  historical_anchor, official_failure, first_person_witness, sensory_detail, mundane_aftermath,
  mechanism_explanation, emotional_appeal, hedged_claim, self_deprecation, skeptic_acknowledgment,
  humor (the last four have 1 to 6 positive labels in the sample).
- **Measured offset: the direct route marks fewer cues present.** Over all cues, 273 positive labels on
  OpenRouter against 259 direct (-5.1%; of the 30 disagreeing labels, 22 are OpenRouter-only and 8
  direct-only). Over the cues that enter s, 136 against 122 (-10.3%).
  - Within Phase 2 every arm is graded on the same route, so the offset does not enter Delta or any
    confirmatory test.
  - **Any comparison of Phase 2 lies with OpenRouter-graded lies carries this offset:** the identity
    check, the reversed-note (behavioral) study and the first study. Such comparisons are descriptive
    only, labelled with the route difference, and are not confirmatory.
- Disclosure: strict decoding was not part of the check (it used the non-strict forced tool). Strict
  mode constrains the answer's form; its effect on the labels is untested.

**Cost estimate.**

Measured rates (RTX PRO 6000 Blackwell, bf16, batched): Gemma about 12 lies/min, Llama about 36
lies/min; grading about $0.013 per lie (primary grader; the same per-token price on either route).

| item | per model | both models | cost |
|---|---|---|---|
| stage 1 pilot (2 hyp x 5 alphas x 2 vectors x 8 categories x 5 targets; coherence only) | 800 | 1,600 | GPU only |
| stage 2 confirmatory (1 alpha x 2 hyp x 2 vectors x 32 x 5) | 640 | 1,280 | graded |
| stage 2 unsteered references (3 conditions x 32 x 5) | 480 | 960 | graded |
| method check (2 vectors x 16 x 5) | 160 | 320 | graded |
| **GPU** (generation, extraction under four wordings, perplexity scoring, loads) | | about 4.9 h | **about $12** |
| **grading** (2,560 lies) | | | **about $33** |
| **total** | | | **about $45** |

The RunPod balance ($37.03) covers the GPU line. The grading line is billed to the owner's Anthropic
credits (direct route). The grading-route check itself cost about $0.80 (164,966 input and 20,135
output tokens).

## 12. Decisions

No open decisions remain.

- **Grading route (decided 2026-10-22):** the Anthropic API directly, for all Phase 2 grading
  (section 11). The check's rule (switch if kappa >= 0.90 or label agreement >= 97%) was met by kappa
  0.915 (agreement 96.2%).
- **Grader failures (owner, 2026-10-22):** strict schema enforcement; 3 attempts, then the cell is
  failed; counts by arm, a balance check and a tipping point (section 7a).

Decided (revisions 2 and 3): two-stage design; one confirmatory alpha per model x hypothesis, the
largest coherent pilot alpha; Holm family of four; K = 32; powered for Delta = 0.10, a smaller-effect
null is inconclusive; covariance-matched placebo only; pilot checked for coherence only; the
identity-check stack with the pipeline as a library; the method check.
