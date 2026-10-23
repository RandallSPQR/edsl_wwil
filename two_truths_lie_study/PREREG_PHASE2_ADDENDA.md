# The Perfect Lie, Phase 2: addenda to the pre-registration

The registration is `PREREG_PHASE2.md`, frozen at the tag `perfect-lie-phase2-prereg-v1` (commit `bc1c179`) and
posted on OSF. It is not edited; changes and the hashes it defers are recorded here, dated, in order.

## Addendum 1 (2026-10-22): probe-stage code, before any activation is extracted

Written after the OSF post and before any pod has run for Phase 2. No activation exists. The registration's
frozen-file section requires the probe code to be committed and hashed before it is used. This addendum does that,
and fixes the mechanical details the registration leaves open. None of them changes a rule of section 4.

**Code and data (sha256 below).**
- `results/phase2/probe/items.py` builds the category split and the probe items (`category_split.json`,
  `probe_items.jsonl.gz`).
- `src/perfect_lie/phase2_probe.py` is the section 4 analysis: the direction, the two transfer tests, the
  cue-mention control, the logistic probe (reported only) and the layer rule. It imports the pipeline's transfer
  rule (`probe.transfer.auroc`, `cluster_boot`, `verdict`: AUROC >= 0.70 and 95% lower bound > 0.50) and its
  logistic probe (`probe.train.fit_logistic`, `cv_score`) from sae-ethos-pipeline v1.1.0 (tag `v1.1.0`, commit
  `94a785c15ec8c3207cb1fbd4a5c321309f07eecb`).
- `results/phase2/probe/pod_server_phase2.py` imports the frozen identity-check server (`pod_server.py`,
  unchanged) and adds extraction and analysis endpoints. Loading and rendering are the frozen code.
- `results/phase2/probe/probe_stage.py` is the driver (pod lifecycle, extraction, analysis, download).
- `tests/test_phase2_probe.py` tests the analysis on simulated activations: null, shared valence, a signal only in
  the frozen wording, a signal missing in one paraphrase set, a signal specific to each persona, sign, the control
  in both directions, the layer rule and its tie, multi-layer selection, determinism, pairing errors. It also checks
  the committed items.

**Fixed details.**
1. **Category split (section 3):** `random.Random(20261023).sample(sorted(final_72), 32)` are the evaluation
   categories; the other 40 are the training categories. The lists are in `category_split.json`.
2. **Items (section 4):** for each model, the 40 training categories x 5 targets. There are full and reversed
   items in the frozen wording and in paraphrase sets A, B and C, plus placebo items in the frozen wording only.
   That is 1,800 items per model.
   - The frozen items are the exact messages the model received in the reversed-note run
     (`liar_delivered_messages`; identical across replicates, checked).
   - A paraphrased item replaces the header line and the target's four belief lines with the set's lines. Each
     frozen line occurs exactly once (checked).
3. **Paraphrase repair (a deviation from the hashed file's bytes, declared here).** The frozen
   `paraphrase_sets.json` writes "well- known" for "well-known" in the two `historical_anchor` lines (P1, P5), in
   all three sets. This is a detokenizer artifact of `paraphrases.py`; its lint compares tokens, so it did not
   catch it. The item builder restores "well-known". It then checks, for every substituted line, that the
   paraphrase equals the frozen line character for character outside the valence spans. This is what section 5
   states the sets do; without the repair, those notes would differ in one non-valence character.
4. **Layers:** L is the 0-based decoder block index. The activation is the block's output, i.e. the residual stream
   after block L, read by a forward hook. On the first item of every shard, the hook output is checked to equal
   `hidden_states[L + 1]`. Candidates are Gemma 21-41 (blocks 0-61) and Llama 11-21 (blocks 0-31), as in section 4.
   The pod's block count is checked before extraction (62 and 32).
5. **Extraction:** one unpadded forward pass per item (batch 1, bf16, no cache), with the renderings of section 2
   (`render` of `pod_server.py`: Llama without the date header, Gemma without the final newline).
   - The last prompt token's block output is recorded at every layer.
   - The mean over the tokens overlapping the note's belief lines is also recorded at every layer (reported, never
     used for selection).
   - Activations are stored as float32 on the network volume.
