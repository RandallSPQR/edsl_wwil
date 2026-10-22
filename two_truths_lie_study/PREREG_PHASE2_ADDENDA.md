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
| `results/phase2/probe/probe_stage.py` | `fe4a7fee7a7702abba146c4f9eb32ba8e05e00293da6e1afc56cb13da378d462` |
| `tests/test_phase2_probe.py` | `3b4cf86b1f1710aee67fb766078918b0e1004f0b84d8dea45652f439c07eb944` |
| `results/phase2/identity_check/pod_server.py` | `f2897167b8c2720985e8e85a1b09f5087e92f7e46c5749cb768a97c295fdf868` |

`pod_server.py` is listed to show it is unchanged from the registration's table.
