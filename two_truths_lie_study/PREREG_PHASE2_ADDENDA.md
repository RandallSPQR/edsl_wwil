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