6. **Tests:**
   - **(a) Held-out personas:** for each target, v from the other four targets' frozen pairs. The held-out target's
     frozen full and reversed items are scored by projection, and the scores are pooled over the five folds.
   - **(b) Held-out wordings:** v from all five targets' frozen pairs; AUROC on each set's full and reversed items.
   - Full is the positive class.
7. **Bootstrap:** the pipeline's `cluster_boot` with clusters = categories, 2,000 resamples and **seed 20261027**
   (the pipeline's default seed is 0). The control's 90% interval uses the same resampling, 5th and 95th
   percentiles.
8. **Logistic probe (reported only):**
   - C is chosen once per layer from {0.01, 0.1, 1, 10} by the pipeline's 5-fold `cv_score` (seed 0) on all frozen
     training pairs, and reused within the held-out-persona folds.
   - The direction is w / sigma in raw units, unit-normalised.
9. **Record:** v_L and c_L at every layer (frozen wording) are saved with the results (`vectors.npz`), beside the
   per-layer table (`probe_result.json`, `PROBE.md`). The gate result is committed before any steered lie exists.
10. **Compute:** both models are extracted on one pod in EUR-IS-1 (the network volume with the weights), image
    `runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04`, transformers 4.53.2. Package versions and
    the GPU are recorded in `extract_log.json`.
    - Spend cap for the probe stage: $8 of RunPod.
    - A local watchdog and the pod's own timer (2.5 h) terminate the pod; the pod is terminated when the work ends.

**Hashes (sha256, files under `two_truths_lie/`).**

| file | sha256 |
|---|---|
| `results/phase2/probe/items.py` | `63b9f907f46c17fcd33d4a1be84004c2f9fbc7f02abc45133f098ab3c85c9454` |
| `results/phase2/probe/category_split.json` | `d4cbfcb4bb52adaf457c6d7da088effb2726ab95f1f59af7f97ad3ae7b390058` |
| `results/phase2/probe/probe_items.jsonl.gz` | `3c69888b8e9e3b1f20a2360f93f43f5415b2814d371fe64ec7a423a105caca11` |
| `src/perfect_lie/phase2_probe.py` | `81eb0e968d215ef14a05a9e62f67ddbe5409dd0070a9016ef3e85ab6c1edeb16` |
| `results/phase2/probe/pod_server_phase2.py` | `b1b30ae08fc7ddb14239a306142180cff6211d147a4be39f7babd5eb9e11854a` |
| `results/phase2/probe/probe_stage.py` | `3b594ef93c3583077bd6f9b61e77d1d8cd8cd487b2f2dea75ad7ae2f99517232` |
| `tests/test_phase2_probe.py` | `3b4cf86b1f1710aee67fb766078918b0e1004f0b84d8dea45652f439c07eb944` |
| `results/phase2/identity_check/pod_server.py` | `f2897167b8c2720985e8e85a1b09f5087e92f7e46c5749cb768a97c295fdf868` |

`pod_server.py` is listed to show it is unchanged from the registration's table.

Revised before any pod ran (2026-10-22): `probe_stage.py` now passes `HF_TOKEN` to the pod when it is set (Llama 3.1
8B is gated and may not be on the volume), tries the GPU types in order (RTX PRO 6000, A100 SXM 80 GB, A100 PCIe
80 GB, H100 PCIe: each stays under the $8 cap for 2.5 h) and can retry until one is free. Its hash above is the
revised file's. No rule or analysis changed.

## Addendum 2 (2026-10-22): a second, non-Claude grader on a 20% subsample (descriptive)

Owner's request, 2026-10-22. Written during the probe stage, before any steered lie or stage-2 reference lie exists
and before any Phase 2 lie is graded. It adds one descriptive grader-robustness analysis. **The primary grader, the
primary analysis (section 7), the Holm families, the labels and the stop rules are unchanged**; nothing in this
addendum can change a label.

The owner asked for this to be added to the freeze before posting. The registration was already posted on OSF (tag
`perfect-lie-phase2-prereg-v1`, commit `bc1c179`), so it is recorded here as an addendum, as the registration
requires, and posted on OSF before any Phase 2 lie is graded.

**Why.** Every Phase 2 cue label comes from one grader (Claude Sonnet 4.5, direct route). A second grader from
another family, on a subsample, shows whether the steered-minus-placebo contrast depends on that grader.

**Grader.** Google `google/gemini-2.5-flash`, the reversed-note study's gate grader, with the same settings:
OpenRouter, temperature 0, reasoning disabled, max output tokens 2000, the frozen rubric v0.6 prompts
(`grader_input_from_record`), the frozen schema as `response_format` (`grader_response_format`, json_schema, strict)
and the frozen parser (`parse_grader_output`). Failures: 3 attempts, then that lie has no Google grade (no
substitute grader). Grading failures are counted by model x hypothesis x arm.
- **A declared exception to section 11's "no Phase 2 lie is graded on OpenRouter".** That rule protects the primary
  grading route, and it still holds for every primary label. The Google labels are a separate, descriptive
  measurement and are never mixed with primary labels in a contrast.
- **Family overlap, stated now:** the Google grader shares a family with the Gemma 3 27B liar (not with Llama), so
  agreement on Gemma is weaker evidence of grader-robustness than agreement on Llama.

**Subsample (seeded, stratified, 20% of every graded arm).** `results/phase2/grader_robustness/subsample.py`
(seed **20261028**) assigns one target to each of the 32 evaluation categories: the categories in a seeded order
are given the five targets in turn. That is 32 of the 160 (category, target) cells, i.e. 20%, stratified by category
(exactly one cell each) and by target (6 or 7 cells each). The list is in `subsample.json`.
- The **same cells** are used for both models, both hypotheses and every graded arm: stage-2 steered and placebo
  lies, the unsteered placebo, full and reversed references, and the method check's steered and placebo lies (on
  those of its 16 categories that are in the list). So every steered lie in the subsample has its placebo pair.
