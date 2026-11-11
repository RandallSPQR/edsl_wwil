# Tiers 1-3 (optional)

Tier 0 (`make reproduce`) is the reproduction: the same records, code and environment give every released number.
The tiers below make new model calls. None of them was run for this release; costs are the study's logged spend or
estimates from it. Each script is a dry run by default and refuses to spend without an explicit cap.

| tier | what it re-does | kind | needs | logged / estimated cost | script |
|---|---|---|---|---|---|
| 1 | grading of the released lies | re-measurement (same lies) | Anthropic API key | ≈ $27 study 1, ≈ $55 reversed, ≈ $36 Phase 2 (all lies; `--fraction` for less) | `tier1_regrade.py` |
| 2 | the lies themselves (studies 1 and 2), with grading and analysis | **replication, not reproduction** | OpenRouter key, EDSL environment | logged $63.73 (study 1 interim), $69.44 (reversed, incl. comprehension); runner estimates print first | `tier2_replicate.sh` |
| 3 | Phase 2 on the open weights: activations, probe, steering, NLL | re-computation on new hardware | one 96 GB GPU (RTX PRO 6000 Blackwell used), HF access to both gated repos, RunPod or similar | logged ≈ $16.5 of pod time (below; identity check not itemised) + Tier 1 grading ≈ $37 | `tier3_gpu.md`, `tier3_fetch_volume.sh` |

## Tier 1: re-grade the released lies

```
python release/tiers/tier1_regrade.py --study reversed --fraction 0.10                 # sample and cost, no calls
PL_GRADER_KEY=... python release/tiers/tier1_regrade.py --study reversed --fraction 0.10 --go --cap-usd 8
```

Output: `build/tier1/<study>/regrades.jsonl` and `agreement.json` (per-cue and pooled kappa against the released primary
grades). Re-running an analysis on the new grades is a further, separate step (replace `grades.primary.cues` in a copy
of the records and run the study's `run_final.py`).

Caveats:
- **API model drift.** The grader id `claude-sonnet-4-5` resolved to `claude-sonnet-4-5-20250929` in Phase 2
  (`models_returned` in every grade). A later call may be served by a different snapshot or refused if the model is
  retired; the script records `models_returned` for every lie.
- **Route.** Studies 1 and 2 were graded through OpenRouter (`anthropic/claude-sonnet-4.5`), Phase 2 directly. Tier 1
  uses the direct route; the route check measured kappa 0.915 between them on 49 lies.
- **Non-determinism.** Grades at temperature 0 are not bit-stable; expect kappa well below 1 on a few cues
  (the Phase 2 route check's lowest per-cue kappa is in `regrade_direct.json`).
- The second graders (gemini-2.5-flash through OpenRouter, gpt-5) are not re-run by this script; the same caveats
  apply with more force (no dated snapshot ids for either).

## Tier 2: replication (new lies)

Tier 2 generates new lies from the same instrument, prompts, notes, models and provider pins, then grades and
analyses them with the registered code. **It is a replication, not a reproduction**: sampling at temperature 0.6 gives
different lies, the API models may have changed, and the outcome is a new estimate with its own uncertainty, to be
compared with the released one, not matched to it.

```
release/tiers/tier2_replicate.sh             # environment check and both runners' dry runs (cost estimates; no calls)
```
The live commands it prints use the runners' own cost guards (`--confirm-spend`, `--cap`); run them only with an owner's
budget. Needs the EDSL environment (`requirements_review.txt` install notes) and an OpenRouter key.

Caveats:
- **Retired or changed models.** gpt-4o-mini, Gemini 2.5 Flash-Lite, gemini-2.5-flash and gpt-5 have no frozen
  snapshot on OpenRouter; any of them may be retired or silently updated. The open-weight liars were pinned to a bf16
  provider (CoreWeave for Llama, as recorded in each lie's `liar_served_provider`); that provider may no longer serve
  them, and a different provider or quantization is a different model for this purpose. The runners refuse fallbacks,
  so an unavailable pin fails cells rather than substituting.
- **Registered gates still apply.** A replication must re-run the agreement gate on its own grades (the gate is fresh
  per study), so the scored cue set can differ.
- **Study 1 stopped at its interim**: a faithful replication runs the same two-look design, which may also stop early
  or extend.

## Tier 3: Phase 2 on GPU

See `tier3_gpu.md` for the command sequence (all drivers are in `two_truths_lie/results/phase2/probe/`; each has
`pod-up`, a run step and `pod-down`, a watchdog and a spend cap). Logged pod time and cost (RTX PRO 6000 Blackwell,
EUR-IS-1, $2.49/h):

| step | pod time | logged cost |
|---|---|---|
| identity check generation (two runs) | not itemised in the log | — |
| probe stage (activations for 1,800 items per model, probe) | ≈ 18 min | ≈ $0.56 |
| Addendum 3 diagnostics | ≈ 6 min | ≈ $0.28 |
| stage-1 pilot | ≈ 2 h | ≈ $5.1 |
| Addendum 5 placebo rerun | ≈ 57 min | ≈ $2.40 |
| method-check pre-check | ≈ 27 min | ≈ $1.12 |
| stage-2 generation, NLL, naturalness | ≈ 2 h 49 min | ≈ $7.05 |
| stage-2 grading (Tier 1 route) | API | ≈ $36.53 direct + $0.61 OpenRouter |

Caveats:
- **Hardware and software.** Activations, NLLs and sampled tokens were computed in bf16 with torch 2.8.0.dev20250319
  (cu128) and transformers 4.53.2 on one RTX PRO 6000 Blackwell. Another GPU, driver, torch build or batch size changes
  bf16 reductions, so activations agree only approximately and seeded sampling diverges after a few tokens; steered
  lies will differ. The probe's AUROC and the steering contrasts are expected to agree within their intervals, not to
  the digit. The exact hook check (Addendum 4) is bitwise on one setup; re-run it on yours.
- **Weights.** Pin the revisions in `dataset/hf_revisions.json` (`revision=` in `from_pretrained`); both repositories
  are gated (licence acceptance).
- **Not released**: the activations themselves (1,800 items x 62 x 5,376 for Gemma, x 32 x 4,096 for Llama: about 2.4 GB
  and 0.9 GB in float32) and the placebo and method-check vectors. They stay on the study's RunPod network volume;
  `tier3_fetch_volume.sh` describes how to retrieve them (about $0.10 of pod time; not run for this release). With
  them, the probe, diagnostics and setup files become CPU-reproducible.
