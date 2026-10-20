# Phase 2 identity check (pod vs API): rules fixed before any outcome

Owner's rules, 2026-10-20, recorded before any pod or diagnostic call.

1. **Diagnostic (not a gate).** 20 prompts per model across conditions, temperature 0, on the pod
   and on the API with the same provider as the behavioral runs (Llama 3.1 8B: CoreWeave bf16;
   Gemma 3 27B: Novita bf16). Report the first divergence position per prompt. If most prompts
   diverge at token 1-2, check the chat template before anything else.
   - Selection: from `full_run/main/replay.jsonl` (the reversed-note run's open-weight lies,
     sha256 7e02f11e...), seeded (20261021), stratified 7 placebo / 7 full / 6 reversed per model.
     The exact delivered messages are sent to both sides; max tokens as in the run.
   - Divergence: both completions tokenised with the pod's tokenizer; first index where the token
     ids differ (none if identical). Prompt token counts (pod tokenizer vs API usage) reported as a
     template check.
2. **Behavioral equivalence.** Unsteered placebo, full and reversed on the pod, frozen instrument
   and sampling (temperature 0.6, top_p 0.9), on a seeded subset of categories, paired by category
   with the API lies of the reversed-note run.
   - Pass: TOST at +/-0.10 on the B difference (pod B - API B) AND on each condition's s
     difference.
   - Fail or inconclusive: Phase 2 uses pod-only references, and the write-up states that the API
     link is not established. Phase 2 is not blocked.
   - Category count: proposed below; the owner decides it before the subset is drawn.
3. **Disclosure of anything inspected.** Recorded here and carried into the pre-registration.
4. **Phase 2 primary references are the pod's own unsteered conditions in all cases.**

## What had been inspected when these rules were committed

- No identity outcome: no pod has run, no temperature-0 completion exists, no pod lie exists.
- From the replay export: counts (1,080 lies per model, 360 per condition), served providers
  (CoreWeave, Novita), checkpoint ids, temperatures (0.6), message roles (Llama system + user;
  Gemma one folded user turn).
- From the reversed-note run (already unblinded and published): per-category SDs used for the
  power calculation below.

## Power calculation for the category count (from the reversed-note run)

Per-category SD across the 72 categories (s = target-cue share, primary grader, gate as registered):

| model | B | s placebo | s full | s reversed |
|---|---|---|---|---|
| Llama 3.1 8B | 0.115 | 0.083 | 0.105 | 0.091 |
| Gemma 3 27B | 0.148 | 0.108 | 0.096 | 0.108 |

Assumption (conservative): Var(pod - API, per category) = 2 x observed variance of the category
means, i.e. all between-category variance is treated as sampling noise; true category effects would
cancel in the pairing. t on K - 1 df.

| K | widest 90% half-width | lowest single-test TOST power at true difference 0 (Gemma B) |
|---|---|---|
| 16 | 0.092 | 0.12 |
| 24 | 0.073 | 0.46 |
| 32 | 0.063 | 0.68 |
| 36 | 0.059 | 0.75 |
| 48 | 0.051 | 0.89 |
| 72 | 0.041 | 0.98 |

The pass requires four TOSTs per model to succeed together, so the joint power is below the
single-test figure.