- Every lie in those cells that the primary grader grades is also sent to the Google grader. The pilot is not
  graded, so it is not included.
- Size: per model, 2 hypotheses x 2 arms x 32 + 3 references x 32 + 2 method-check arms x (the method-check
  categories in the list) = at most 256 lies; at most 512 for both models. Cost about $0.002 per lie on
  OpenRouter, under $2 in all.

**Analysis (descriptive; reported beside the primary, after unblinding).** s is computed exactly as for the
primary (the same scorable cues), from the Google labels.
- Per model x hypothesis: d_k = s_G(steered) - s_G(placebo) for the subsample's cell in category k; the mean over
  the categories with a complete pair, with a 95% t interval on K - 1 df. **Beside it, the same contrast from the
  primary grader on the same cells**, so a grader difference is not confounded with the subsample, and the primary
  Delta on all 160 cells.
- The same for the method check (v_fp vs its placebo), and for the references: s_full - s_reversed and each
  steered and placebo arm's shift relative to the unsteered placebo reference.
- Per-cue agreement between the primary and Google labels on the subsample (Cohen's kappa, all cues and the
  cues that enter s), by model.
- No test, no Holm family and no label. A sign or size difference between the graders is reported as found.
- **Blinding:** the Google labels are not read before unblinding (section 10); they are graded with the primary
  labels and stored without being summarised.

**Code.** The grading call and this analysis are committed, tested on simulated data and hashed in a later dated
addendum, before any stage-2 lie is graded, as section 10 requires for analysis code.

**Hashes (sha256, files under `two_truths_lie/`).**

| file | sha256 |
|---|---|
| `results/phase2/grader_robustness/subsample.py` | `4a33f82ba7163de4c4482744b451270f7ee3f2a7d70b4dd01a0cdca753deed34` |
| `results/phase2/grader_robustness/subsample.json` | `71a92a9c03fcd3ede46eca2c7b17195947b6f45461f2c023b270d27a5701c600` |

## Addendum 3 (2026-10-22): probe-stage diagnostics, before the dose-finding pilot

Owner's request, 2026-10-22. Written after the probe stage (results commit `46eebf5`: both models pass; Gemma 3 27B
at layer 35, Llama 3.1 8B at layer 12) and before any diagnostic below is computed, any steered lie is generated or
any Phase 2 lie is graded. **The gate decisions and the layer choices stand as registered**; nothing in this addendum
changes them.

**1. The cue-mention control is uninformative by design (recorded; not replaced).**
- Every placebo item is byte-identical to another target's full item: the placebo note of a target is another
  persona's full note (the cycle P1->P2->P3->P1, P5<->P6), and the prompt never names the target (400 of 400 placebo
  items, both models). The placebo items are therefore the full items relabelled, their mean activation equals the
  full items' mean, and c_L = -v_L / 2 exactly at every layer. The control's AUROC (about 0) and cos(v, c) = -1
  follow by construction and say nothing about the instrument.
- The concern the control addressed, a cue-mention confound, is excluded by construction: full and reversed notes
  name identical cues with the same cue words (the registered word-level lint). The concern that the direction
  tracks the frozen valence words rather than valence is addressed by the held-out-wording transfer (section 4).
- The control stays in the reported tables (as committed), labelled uninformative. It was never part of the stop
  rule.

**2. Diagnostics on the stored activations (one short pod session, cap $3 of RunPod).** Code below, hashed; run on
the last-token activations already on the network volume (`/workspace/phase2/probe/<slug>/`). No model is loaded.
- **(a) Label-permutation null.** At the selected layer and its two neighbours (Gemma 34, 35, 36; Llama 11, 12, 13),
  both models, 1,000 permutations (seed **20261029**).
  - One permutation shuffles labels within persona at the pair level: the full and reversed labels of each
    (category, target) pair are swapped with probability 1/2, and the same swap is applied to that pair in every
    wording (frozen, A, B, C).
  - The registered held-out-persona test and the three held-out-wording tests are recomputed under the permuted
    labels. The direction is the difference of the labelled-full and labelled-reversed means, which with the true
    labels is the registered direction.
  - **Why pairs, not a free shuffle of a persona's 80 labels:** a free shuffle can put both items of a pair on one
    side. The two items share everything but the valence words, so the null would then measure item content, not
    the test. In simulation (pairs sharing a large content component), the free shuffle put the wording-test null
    mean near 0.73 and the pair-level shuffle near 0.52. Every registered test compares complete pairs, and the
    pair-level shuffle keeps that.
  - Reported per model x layer x test: the null distribution (mean, SD, 2.5% / 50% / 97.5% quantiles, max), the
    observed AUROC and the permutation p = (1 + #{null >= observed}) / 1,001. The observed AUROC is recomputed by
    this code and checked against the registered value.
  - **Stop rule:** if the mean null AUROC of **any** reported test (model x layer x test, 2 x 3 x 4 = 24) lies
    outside [0.40, 0.60], the diagnostics are reported and **the pilot is not run**. A mismatch between the
    recomputed and the registered observed AUROC is reported, and the pilot then waits for the owner.
- **(b) Within-fold persona AUROC (descriptive).** Every candidate layer, both models. For each held-out target:
  the registered fold direction (v from the other four targets), and the AUROC of that target's frozen full vs
  reversed projections only, with the registered cluster bootstrap (95%, clusters = categories, 2,000 resamples,
  seed 20261027). Reported beside the registered pooled figure, with each fold's mean projection on unit v per
  class. No rule.
- **Compute.** One pod in EUR-IS-1 with the same network volume, image and installs as Addendum 1. The driver
  refuses a pod whose hourly price x watchdog hours (1 h) exceeds $3. The pod's own timer and a local watchdog
  terminate it, and it is terminated when the work ends.

**3. Exception approved (owner, 2026-10-22).** The Google-grader subsample of Addendum 2 (descriptive only) is graded
through OpenRouter. All primary grading stays on the direct Anthropic route of section 11.

**Hashes (sha256, files under `two_truths_lie/`).**

| file | sha256 |
|---|---|
| `src/perfect_lie/phase2_diagnostics.py` | `d6e668b034af92094414a002f8c41486d18268ddcfb61ec8965b208e626d9984` |
| `tests/test_phase2_diagnostics.py` | `5b301e475922b250283f112bc3d8cb9475c8913b1bd8ff1c3102149468d19df1` |
| `results/phase2/probe/pod_server_phase2_diag.py` | `15ba30a49e6c8a320b83a127e53b9d7a9b95d6ac7ec3efe06b9c87f88d428454` |
| `results/phase2/probe/diag_stage.py` | `d9b18427e14608e82561313fc93c07314d9aceb277d6adb6ed005a38d3624404` |

The tests replace the pipeline's AUROC and cluster bootstrap with plain implementations, so they run without the
pipeline (8 pass). On the pod, the pipeline's own functions are used. The probe-stage files of Addendum 1 are
imported unchanged.

## Addendum 4 (2026-10-23): stage-1 pilot code and the coherence details, before any steered lie exists

Owner's go for the pilot, 2026-10-23, after Addenda 2 and 3 were posted on OSF. Written and hashed before any
steered lie is generated. Section 6 requires the pod server's steering extension to be committed and hashed by a dated
addendum before it is used. This addendum does that and fixes the mechanical details that section 6 leaves open.
**The design, the coherence thresholds and the alpha rule are unchanged.**

**Before the pilot (descriptive, committed `fba75e6`).** At the selected layers, per-persona residual norms differ by
1.02x (Gemma) and 1.01x (Llama). The alpha = 1 step is 4.0-4.1% (Gemma) and 3.7% (Llama) of every persona's residual
norm. Gemma's per-persona full - reversed gap on unit v differs by 2.98x (Llama 1.29x). Alpha stays as section 6
defines it (unit(v) x alpha x ||v||); a residual-norm-relative alpha would rescale every persona by the same constant.

**Fixed details.**
1. **Categories:** `random.Random(20261025).sample(sorted(training_40), 8)` = business, electricity, film, kites,
   knots, mathematics, mining, music. x 5 targets = 40 items per hypothesis.
2. **Items:** the probe stage's frozen-wording items (the exact messages of the reversed-note run, Addendum 1): the
   reversed note for H1, the full note for H2. Renderings as in section 2.
3. **Vectors** (layer L\* = Gemma 35, Llama 12):
   - Steered: unit(v_L\*), the probe stage's v (`vectors.npz`).
   - Placebo: pipeline `probe.vectors.placebo_cov(Xc, seed)`. Xc is the centred last-token block-L\* outputs of the
     400 frozen full and reversed training items. Seed **20261030** (Gemma) and **20261031** (Llama). One placebo
     per model, used for both hypotheses and every alpha, and saved for stage 2.
   - Added vector: sign x alpha x ||v_L\*|| x unit(d), with sign +1 for H1 and -1 for H2, for both the steered and
     the placebo direction.
   - It is added by a forward hook on decoder block L\* to the block's output at every position, prompt and
     generated (padding positions too; they are masked from attention).
   - Before generation, one prompt per model and vector is checked at the alpha = 1 coefficient, or the run stops.
     The checks are exact (bitwise, in the block's bf16): the hook's output equals its input plus the added vector;
     the model carries that output forward (hidden_states[L\* + 1]); the hook saw every prompt position; and block
     L\*'s input is unchanged by steering (relative difference < 1e-3). The steered minus unsteered
     hidden_states[L\* + 1], compared with the intended vector, is recorded as the precision of bf16 steering (see the
     revision notes below).
4. **Generation:** the frozen `generate_batch` of the identity check, run inside the hook. Temperature 0.6, top_p 0.9,
   top_k off, max 1,500 new tokens. Batches of 12 (Gemma) and 24 (Llama), as in the identity check. Batch seed =
   20261032 + 100,000 x model index (Gemma 0, Llama 1) + 10,000 x hypothesis index (H1 0, H2 1) + the batch's first item
   index. The seed is shared by the steered, placebo and unsteered batches of a hypothesis at every alpha (common
   random numbers).
5. **Unsteered continuations (added; needed by the perplexity criterion).** Per model and hypothesis, the same 40
   items unsteered (alpha 0), with the same seeds: 80 lies per model, on top of the registered 800. They are not
   graded.
6. **Coherence measures**, per model x hypothesis x alpha, computed for the steered and for the placebo lies (40 each):
   - **Viability:** the frozen `scoring.lie_viability`, with the prompt's word range (300-400, slack 0.2). A lie
     fails if it is flagged too short, too long, truncated by the output cap or degenerate (section 6: "word range,
     not degenerate"). Refusal language is counted and reported, not used. Rule: >= 95% viable.
   - **Perplexity:** per lie, the ratio exp(mean NLL of its first 64 generated tokens - mean NLL of the first 64
     tokens of the unsteered lie for the same item and hypothesis). Both NLLs are teacher-forced under the unsteered
     model (one unpadded forward pass). Rule: the median over the 40 lies <= 2.0. Section 6 says "median ratio", so
     this pairs each lie with its own unsteered continuation instead of pooling as the pipeline does.
   - **Repetition:** the pipeline's `rep4_share` on all of the lie's generated tokens, averaged over the 40 lies.
     Rule: <= 0.25. Section 6 does not limit it to 64 tokens; all tokens is stricter.
7. **Gate and alpha rule (section 6, unchanged):** an alpha is coherent for a model and hypothesis if the steered and
   the placebo lies both pass all three. The confirmatory alpha is the largest coherent grid alpha. With none, that
   model and hypothesis is untestable. The four alphas are committed before stage 2.
8. **Nothing is graded and no cue is scored.** Records (text, token ids, finish reason, NLLs) are kept for the record,
   under `results/phase2/pilot/<slug>/`. The pilot report shows coherence measures only.
9. **Compute:** one pod in EUR-IS-1 (network volume, image and installs as before). Cap **$8 of RunPod** for the
   pilot, within section 11's GPU line. The driver refuses a pod whose hourly price x watchdog hours (3 h) exceeds
   the cap. A local watchdog and the pod's own timer terminate it, and it is terminated when the work ends.
   Generation resumes batch by batch if a pod has to be replaced.

**Hashes (sha256, files under `two_truths_lie/`).**

| file | sha256 |
|---|---|
| `src/perfect_lie/phase2_pilot.py` | `640ebaf8af97658a346f800c914059a9367ac26d40ec5e79b818b0e12c8aaed8` |
| `tests/test_phase2_pilot.py` | `d236104fd94e6d64bd719e6d9e3ffc71d41cd3a82cfe4b048abe8b6aeb77e9f2` |
| `results/phase2/probe/pod_server_phase2_pilot.py` | `2b51e224397a02c165113ad83b4648e9ebaeaf589afd196b3ad51dc6b99cacf1` |
| `results/phase2/probe/pilot_stage.py` | `9c758764dda655eab4fe2413b77ddf99d23c0ec663b76c3fa8366e619dc435fa` |
| `results/phase2/probe/scale_stage.py` | `dd925139d0ffd6138a5db89ddf970cdc41ce2a0d9e387cc5e71ecaf984527d7c` |
| `results/phase2/probe/pod_server_phase2_scale.py` | `7d99c082d3120872aa34068035adab9065579592e46e6714c0692ddd054db5c7` |
| `src/perfect_lie/phase2_scale.py` | `3621358cf5d101c46e947bc3ff39aeff2ecc9041ca5d8421656de7fe8fae4698` |
| `tests/test_phase2_scale.py` | `39018771956e8c35592dfccc171863ca9186bf658de6f55e6a2fa8728d9e5544` |

The pilot server imports the probe-stage server (Addendum 1) unchanged. The pilot driver reuses the scale report's
driver for the pod's file list. The tests run without the pipeline (12 pilot tests, 2 scale tests pass). The
steering hook runs only on the pod, where the hook check above verifies it before use.

Revised before any steered lie (2026-10-23): the first pod run (pod `ht0a8t3cabu5ok`, Llama) stopped at the hook check
as specified. At alpha = 1 the measured displacement had a median relative error of 0.046 (max 0.15, at the
first-token position) and a minimum cosine of 0.989 (placebo: 0.048, 0.17, 0.985) against the 0.05 / 0.99 tolerance.
This is bf16 rounding, not a hook fault. The block output is bf16, so h + add is rounded to about 2^-9 of each element
of h. With ||add|| at 3.7% of Llama's residual norm, that is about 5% of ||add||, largest where ||h|| is largest. The
pipeline steers the same way. The mechanism check now runs at 100 x the coefficient, with a tighter tolerance. The
alpha = 1 figures are recorded in each model's `setup.json` and reported. Only `pilot_stage.py` changed (its hash
above is the revised file's). The pod server, the design, the measures and the rules are unchanged, and no lie had
been generated.

Second revision, before any steered lie (2026-10-23): the 100 x mechanism check also stopped the run. Median relative
error was 0.0024 and minimum cosine 0.9997, but the maximum was 0.023 (placebo 0.027) against 0.01, at one position.
The likely cause is bf16 rounding at the first token, whose norm far exceeds the others'. Rather than set a third
tolerance, the mechanism check is now exact (bitwise; above) and cannot fail through rounding. The error against the
intended vector is recorded, not tested. On the same pod, before it was terminated, the unchanged endpoints were
smoke-tested on two items with 40 new tokens: unsteered, steered and placebo generation, and NLL scoring. Nothing
from that smoke test is kept or used. The pod server and the driver changed (hashes above are the revised files');
the design, the measures and the rules are unchanged. Pod time so far: about 8 minutes.

## Addendum 5 (2026-10-23): a new placebo, and the placebo half of the pilot rerun, before stage 2

Owner's decision, 2026-10-23. Decided on coherence alone, after the stage-1 pilot (commit `7928d46`) and before any
stage-2 lie exists. No lie has been graded and no cue scored.

**Why.** Section 6's placebo (pipeline `vectors.placebo_cov` on the covariance of the training activations at L\*)
turned out aligned with the steering direction: cos(placebo, v) = 0.64 (Gemma) and 0.24 (Llama). The covariance of
the full and reversed training items includes the full - reversed difference, a large share of its variance. A
placebo carrying 0.64 of v's own component would leave the steered - placebo contrast with about a third of the
steering effect, if the effect is linear in the push along v.

**New placebo (both models; replaces the section 6 / Addendum 4 placebo).**
- H = the last-token block-L\* outputs of the 400 frozen full and reversed training items. Each condition is
  centred on its own mean (removes the full - reversed difference).
- p = pipeline `probe.vectors.placebo_cov`(that centred matrix, seed), with seed **20261033** (Gemma) and
  **20261034** (Llama).
- Any remaining v component is projected out: p <- p - (p . unit v) unit v. Then p is renormalised.
- Added vector: sign x alpha x ||v_L\*|| x unit(p), the same length as the steered vector at every alpha.
- Reported: cos(new placebo, v) after the projection (target 0; the run stops if |cos| > 1e-6), cos before the
  projection (after the centring alone), cos with the retired placebo, and the norm match (the run stops if it is
  not 1 to 1e-9).
- The retired placebo stays on the volume (`pilot_vectors.npz`); the new one is `pilot_vectors_v2.npz`.

**Rerun: the placebo half of the pilot only.** The same 8 categories x 5 targets, both hypotheses, alpha in {0.25,
0.5, 1, 2, 4}, the same batch seeds, generation settings and renderings. The exact hook check is run for the new
placebo before generation. The same coherence measures and gate are used (Addendum 4). That is 400 placebo lies per
model.
- The pilot's steered lies and its unsteered continuations are reused unchanged; the steered lies are not
  regenerated.
- **The registered alpha rule is re-applied** to the pilot's steered results with the new placebo results: per model
  and hypothesis, the largest grid alpha at which both pass.
- **The confirmatory alphas may change as a result** (in either direction) and are replaced by the rerun's. Those
  are the alphas committed before stage 2.
- **The old placebo is retired.** Its pilot results and the alphas they gave (Gemma 1.0 / 1.0, Llama 4.0 / 4.0) stay
  in the record as reported (`PILOT.md`, `pilot_result.json`). The rerun's are `PILOT2.md`,
  `pilot2_result.json` and `records_placebo2.jsonl`.

**Stage 2** uses the new placebo for every placebo arm, the method check's included. Section 6 re-applies the coherence
gate in stage 2 before any grading.

**Compute.** One pod as before. Cap **$4 of RunPod**. The driver refuses a pod whose hourly price x watchdog hours
(1.5 h) exceeds the cap. A local watchdog and the pod's own timer terminate it, and it is terminated when the work
ends.

**Hashes (sha256, files under `two_truths_lie/`).**

| file | sha256 |
|---|---|
| `results/phase2/probe/pod_server_phase2_placebo2.py` | `5644b7cc80af18000cb50be9c216b9068ce3f97f3d1ed2eec56837b406c59d32` |
| `results/phase2/probe/pilot2_stage.py` | `e7e0b6614fd1a2dbddfc937c6caf4b01b0297bcedde1c47f92d05d4f9e517c75` |

The new server imports the pilot server of Addendum 4 unchanged and points its vector lookup at the new file. The
driver reuses the pilot driver and `src/perfect_lie/phase2_pilot.py` (Addendum 4) unchanged. Before the run, the
driver's analysis was dry-run on the pilot's own records (it reproduces the pilot's result).
